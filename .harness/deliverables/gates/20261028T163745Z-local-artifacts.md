# 门记录 20261028T163745Z — 本地产物目录不再被当成仓库内容（scope=build/entry/secret/guide）

批次：只改「机器本地产物目录」这一类东西——`scopes/common.py` 里立一份 `LOCAL_ARTIFACTS`
清单（此前抄了四份、三份各缺一样），`build_guide`、`git_clean`、`entry.SKIP_DIRS`、
`secret.SKIP_PARTS` 都改成引它；`build.py` 新增 `go_files()`，`check_gofmt` 从 `gofmt -l .`
改成喂明确文件清单，并补「排除后没东西可判 = 判不了」分支；语料补 `ENT007b`/`BLD005b`/`BLD004`
三条样本，`BLD004` 从 `UNCOVERED` 收回。没动业务代码，没动 `.go` 文件，**没删那 303M 缓存**
（破坏性操作要人确认；这里修的是判定口径，不是环境）。

命令：`make check-all`／`make check`
退出码：0

改前基准：把 `3bd2915` 那四个 scope 文件用 `git show` 取到 `/tmp`，**在同一棵带 `.go/` 缓存的
树上**跑 pre-fix 代码——两边扫到的是同一批东西，所以这一列可以和「改后」直接相减：

```text
1 ERROR, 6 WARN  (scopes: entry, commit, cmd, workflow, hooks, budget, modules, secret, stale, state, worktree, build, baseline; mode: normal)
ERROR entry        .harness/codebase-guide/index.json:1  ENT007   新欠（账本 0 条）：索引与磁盘不一致（派生数据过期）：跑 make fix，别手改
WARN  build        .:1  BLD004   gofmt 退出码 2：.go/pkg/mod/github.com/!kyle!banks/depth@v1.2.1/depth.go | .go/pkg/mod/github.com/!p!gshen/go-xxl-executor@v1.0.2/app/test_jobhandler.go | …（共 6 条首行，全部落在 .go/pkg/mod）
WARN  secret       config.yaml:15  SEC002   弱默认凭据 database.primary.password（6 位）
WARN  secret       config.yaml:23  SEC002   弱默认凭据 database.secondary.password（6 位）
WARN  secret       config.yaml:36  SEC001   基线内（账本 1 条）：高熵密钥入库 jwt.secret
WARN  secret       config.yaml:46  SEC002   弱默认凭据 xxl-job.job_upass（5 位）
WARN  stale        docs/swagger.json:1  STL004   swagger paths 为空
判不了（1）: stale:swagger 时效
```

改后：`make check-all` = `0 ERROR, 5 WARN`，`make check` = `0 ERROR, 5 WARN`；
`make selftest` = 违规样本 99 条、正对照 19 条、判不了 0 条、缺口 0 条（13 个域 / 13 份语料）。
证据文件 `.harness/deliverables/evidence/verify-20261028T163938Z.txt`。
慢域一条 WARN 都没有少错：`build` 现在扫的是 `go_files()` 给的 180 个文件。

新欠逐条：**本批没有新增 ERROR，也没有新增 WARN。** 两条消失的逐条归因：

- `ENT007`（1 条 ERROR → 不报）：派生索引里躺着 2 条 `.go`、`.go/pkg` 条目，那是模块缓存不是
  仓库内容。`GUIDE_IGNORE` 少这一项，`entry`/`secret`/`git_clean` 却都有——同一件事四份清单，
  缺的那份只在一棵带缓存的树上才现形，所以干净检出与现树的索引永远对不上。改后 `grep -c '"\.go'
  .harness/codebase-guide/index.json` = 0（改前同一命令 = 2）。
- `BLD004`（1 条 WARN → 不报）：`gofmt -l .` 走进 `.go/pkg/mod`，现树实测 exit=2、命中 1078 个
  路径（全在缓存里），stderr 是依赖源码的语法错误——门禁把「环境里的脏目录」报成「工具链不可用」。
  改后 `gofmt -l $(go_files)` exit=0、命中 0。

其余 5 条 WARN（SEC001 基线内、SEC002 三条、STL004）逐条与基准一致，未变化。

上升归因：ERROR 1 → 0，WARN 6 → 5；下降的两条都由本批口径修正解释，无一条上升。

判不了：`stale:swagger 时效`（`@Router` 注解为 0，全库如此，与基准同）——这不是通过。
本批新增一条**可判不了**分支：`build:gofmt`（排除产物目录后没有 `.go` 可判时报 WARN + 登记
`not_applicable`，不再冒充通过）；现树有 180 个文件，这条分支在现树不触发，只在语料里造出来。

自查（反向验证，当场真做过，不靠语料代替）：

- 三条样本先红后绿：`ENT007b`（带 `.go/` 缓存的树上生成的索引，干净检出也认它新鲜）、
  `BLD005b`（缓存里的文件再乱也不算欠账）、`BLD004`（没东西可判 = 判不了而不是通过）——
  改前跑都报「不符合」，改后转符合；`BLD004` 因此从 `UNCOVERED` 收回。
- `rglob("*.go")` 连目录也匹配（`.go` 本身就是一个目录），第一版只判父目录，结果
  `go_files` 里留下 `['.go', 'ok.go']`；现在 `is_file()` + 全路径分段都判，实测 180 条、0 条在缓存里。
- 派生数据同一份实现算与判：`make index && make guide` 重跑两次，`.harness/codebase-guide/index.json`
  与 `.harness/INDEX.md` 无差异（`git status` 只剩本批改动）。

另：`/tmp/hbase`（`e38496c` 的临时检出）仍挂在 `git worktree list` 上，本批合回 main 后移除。

commit：基准 `3bd2915`（本批提交即它的下一条；`git log --oneline -2` 可核对相邻关系）。
