# 门记录 20261028T162148Z — 任务级隔离（scope=worktree）

批次：只加「一个任务一棵树」这一类东西——`scripts/wt.py`、`scopes/worktree.py`、
`tests/cases/worktree.py`、registry 一行、Makefile 三个 target、入口/对照表/看板的同步行。
没动业务代码，没动 .go 文件。

命令：`make check-all`（改后）／`make check`（改后快域）
退出码：0

改前基准：在 `e38496c` 的**干净检出临时树**里跑 `make check-all`（临时树不在版本控制里，
所以基准没有 evidence 文件，原样粘贴如下）。注意这一列与「改后」不可直接相减：临时树里
没有 `.go/` 模块缓存，两边扫到的东西本来就不是同一批。

```text
1 ERROR, 6 WARN  (scopes: entry, commit, cmd, workflow, hooks, budget, modules, secret, stale, state, build, baseline; mode: normal)
ERROR entry        .harness/codebase-guide/index.json:1  ENT007   新欠（账本 0 条）：索引与磁盘不一致（派生数据过期）：跑 make fix，别手改
WARN  build        .harness/deliverables/evidence/verify-20261028T142010Z.txt:1  BLD002   证据（...commit edfdaf48）之后 Go 源码又改了 123 处：结论过期，重跑 make evidence
WARN  secret       config.yaml:15  SEC002   弱默认凭据 database.primary.password（6 位）
WARN  secret       config.yaml:23  SEC002   弱默认凭据 database.secondary.password（6 位）
WARN  secret       config.yaml:36  SEC001   基线内（账本 1 条）：高熵密钥入库 jwt.secret
WARN  secret       config.yaml:46  SEC002   弱默认凭据 xxl-job.job_upass（5 位）
WARN  stale        docs/swagger.json:1  STL004   swagger paths 为空
判不了（1）: stale:swagger 时效
```

改后：`0 ERROR, 6 WARN`（慢域全跑；证据文件
`.harness/deliverables/evidence/verify-20261028T161926Z.txt`，`# commit: e38496c0`，
工作区 dirty）；快域 `make check` = `0 ERROR, 5 WARN`。

新欠逐条：**本批没有新增 ERROR**。两处数字变化都不是本批改出来的，逐条归因：

- `ENT007`（基准里的 1 条 ERROR → 改后不报）：临时树里没有 `.go/`，而 `make guide` 在有缓存的
  树上会把 `.go`、`.go/pkg` 写进派生索引。基准里那条 ERROR 是**派生数据不可复现**的症状，
  本批只是恰好在带缓存的树上重跑了 `make guide`，让它暂时不报。根因未修，已登记 `T-12`。
- `BLD002`（基准有 → 改后无）：本批重跑了 `make evidence`，过期结论被新结论替掉，不是修掉了什么。
- `BLD004`（改后新出现的 WARN，基准里没有）：`gofmt -l .` 走进 `.go/pkg/mod` 里的依赖源码，
  退出码 2 被报成「工具链不可用」。同一个根因，同属 `T-12`；临时树里没有那个目录所以基准看不到。
- 其余 4 条（SEC001 基线内、SEC002 三条、STL004）逐条与基准一致，未变化。

上升归因：ERROR 无上升（1 → 0）；WARN 计数持平（6 → 6），成员变化已全部归因到 `T-12`
与「重跑 evidence」两件事，没有一条是本批引入的。

判不了：`stale:swagger 时效`（`@Router` 注解为 0，全库如此）——这不是通过。
`worktree` 域本次**没有**登记判不了：它是真跑过 git 的（临时夹具 + 本仓库现树各扫一遍）。

自查（反向验证，当场真做过，不靠语料代替）：

- `python3 .harness/scripts/verify.py --scope worktree` 在看板还没登记 `go125` 时报
  `WKT002 树 go125 在看板里找不到对应的任务`，把 `T-2` 写成 `doing` + `worktree: go125` 之后转绿。
- 一次性临时仓库（`/tmp`，测完已删）走完整生命周期，六条路径逐条对：`task-new` 开树并把看板
  写成 `doing`+`worktree`；未登记 id 拒绝（exit 2）；已存在的树拒绝（exit 2）；任务没 done
  拒绝收尾（exit 1）；已合并前拒绝（exit 1）；工作区脏最先拒绝（exit 1）；三条都过后撤树，
  `task-list` 报「是空的」。
- `scopes/worktree.py` 前两版在 scope 里用 `git(root.parent / name, ...)` 读分支——那读的是
  「当前这棵树」自己，每棵树都扫自己、别人的树一条没看着还全绿。现在路径只由 `wt.py` 算。

commit：基准 `e38496c`（本批提交即它的下一条；`git log --oneline -2` 可核对相邻关系）。
