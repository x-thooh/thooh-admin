"""entry: 入口文件（AGENTS.md）与目录地图的对账。

  ENT001  根 AGENTS.md 缺失，或头部注释 `<!-- agents: scope=. parent= -->` 不合规
  ENT002  子目录入口的 header 不合规，或 parent 指向不存在的入口
  ENT003  入口行数超过 config.json 的额度（根另有一档）
  ENT004  目录地图与磁盘不一致（多一个报、少一个也报）
  ENT005  硬规则里某条既没有 `scope=<域>` 也没有「无断言」——没有载体的规则是愿望
  ENT006  规则标注的 scope 没有注册：声明即承诺，没实现的域不许广播
  ENT007  codebase-guide/index.json 与磁盘不一致（派生数据过期；`--fix` 可重建）
  ENT008  一个 AGENTS.md 都没扫到（路径写错与全绿长得一样，断言坑 #11）

为什么 ENT004 是双向：只判「地图里的路径存在」会漏掉「磁盘新增了目录但没人写进地图」，
那种目录下开会话时没有入口可加载；只判反方向则漏掉地图里的死路径。
"""

import re
from pathlib import Path

from .common import add, build_guide, code_lines, load_json

NAME = "entry"
PLAN = "入口文件（根与各目录 AGENTS.md）自己站得住：头部 scope/parent、目录地图与磁盘双向比对、" \
    "每条规则指向真存在的 code、派生索引不过期"
REFLECT = ("ENT001", "ENT002", "ENT003", "ENT004", "ENT005", "ENT006", "ENT007", "ENT008")
HEADER = re.compile(r"<!--\s*agents:\s*scope=(\S+)\s+parent=(\S*)\s*-->")
RULE_LINE = re.compile(r"^\s*(\d+)\.\s+(.*)$")
SCOPE_TAG = re.compile(r"`scope=([A-Za-z_][A-Za-z0-9_]*)`")
SKIP_DIRS = {".git", ".go", ".idea", "node_modules", "__pycache__", ".ruff_cache"}
GUIDE_REL = ".harness/codebase-guide/index.json"


def entry_files(root):
    return sorted(p for p in Path(root).rglob("AGENTS.md") if not any(part in SKIP_DIRS for part in p.relative_to(root).parts))


def header_of(path):
    """第一行里必须出现 header；返回 (scope, parent) 或 None。"""
    try:
        first = path.read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError):
        return None
    m = HEADER.search(first)
    return (m.group(1), m.group(2)) if m else None


def top_dirs(root):
    return sorted(
        p.name
        for p in Path(root).iterdir()
        if p.is_dir() and p.name not in SKIP_DIRS and not p.name.startswith(".")
    ) + ([".harness"] if (Path(root) / ".harness").is_dir() else [])


