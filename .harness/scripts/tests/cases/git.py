"""git：`git -C` 调用必须摘环境或注明目标就是本仓库。

违规样本一处不带 env 的调用；正对照：带 env=gitenv.clean()、带注释（上一行/行尾）都不报。
"""

from scopes import git as sc_git
from support import codes_of, ctx_for, new_root

NAME = "git"
REL = ".harness/scripts/x.py"
BAD = 'import subprocess\nsubprocess.run(["git", "-C", str(root), "log"], check=False)\n'
ENV = 'subprocess.run(\n    ["git", "-C", str(root), "log"], env=gitenv.clean()\n)\n'
COMMENT = '# 目标就是本仓库\nsubprocess.run(["git", "-C", str(root), "log"])\n'
TRAIL = 'subprocess.run(["git", "-C", str(root), "log"])  # 目标就是本仓库\n'


def codes(src):
    f = []
    sc_git.run(ctx_for(new_root({REL: src})), f)
    return codes_of(f)


def cases():
    return [
        ("GTE001", "不带 env 也没注释的 git -C", "GTE001" in codes(BAD)),
        ("GTE001b", "正对照：env=gitenv.clean() 不报", bool(codes(ENV))),
        ("GTE001c", "正对照：上一行注释不报", bool(codes(COMMENT))),
        ("GTE001d", "正对照：行尾注释不报", bool(codes(TRAIL))),
    ]
