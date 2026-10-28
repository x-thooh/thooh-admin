"""state：看板形状、闭集取值、完成态证据、INDEX 新鲜度。

夹具是一份最小 board.json。`INDEX.md` 在负例里放一段假内容（它自己会多报一条 STATE007，
不影响「预期的那条有没有报」）；正对照则现算一份真 INDEX，要求 0 条——只有那时才能证明
这条域不是「永远在报」。
"""

import json
from datetime import date, timedelta

import discovery
from scopes import state as sc_state
from support import codes_of, ctx_for, new_root

NAME = "state"

TODAY = date.today().isoformat()

TASK_OPEN = {"id": "T-1", "title": "补一样东西", "status": "open", "priority": "high"}
TASK_DONE = {"id": "T-2", "title": "已经补好", "status": "done", "priority": "low",
             "evidence": "path:keep.txt"}
BOARD_OK = {"updated": TODAY, "tasks": [TASK_OPEN, TASK_DONE]}

FAKE_INDEX = "# INDEX.md — 假内容，只为了把 STATE007 与别的判定分开\n"


def with_tasks(tasks, **over):
    board = {"updated": TODAY, "tasks": tasks}
    board.update(over)
    return board


def codes_for(board, index=FAKE_INDEX, extra=None, quality=None):
    files = {
        ".harness/tasks/board.json": json.dumps(board, ensure_ascii=False),
        ".harness/INDEX.md": index,
    }
    files.update(extra or {})
    # None = 这个文件不该存在（造「缺失」用），不是「写了个空文件」
    files = {k: v for k, v in files.items() if v is not None}
    out = []
    sc_state.run(ctx_for(new_root(files), quality), out)
    return codes_of(out)


def control_codes():
    """正对照：先把真 INDEX 现算进树里，再要求这条域一条都不报。"""
    root = new_root({
        ".harness/tasks/board.json": json.dumps(BOARD_OK, ensure_ascii=False),
        "keep.txt": "证据文件在\n",
    })
    (root / ".harness/INDEX.md").write_text(discovery.render(root), encoding="utf-8")
    out = []
    sc_state.run(ctx_for(root), out)
    return codes_of(out)


def cases():
    out = [
        ("STATE001", "看板整个不在",
         "STATE001" in codes_for(BOARD_OK, extra={".harness/tasks/board.json": None})),
    ]
    # 「不在」与「在但是空的」是两件事，各造一条
    out.append(("STATE001b", "tasks 是空数组：空看板与都做完了长得一样",
                "STATE001" in codes_for(with_tasks([]))))
    out += [
        ("STATE002", "任务缺 priority",
         "STATE002" in codes_for(with_tasks([{k: v for k, v in TASK_OPEN.items() if k != "priority"}]))),
        ("STATE002b", "updated 不是日期：时效判不了",
         "STATE002" in codes_for(with_tasks([TASK_OPEN], updated="上周三"))),
        ("STATE002c", "updated 在未来：未来的账本只有计划没有事实",
         "STATE002" in codes_for(with_tasks([TASK_OPEN], updated="2099-01-01"))),
        ("STATE003", "status 用同义词（进行中）",
         "STATE003" in codes_for(with_tasks([{**TASK_OPEN, "status": "进行中"}]))),
        ("STATE003b", "priority 不在闭集",
         "STATE003" in codes_for(with_tasks([{**TASK_OPEN, "priority": "urgent"}]))),
        ("STATE003c", "blocked 没写等什么",
         "STATE003" in codes_for(with_tasks([{**TASK_OPEN, "status": "blocked"}]))),
        ("STATE004", "两条任务同号",
         "STATE004" in codes_for(with_tasks([TASK_OPEN, dict(TASK_OPEN)]))),
        ("STATE005", "done 没有 evidence",
         "STATE005" in codes_for(with_tasks([{k: v for k, v in TASK_DONE.items() if k != "evidence"}]))),
        ("STATE005b", "evidence 不是 commit: 也不是 path:",
         "STATE005" in codes_for(with_tasks([{**TASK_DONE, "evidence": "已经确认过了"}]))),
        ("STATE006", "path: 指向的文件不在磁盘上",
         "STATE006" in codes_for(with_tasks([{**TASK_DONE, "evidence": "path:gone.txt"}]))),
        ("STATE006b", "commit: 在没有 git 的树里——判不了，报 WARN 不冒充通过",
         "STATE006" in codes_for(with_tasks([{**TASK_DONE, "evidence": "commit:deadbeef"}]))),
        ("STATE007", "INDEX 与现算的不一致（派生过期）", "STATE007" in codes_for(BOARD_OK)),
        ("STATE008", "看板 35 天没动（额度 30 天）",
         "STATE008" in codes_for(with_tasks([TASK_OPEN],
                                            updated=(date.today() - timedelta(days=35)).isoformat()))),
        ("STATE008b", "看板 61 天没动（两倍额度）→ ERROR",
         "STATE008" in codes_for(with_tasks([TASK_OPEN],
                                            updated=(date.today() - timedelta(days=61)).isoformat()))),
        ("STATE00n", "正对照：形状齐、证据在、INDEX 是现算的", bool(control_codes())),
    ]
    return out
