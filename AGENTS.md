<!-- agents: scope=. parent= -->
# AGENTS.md — 本文件是地图，不是手册

规则在文件里，不在会话里。细节一律下沉到 `.harness/`：断言与阈值在 `.harness/scripts/`，
规范与规则↔断言对照表在 `.harness/specs/standards.md`，跨会话决策在 `.harness/memory/`，
流程（阶段、门径、转移）在 `.harness/workflow/`。业务知识（模块怎么分层、SQL 怎么改）在
`docs/` 与各目录入口里。

## 常用命令

命令只从这张表走。表里没有的脚本不是命令——想用它，先加进 `Makefile`。

| 命令 | 做什么 |
| --- | --- |
| `make help` | 列出这张表里的目标 |
| `make init` | 装 git 钩子、建状态目录、生成代码库索引、跑 selftest |
| `make check` | 门禁（跳过慢域 build）；退出码 0 才算过 |
| `make check-all` | 门禁 + `go build`/`go vet`/`gofmt`/证据时效 |
| `make check-json` | 同一套检查的原始计数 |
| `make check-strict` | 示例数据按 ERROR 处理 |
| `make fix` | 只重建派生数据（codebase-guide），要求工作区干净 |
| `make evidence` | 把一次全量校验的完整输出存进 `.harness/deliverables/evidence/` |
| `make selftest` | 反向测试：每条断言都要真的会报 |
| `make commit-msg` | 判最近一条提交信息（提交时钩子跑同一套判据） |
| `make build` / `vet` / `fmt` / `test` | Go 工具链 |
| `make go-all` | build + vet（等价于 check-all 里的慢域） |
| `make guide` | 重新生成 `.harness/codebase-guide/`（派生，禁手改） |
| `make index` | 重新生成 `.harness/INDEX.md`（派生：下一步、没人守的规则、流程装机状态） |
| `make up` / `down` | 起停本地依赖（docker compose） |
| `make clean` | 删派生目录与 go 构建缓存，不动状态目录 |

这张表与 Makefile 的 target、磁盘上的脚本三方对账：`scope=cmd`。

`GOPATH` 与 `GOPROXY` 在 Makefile 里钉死（GOPATH 在仓库外）。别在 shell 里改它：
仓库内出现 `.go/` 目录时，一次 `git add -A` 就会把上万个模块缓存对象写进 `.git`。

## 目录地图

```text
admin      业务模块（admin/demo/...），形状同 modules
app        框架层：admin/{api,router,service}、core（启动与中间件）
common     config 结构体、全局变量，被 app 与 modules 共用
docs       swagger 生成物（swag init 产出，禁手改）
modules    业务模块，一个目录 = api.go + model.go + router.go + func Init(e *gin.Engine)
pkg        独立工具包（mysql、redis、logger、utils）
tests      Go 测试与手工请求脚本
web        前端构建产物（只入库结果，不入库源码）
skills     可安装流程（每条一个目录，正文是 SKILL.md）；与声明账本双向对账
.harness   agent 工程层：脚本、状态、知识、规范、流程
```

## 硬规则

1. 命令只走 `Makefile`；未注册的脚本一律不当命令用。跑脚本前先问「`make` 里有它吗」。
   `scope=cmd`
2. 加一个功能模块必须改两处：建目录（api.go/model.go/router.go + `func Init`）与
   `app/admin/router.go` 里 import + `alias.Init(e)`。漏一处路由静默不存在，编译照过。
   `scope=modules`
3. 提交前 `make check` 退出码 0。合并前 `make check-all` 至少一次。`scope=build`
4. go.mod 的 `go` 指令不得低于 1.25；升级工具链是单独一轮，不夹在功能提交里。`scope=build`
5. 密钥与本地覆盖配置不入库。存量豁免逐条写进 `.harness/accepted.json`（理由 + 负责人 +
   复查日期），不许整表放行。`scope=secret`
6. 生成物跟着源码走：`docs/` 与 `@Router` 注解、`web/` 与静态挂载表必须一致。`scope=stale`
7. 账本只减不增。新增一条欠账 = ERROR；要么修掉，要么逐条盖章。`scope=baseline`
8. 入口与磁盘对齐：新增一级目录必须进「目录地图」；子目录入口只在规则真不同时才写。`scope=entry`
9. 结论 = 命令 + 退出码 + 完整输出。「修好了」不是结论。`scope=build`
10. 工作树里一次只做一类修改，改前先 `git status` 确认干净。无断言（人判）：
    任务是否隔离在 worktree 里，脚本判不了别人的机器。
