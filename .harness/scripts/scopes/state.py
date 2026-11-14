"""state: 状态层自己站得住——看板是真事实，INDEX 是新鲜的派生数据。

  STATE001  board.json 缺失、读不动，或 tasks 为空（0 样本守卫，断言坑 #11）
  STATE002  条目不成形：缺 id/title/status/priority 之一（写了空算没写），或 `updated` 不是合法日期、在未来
  STATE003  status/priority 不在闭集；blocked 没写 waiting_on——「被什么卡住」正是这条记录的意义
  STATE004  id 重复：看板靠 id 说话，两条同号等于没人知道说的是哪条
  STATE005  done 却没有 evidence，或证据不是 `commit:<sha>` / `path:<文件>`
  STATE006  证据核验失败：commit 取不到对象、path 文件不存在；没有 git 时报 WARN 并登记判不了
  STATE007  INDEX.md 缺失或与现算的不一致（派生过期；`--fix` 可重建）
  STATE008  看板过期：`updated` 落后超过 `board_stale_days` 天 WARN，两倍即 ERROR（限时而非禁止）

`scope=state` 管的是「状态是不是真的」，不管账本（那是 baseline 域）。
INDEX 的重建走 `discovery.render()`——生成与校验共用一份实现，两个各算一遍的口径迟早漂移。
"""

import re
import subprocess
from datetime import date, datetime
from pathlib import Path

import ageing

from .common import add, as_list, load_json, number, text

NAME = "state"

PLAN = "状态层是事实不是装饰：看板每条有形状与闭集取值、完成态带可核验证据，INDEX 与磁盘现算一致"
REFLECT = (
    "STATE001",
    "STATE002",
    "STATE003",
    "STATE004",
    "STATE005",
    "STATE006",
    "STATE007",
    "STATE008",
)

BOARD_REL = ".harness/tasks/board.json"
INDEX_REL = ".harness/INDEX.md"
STATUSES = ("open", "doing", "blocked", "done")
PRIORITIES = ("high", "medium", "low")
REQUIRED = ("id", "title", "status", "priority")
EVIDENCE = re.compile(r"^(commit:([0-9a-f]{7,40})|path:(\S+))$")
DEFAULT_STALE_DAYS = 30


def parse_day(value):
    """ISO 日期 → date；不是日期就返回 None（缺失与坏值分开判，不静默当 0 天）。"""
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def has_commit(root, sha):
    """True/False = 有没有这个提交对象；None = 判不了（这里没有 git 可问）。"""
    # 目标就是本仓库：root 即被检的那棵树
    inside = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-dir"],
                            check=False, capture_output=True, text=True)
    if inside.returncode != 0:
        return None
    # 目标就是本仓库：root 即被检的那棵树
    probe = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{sha}^{{commit}}"],
                           check=False, capture_output=True, text=True)
    return probe.returncode == 0


def check_task(task, index, findings, root):
    tid = f"第 {index + 1} 条"
    if not isinstance(task, dict):
        add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE002", f"{tid} 不是对象：读不出它是什么任务")
        return
    tid = str(task.get("id") or tid).strip() or tid
    for field in REQUIRED:
        if not text(task.get(field)):
            add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE002",
                f"{tid} 缺 {field}（或写了空）：缺一项这条任务就没人能接着做")
    status = str(task.get("status") or "").strip()
    priority = str(task.get("priority") or "").strip()
    if status and status not in STATUSES:
        add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE003",
            f"{tid} 的 status={status!r} 不在闭集 {list(STATUSES)}：同义词让聚合口径失效")
    if priority and priority not in PRIORITIES:
        add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE003",
            f"{tid} 的 priority={priority!r} 不在闭集 {list(PRIORITIES)}")
    if status == "blocked" and not text(task.get("waiting_on")):
        add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE003",
            f"{tid} 标了 blocked 却没写 waiting_on：「被什么卡住」正是这条记录的全部意义")
    if status == "done":
        evidence = str(task.get("evidence") or "").strip()
        if not evidence:
            add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE005",
                f"{tid} 标了 done 但没有 evidence：完成态必须带可核验证据（commit:<sha> 或 path:<文件>）")
            return
        m = EVIDENCE.match(evidence)
        if not m:
            add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE005",
                f"{tid} 的 evidence={evidence!r} 不是 commit:<sha> 也不是 path:<文件>：核对不了")
            return
        if m.group(2):
            state = has_commit(root, m.group(2))
            if state is False:
                add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE006",
                    f"{tid} 的证据 commit:{m.group(2)} 在本仓库取不到：引用一个不存在的完成是假账")
            elif state is None:
                add(findings, "WARN", NAME, BOARD_REL, 1, "STATE006",
                    f"{tid} 的证据是 commit:{m.group(2)}，但这里没有 git 可查——判不了，不是通过")
        elif not (Path(root) / m.group(3)).is_file():
            add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE006",
                f"{tid} 的证据 path:{m.group(3)} 在磁盘上不存在：文件没了，这条 done 就没人认")


