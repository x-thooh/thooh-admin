"""secret: 凭据有没有跟着代码一起走出去。

  SEC001  高熵密钥入库（配置键名是 secret/token/password 一类，值又长又杂）——ERROR
  SEC002  弱默认凭据（`123456`、`admin`）——WARN：它不是「泄漏」，是「形同虚设」，
          但改它常常要连着环境，所以按限时处理，不一刀切拦提交
  SEC003  本地覆盖文件被纳入版本控制（`.env`、`config.local.yaml`）——ERROR
  SEC004  一个候选文件都没扫到（扫描根写错、git 命令失败）——ERROR，绝不静默通过（断言坑 #11）
  SEC005  高熵键只躺在被 gitignore 排除的本地文件里（`.deploy/config.yaml` 一类）——WARN：
          「入库」这件事判不了它，但沉默会让人以为部署配置是干净的，所以点名到文件

消息里只写**键路径**，绝不写值：SEC001 的发现会进 `.harness/deliverables/`、进终端输出、
可能进提交信息。把密钥原文打印出来去修「密钥入库」，是把一个问题变成两个。

键路径同时是账本的指纹来源。`accepted.json` 里那条豁免写的就是
`SEC001:高熵密钥入库 jwt.secret`——改消息格式等于把已盖章的豁免作废（BASE012 会报出来）。
"""

import math
import re
import subprocess
from pathlib import Path

import tracked as trackedlib
from .common import LOCAL_ARTIFACTS, add, quality_get

NAME = "secret"
PLAN = "配置里的密钥与弱凭据：只报「哪个键路径有问题」，永不报出值本身；命中基线的老账标「基线内」"
REFLECT = ("SEC001", "SEC002", "SEC003", "SEC004", "SEC005")
SECRET_KEYS = ("secret", "password", "passwd", "token", "apikey", "accesskey",
               "access_key", "privatekey", "private_key", "dsn", "upass", "clientsecret")
WEAK = {"123456", "1234567", "12345678", "admin", "admin123", "root", "test", "password",
        "secret", "changeme", "change-me", "xxx", "default", "guest", "888888", "aa123456"}
PLACEHOLDER = re.compile(r"\$\{|\{\{|<[^>]+>|YOUR_|your_|xxxxx|example\.com|placeholder", re.I)
YAML_LINE = re.compile(r"^(\s*)([A-Za-z_][\w.-]*|\"[^\"]+\"):\s*(.*?)\s*(?:#.*)?$")
GO_ASSIGN = re.compile(
    r"(?i)\b(\w*(?:secret|password|passwd|token|apikey|accesskey|privatekey|dsn))\w*\s*[:=]\s*\"([^\"]{16,})\"")
LOCAL_OVERRIDES = (".env", ".env.local", "config.local.yaml", "config.local.yml",
                   "config.dev.yaml", "id_rsa", "service-account.json")
SCAN_SUFFIXES = {".go", ".yaml", ".yml", ".json", ".sh", ".md"}
SCAN_NAMES = {"Dockerfile", "Makefile", "docker-compose.yml", "config.yaml", ".env"}
# 本地产物（common.LOCAL_ARTIFACTS）+ 生成物：这两类都不是「人写的凭据可能藏在哪」的答案，
# 扫它们只会得到一批没人能修的告警（web/ 与 docs/ 是构建产物，dist/ 与 static/ 同理）。
SKIP_PARTS = LOCAL_ARTIFACTS | {"web", "docs", "dist", "static"}


def sh(argv, cwd):
    try:
        p = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, str(exc)
    return p, (p.stdout or "") + (p.stderr or "")


def entropy(value):
    counts = {}
    for ch in value:
        counts[ch] = counts.get(ch, 0) + 1
    total = len(value)
    return -sum(c / total * math.log2(c / total) for c in counts.values())


def looks_secret(value):
    """长 + 杂 + 不像占位符。三个条件缺一不可，否则会淹在噪声里。"""
    if len(value) < 20 or PLACEHOLDER.search(value):
        return False
    if entropy(value) < 3.5:
        return False
    classes = sum(bool(re.search(p, value)) for p in (r"[a-z]", r"[A-Z]", r"\d", r"[^\w]"))
    return classes >= 2 or len(value) >= 40


def scan_yaml(path, findings, root):
    rel = path.relative_to(root).as_posix()
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    parsed = []
    for lineno, raw in enumerate(lines, 1):
        m = YAML_LINE.match(raw)
        if m and raw.strip() and not raw.lstrip().startswith("#"):
            indent, key, value = m.groups()
            parsed.append((lineno, indent, key.strip('"'), value))
    stack = []
    for lineno, indent, key, value in parsed:
        width = len(indent)
        while stack and stack[-1][0] >= width:
            stack.pop()
        stack.append((width, key))
        if not value or value in ("null", "~", "{}", "[]"):
            continue
        trail = ".".join(k for _w, k in stack)
        leaf = key.lower()
        if not any(k in leaf for k in SECRET_KEYS):
            continue
        if looks_secret(value):
            add(findings, "ERROR", NAME, rel, lineno, "SEC001", f"高熵密钥入库 {trail}")
        elif value.lower() in WEAK:
            add(findings, "WARN", NAME, rel, lineno, "SEC002",
                f"弱默认凭据 {trail}（{len(value)} 位）：换成环境变量或随机值")


