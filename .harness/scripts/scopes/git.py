"""git: 跨树 git 调用的环境隔离只钉在 wt.git() 一个入口上，这里把其余入口也钉住。

  GTE001  `.harness/scripts/**/*.py` 里有 `["git", "-C", …]` 调用，既没带 `env=gitenv.clean()`，
          紧邻也没有「目标就是本仓库」注释

为什么要有它（看板 T-35）：钩子会给子进程导出 GIT_DIR / GIT_INDEX_FILE，`-C` 管不住它们（见
gitenv.py）。目前几处直接调用都以「被检的那棵树」为目标所以不串台，但以后有人拿它读别的树时
没有任何东西会响。判据：调用跨行的范围内、或调用起始行的上一行，要么有 `env=gitenv.clean()`，
要么有含「目标就是本仓库」的注释——二选一，逼写的人当场回答「这个目标可能不是当前仓库吗」。
"""

import ast
import re
from pathlib import Path

from .common import LOCAL_ARTIFACTS, add

NAME = "git"
PLAN = "直接 `git -C` 的调用要么摘掉钩子环境（env=gitenv.clean()），要么注明目标就是本仓库"
REFLECT = ("GTE001",)
SCRIPTS_REL = ".harness/scripts"
ENV_OK = re.compile(r"env\s*=\s*gitenv\.clean\(")
COMMENT_OK = re.compile(r"#.*目标就是本仓库")


def is_git_c(node):
    """Call 的第一个位置参数是以 "git", "-C" 开头的列表。"""
    if not isinstance(node, ast.Call) or not node.args or not isinstance(node.args[0], ast.List):
        return False
    head = [e.value for e in node.args[0].elts[:2] if isinstance(e, ast.Constant)]
    return head == ["git", "-C"]


def check_file(path, rel, findings):
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    for node in ast.walk(ast.parse(src)):
        if not is_git_c(node):
            continue
        first = max(node.lineno - 1, 1)  # 含调用上一行
        span = "\n".join(lines[first - 1:node.end_lineno])
        if ENV_OK.search(span) or COMMENT_OK.search(span):
            continue
        add(findings, "ERROR", NAME, rel, node.lineno, "GTE001",
            "`git -C` 调用没带 env=gitenv.clean()，紧邻也没写「目标就是本仓库」：目标若不是当前仓库，钩子环境会串台")


def run(ctx, findings):
    root = Path(ctx["root"])
    base = root / SCRIPTS_REL
    files = sorted(p for p in base.rglob("*.py") if not any(x in LOCAL_ARTIFACTS for x in p.relative_to(root).parts))
    if not files:
        add(findings, "ERROR", NAME, SCRIPTS_REL, 1, "GTE001",
            "一个脚本都没扫到——路径写错与全绿长得一样（断言坑 #11）")
        return
    for p in files:
        check_file(p, str(p.relative_to(root)), findings)
