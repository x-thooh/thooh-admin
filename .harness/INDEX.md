# INDEX.md — 这套 harness 现在长什么样

派生数据：由 `.harness/scripts/discovery.py` 生成，禁手改；过期由 `scope=state`（STATE007）抓。
它只回答三件事：下一步做什么、哪些规则没人守、哪些流程没装机。

## 下一步（看板）

- 看板更新于 2026-10-30，共 39 条：open 3、doing 1、blocked 1、done 34
- 高优先级未完成（逐条点名，不写概括句）：
  - `T-1` sys_config 的 DDL 与 GORM 模型列名不一致
  - `T-20` app/admin/model 的列名以 thooh-go.sql 为准重写
- `T-9` main.go 里 r.Static() 挂载的 ./static/images 目录不存在：blocked，等 使用者回答：静态资源是否入库

## 检查面：已注册的域

| 域 | 管什么（PLAN） | code |
| --- | --- | --- |
| `entry` | 入口文件（根与各目录 AGENTS.md）自己站得住：头部 scope/parent、目录地图与磁盘双向比对、每条规则指向真存在的 code、派生索引不过期 | ENT001, ENT002, ENT003, ENT004, ENT005, ENT006, ENT007, ENT008 |
| `git` | 直接 `git -C` 的调用要么摘掉钩子环境（env=gitenv.clean()），要么注明目标就是本仓库 | GTE001 |
| `commit` | 一次提交一件事：标题是动宾短语、不并列、不超长；正文出现「顺带/另外/同时」就是该拆的信号 | MSG001, MSG002, MSG003, MSG004, MSG005 |
| `cmd` | 入口的命令表、Makefile 的 target、磁盘上的脚本三方一一对应：表里没有的不算命令，Makefile 里没有的不算文档 | CMD001, CMD002, CMD003, CMD004, CMD005 |
| `workflow` | 一次修改的五段循环有唯一事实源（flow.json：阶段、门径、转移），可安装流程的声明与磁盘双向对账 | FLOW001, FLOW002, FLOW003, FLOW004, FLOW005, FLOW006, FLOW007, FLOW008, FLOW009, FLOW010 |
| `hooks` | 动手前每个域说清自己管什么（PLAN）、复盘时能报哪些 code（REFLECT）；这张表与 scopes/ 源码逐条对账 | HOOK001, HOOK002, HOOK003, HOOK004, HOOK005 |
| `budget` | 工具层每个文件按角色有行数额度（域 / 调度 / 共享 helper / 反向语料），超限即该拆；额度写在 config.json | BUDGET001, BUDGET002 |
| `modules` | 业务模块清单与 `app/admin/router.go` 的注册表双向对账：多一个没注册的模块、少一个还在注册的文件都算缺陷；模块骨架（api.go/model.go/router.go）齐不齐也在这里判 | MOD001, MOD002, MOD003, MOD004, MOD005, GTE001 |
| `secret` | 配置里的密钥与弱凭据：只报「哪个键路径有问题」，永不报出值本身；命中基线的老账标「基线内」 | SEC001, SEC002, SEC003, SEC004, SEC005 |
| `stale` | 会过期的引用：前端产物里被 `r.Static()` 挂载的资产还存不存在、swagger 三份元数据（注解 / docs.go / json / yaml）是否互相一致、文档时效是否越过告警线 | STL001, STL002, STL003, STL004, STL005 |
| `state` | 状态层是事实不是装饰：看板每条有形状与闭集取值、完成态带可核验证据，INDEX 与磁盘现算一致 | STATE001, STATE002, STATE003, STATE004, STATE005, STATE006, STATE007, STATE008 |
| `worktree` | 任务级隔离是真的：每棵任务树在看板里有对应的进行中任务、分支名与树对得上、任务做完树就撤 | WKT001, WKT002, WKT003, WKT004 |
| `build` | 慢域：go.mod 的工具链下限、`go build` / `go vet` 是否真的跑过并留下带 commit 的证据、证据是否过期、gofmt 是否干净 | BLD001, BLD002, BLD003, BLD004, BLD005, BLD006 |
| `baseline` | 存量欠账的账本：老账逐条标「基线内 / 新欠」，总数只减不增；accepted 豁免必须有理由、负责人和未过期的复查日期 | BASE011, BASE012, BASE013, BASE014 |

## 没有断言兜着的规则

- 没有：每条硬规则都指向一个已注册的域

## 可安装流程

- `add-module`：已装机

## 账与豁免

- 账本 `.harness/baseline.txt`：0 条老账（只减不增，BASE013）
- 豁免 0 条，其中复查日期已过 0 条（过期未续 = BASE012）

## 阈值（唯一来源 config.json）

| 键 | 值 |
| --- | --- |
| `agents_max_lines` | 150 |
| `sub_agents_max_lines` | 80 |
| `subject_max_chars` | 50 |
| `board_stale_days` | 30 |
| `stale_days_warn` | 7 |
| `stale_days_error` | 14 |
| `go_version_min` | 1.25 |
| `budget` | corpus=500, scopes=300, scripts=300, shared=420 |
| `slow_scopes` | build |
