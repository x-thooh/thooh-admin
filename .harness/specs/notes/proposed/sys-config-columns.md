# 笔记：`sys_config` 的列名以哪一边为准

- scope: `app/admin/model/system`
- status: proposed
- written_by: session 2026-10-28
- version: 1
- supersedes: —
- 看板：`T-1`（`.harness/tasks/board.json`）

## 问题

`thooh-go.sql:390` 建表用的是短列名（`id`、`kenam`、`keval`、`name`、`notes`、`ornum`、
`crtim`、`uptim`），而 `app/admin/model/system/sysConfig.go:12` 的 GORM tag 用的是
`config_id`、`config_key`、`config_value`、`create_time`……。两边现在对不上，按模型查这张表
会在运行时报 Unknown column——编译与 `make check` 都判不出来。

## 不显然之处

**这不是「dump 写错了」那种一边倒的错**：短列名是全仓一致的命名风格（同批 dump 里其它
`sys_*` 表也是 `crtim`/`uptim`/`intag`），说明这套列名曾经是刻意的方案，模型那侧才是后来改的。
所以「改 DDL 迁就模型」可能同时推翻另外十几张表的约定；而「改模型 tag 迁就 DDL」要让
`json` 字段名与前端契约一起动。两个方向都不是免费午饭，选错的那边会把漂移摊到全仓。

## 提案（两个方向，等使用者定）

- A：以模型为准，改 DDL（`sys_config` 一张表先迁），代价是要写一次真实迁移，且与其余
  `sys_*` 表的短名风格分裂。
- B：以 DDL 为准，改模型 tag（9 个字段），代价是 `json` 输出键名跟着变，前端要一起改。

判据补一条就够：定下来之后，把「模型 tag ↔ dump 列名」做成断言（新 code 挂在 `modules`
或新的 `schema` 域），否则这个漂移会一直静默。**现在没有任何断言覆盖它**——这是它活到今天的
原因，也是这篇笔记存在的理由。
