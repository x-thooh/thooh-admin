"""workflow: 流程层（`.harness/workflow/` + 仓库根 `skills/`）自己站得住。

  FLOW001  flow.json 不在、读不动、stages 为空或条目不成形（0 样本守卫）
  FLOW002  阶段清单与 REQUIRED_STAGES 不齐：缺一段，或多出一段没登记的
  FLOW003  某个阶段既没有 gate（可跑的门径）也没有 manual（明写人判）——没有过法的步骤等于没做
  FLOW004  门径指的 make target 在 Makefile 里不存在，或 Makefile 根本读不到
  FLOW005  转移表为空、某条 from/to 指向不存在的阶段、没写条件，或非末阶段没有出口
  FLOW006  skills.declared.yaml 不在、读不动，或一条都没声明
  FLOW007  声明了但 skills/<id>/ 不在磁盘上：声明即承诺，没装机就是空头支票
  FLOW008  skills/ 下有目录但没声明：多一条没人知道的流程，等于没有流程
  FLOW009  流程的 SKILL.md 不在，或缺「什么时候跑 / 怎么跑 / 怎么验证装好了」之一
  FLOW010  contract.md 不在，或六问缺一条

为什么 gate 复用 `cmd.make_targets` 而不是自己再写一遍正则：「这条命令存不存在」是同一个判据，
让两个域各判一遍，两边就会各自漂移，而报错的人看不出该信谁。
"""

import re
from pathlib import Path

from .cmd import make_targets
from .common import add, as_list, load_json, rel_to, text

NAME = "workflow"

PLAN = "一次修改的五段循环有唯一事实源（flow.json：阶段、门径、转移），可安装流程的声明与磁盘双向对账"
REFLECT = (
    "FLOW001",
    "FLOW002",
    "FLOW003",
    "FLOW004",
    "FLOW005",
    "FLOW006",
    "FLOW007",
    "FLOW008",
    "FLOW009",
    "FLOW010",
)

FLOW_REL = ".harness/workflow/flow.json"
DECLARED_REL = ".harness/workflow/skills.declared.yaml"
CONTRACT_REL = ".harness/workflow/contract.md"
SKILLS_DIR = "skills"

REQUIRED_STAGES = ("survey", "plan", "act", "reflect", "deliver")
SKILL_SECTIONS = ("什么时候跑", "怎么跑", "怎么验证装好了")
CONTRACT_QUESTIONS = ("记忆放哪", "覆盖模型", "入库策略", "脚本权限", "存量欠账", "分几期")
DECLARED_ID = re.compile(r"^\s*-\s+id:\s*(\S+)\s*$", re.M)


def read_of(path):
    """读文本；读不到当空串——缺失由各个检查自己判，不在这里抛。"""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def skill_dirs(root):
    base = Path(root) / SKILLS_DIR
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


def declared_ids(root, findings):
    """声明账本里的 id 清单；账本不可用时返回 None（调用方不许拿空清单当「没装」）。"""
    path = Path(root) / DECLARED_REL
    if not path.is_file():
        add(findings, "ERROR", NAME, DECLARED_REL, 1, "FLOW006",
            "声明账本不在：磁盘侧与意图侧无从对账，判不了不等于合规")
        return None
    ids = DECLARED_ID.findall(read_of(path))
    if not ids:
        add(findings, "ERROR", NAME, DECLARED_REL, 1, "FLOW006",
            "文件在但一条流程都没声明：0 条与「这个仓库不需要流程」在磁盘上长得一模一样。"
            "真决定不装就把 workflow 层一起撤掉，别留一个空账本当通过")
    return ids


def check_stages(flow, findings, targets):
    entries = as_list(flow.get("stages"))
    if not entries:
        add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW001",
            "stages 是空的：0 个阶段与「流程没问题」长得一模一样（断言坑 #11）")
        return []
    stages = [e for e in entries if isinstance(e, dict)]
    if len(stages) != len(entries):
        add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW001",
            f"stages 里有 {len(entries) - len(stages)} 条不是对象：读不出 id 与 gate，等于没写")
    ids = [str(s.get("id") or "").strip() for s in stages]
    if any(not i for i in ids):
        add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW001", "有阶段没写 id：转移表没法指向它")
    named = {i for i in ids if i}
    for miss in [r for r in REQUIRED_STAGES if r not in named]:
        add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW002",
            f"缺阶段 {miss}：五段循环少一段，剩下的门径就不成立（没盘点过的「改完就绿」不是结论）")
    for extra in sorted(named - set(REQUIRED_STAGES)):
        add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW002",
            f"多出一个阶段 {extra}，不在 REQUIRED_STAGES 常量表里：加阶段先改脚本里的表，别只改数据")

    for stage in stages:
        sid = str(stage.get("id") or "?").strip()
        gate, manual = stage.get("gate"), stage.get("manual")
        if not text(gate) and not text(manual):
            add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW003",
                f"阶段 {sid} 既没有 gate 也没有 manual：写了空算没写（缺失≠空≠0）——"
                "这一步没有过法，走到这里的人只能自己编")
            continue
        if not text(gate):
            continue
        g = str(gate).strip()
        if g not in targets:
            add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW004",
                f"阶段 {sid} 的门径是 `make {g}`，Makefile 里没有这个 target："
                "流程不能承诺一条跑不了的命令")
    return [i for i in ids if i]


