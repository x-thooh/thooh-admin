"""cmd：命令表 ↔ Makefile ↔ 脚本文件三方对账。

`AGENTS.md` 说「命令只从这张表走」，`Makefile` 说「未在这里注册的脚本不许当命令用」。
两句都是声明，谁也没检查过对方——本域就是那检查。它管的是三边对账里最容易烂的一条边：
文档里的命令表是给人抄的，抄错一次就少跑一次门禁，而没有任何脚本会发现「这条命令不存在」。

判据两头都要堵（缺的不是空，空也不是零）：
  CMD001  表里写了 `make X`，Makefile 里没有这个 target —— 文档承诺了一条不存在的命令
  CMD002  Makefile 里有带 `##` 的 target，表里没登记 —— 命令存在但没人知道它算数
  CMD003  Makefile 引用的脚本文件不在磁盘上 —— target 在，一跑就炸
  CMD004  `.harness/scripts/` 顶层有脚本，Makefile 与 registry 都不提它 —— 第二条入口
  CMD005  一个 target 或一行表格都没扫到 —— 路径写错与「全都合规」长得一模一样

不判什么：target 的命令行本身对不对（那是 build 域和实跑的事），以及 `make help` 的排版。
"""

import re
from pathlib import Path

from scopes.common import add, rel_to

NAME = "cmd"

PLAN = "入口的命令表、Makefile 的 target、磁盘上的脚本三方一一对应：表里没有的不算命令，Makefile 里没有的不算文档"
REFLECT = ("CMD001", "CMD002", "CMD003", "CMD004", "CMD005")

TABLE_SECTION = "## 常用命令"
NEXT_H2 = re.compile(r"^## ", re.M)
# `make init`、`make build` / `vet` / `fmt`、`make check-commit`（后面还跟参数说明）：
# 一格可能并列多个 target，名字后面允许空格接别的写法
CELL_TOKEN = re.compile(r"`(?:make\s+)?([a-z0-9][a-z0-9_-]*)\b")
# 只有带 `## ` 的 target 才是「给人用的命令」——help 打印的就是这一批，命令表必须与它同集
DOC_TARGET = re.compile(r"^([a-z0-9][a-z0-9_-]*):.*##\s", re.M)
SCRIPT_PATH = re.compile(r"\$\(SCRIPTS\)/([A-Za-z0-9_./-]+)")


def read_of(path):
    """读文本；读不到当空串——缺失由 CMD005 判，不在这里抛。"""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def section_of(md, title=TABLE_SECTION):
    """取「常用命令」一节的正文；标题不存在返回 None（由 CMD005 报，不静默当空表）。"""
    start = md.find(title)
    if start < 0:
        return None
    rest = md[start + len(title):]
    nxt = NEXT_H2.search(rest)
    return rest[: nxt.start()] if nxt else rest


def table_commands(md):
    section = section_of(md)
    if section is None:
        return None
    found = set()
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = line.split("|")
        for name in CELL_TOKEN.findall(cells[1] if len(cells) > 1 else ""):
            found.add(name)
    return found


def make_targets(makefile_text):
    return {m for m in DOC_TARGET.findall(makefile_text)}


def script_refs(makefile_text):
    """Makefile 里出现的 `$(SCRIPTS)/...` 路径，含 `VAR := $(SCRIPTS)/x.py` 定义的变量。"""
    direct = set(SCRIPT_PATH.findall(makefile_text))
    return {p for p in direct if p}


def run(ctx, findings):
    root = Path(ctx["root"])
    agents = root / "AGENTS.md"
    makefile = root / "Makefile"
    scripts = root / ".harness" / "scripts"

    if not agents.is_file() or not makefile.is_file():
        lack = [rel_to(root, p) for p in (agents, makefile) if not p.is_file()]
        add(findings, "ERROR", NAME, ", ".join(lack), 1, "CMD005",
            "命令对账缺输入（入口文件或 Makefile 不在）：判不了不等于合规")
        return

    listed = table_commands(read_of(agents))
    if listed is None:
        add(findings, "ERROR", NAME, rel_to(root, agents), 1, "CMD005",
            "AGENTS.md 里没有「## 常用命令」一节：命令表是这张域的唯一入口，标题改名等于把命令清了")
        return
    targets = make_targets(read_of(makefile))
    if not targets:
        add(findings, "ERROR", NAME, rel_to(root, makefile), 1, "CMD005",
            "Makefile 里没扫到带 `##` 说明的 target：0 个样本和「命令表干净」长得一模一样")
        return

    for name in sorted(listed - targets):
        add(findings, "ERROR", NAME, rel_to(root, agents), 1, "CMD001",
            f"命令表写了 `make {name}`，Makefile 里没有这个 target：照着表跑的人只会拿到 "
            f"「No rule to make target」——文档不能承诺一条不存在的命令")
    for name in sorted(targets - listed):
        add(findings, "ERROR", NAME, rel_to(root, agents), 1, "CMD002",
            f"Makefile 里有 target `{name}`（带 ## 说明，help 会打印），命令表没登记："
            "表是唯一的命令清单，没进表就等于它不该存在")

    for ref in sorted(script_refs(read_of(makefile))):
        if not (scripts / ref).is_file():
            add(findings, "ERROR", NAME, rel_to(root, makefile), 1, "CMD003",
                f"Makefile 引用 $(SCRIPTS)/{ref}，文件不在磁盘上：target 还在，一跑就炸")

    stems = {p.stem for p in scripts.glob("*.py") if p.stem != "__init__"}
    make_text = read_of(makefile)
    for stem in sorted(stems):
        own = scripts / f"{stem}.py"
        referenced = stem in make_text or any(
            stem in read_of(p) for p in sorted(scripts.glob("*.py")) if p != own
        )
        if referenced:
            continue
        add(findings, "ERROR", NAME, rel_to(root, own), 1, "CMD004",
            f"{stem}.py 既不在 Makefile 里当命令，也不被任何脚本引用：它是第二条入口，"
            "而这条规则说的是「未注册的脚本不当命令用」")
