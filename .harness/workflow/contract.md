# 契约：动手前必须问完的六个问题

阶段 1（规划）的输入。六问没答完就动手 = 让 agent 替使用者猜，猜错的代价是整层返工。
**答案记进 `.harness/memory/decisions.md`**（带日期与 status），本文件只留问题与本仓库的既成答案。
无人可问时（无头跑批）按保守默认作答并标 `assumed: true`，不许跳过这一节。

## 一、记忆放哪

答：进 harness——`.harness/memory/`（全仓决策、踩坑）与 `.harness/specs/notes/`（模块级决策）。
不另建独立的笔记目录：两处都写等于两处都不维护。

## 二、覆盖模型：几份入口

答：根 `AGENTS.md` 一份为主，**只有规则真不同**的目录才有第二份（`.harness/`、`modules/`、
`app/`、`docs/`、`web/`、`pkg/`）。判据是「那里的规则跟别处不一样」，不是「那里有个目录」。

## 三、git 入库策略

答：`specs/`、`scripts/`、`workflow/`、`baseline.txt`、`accepted.json`、`memory/`、`tasks/`、
`deliverables/` 全部入库——状态只有进版本库才谈得上回滚与归因。
不入库的是本地噪声：`.deploy/.mysqlpw`（口令）、`codebase-guide/` 之外的派生缓存。

## 四、脚本权限：哪些自动改

答：`--fix` 只重建派生数据（`codebase-guide/index.json`），前置条件是工作区干净。
理由、版本选择、业务代码一律只报告，不代劳——脚本代劳等于伪造证据。

## 五、存量欠账：清零还是记账

答：记账。首版账本为空（零基线），bootstrap 当天的 ERROR 要么当场修掉，要么逐条进
`accepted.json`（理由 + 负责人 + 复查日期）；账本与豁免总数只减不增（BASE013）。

## 六、分几期

答：分三期。第一期 = 入口 + 断言 + 状态骨架（已完成）；第二期 = 流程层（`workflow/` +
`skills/` 对账，本批）；第三期 = 复盘与任务级隔离（`retro`/`round`/`wt` 与 `INDEX.md`）。
分期写进 `.harness/specs/standards.md` 的「第二期不做的事」，做完一条删一条。
