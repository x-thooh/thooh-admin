"""worktree: 一个任务一棵树——树、分支、看板三边对得上。

  WKT001  树还在而看板里这条任务已经 done：收尾做了一半（树没撤，下一个人不知道它算不算数）
  WKT002  树还在而看板里没有对应任务，或任务还挂在 open/blocked：先建树后记账，做的事没被登记
  WKT003  判不了：这里不是 git 仓库、拿不到 worktree 清单，或某棵树读不出分支
  WKT004  树的分支既不是 `task/<看板 id>` 也不是目录名本身：树与分支对不上，接手的人找不到工作

布局约定（`<主树同级>/<主树目录名>-wt/<id>`）只写在 `wt.py` 里一处，这里 import 它——
两个各算一遍的地方迟早漂移，而漂移的形态就是「脚本建在 A，门禁去找 B，两边都说没树」。
人工建的树照样要能被判，所以读的是磁盘与 git，不是脚本的运行记录。
「忘了开树」判不了（任务可能在别人机器上做），那条写在根 `AGENTS.md` 硬规则里靠人守。
"""

from pathlib import Path

import wt as wtlib
from .common import add, rel_to

NAME = "worktree"

PLAN = "任务级隔离是真的：每棵任务树在看板里有对应的进行中任务、分支名与树对得上、任务做完树就撤"
REFLECT = ("WKT001", "WKT002", "WKT003", "WKT004")

OPEN_STATUSES = ("open", "blocked")
TERMINAL_STATUS = "done"


def trees_of(root):
    """返回 (任务树目录清单, 判不了的原因)。

    给 Path 而不是目录名：读分支要在真正的树里跑 git。拿当前根目录拼名字，判的其实是
    「我自己」——每棵树都把自己扫一遍，别人的树一条没看着还全绿。
    """
    parent, problem = wtlib.wt_parent(root)
    if problem:
        return [], problem
    if not parent.is_dir():
        return [], None
    return sorted((p for p in parent.iterdir() if p.is_dir()), key=lambda p: p.name), None


def run(ctx, findings):
    root = Path(ctx["root"])
    trees, problem = trees_of(root)
    if problem:
        ctx.setdefault("not_applicable", []).append(f"{NAME}:{problem}")
        add(findings, "WARN", NAME, rel_to(root, root), 1, "WKT003",
            f"{problem}——这一域判不了，不是通过：没有 git 就无从知道树与分支")
        return
    if not trees:
        return
    tasks, board_problem = wtlib.board_tasks(root)
    if board_problem:
        ctx.setdefault("not_applicable", []).append(f"{NAME}:{board_problem}")
        add(findings, "WARN", NAME, wtlib.BOARD_REL, 1, "WKT003",
            f"{board_problem}：有 {len(trees)} 棵树却没法核对看板——判不了，不是通过")
        return
    for path in trees:
        name = path.name
        task = wtlib.find_task(tasks, name)
        if task is None:
            add(findings, "ERROR", NAME, rel_to(root, path), 1, "WKT002",
                f"树 {name} 在看板里找不到对应的任务（id 或 worktree 字段）："
                "先建树后记账，做的事没被登记")
            continue
        status = str(task.get("status") or "")
        if status == TERMINAL_STATUS:
            add(findings, "ERROR", NAME, rel_to(root, path), 1, "WKT001",
                f"任务 {task.get('id')} 已经 done，树 {name} 还在：收尾做了一半，"
                "要么撤树（make task-done），要么把任务改回 doing")
            continue
        if status in OPEN_STATUSES:
            add(findings, "ERROR", NAME, rel_to(root, path), 1, "WKT002",
                f"任务 {task.get('id')} 还是 {status}，树 {name} 却已经开起来：顺序反了")
            continue
        code, branch, _err = wtlib.git(path, "rev-parse", "--abbrev-ref", "HEAD")
        if code != 0:
            add(findings, "WARN", NAME, rel_to(root, path), 1, "WKT003",
                f"读不到树 {name} 的分支名（{path} 不是 git 认的工作树）——判不了，不是通过")
            continue
        if branch not in (f"task/{task.get('id')}", name):
            add(findings, "ERROR", NAME, rel_to(root, path), 1, "WKT004",
                f"树 {name} 的分支是 {branch!r}，既不是 `task/{task.get('id')}` 也不是目录名："
                "树与分支对不上，接手的人找不到这份工作")
