# 规范：规则 ↔ 断言对照表

这是 `AGENTS.md`「硬规则」的执行侧台账：一条规则要么有断言，要么写明「无断言」+ 强度来源。
要么有断言要么没人守——写「应该」而没人检查，等于没写。

阈值与路径都在 `.harness/config.json`（单一来源），本文件不重复数字。

## 已注册的域

| 域 | 管什么 | 快/慢 | 文件 |
| --- | --- | --- | --- |
| `entry` | 入口文件、目录地图、派生索引 | 快 | `scripts/scopes/entry.py` |
| `modules` | 功能模块 ↔ `app/admin/router.go` 双向对账 | 快 | `scripts/scopes/modules.py` |
| `secret` | 凭据入库、弱默认、本地覆盖文件 | 快 | `scripts/scopes/secret.py` |
| `stale` | swagger 三方一致、web 产物引用、生成物时效 | 快 | `scripts/scopes/stale.py` |
| `build` | go build / vet / gofmt / go 指令 / 证据时效 | 慢 | `scripts/scopes/build.py` |
| `baseline` | 账本格式、豁免保质期、总数只减不增 | 快 | `scripts/scopes/baseline.py` |

## 规则 ↔ 断言

| # | 规则 | 断言 | 严重度 | 反向样本 |
| --- | --- | --- | --- | --- |
| 1 | 命令只从 `Makefile` 走 | 无断言（人判）。强度来源：`make help` 的清单与本文件「常用命令」表一一对应；第二期把它做成 `scripts` 域的断言（未注册脚本报错） | — | — |
| 2 | 模块要在两处登记 | `scope=modules`：MOD001 未注册、MOD002 死引用、MOD003 只 import 不挂、MOD004 形状不完整、MOD005 样本为 0 | ERROR | `make selftest`：MOD001–MOD005、MOD003c（注释里的挂载不算）、MOD00n 正对照 |
| 3 | 提交前 `make check` 退出码 0；合并前 `make check-all` | `scope=build`：BLD003 编译/vet 失败、BLD005 未 gofmt；BLD001/BLD002 证据缺失与过期为 WARN（留痕是流程账，不当提交门）。`.git/hooks` 由 `make init` 装 pre-commit 跑快域 | ERROR / WARN | BLD003、BLD005、BLD001、BLD002 + 两条正对照 |
| 4 | go 指令不低于 `go_version_min` | `scope=build`：BLD006 | ERROR | BLD006 + BLD006n |
| 5 | 密钥与本地覆盖配置不入库 | `scope=secret`：SEC001 高熵、SEC002 弱默认（WARN）、SEC003 覆盖文件被跟踪、SEC004 样本为 0 | ERROR / WARN | SEC001–SEC004 + SEC00n（`${...}` 占位符不报） |
| 6 | 生成物跟着源码走 | `scope=stale`：STL001 三方元数据一致、STL002 产物引用齐全、STL003 时效（限时）、STL004 paths 空（WARN）、STL005 样本为 0 | ERROR / WARN | STL001、STL002、STL004、STL005、STL00n。**STL003 无样本**：要跨天提交才造得出来，见下「判不了」 |
| 7 | 账本只减不增、豁免要盖章 | `scope=baseline`：BASE011 格式/必填、BASE012 过期、BASE013 上升、BASE014 可刷新（WARN） | ERROR / WARN | BASE011、BASE011b、BASE012、BASE013 + BASE00n 零基线正对照 |
| 8 | 入口与磁盘对齐 | `scope=entry`：ENT001/002 header、ENT003 行数、ENT004 地图双向、ENT005 规则无载体、ENT006 未注册 scope、ENT007 派生索引、ENT008 样本为 0 | ERROR | ENT001–ENT008 + ENT00n 正对照 |
| 9 | 结论 = 命令 + 退出码 + 完整输出 | `scope=build`：BLD001/BLD002 管证据在不在、新不新；证据内容本身是不是真的判不了（脚本不能替人相信一句话） | WARN | BLD001、BLD002 |
| 10 | 一次一类修改、工作树干净 | 无断言（人判）。任务是否在 worktree 里做，别人机器上判不了；写在这里靠下一次 `git status` | — | — |
| 11 | 判不了就说判不了 | 各域的样本守卫（MOD005 / SEC004 / STL005 / ENT008）+ `not_applicable` 清单；BLD004 工具链缺失走 WARN | ERROR / WARN | 每条样本守卫都在 selftest 里单独造一例「目录为空」 |

## 判不了（不是通过）

| 情形 | 现在怎么处理 |
| --- | --- |
| `@Router` 注解为 0（当前全库如此） | STL003 登记 `stale:swagger 时效` 为判不了，不拿「docs 比源码旧」当 ERROR |
| `--scope baseline` 单查 | 上游没跑，降级与新欠判不了；调度器输出里明说 |
| 没有 git（导出、裸文件目录） | BASE013、BLD002、STL003 全报 WARN + 判不了 |
| 慢域被跳过 | 打印「已跳过慢域（N）：build——不是通过」，退出码不受影响 |

## 账本

- `.harness/baseline.txt`：首版为空（零基线）。bootstrap 当天的 ERROR 要么修掉，要么逐条进 `accepted.json`。
- `.harness/accepted.json`：`scope`/`path`/`fingerprint`/`count`/`reason`/`owner`/`review_by` 全必填。
  指纹 = `code:` + 消息里数字抹成 `#`；改消息措辞等于作废一条已盖章的豁免（BASE012/BASE011 会追）。
- 现存一条：`config.yaml` 的 `jwt.secret`（高熵，轮换属单独一轮），复查日期见文件。

## 第二期不做的事（写明，避免当成已完成）

- `workflow/`：阶段、转移、契约与 flow.json；门记录模板。
- `skills/` 与 `skills.declared.yaml` 的双向对账（声明即承诺）。
- `INDEX.md` 派生索引、`retro`/`round` 复盘脚本、commit-msg 钩子（动宾短语 + 一件事）。
- 「文档点名的路径必须存在」这类断言：本仓库大量反引号写的是**目标代码**路径，
  按仓库根判会产出一批语义正确的误报，只保留链接与 code/scope 名的检查。
