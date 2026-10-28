"""modules: 功能模块与路由注册表的双向对账。

本仓库的模块**不是靠约定被发现**的：`app/admin/router.go` 里的 import 与 `xxx.Init(e)`
是手写的，加一个模块要改两处。改漏一处的症状各不相同，所以四条断言分开判：

  MOD001  磁盘上有模块（router.go 导出 Init）但注册表没挂它——路由静默缺失，编译照过
  MOD002  注册表 import 了模块根下不存在的路径——死引用，`go build` 会失败但报错很绕
  MOD003  注册表 import 了模块但没有对应的 `alias.Init(` 调用——只 import 不挂路由，
          这一条 MOD001 抓不到（import 在，模块也在，缺的只是那句调用）
  MOD004  模块形状不完整：有 api.go 却没有 router.go，或 router.go 里没有导出的
          `func Init(`——本仓库约定一个功能模块 = api.go + model.go + router.go
  MOD005  扫描样本为 0（模块根改名、注册表文件丢失）——扫不到东西和全绿长得一样（断言坑 #11）

匹配 `alias.Init(` 前一律先剥注释再抹字面量：注册表里有 `//file.InitFile(e)` 这种
注释掉的历史挂载，直接正则会在注释上命中，把「已下线」读成「已注册」。
"""

import re
from pathlib import Path

from .common import add, blank_strings, code_lines, go_package, quality_get

NAME = "modules"
PLAN = "业务模块清单与 `app/admin/router.go` 的注册表双向对账：多一个没注册的模块、" \
    "少一个还在注册的文件都算缺陷；模块骨架（api.go/model.go/router.go）齐不齐也在这里判"
REFLECT = ("MOD001", "MOD002", "MOD003", "MOD004", "MOD005")
IMPORT_RE = re.compile(r'^(?:(?P<alias>[\w.]+|\.)\s+)?"(?P<path>[^"]+)"$')
INIT_RE = re.compile(r"\b(?P<alias>[A-Za-z_]\w*)\.Init\w*\(")
SHAPE_FILES = ("api.go", "model.go", "router.go")
FUNC_INIT_RE = re.compile(r"^func\s+Init\s*\(", re.M)


def module_prefix(root):
    """go.mod 的 module 名，本仓库是 `vben`。"""
    try:
        for line in (Path(root) / "go.mod").read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("module "):
                return line.split()[1].strip()
    except (OSError, IndexError):
        return ""
    return ""


def find_modules(root, roots):
    """模块根下所有**含 .go 文件**的目录（父目录只当分组，不算模块）。"""
    out = []
    for rel_root in roots:
        base = Path(root) / rel_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.go")):
            if not path.is_file():
                continue
            d = path.parent
            if d not in out:
                out.append(d)
    return out


def registry_imports(path):
    """注册表里的 [(alias, import_path, line)]；alias 为空表示包名即路径末段。"""
    out = []
    code = "\n".join(seg for _lineno, seg in code_lines(path))
    lines = [ln.strip() for ln in code.splitlines()]
    in_block = False
    for idx, line in enumerate(lines, 1):
        if in_block:
            if line.startswith(")"):
                in_block = False
                continue
        elif line.startswith("import ("):
            in_block = True
            continue
        elif line.startswith("import "):
            line = line[len("import "):]
        else:
            continue
        m = IMPORT_RE.match(line)
        if m:
            alias = m.group("alias") or ""
            if alias == ".":
                alias = "."
            out.append((alias, m.group("path"), idx))
    return out


def init_aliases(path):
    """注册表里真实出现的 `<alias>.Init...(` 调用的 alias 集合（注释与字面量已剔除）。"""
    aliases = set()
    for lineno, seg in code_lines(path):
        for m in INIT_RE.finditer(blank_strings(seg)):
            aliases.add(m.group("alias"))
    return aliases


def run(ctx, findings):
    root = Path(ctx["root"])
    quality = ctx.get("quality") or {}
    roots = [str(r) for r in quality_get(quality, "module_roots", ["modules"]) or []]
    registry_rel = quality_get(quality, "registry_file", "app/admin/router.go")
    registry = root / str(registry_rel)

    if not registry.is_file():
        add(findings, "ERROR", NAME, str(registry_rel), 1, "MOD005",
            f"路由注册表 {registry_rel} 不存在——所有对账都失去了事实源")
        return

    prefix = module_prefix(root)
    present = find_modules(root, roots)
    if not present:
        add(findings, "ERROR", NAME, roots[0] if roots else ".", 1, "MOD005",
            f"模块根 {roots} 下没扫到任何含 .go 的目录——先确认目录改名还是 glob 失效")
        return

    imports = registry_imports(registry)
    # 注册表里指向模块根目录的 import：路径 -> (alias, 行号)
    registered = {}
    for alias, imp_path, line in imports:
        if prefix and imp_path.startswith(prefix + "/"):
            sub = imp_path[len(prefix) + 1:]
            if any(sub == r or sub.startswith(r + "/") for r in roots):
                registered[imp_path] = (alias, line)

    # 死引用：注册表 import 了模块根下不存在的路径
    for imp_path, (alias, line) in sorted(registered.items()):
        if not (root / imp_path[len(prefix) + 1:]).is_dir():
            add(findings, "ERROR", NAME, str(registry_rel), line, "MOD002",
                f"import {imp_path} 指向的目录不存在——死引用")

    aliases = init_aliases(registry)
    seen_dirs = set()
    for d in present:
        rel = d.relative_to(root).as_posix()
        seen_dirs.add(rel)
        files = {p.name for p in d.iterdir() if p.is_file()}
        router = d / "router.go"
        if "api.go" in files and "router.go" not in files:
            add(findings, "ERROR", NAME, f"{rel}/api.go", 1, "MOD004",
                f"{rel} 有 api.go 但没有 router.go——本仓库一个功能模块 = "
                + " + ".join(SHAPE_FILES) + "，缺一个就挂不上路由")
            continue
        if not router.is_file():
            continue  # 纯 model/service 包（如 modules/sys/actor）不是模块，不判形状
        if go_package(router) == "":
            add(findings, "ERROR", NAME, f"{rel}/router.go", 1, "MOD004",
                "router.go 解析不出 package 子句")
            continue
        if not FUNC_INIT_RE.search(router.read_text(encoding="utf-8")):
            add(findings, "ERROR", NAME, f"{rel}/router.go", 1, "MOD004",
                "router.go 里没有导出的 `func Init(`——注册表靠这个名字挂载")

        imp_path = f"{prefix}/{rel}"
        entry = registered.get(imp_path)
        if entry is None:
            add(findings, "ERROR", NAME, str(registry_rel), 1, "MOD001",
                f"{rel} 导出 Init 但 {registry_rel} 没 import 它——路由静默缺失")
            continue
        alias, line = entry
        use = alias if alias else imp_path.rsplit("/", 1)[-1]
        if use not in aliases:
            add(findings, "ERROR", NAME, str(registry_rel), line, "MOD003",
                f"import 了 {imp_path}（别名 {use}）但没有 {use}.Init(...) 调用"
                "——只 import 不挂路由，编译器不会报（别名被 import 本身「用掉」了）")

    # 注册表引用了模块根下的目录，但那个目录不在扫描结果里（例如只剩 .md）
    for imp_path, (alias, line) in sorted(registered.items()):
        rel = imp_path[len(prefix) + 1:]
        if rel not in seen_dirs and (root / rel).is_dir():
            add(findings, "ERROR", NAME, str(registry_rel), line, "MOD004",
                f"{rel} 被注册但没有 .go 文件——空的模块目录")
