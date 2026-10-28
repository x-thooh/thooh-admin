"""worktree：树—分支—看板三边对账。

夹具必须是**真的** git 工作树：这一域读 `git worktree list` 与 `git rev-parse`，拿假目录
糊不过去。每份夹具 `git init` + 一次提交，再按需要 `git worktree add`；`branch=None` 表示
「只长了一个目录、不是工作树」，那正是 WKT003 的现场。

临时树放在临时主树的同级 `<名>-wt/`——布局约定与 `wt.py` 一致，夹具跟着实现走，
改了布局不用改整批用例。
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


def run(tasks, trees=(), repo=True, advance=False, dirty=False):
    """返回 (code 清单, ctx, findings)——ctx 核「判不了有没有登记」，findings 核严重度。

    `advance` 与 `dirty` 是 WKT001 两档的现场：前者在树里再提交一次，让这份工作**还没合进主树**
    （ERROR 档）；后者只写文件不提交——已经合并、只是还没提交，仍是 WARN，但消息必须点名那笔
    改动，因为 `make task-done` 会先拒绝撤这样的树。两个都不开就是收尾的必经中间态；以前它和
    未落地共用一个 ERROR，于是「标记 done 并把它提交进去」这一步自己把自己挡在门外。
    """
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
                continue
            path = parent / name
            git(main, "worktree", "add", "-q", "-b", branch, str(path), "HEAD")
            if advance or dirty:
                (path / "keep.txt").write_text("还没落地\n", encoding="utf-8")
            if advance:
                git(path, "add", "-A")
                git(path, "commit", "-q", "-m", "树里的一次提交")
    ctx = ctx_for(main)
    findings = []
    sc.run(ctx, findings)
    return codes_of(findings), ctx, findings


def codes(tasks, trees=(), repo=True, advance=False, dirty=False):
    return run(tasks, trees, repo, advance, dirty)[0]


def one(tasks, code, trees=(), repo=True, advance=False, dirty=False):
    """取这条 code 的第一条发现（核档位或消息点名时用）；没报出来给 None。"""
    for finding in run(tasks, trees, repo, advance, dirty)[2]:
        if finding.code == code:
            return finding
    return None


def tier(tasks, code, want, trees=(), repo=True, advance=False, dirty=False, says=""):
    """档位核对：severity 等于 want，且（写了 says 时）消息点名了那件事。

    两档的差别只在档位与消息上，只核「有没有报」等于没判——`reverse.py` 的 fired 分不出
    ERROR 与 WARN，这里必须自己核。
    """
    finding = one(tasks, code, trees, repo, advance, dirty)
    return finding is not None and finding.severity == want and says in finding.message


def any_finding(tasks, trees=(), repo=True):
    """正对照填这个：第三个元素一律是「有没有报出东西」，正对照期望它 False。

    看着别扭但这是 `reverse.py` 的口径（别的域也这么写）：样本只报事实，
    「该不该报」由描述开头的「正对照」决定，不由夹具自己判。
    """
    return bool(codes(tasks, trees, repo))


def cases():
    return [
        ("WKT001", "done 且这份工作已合进主树：只差撤树，WARN 并点名 make task-done",
         tier([TASK_DONE], "WKT001", "WARN", [("T-1", "task/T-1")], says="make task-done")),
        ("WKT001b", "已合并而树里还有没提交的东西：仍是 WARN，但消息要点名那笔改动",
         tier([TASK_DONE], "WKT001", "WARN", [("T-1", "task/T-1")], dirty=True, says="没提交")),
        ("WKT001c", "done 而这份工作还没合进主树：done 与未落地互相矛盾，ERROR",
         tier([TASK_DONE], "WKT001", "ERROR", [("T-1", "task/T-1")], advance=True,
              says="没合进主树")),
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