def check_transitions(flow, findings, ids):
    if not ids:
        return
    trans = as_list(flow.get("transitions"))
    if not trans:
        add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW005",
            "transitions 是空的：阶段之间没有过法，五段就只是五个词")
        return
    named, last, froms = set(ids), ids[-1], set()
    for t in trans:
        if not isinstance(t, dict):
            add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW005", "有一条转移不是对象：读不出 from/to")
            continue
        src, dst = str(t.get("from") or ""), str(t.get("to") or "")
        for side, val in (("from", src), ("to", dst)):
            if val not in named:
                add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW005",
                    f"转移 {src}→{dst} 的 {side}={val!r} 不在 stages 里：指向一个不存在的阶段")
        if not text(t.get("on")):
            add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW005",
                f"转移 {src}→{dst} 没写 on（什么时候走这条）：没有条件的转移是路线，不是规则")
        froms.add(src)
    for sid in ids:
        if sid != last and sid not in froms:
            add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW005",
                f"阶段 {sid} 没有出口转移：走到这里就断了，而断掉的一步没人会补")


def check_skills(root, findings, declared, disk):
    for sid in sorted(disk - declared):
        add(findings, "ERROR", NAME, f"{SKILLS_DIR}/{sid}", 1, "FLOW008",
            f"磁盘上有 skills/{sid}/ 但声明账本里没有：多一条没人登记的流程，"
            "下一次没人会去加载它")
    for sid in sorted(declared - disk):
        add(findings, "ERROR", NAME, DECLARED_REL, 1, "FLOW007",
            f"声明了 {sid} 但磁盘上没有 skills/{sid}/：声明即承诺，这条现在是空头支票")
    for sid in sorted(declared & disk):
        path = Path(root) / SKILLS_DIR / sid / "SKILL.md"
        rel = f"{SKILLS_DIR}/{sid}/SKILL.md"
        if not path.is_file():
            add(findings, "ERROR", NAME, rel, 1, "FLOW009",
                f"{sid} 装机了但没有 SKILL.md：流程只存在于目录名里")
            continue
        body = read_of(path)
        for section in SKILL_SECTIONS:
            if f"## {section}" not in body:
                add(findings, "ERROR", NAME, rel, 1, "FLOW009",
                    f"{sid} 的 SKILL.md 缺「## {section}」：三条缺一就不是可安装流程，"
                    "而是半本操作手册")


def check_contract(root, findings):
    path = Path(root) / CONTRACT_REL
    if not path.is_file():
        add(findings, "ERROR", NAME, CONTRACT_REL, 1, "FLOW010",
            "契约文件不在：六问没答完就动手，猜错的代价是整层返工")
        return
    body = read_of(path)
    for question in CONTRACT_QUESTIONS:
        if question not in body:
            add(findings, "ERROR", NAME, CONTRACT_REL, 1, "FLOW010",
                f"契约里少了「{question}」这一问：少一问就是替使用者猜了一件事")


def run(ctx, findings):
    root = Path(ctx["root"])
    makefile = root / "Makefile"
    targets = make_targets(read_of(makefile)) if makefile.is_file() else set()
    if not targets:
        add(findings, "ERROR", NAME, rel_to(root, makefile), 1, "FLOW004",
            "读不到 Makefile 里带 `##` 说明的 target：门径无从对账，「没对上」与「没法对」都是判不了")
    ids = []
    flow = load_json(root, FLOW_REL, NAME, findings, "FLOW001")
    if flow is not None and not isinstance(flow, dict):
        add(findings, "ERROR", NAME, FLOW_REL, 1, "FLOW001",
            "flow.json 顶层不是对象：阶段与转移没处放，读它的人只能猜")
    elif isinstance(flow, dict):
        ids = check_stages(flow, findings, targets)
        check_transitions(flow, findings, ids)

    declared = declared_ids(root, findings)
    disk = set(skill_dirs(root))
    if declared is not None:
        check_skills(root, findings, set(declared), disk)
    check_contract(root, findings)