11. 判不了就说判不了，不冒充通过。缺样本、缺工具链、缺上游 scope 的域一律登记
    `not_applicable`，输出里与「通过」分得很开。`scope=baseline`
12. 一次提交说一件事：标题是动宾短语、不并列、不超长，正文不许出现「顺带 / 另外 / 同时 /
    此外」。落笔时 `commit-msg` 钩子判 ERROR，复盘时 `scope=commit` 判 WARN——
    HEAD 已经写进历史，改它比一条措辞欠账贵。
13. 一次修改走五段（盘点→规划→行动→反思→交付），每段的过法在 `.harness/workflow/flow.json`：
    要么有 `gate`（一条真能跑的 `make` 目标），要么明写 `manual`。跳过反思段 = 没跑过
    `make selftest` 就说「修好了」。`scope=workflow`
14. 状态层是事实不是装饰：看板的 status/priority 只能取闭集值，`done` 必须带可核验证据
    （`commit:<sha>` 或 `path:<存在的文件>`），`blocked` 必须写等什么；INDEX 只由 `make index`
    派生。`scope=state`

## 任务路由

| 要做的事 | 先读 |
| --- | --- |
| 加/改一个业务模块 | `modules/AGENTS.md`、`.harness/specs/standards.md` 的 modules 段 |
| 改框架层、中间件、启动 | `app/AGENTS.md`、`.harness/memory/decisions.md` |
| 改数据库模型或 `vben-go.sql` | `pkg/AGENTS.md`（迁移与全量 dump 的关系） |
| 动生成物（docs/、web/） | `docs/AGENTS.md`、`web/AGENTS.md` |
| 加一条断言或改阈值 | `.harness/scripts/registry.py`、`.harness/specs/standards.md` |
| 加一条可安装流程 | `.harness/workflow/README.md`、`.harness/workflow/skills.declared.yaml` |
| 查「上次为什么这么定」 | `.harness/memory/decisions.md`、`.harness/memory/lessons.md` |
| 看下一步该做什么 | `.harness/INDEX.md`（派生）、`.harness/tasks/board.json` |

## 开工四步

1. `git status`——工作区是不是只有你要改的东西；不是，先停下来问。
2. `make check`——把现状原样记下来，作为「改之前长什么样」。
3. 一次一类改动，改完立刻 `make check`（动了 .go 就再加 `make check-all`）。
4. 落痕：改了什么、为什么、跑了什么，写进 `.harness/memory/` 或提交信息。

这四步是五段循环的压缩版（盘点→规划→行动→反思→交付）；段数不许省，只许压缩，
展开与每段的门径在 `.harness/workflow/flow.json`。

## 证据规则

任何「已经修好 / 已经绿了」的说法必须带 `make evidence` 的产物：文件在
`.harness/deliverables/evidence/`，内含命令、UTC 时间、`# commit:` 与完整输出。
账本（`.harness/baseline.txt`）与豁免（`.harness/accepted.json`）同理：逐条列，
不许只报计数。

## 评审与复盘

- 评审先看 `make check-json` 的计数，再看逐条清单；两数不一致就是有人在聚合口径上动了手脚。
- 复盘三问：这次拦到了什么 / 漏了什么 / 该加哪条断言。答案进 `.harness/memory/lessons.md`。
- `scope=baseline` 只减不增；`make selftest` 必须为每个已注册 scope 至少准备一个违规样本。

## 维护本文件

- 新增一条硬规则：先在 `.harness/specs/standards.md` 的对照表里占一行（有断言或写明「无断言」+
  强度来源），再回到这里写规则本身，并标 `scope=<域>` 或「无断言」。
- `scope=` 只能写 `registry.py` 里已注册的域；没实现的域不许广播（声明即承诺）。
- 改规则先改断言表，再改本文件；只改文字不改脚本 = 文档与脚本漂移。
- 本文件上限 150 行（`ENT003` 强制）；子目录入口上限 80 行。超了就下沉，别删内容。
