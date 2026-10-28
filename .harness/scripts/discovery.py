#!/usr/bin/env python3
"""discovery：把状态层拼成一眼能读完的 `.harness/INDEX.md`。

派生数据，禁手改——内容由 `scope=state` 的 STATE007 与磁盘对账（本文件的 `render()` 就是
唯一实现，脚本与断言不会各算一遍）。它只回答三个问题：下一步做什么、哪些规则没人守、
哪些流程没装机。数字一律现算，不写「大概」「上次是」。

用法：make index
"""

import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from registry import SCOPES  # noqa: E402
from scopes.entry import SCOPE_TAG, rule_blocks  # noqa: E402

INDEX_REL = ".harness/INDEX.md"
BOARD_REL = ".harness/tasks/board.json"
DECLARED_REL = ".harness/workflow/skills.declared.yaml"
SKILLS_DIR = "skills"
OPEN_STATUSES = ("open", "doing", "blocked")
GENERATED_BY = ".harness/scripts/discovery.py"


def read(root, rel):
    try:
        return (Path(root) / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def load_board(root):
    raw = read(root, BOARD_REL)
    if not raw:
        return None, "看板不在（`.harness/tasks/board.json`）——下一步没人知道"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"看板读不动：{exc}"
    return data, None


def board_block(root):
    data, problem = load_board(root)
    if problem:
        return [f"- {problem}"], []
    tasks = [t for t in (data.get("tasks") or []) if isinstance(t, dict)]
    counts = {}
    for t in tasks:
        counts[str(t.get("status") or "?")] = counts.get(str(t.get("status") or "?"), 0) + 1
    order = [s for s in OPEN_STATUSES if counts.get(s)]
    order += [s for s in sorted(counts) if s not in OPEN_STATUSES]
    if not order:
        lines = ["- 看板是空的：一个「还没做」都没登记，而空看板与「都做完」在磁盘上长得一样"]
    else:
        summary = "、".join(f"{s} {counts[s]}" for s in order)
        lines = [f"- 看板更新于 {data.get('updated') or '（没写日期）'}，共 {len(tasks)} 条：{summary}"]
    open_ones = [t for t in tasks if t.get("status") in OPEN_STATUSES]
    if not open_ones:
        lines.append("- 未完成项 0 条：这一轮的账还完了；下一条欠账出现时再回来登记。")
    high = [t for t in open_ones if t.get("priority") == "high"]
    if high:
        lines.append("- 高优先级未完成（逐条点名，不写概括句）：")
        for t in high:
            tail = f"——卡在：{t['waiting_on']}" if t.get("waiting_on") else ""
            lines.append(f"  - `{t.get('id')}` {t.get('title')}{tail}")
    blocked = [t for t in open_ones if t.get("status") == "blocked"]
    for t in blocked:
        lines.append(
            f"- `{t.get('id')}` {t.get('title')}：blocked，等 {t.get('waiting_on') or '（没写等什么）'}"
        )
    return lines, [str(t.get("id") or "?") for t in open_ones]


def scope_block():
    lines = ["| 域 | 管什么（PLAN） | code |", "| --- | --- | --- |"]
    for mod in SCOPES:
        codes = ", ".join(getattr(mod, "REFLECT", ()) or ()) or "（没登记）"
        plan = (getattr(mod, "PLAN", "") or "").replace("\n", " ").strip() or "（没登记）"
        lines.append(f"| `{mod.NAME}` | {plan} | {codes} |")
    return lines


def unguarded_block(root):
    text = read(root, "AGENTS.md")
    blocks = rule_blocks(text) if text else None
    if not blocks:
        return ["- 读不到根 `AGENTS.md` 的「硬规则」一节——判不了，不当成「规则都有人守」"]
    out = []
    for block in blocks:
        if SCOPE_TAG.search(block):
            continue
        out.append(f"- {block.strip()}")
    if not out:
        return ["- 没有：每条硬规则都指向一个已注册的域"]
    return out + ["- 这些条靠人守。要么补断言，要么留着并在评审时逐条问一遍。"]


def skills_block(root):
    import re

    declared = re.findall(r"^\s*-\s+id:\s*(\S+)\s*$", read(root, DECLARED_REL), re.M)
    base = Path(root) / SKILLS_DIR
    disk = sorted(p.name for p in base.iterdir() if p.is_dir()) if base.is_dir() else []
    lines = []
    for sid in declared:
        mark = "已装机" if sid in disk else "**没装机（声明即承诺，这条现在是空头支票）**"
        lines.append(f"- `{sid}`：{mark}")
    for sid in disk:
        if sid not in declared:
            lines.append(f"- `{sid}`：**磁盘上有但没声明**——下一次没人会去加载它")
    if not lines:
        lines = ["- 一条流程都没声明：阶段 4 的产出就是至少一条，空账本不是「不需要流程」"]
    return lines


def ledger_block(root):
    lines = []
    raw = read(root, ".harness/baseline.txt")
    rows = [ln for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    lines.append(f"- 账本 `.harness/baseline.txt`：{len(rows)} 条老账（只减不增，BASE013）")
    raw = read(root, ".harness/accepted.json")
    if not raw:
        lines.append("- 豁免 `.harness/accepted.json` 不在——判不了，不当成「没有豁免」")
        return lines
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        lines.append("- 豁免 `.harness/accepted.json` 读不动——判不了，不当成「没有豁免」")
        return lines
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and isinstance(data.get("accepted"), list):
        items = data["accepted"]
    else:
        lines.append("- 豁免文件的形状读不懂（既不是数组也没有 accepted 清单）——报不出条数，不拿 0 充数")
        return lines
    today = date.today().isoformat()
    expired = [a for a in items if isinstance(a, dict) and str(a.get("review_by") or "") < today]
    lines.append(f"- 豁免 {len(items)} 条，其中复查日期已过 {len(expired)} 条（过期未续 = BASE012）")
    for a in items:
        if isinstance(a, dict) and str(a.get("review_by") or "") < today:
            lines.append(f"  - 已过期：`{a.get('scope')}` / `{a.get('path')}`（复查日期 {a.get('review_by')}）")
    return lines


def config_block(root):
    try:
        cfg = json.loads(read(root, ".harness/config.json") or "{}")
    except json.JSONDecodeError:
        return ["- `config.json` 读不动——阈值判不了，别猜"]
    keys = ("agents_max_lines", "sub_agents_max_lines", "subject_max_chars", "board_stale_days",
            "stale_days_warn", "stale_days_error", "go_version_min")
    lines = ["| 键 | 值 |", "| --- | --- |"]
    for k in keys:
        if k in cfg:
            lines.append(f"| `{k}` | {cfg[k]} |")
    budget = cfg.get("budget")
    if isinstance(budget, dict):
        lines.append(f"| `budget` | {', '.join(f'{k}={v}' for k, v in sorted(budget.items()))} |")
    lines.append(f"| `slow_scopes` | {', '.join(cfg.get('slow_scopes') or []) or '（无）'} |")
    return lines


def render(root):
    root = Path(root)
    board_lines, _open_ids = board_block(root)
    sections = [
        ("下一步（看板）", board_lines),
        ("检查面：已注册的域", scope_block()),
        ("没有断言兜着的规则", unguarded_block(root)),
        ("可安装流程", skills_block(root)),
        ("账与豁免", ledger_block(root)),
        ("阈值（唯一来源 config.json）", config_block(root)),
    ]
    out = [
        "# INDEX.md — 这套 harness 现在长什么样",
        "",
        f"派生数据：由 `{GENERATED_BY}` 生成，禁手改；过期由 `scope=state`（STATE007）抓。",
        "它只回答三件事：下一步做什么、哪些规则没人守、哪些流程没装机。",
        "",
    ]
    for title, lines in sections:
        out += [f"## {title}", ""] + lines + [""]
    return "\n".join(out).rstrip() + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    # `--root X` 与位置参数都收：Makefile 统一用 `--root`，人手敲的路径也别报错。
    if argv[:1] == ["--root"]:
        del argv[0:1]
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        # 以 `-` 开头的参数若被当成仓库根，就在错的目录里凭空长出一棵 .harness/ 树
        print(f"参数不对：{argv}\n用法：discovery.py [--root 仓库根]", file=sys.stderr)
        return 2
    root = Path(argv[0]).resolve() if argv else HERE.parents[1]
    target = root / INDEX_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(root), encoding="utf-8")
    print(f"wrote {target.relative_to(root)}（派生数据，改动请用 make index）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
