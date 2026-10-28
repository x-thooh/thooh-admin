"""workflow：flow.json ↔ Makefile ↔ skills 声明/磁盘 ↔ 契约。

夹具是一棵最小仓库：五段 flow.json、一份带 `##` 说明的 Makefile、一条已装机的流程、契约六问。
每条样本只坏一处——「两边同时坏」判不出是谁的功劳，正对照也一样：夹具全对时必须 0 条。
"""

import json

from scopes import workflow as sc_wf
from support import codes_of, ctx_for, new_root

NAME = "workflow"

MAKEFILE = """ROOT := .
.PHONY: check selftest evidence

check: ## 跑门禁
\t@echo check
selftest: ## 反向测试
\t@echo t
evidence: ## 存证据
\t@echo e
"""

STAGES = [
    {"id": "survey", "title": "盘点", "gate": "check"},
    {"id": "plan", "title": "规划", "manual": "六问答完由评审人核"},
    {"id": "act", "title": "行动", "gate": "check"},
    {"id": "reflect", "title": "反思", "gate": "selftest"},
    {"id": "deliver", "title": "交付", "gate": "evidence"},
]
TRANSITIONS = [
    {"from": "survey", "to": "plan", "on": "基准已记录"},
    {"from": "plan", "to": "act", "on": "规则写好"},
    {"from": "act", "to": "reflect", "on": "门禁退出码 0"},
    {"from": "reflect", "to": "deliver", "on": "上升已归因"},
]
FLOW = {"name": "最小流程", "stages": STAGES, "transitions": TRANSITIONS}

DECLARED = "skills:\n  - id: demo\n    title: 演示流程\n"
SKILL = """# 流程：演示

## 什么时候跑

需要的时候。

## 怎么跑

`make check`。

## 怎么验证装好了

删掉一处登记，`make check` 必须报出来。
"""
CONTRACT = """# 契约：动手前六个问题

## 一、记忆放哪

答：进 harness。

## 二、覆盖模型

答：根一份为主。

## 三、git 入库策略

答：状态入库。

## 四、脚本权限

答：`--fix` 只重建派生数据。

## 五、存量欠账

答：记账。

## 六、分几期

答：三期。
"""


def flow_of(stages=None, transitions=None):
    return json.dumps(
        {
            "name": "最小流程",
            "stages": STAGES if stages is None else stages,
            "transitions": TRANSITIONS if transitions is None else transitions,
        },
        ensure_ascii=False,
    )


def fixture(**over):
    files = {
        "Makefile": MAKEFILE,
        ".harness/workflow/flow.json": flow_of(),
        ".harness/workflow/skills.declared.yaml": DECLARED,
        ".harness/workflow/contract.md": CONTRACT,
        "skills/demo/SKILL.md": SKILL,
    }
    files.update(over)
    return new_root({k: v for k, v in files.items() if v is not None})


def fired(files, code):
    out = []
    sc_wf.run(ctx_for(fixture(**files)), out)
    return code in codes_of(out)


def cases():
    out = []

    out.append(("FLOW001", "flow.json 整个不在：判不了不是合规",
                fired({".harness/workflow/flow.json": None}, "FLOW001")))
    out.append(("FLOW001b", "stages 是空数组：0 个阶段与全绿长得一样",
                fired({".harness/workflow/flow.json": flow_of(stages=[])}, "FLOW001")))
    out.append(("FLOW001c", "顶层不是对象",
                fired({".harness/workflow/flow.json": "[1, 2]"}, "FLOW001")))

    no_plan = [s for s in STAGES if s["id"] != "plan"]
    t = [{"from": "survey", "to": "act", "on": "基准已记录"}] + TRANSITIONS[1:]
    out.append(("FLOW002", "五段少了 plan",
                fired({".harness/workflow/flow.json": flow_of(stages=no_plan, transitions=t)}, "FLOW002")))
    extra = [s for s in STAGES if s["id"] != "deliver"]
    extra += [{"id": "audit", "title": "审计", "gate": "check"}, STAGES[4]]
    tx = TRANSITIONS[:3] + [{"from": "reflect", "to": "audit", "on": "归因完"},
                            {"from": "audit", "to": "deliver", "on": "审计过"}]
    out.append(("FLOW002b", "多出一个常量表里没登记的阶段",
                fired({".harness/workflow/flow.json": flow_of(stages=extra, transitions=tx)}, "FLOW002")))

    no_gate = [dict(s) for s in STAGES]
    no_gate[0]["gate"] = ""
    out.append(("FLOW003", "survey 既没 gate 也没 manual（写了空）",
                fired({".harness/workflow/flow.json": flow_of(stages=no_gate)}, "FLOW003")))

    ghost = [dict(s) for s in STAGES]
    ghost[0]["gate"] = "ghost"
    out.append(("FLOW004", "门径写 make ghost，Makefile 里没这个 target",
                fired({".harness/workflow/flow.json": flow_of(stages=ghost)}, "FLOW004")))
    out.append(("FLOW004b", "Makefile 读不到：门径无从对账",
                fired({"Makefile": None}, "FLOW004")))

    out.append(("FLOW005", "transitions 是空的：五段只是五个词",
                fired({".harness/workflow/flow.json": flow_of(transitions=[])}, "FLOW005")))
    out.append(("FLOW005b", "转移指向不存在的阶段",
                fired({".harness/workflow/flow.json": flow_of(
                    transitions=TRANSITIONS[:3] + [{"from": "reflect", "to": "ship", "on": "好了"}])}, "FLOW005")))
    out.append(("FLOW005c", "非末阶段没有出口（砍掉 reflect→deliver）",
                fired({".harness/workflow/flow.json": flow_of(transitions=TRANSITIONS[:3])}, "FLOW005")))
    out.append(("FLOW005d", "转移没写条件 on",
                fired({".harness/workflow/flow.json": flow_of(
                    transitions=TRANSITIONS[:3] + [{"from": "reflect", "to": "deliver"}])}, "FLOW005")))

    out.append(("FLOW006", "声明账本不在",
                fired({".harness/workflow/skills.declared.yaml": None}, "FLOW006")))
    out.append(("FLOW006b", "账本在但一条都没声明",
                fired({".harness/workflow/skills.declared.yaml": "skills:\n"}, "FLOW006")))

    out.append(("FLOW007", "声明了 demo 但 skills/demo/ 不在磁盘上",
                fired({"skills/demo/SKILL.md": None}, "FLOW007")))
    out.append(("FLOW008", "磁盘上有 skills/loose/ 但没声明",
                fired({"skills/loose/SKILL.md": SKILL}, "FLOW008")))

    thin = SKILL.replace("## 怎么验证装好了", "## 备注")
    out.append(("FLOW009", "SKILL.md 缺「怎么验证装好了」这一条",
                fired({"skills/demo/SKILL.md": thin}, "FLOW009")))

    out.append(("FLOW010", "契约文件不在",
                fired({".harness/workflow/contract.md": None}, "FLOW010")))
    out.append(("FLOW010b", "契约里少了「分几期」这一问",
                fired({".harness/workflow/contract.md": CONTRACT.replace("分几期", "分期安排")}, "FLOW010")))

    f = []
    sc_wf.run(ctx_for(fixture()), f)
    out.append(("FLOW00n", "正对照：阶段齐、门径可跑、声明与磁盘一致", bool(codes_of(f))))
    return out