def map_entries(text):
    """「## 目录地图」下第一个围栏块的首列 token。"""
    m = re.search(r"^##\s*目录地图\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return None
    block = m.group(1)
    fence = re.search(r"```[a-zA-Z]*\n(.*?)```", block, re.S)
    if not fence:
        return None
    out = []
    for line in fence.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        token = line.split()[0]
        out.append(token.rstrip("/"))
    return out


def rule_blocks(text):
    """硬规则节的逐条文本。"""
    m = re.search(r"^##\s*硬规则\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return None
    blocks, cur = [], None
    for line in m.group(1).splitlines():
        if RULE_LINE.match(line) or re.match(r"^\s*\d+\.\s", line):
            if cur:
                blocks.append(cur)
            cur = line
        elif cur is not None and line.strip():
            cur += " " + line.strip()
    if cur:
        blocks.append(cur)
    return blocks


def check_headers(root, files, findings, quality):
    root_cap = quality.get("agents_max_lines", 150)
    sub_cap = quality.get("sub_agents_max_lines", 80)
    for path in files:
        rel = path.relative_to(root).as_posix()
        parent_dir = path.parent.relative_to(root).as_posix()
        head = header_of(path)
        if path.parent == root:
            if head is None or head[0] != "." or head[1] not in ("", "-"):
                add(findings, "ERROR", NAME, rel, 1, "ENT001",
                    "根入口首行必须是 `<!-- agents: scope=. parent= -->`（scope 写 `.`，parent 留空）")
            cap = root_cap
        else:
            if head is None:
                add(findings, "ERROR", NAME, rel, 1, "ENT002",
                    "子目录入口首行缺 `<!-- agents: scope=<目录> parent=<上级目录> -->`，"
                    "宿主靠它判断覆盖链")
                continue
            scope, parent = head
            if scope != parent_dir:
                add(findings, "ERROR", NAME, rel, 1, "ENT002",
                    f"header 的 scope={scope!r} 与所在目录 {parent_dir!r} 不一致")
            parent_entry = (root / parent / "AGENTS.md") if parent not in ("", ".") else (root / "AGENTS.md")
            if not parent_entry.is_file():
                add(findings, "ERROR", NAME, rel, 1, "ENT002",
                    f"parent={parent!r} 指向的 {parent_entry.relative_to(root)} 不存在——覆盖链断了")
            cap = sub_cap
        try:
            lines = len(path.read_text(encoding="utf-8").splitlines())
        except OSError as exc:
            add(findings, "ERROR", NAME, rel, 1, "ENT001", f"读不了：{exc}")
            continue
        if lines > cap:
            add(findings, "ERROR", NAME, rel, lines, "ENT003",
                f"入口 {lines} 行，超过上限 {cap}；入口是地图不是手册，细节下沉到 .harness/")


def check_map(root, findings):
    path = Path(root) / "AGENTS.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    entries = map_entries(text)
    if entries is None:
        add(findings, "ERROR", NAME, "AGENTS.md", 1, "ENT004",
            "缺少「## 目录地图」里的围栏块——地图解析不到，双向对账无从谈起")
        return
    disk = set(top_dirs(root))
    listed = set(entries)
    for missing in sorted(disk - listed):
        add(findings, "ERROR", NAME, "AGENTS.md", 1, "ENT004",
            f"磁盘上有目录 {missing}/ 但地图里没有——在那里开会话加载不到入口")
    for dead in sorted(listed - disk):
        add(findings, "ERROR", NAME, "AGENTS.md", 1, "ENT004",
            f"地图写了 {dead} 但磁盘上不存在——死路径")


def check_rules(root, findings, quality, registered):
    path = Path(root) / "AGENTS.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    blocks = rule_blocks(text)
    if blocks is None:
        add(findings, "ERROR", NAME, "AGENTS.md", 1, "ENT005", "缺少「## 硬规则」一节")
        return
    if not blocks:
        add(findings, "ERROR", NAME, "AGENTS.md", 1, "ENT005",
            "硬规则节里没有编号条目——扫到 0 条规则与全绿长得一样（断言坑 #11）")
        return
    for block in blocks:
        num = RULE_LINE.match(block).group(1)
        tags = SCOPE_TAG.findall(block)
        if not tags and "无断言" not in block:
            add(findings, "ERROR", NAME, "AGENTS.md", 1, "ENT005",
                f"硬规则 {num} 既没有 `scope=` 也没写「无断言」——没有载体的规则不会被执行")
        for tag in tags:
            if tag not in registered:
                add(findings, "ERROR", NAME, "AGENTS.md", 1, "ENT006",
                    f"硬规则 {num} 标注 `scope={tag}` 但没有注册这个域：声明即承诺")


def check_guide(root, findings):
    target = Path(root) / GUIDE_REL
    expected = build_guide(root)
    if not target.is_file():
        add(findings, "ERROR", NAME, GUIDE_REL, 1, "ENT007",
            "codebase-guide/index.json 不存在：跑 make fix 生成")
        return
    actual = load_json(root, GUIDE_REL, NAME, findings, "ENT007")
    if actual is None:
        return
    if actual != expected:
        add(findings, "ERROR", NAME, GUIDE_REL, 1, "ENT007",
            "索引与磁盘不一致（派生数据过期）：跑 make fix，别手改")


def _fix_guide(root):
    import json

    target = Path(root) / GUIDE_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_guide(root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return "重生成 .harness/codebase-guide/index.json"


FIXERS = {"ENT007": (_fix_guide, GUIDE_REL)}


def run(ctx, findings):
    root = Path(ctx["root"])
    quality = ctx.get("quality") or {}
    files = entry_files(root)
    if not files:
        add(findings, "ERROR", NAME, "AGENTS.md", 1, "ENT008",
            "一个 AGENTS.md 都没扫到——先有根入口，其余对账才有意义")
        return
    check_headers(root, files, findings, quality)
    check_map(root, findings)
    check_rules(root, findings, quality, set(ctx.get("registry") or ()))
    check_guide(root, findings)