def scan_go(path, findings, root):
    rel = path.relative_to(root).as_posix()
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    for lineno, raw in enumerate(lines, 1):
        for m in GO_ASSIGN.finditer(raw):
            value = m.group(2)
            if looks_secret(value):
                add(findings, "ERROR", NAME, rel, lineno, "SEC001",
                    f"高熵密钥入库 {rel}:{m.group(1)}")
            elif value.lower() in WEAK:
                add(findings, "WARN", NAME, rel, lineno, "SEC002",
                    f"弱默认凭据 {m.group(1)}（{len(value)} 位）")


def candidates(root):
    out = []
    for path in Path(root).rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_PARTS for part in rel.parts[:-1]):
            continue
        if path.suffix in SCAN_SUFFIXES or path.name in SCAN_NAMES:
            out.append(path)
    return sorted(out)


def scan_json(path, findings, root):
    """嵌套 JSON（service-account、前端构建配置）按 key 递归；读不动就当不是 JSON，跳过。"""
    import json

    rel = path.relative_to(root).as_posix()
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return
    stack = [((), data)]
    while stack:
        keys, node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                trail = keys + (str(key),)
                if isinstance(value, (dict, list)):
                    stack.append((trail, value))
                    continue
                if not isinstance(value, str) or not value:
                    continue
                leaf = str(key).lower()
                if not any(k in leaf for k in SECRET_KEYS):
                    continue
                if looks_secret(value):
                    add(findings, "ERROR", NAME, rel, 1, "SEC001",
                        f"高熵密钥入库 {'.'.join(trail)}")
                elif value.lower() in WEAK:
                    add(findings, "WARN", NAME, rel, 1, "SEC002",
                        f"弱默认凭据 {'.'.join(trail)}（{len(value)} 位）")
        elif isinstance(node, list):
            for value in node:
                if isinstance(value, (dict, list)):
                    stack.append((keys, value))


def check_tracked_overrides(root, findings):
    p, out = sh(["git", "ls-files"], root)
    if p is None or p.returncode != 0:
        add(findings, "WARN", NAME, ".", 1, "SEC004", f"git ls-files 失败，SEC003 判不了：{out}")
        return
    tracked = set(out.split())
    for rel in sorted(tracked & set(LOCAL_OVERRIDES)):
        add(findings, "ERROR", NAME, rel, 1, "SEC003",
            f"{rel} 被纳入版本控制——本地覆盖文件应当只存在于工作区")


def scan_one(path, findings, root):
    """按后缀挑扫描器；SEC001/SEC002/SEC005 的判断都在被调的那一个里。"""
    if path.suffix in {".yaml", ".yml"}:
        scan_yaml(path, findings, root)
    elif path.suffix == ".go":
        scan_go(path, findings, root)
    elif path.suffix == ".json":
        scan_json(path, findings, root)


def run(ctx, findings):
    root = Path(ctx["root"])
    quality = ctx.get("quality") or {}
    extra = [str(x) for x in quality_get(quality, "secret_extra_paths", []) or []]
    files = candidates(root) + [(root / e) for e in extra if (root / e).is_file()]
    files = [f for f in files if f.is_file()]
    if not files:
        add(findings, "ERROR", NAME, ".", 1, "SEC004",
            "没有扫到任何候选文件——扫描根写错或后缀表过期，这不是通过")
        return
    # 「入库」的主语是 git 会带走的东西：`.deploy/` 里那份真凭据不会进提交，把它报成
    # SEC001 就等于拦下以后每一次提交。读不到 ignore 规则时（没有 git）一律当会入库——
    # 宁可多报，不许因为读不到规则就静默少扫；这一条同时登记为判不了。
    hidden, problem = trackedlib.ignored(root)
    if problem:
        ctx.setdefault("not_applicable", []).append(f"{NAME}:gitignore 判定")
        hidden = frozenset()
    local_only = []
    for path in files:
        if trackedlib.is_ignored(path.relative_to(root).parts, hidden):
            local_only.append(path)
        else:
            scan_one(path, findings, root)
    if local_only:
        probe = []
        for path in local_only:
            scan_one(path, probe, root)
        keys = [x for x in probe if x.code == "SEC001"]
        for x in probe:
            if x.code != "SEC001":
                add(findings, x.severity, NAME, x.path, x.line, x.code, x.message)
        if keys:
            where = "、".join(sorted({x.path for x in keys}))
            add(findings, "WARN", NAME, keys[0].path, keys[0].line, "SEC005",
                f"{len(keys)} 个高熵键在 gitignore 排除的本地文件里（{where}）："
                "不会入库所以不判 SEC001，但那是部署侧的真凭据")
    check_tracked_overrides(root, findings)
