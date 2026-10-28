# 决策记录（全仓级）

只放 `scope: *` 的决策。模块级决策进 `.harness/specs/notes/` 用 `scope` 字段标归属——
不另建第二套目录树。每条带 `written_by` / `version` / `supersedes` / `status`。
作废不删：`status: superseded` 保留痕迹，因为「当初为什么这么定」是这层唯一的存在理由。

## D-1 记忆只放 `.harness/` 内

- 决策：全仓决策进 `.harness/memory/decisions.md`，模块级进 `.harness/specs/notes/{proposed,implemented,rejected}/`。
- 为什么：两处都写 = 两处都不维护；跨会话召回需要一个能被断言检查的位置。
- 被否：独立 `docs/decisions/`（要额外记路径映射，且不在 verify 的检查面上）。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-2 入口 = 根 + 每个一级目录各一份

- 决策：根 `AGENTS.md` 管全仓与任务路由；`admin/ app/ common/ modules/ pkg/ web/` 各一份，
  header 为 `<!-- agents: scope=<目录> parent=. -->`，`parent` 必须指向存在的入口。
- 为什么：覆盖默认是「少而广」，但这六个目录的硬规则确实不同（`modules/` 管注册协议、
  `web/` 管「产物禁止手改」、`pkg/` 与 `common/` 管基础设施边界），差异写进根文件会撑破行数上限。
- 依据：宿主实测（D-3）证明子目录入口真的会进上下文；没实测前不许写第二份。
- 被否：只写根文件（`web/` 与 `modules/` 的规则会被埋在 150 行里）；每个二级目录一份（副本同步成本）。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-3 实证宿主会按目录注入子目录 AGENTS.md

- 做法：`probe/AGENTS.md` 写一行唯一标记，同目录 `notes.txt` 写「本文件没有标记」；让子代理只读
  `notes.txt`，再从上下文回答是否出现该标记。
- 结果：标记出现在子代理上下文（来源指向 `probe/AGENTS.md`），同一标记也出现在主会话上下文——
  按目录解析成立，不是只读 cwd 及其祖先。
- 留痕：宿主 Qoder Desktop（会话 39df461d），日期 2026-10-28，结论「分层入口可用」；探针测完即删。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-4 memory / specs / tasks / deliverables 全部入库

- 决策：上述四类进 git；`.go/`（mise 把 GOPATH 指向仓库内缓存）与 `.idea/` 不入库。
- 为什么：换机器或换 agent 后「为什么这么定」「下一步做什么」必须还在；`.go/` 是 274 MB 依赖缓存。
- 代价：`.gitignore` 若有 `.*` 这类整类忽略规则，必须显式放回 `.harness`，否则整层被静默忽略
  （本仓库上游的 `.*` 正是这种情况，已实测）。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-5 脚本权限：只报告，`--fix` 只重建派生数据

- 决策：`--fix` 白名单只有 `ENT007`（重生成 `codebase-guide/index.json`）；写证据、选版本、补理由一律不自动。
- 前置：`--fix` 要求工作区除目标文件外干净；`.go/`、`.idea/` 等易变路径不参与「干净」判定。
- 为什么：脚本代劳写证据等于伪造；易变路径不排除会让 `--fix` 永远拒绝执行（断言坑 #2）。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-6 空基线 + 逐条显式豁免

- 决策：`baseline.txt` 首版为空；bootstrap 当天的 ERROR 不整表灌入，只把确实该留到下一轮的一条
  逐条写进 `accepted.json`，带理由、负责人、复查日期 2026-11-28。
- 为什么：零基线要求首版为空；豁免必须有人和日期，否则只是没人负责的注释。
- 账本前后条数：baseline 0 条 + accepted 1 条，只减不增。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-7 两期交付：一期入口 + 断言，二期流程 + 状态

- 一期：`AGENTS.md` 七份、`verify` 六域（entry / modules / build / stale / secret / baseline）、
  `baseline` 与 `accepted`、git hook、反向测试。
- 二期：`workflow/` 与 `gates` 域、`skills/` 与声明账本双向对账、`INDEX.md`、复盘与环比脚本、
  任务看板断言、`commit-msg` 钩子。
- 为什么：一期只交付「能判分的最小完整状态」；未上线的域不注册，避免「声明即承诺」变成空头支票。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-8 首批 scope 的取舍与被否项

- 上线：`entry`、`modules`、`build`（慢域，读证据）、`stale`、`secret`、`baseline`（最后跑）。
- 因无样本被否：接口注解与 `swagger.json.paths` 对账。全仓注解 0 处、`paths` 为空，样本数为 0 的
  断言和全绿长得一样（断言坑 #11），改由 `STL004` 报「空壳」WARN。
- 人判：web 构建产物是否与后端同步（前端源码不在本仓库，没有可判死的输入）。
- 未上线的 `gates` / `notes` / `worktree` / `conf` 域不注册：没实现的不许广播。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-9 Go 1.25 升级与 6 条 vet 的处置

