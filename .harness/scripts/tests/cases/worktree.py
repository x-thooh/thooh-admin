"""worktree：树—分支—看板三边对账。

夹具必须是**真的** git 工作树：这一域读 `git worktree list` 与 `git rev-parse`，拿假目录
糊不过去。每份夹具 `git init` + 一次提交，再按需要 `git worktree add`；`branch=None` 表示
「只长了一个目录、不是工作树」，那正是 WKT003 的现场。

临时树放在临时主树的同级 `<名>-wt/`——布局约定与 `wt.py` 一致，夹具跟着实现走，
改了布局不用改九个用例。
"""

import json
from datetime import date

from scopes import worktree as sc
from support import codes_of, ctx_for, git, new_root

NAME = "worktree"

TODAY = date.today().isoformat()

TASK_DOING = {"id": "T-1", "title": "做一件事", "status": "doing", "priority": "high", "worktree": "T-1"}
TASK_OPEN = {**TASK_DOING, "status": "open", "worktree": ""}
TASK_DONE = {**TASK_DOING, "status": "done", "evidence": "path:keep.txt", "worktree": "T-1"}
TASK_HANDMADE = {"id": "T-2", "title": "人工开的树", "status": "doing", "priority": "high", "worktree": "handmade"}


def board_of(*tasks):
    return {"updated": TODAY, "note": "夹具", "tasks": list(tasks)}


def run(tasks, trees=(), repo=True):
    """返回 (code 清单, ctx)——ctx 留着核「判不了有没有登记」，那是这一域的另一半。"""
    root = new_root({".harness/tasks/board.json": json.dumps(board_of(*tasks), ensure_ascii=False)})
    main = root.resolve()
    if repo:
        git(main, "init", "-q", "-b", "main")
        git(main, "add", "-A")
        git(main, "commit", "-q", "-m", "夹具")
        parent = main.parent / f"{main.name}-wt"
        parent.mkdir(parents=True, exist_ok=True)
        for name, branch in trees:
            if branch is None:
                (parent / name).mkdir(parents=True, exist_ok=True)
            else:
                git(main, "worktree", "add", "-q", "-b", branch, str(parent / name), "HEAD")
    ctx = ctx_for(main)
    findings = []
    sc.run(ctx, findings)
    return codes_of(findings), ctx


def codes(tasks, trees=(), repo=True):
    return run(tasks, trees, repo)[0]


def any_finding(tasks, trees=(), repo=True):
    """正对照填这个：第三个元素一律是「有没有报出东西」，正对照期望它 False。

    看着别扭但这是 `reverse.py` 的口径（别的域也这么写）：样本只报事实，
    「该不该报」由描述开头的「正对照」决定，不由夹具自己判。
    """
    return bool(codes(tasks, trees, repo))


def cases():
    return [
        ("WKT001", "任务已 done，树还在：收尾做了一半",
         "WKT001" in codes([TASK_DONE], [("T-1", "task/T-1")])),
        ("WKT002", "树在看板里没人登记：先建树后记账",
         "WKT002" in codes([TASK_DOING], [("T-9", "task/T-9")])),
        ("WKT002b", "任务还挂 open，树却已开起来：顺序反了",
         "WKT002" in codes([TASK_OPEN], [("T-1", "task/T-1")])),
        ("WKT003", "这里不是 git 仓库：树与分支都无从知道",
         "WKT003" in codes([TASK_DOING], [], repo=False)),
        ("WKT003b", "判不了要登记 not_applicable，不许当成通过",
         any("worktree:" in x for x in run([TASK_DOING], [], repo=False)[1].get("not_applicable", []))),
        ("WKT003c", "目录在却不是工作树：读不出分支",
         "WKT003" in codes([TASK_DOING], [("T-1", None)])),
        ("WKT004", "分支既不是 task/<id> 也不是目录名：树与分支对不上",
         "WKT004" in codes([TASK_DOING], [("T-1", "feature/login")])),
        ("WKT00n", "正对照：task/<看板 id> 分支 + doing，三边对齐",
         any_finding([TASK_DOING], [("T-1", "task/T-1")])),
        ("WKT00n2", "正对照：人工建的树，目录名就是分支名（go125 那种）",
         any_finding([TASK_HANDMADE], [("handmade", "handmade")])),
        ("WKT00n3", "正对照：-wt/ 目录存在但没有树——都在主树上做，不是违规",
         any_finding([TASK_OPEN])),
    ]
