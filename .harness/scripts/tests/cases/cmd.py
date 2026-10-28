"""cmd：命令表 ↔ Makefile ↔ 脚本文件。

夹具是一对最小文件：`AGENTS.md` 的「## 常用命令」表 + 一个只带 `##` 说明行的 Makefile。
每条样本只改一处，改完必须只有预期的那个 code 报出来——两边同时坏就判不出是谁的功劳。
"""

from scopes import cmd as sc_cmd
from support import codes_of, ctx_for, new_root

NAME = "cmd"

AGENTS = """<!-- agents: scope=. parent= -->
# x

## 常用命令

| 命令 | 做什么 |
| --- | --- |
| `make check` | 跑门禁 |

## 目录地图
"""

MAKEFILE = """ROOT := .
CHECK := $(SCRIPTS)/verify.py
.PHONY: check

check: ## 跑门禁
\t@python3 $(CHECK)
"""


def fixture(agents=AGENTS, makefile=MAKEFILE, extra=None):
    files = {"AGENTS.md": agents, "Makefile": makefile, ".harness/scripts/verify.py": "# verify\n"}
    files.update(extra or {})
    return new_root(files)


def cases():
    out = []
    root = fixture(agents=AGENTS.replace("`make check`", "`make check`、`make ghost`"))
    f = []
    sc_cmd.run(ctx_for(root), f)
    out.append(("CMD001", "表里写了 make ghost，Makefile 没这个 target", "CMD001" in codes_of(f)))

    root = fixture(makefile=MAKEFILE + "\ndeploy: ## 上线\n\t@echo x\n")
    f = []
    sc_cmd.run(ctx_for(root), f)
    out.append(("CMD002", "Makefile 有 deploy，命令表没登记", "CMD002" in codes_of(f)))

    # 顺带留一行提到 verify.py 的注释：否则这个夹具会连 CMD004 一起报，样本就不孤立了
    root = fixture(makefile=MAKEFILE.replace("verify.py", "gone.py") + "\n# verify 仍在磁盘上\n")
    f = []
    sc_cmd.run(ctx_for(root), f)
    out.append(("CMD003", "Makefile 引用了不存在的脚本", "CMD003" in codes_of(f)))

    root = fixture(extra={".harness/scripts/loose.py": "# 没人调用\n"})
    f = []
    sc_cmd.run(ctx_for(root), f)
    out.append(("CMD004", "scripts/ 里有既不当命令也没被引用的脚本", "CMD004" in codes_of(f)))

    root = fixture(agents=AGENTS.replace("## 常用命令", "## 命令一览"))
    f = []
    sc_cmd.run(ctx_for(root), f)
    out.append(("CMD005", "入口里没有「常用命令」这一节", "CMD005" in codes_of(f)))

    root = fixture(makefile=MAKEFILE.replace("## 跑门禁", "跑门禁"))
    f = []
    sc_cmd.run(ctx_for(root), f)
    out.append(("CMD005b", "Makefile 一个带 ## 的 target 都没扫到", "CMD005" in codes_of(f)))

    root = new_root({"Makefile": MAKEFILE})
    f = []
    sc_cmd.run(ctx_for(root), f)
    out.append(("CMD005c", "命令对账缺输入：AGENTS.md 不在", "CMD005" in codes_of(f)))

    f = []
    sc_cmd.run(ctx_for(fixture()), f)
    out.append(("CMD00n", "正对照：表、target、脚本三方一致", bool(codes_of(f))))
    return out