def check_board(root, findings, quality):
    board = load_json(root, BOARD_REL, NAME, findings, "STATE001")
    if board is None or not isinstance(board, dict):
        return
    tasks = as_list(board.get("tasks"))
    if not tasks:
        add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE001",
            "tasks 是空的：一个「还没做」都没登记，而空看板与「都做完了」在磁盘上长得一样")
        return
    seen = {}
    today = date.today()
    for i, task in enumerate(tasks):
        check_task(task, i, findings, root)
        if isinstance(task, dict) and text(task.get("id")):
            key = str(task.get("id")).strip()
            seen[key] = seen.get(key, 0) + 1
    for tid, count in sorted(seen.items()):
        if count > 1:
            add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE004",
                f"id {tid} 出现 {count} 次：看板靠 id 说话，两条同号等于没人知道说的是哪条")
    updated = parse_day(board.get("updated"))
    if updated is None:
        add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE002",
            f"看板的 updated={board.get('updated')!r} 不是 YYYY-MM-DD：时效判不了，别说它新鲜")
        return
    if updated > today:
        add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE002",
            f"看板的 updated={updated} 在未来：未来的账本没有事实，只有计划")
        return
    raw_limit = quality.get("board_stale_days") if isinstance(quality, dict) else None
    limit = number(raw_limit) or DEFAULT_STALE_DAYS
    days = ageing.age_days(ageing.day_ts(updated), ageing.day_ts(today))
    if days >= 2 * limit:
        add(findings, "ERROR", NAME, BOARD_REL, 1, "STATE008",
            f"看板已经 {days} 天没动（额度 {limit} 天的两倍）：过期到没人会再信它，就该当问题处理")
    elif days >= limit:
        add(findings, "WARN", NAME, BOARD_REL, 1, "STATE008",
            f"看板已经 {days} 天没动（{limit} 天为限）：不是禁止，但下一步该由它说话时它得是新鲜的")


def check_index(root, findings):
    import discovery

    path = Path(root) / INDEX_REL
    expected = discovery.render(root)
    if not path.is_file():
        add(findings, "ERROR", NAME, INDEX_REL, 1, "STATE007",
            f"{INDEX_REL} 不存在：跑 make index 生成")
        return
    try:
        actual = path.read_text(encoding="utf-8")
    except OSError as exc:
        add(findings, "ERROR", NAME, INDEX_REL, 1, "STATE007", f"读不了：{exc}")
        return
    if actual != expected:
        add(findings, "ERROR", NAME, INDEX_REL, 1, "STATE007",
            "INDEX.md 与现算的不一致（派生数据过期或被人手改过）：跑 make index，别手改")


def _fix_index(root):
    import discovery

    target = Path(root) / INDEX_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(discovery.render(root), encoding="utf-8")
    return f"重生成 {INDEX_REL}"


FIXERS = {"STATE007": (_fix_index, INDEX_REL)}


def run(ctx, findings):
    root = Path(ctx["root"])
    quality = ctx.get("quality") or {}
    check_board(root, findings, quality)
    check_index(root, findings)