- 决策：`go.mod` 的 `go` 指令升到 1.25（toolchain 由 mise 提供 go1.25.4），并真修 6 条 vet：
  信号通道加缓冲、两处日志格式串、三处 `string(int64)` 改 `strconv.FormatInt`。
- 为什么：仓库 0 个 `_test.go`、无 CI、无 lint，`go vet` 从未在本仓跑过；升级后「非常量格式串」
  检查（Go 1.24 起）开始报，属升级暴露的存量，不是 1.25 的兼容性破坏。
- 影响：`getRouters` 返回的路由名从乱码 rune 变成数字后缀（前端若按名字持久化会受影响），需人判。
- 被否：把 6 条写进 `accepted` 当存量豁免——否，因为都在 `go vet` 默认集内且修复是局部改写。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-10 命令集中到根 `Makefile`（唯一入口）

- 决策：仓库根 `Makefile` 是所有命令的唯一入口：`init` / `check` / `check-all` / `check-json` /
  `check-strict` / `fix` / `guide` / `evidence` / `selftest` / `build` / `vet` / `fmt` / `test` /
  `go-all` / `up` / `down` / `clean`。`.harness/scripts/` 里的脚本不再是命令，只被 make 调用。
- 为什么：门禁的价值取决于「顺手能跑」。人记不住 `python3 .harness/scripts/verify.py --root … --all`
  这种串，记不住就跳过，跳过了门禁等于不存在。
- 附带钉死：`GOPATH=$(HOME)/.go`、`GOPROXY=https://goproxy.cn,direct`、`GOFLAGS=-buildvcs=false`
  写在 Makefile 里而不是靠各人 shell。仓库内出现 `.go/` 缓存目录时，一次 `git add -A` 会把上万个
  模块对象写进 `.git`（今天在主树实际遇到，见 lessons L-1）。
- 断言载体：无（对照表第 1 行标「无断言（人判）」）。第二期把「未注册脚本报错」做成 `scripts` 域。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-11 一期（入口 + 断言）收口

- 事实：`make check-all` 报 **0 ERROR / 6 WARN**，其中 1 条 WARN 是 `accepted.json` 里已盖章的
  `jwt.secret`；`make selftest` 39 条样本全部符合预期（32 违规 + 7 正对照），
  未造样本 2 条（`STL003` 需跨天提交、`BLD004` 需坏环境）——都写进对照表，不当通过。
- 一期实际改动：入口 9 份（根 + 8 个一级目录/`.harness`）、断言 6 个域共 28 个 code、
  状态 3 件（`baseline.txt` 空、`accepted.json` 1 条、`deliverables/evidence/` 1 份）。
- 真修而非记账：`docs/swagger.json` 的 `info.title` 从 `vben-g 接口文档` 改回 `vben-go 接口文档`
  （STL001 报出来的三方不一致，`main.go` 注解与 `swagger.yaml` 都是 `vben-go`）。这是生成物里
  的一次手工纠正，下次跑 `swag init` 会被覆盖成注解的值——方向一致，不必豁免。
- 判不了而不报的东西：`r.Static()` 挂载的目录存在性（`./static/images` 实际不存在）。
  它不在首批商定的四个域里，加进来会把一期范围撑开；记在这里，二期或单独一轮再判。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-12 阶段清单放 `flow.json`，入口只留指针

- 决策：五段循环（盘点→规划→行动→反思→交付）的阶段、门径、转移只写在
  `.harness/workflow/flow.json`；根 `AGENTS.md` 的「开工四步」保留为压缩版并加一句指针，
  `README.md` 只讲为什么这么排，不复制阶段清单。
- 为什么：两处列同一件事就是两个事实源。阶段进 JSON 才能被断言检查（FLOW002/FLOW005），
  进散文就只能靠人肉对齐。
- 门径的表达：每个阶段要么有 `gate`（必须是 Makefile 里带 `##` 的真 target，FLOW004），
  要么有 `manual`（明写人判与理由，FLOW003）。`plan` 段选后者——意图判不了，不拿弱断言假装守住。
- 复用而非重写：gate 的对账调 `scopes/cmd.py` 的 `make_targets`。「这条命令存不存在」让两个域
  各判一遍，两边会各自漂移，报错的人看不出该信谁。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active

## D-13 阶段 4 只装一条流程：`skills/add-module`

- 决策：交付一条可安装流程 `skills/add-module/SKILL.md`，由 `skills.declared.yaml` 声明；
  其余任务（改 SQL、改前端产物）暂不做成流程，留在任务路由表里。
- 为什么：这条流程的失败模式最贵也最静默——漏登记路由编译照过；它有固定的两段修改点，
  值得写成流程。别的任务还没有「每次都漏同一步」的证据。
- 被否：一上来铺 5–6 条流程——没有装机证据的流程是文档不是流程，且每条都要过 FLOW009 三条验收。
- `skills/` 放仓库根（与 `.harness/` 同级）。它同时是 `entry` 的目录地图项：新增一级目录不进地图
  就报 ENT004，地图与磁盘的一致性是机器判的，不靠自觉。
- written_by: session 2026-10-28 / version: 1 / supersedes: — / status: active
