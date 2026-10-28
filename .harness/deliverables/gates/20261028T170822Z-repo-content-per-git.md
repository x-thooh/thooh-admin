# 门记录 20261028T170822Z — 仓库内容按 git 认定，不按磁盘（scope=secret/entry/cmd）

批次：只改「这条路径 git 会不会带走」这一件事的落点——新增 `scripts/tracked.py`（唯一实现 + CLI）、
`common.build_guide` 用它过滤派生索引、`secret` 用它区分 SEC001 与新增的 SEC005、Makefile 注册
`make ignored`、入口命令表加一行、语料加 `SEC005`/`SEC001b`/`ENT007c`、文档四处
（standards 两行 + decisions D-18 + lessons L-9 + 看板 T-14）。没动业务代码，没动任何凭据的值。

命令：`make check-all`（任务树）+ `make selftest`
退出码：0 / 0

改前基准——**这一列来自快进合回 main 之后的主树实测**（`f608aeb`），不是任务树：
任务树里没有 `.deploy/`，在任务树里跑多少遍都看不到这个故障。

```text
$ make check-all                       # 主树，快进合回后
3 ERROR, 6 WARN  (scopes: entry, commit, cmd, workflow, hooks, budget, modules, secret, stale, state, worktree, build, baseline; mode: normal)
ERROR secret       .deploy/config.yaml:15  SEC001   新欠（账本 0 条）：高熵密钥入库 database.primary.password
ERROR secret       .deploy/config.yaml:23  SEC001   新欠（账本 0 条）：高熵密钥入库 database.secondary.password
ERROR secret       .deploy/config.yaml:36  SEC001   新欠（账本 0 条）：高熵密钥入库 jwt.secret
WARN  secret       .deploy/config.yaml:46  SEC002   弱默认凭据 xxl-job.job_upass（5 位）
WARN  secret       config.yaml:15  SEC002   弱默认凭据 database.primary.password（6 位）
WARN  secret       config.yaml:23  SEC002   弱默认凭据 database.secondary.password（6 位）
WARN  secret       config.yaml:36  SEC001   基线内（账本 1 条）：高熵密钥入库 jwt.secret
WARN  secret       config.yaml:46  SEC002   弱默认凭据 xxl-job.job_upass（5 位）
WARN  stale        docs/swagger.json:1  STL004   swagger paths 为空
判不了（1）: stale:swagger 时效

$ git status --short                   # 同一次 make init 在主树重算出的派生索引
 M .harness/codebase-guide/index.json   # 与提交进去的差一条 .deploy
```

`.deploy/` 被 `.gitignore` 的 `.*` 排除（`git check-ignore -v` 认到 `.gitignore:23`），
`git ls-files .deploy` 为空——它不会入库，而「高熵密钥入库」这条 ERROR 会拦下主树以后每一次提交。

改后（任务树，同一批代码）：`0 ERROR, 5 WARN`；`make selftest` = 违规样本 102 条、正对照 20 条、
判不了 0 条、缺口 0 条。主树的实测在本批合回后的收尾门记录里（不许拿任务树的数字宣布完成）。

新欠逐条：**没有新增 ERROR**；WARN 计数在任务树不变（5 条，成员同基准）。主树侧的变化：
三条 SEC001 不再是 ERROR，其中高熵那一类聚合成一条 SEC005 WARN 点名到文件，弱凭据那条照报——
`SEC001:高熵密钥入库 jwt.secret` 在 `config.yaml` 上的消息格式一字未动，
已盖章的豁免指纹（`accepted.json` 那条，BASE012 判它）不受影响。

上升归因：ERROR 3 → 0（主树），0 → 0（任务树）；WARN 主树 6 → 5（三条 SEC001 折叠成一条
SEC005，另一条留在 SEC002），无一条上升。

判不了：`stale:swagger 时效`（与基准同）。本批新增一处登记：**没有 git 时不知道谁被排除**，
`secret` 登记 `secret:gitignore 判定` 并按「全部都会入库」判——宁可多报，不许静默少扫。
`cmd` 域判不了「Makefile 每条命令跑得通」这条沿用上一批（`make ignored` 本批当场真跑过）。

自查（反向验证，当场真做过）：

- `ENT007c` 先证明它有力气：把 `trackedlib.ignored` 换成「谁都不排除」（= 旧行为）后样本返回
  True（生成树与干净检出的索引对不上，ENT007 会报）；装回真实现后转绿。
- `SEC005` 夹具用真 `git init` + `.gitignore` 的 `/deploy/`：`SEC001` 不报、`SEC002` 照报、
  `SEC005` 报出。反方向 `SEC001b`：未跟踪但没被排除的文件仍然算入库（防止修法过窄成「只判已跟踪的」）。
- `python3 .harness/scripts/tracked.py <主树>` 实测返回 `.deploy`、`.go`、`.idea`；
  在任务树只返回 `.go`——两张磁盘的差就是这条断言存在的理由。
- `make ignored` 在任务树 exit 0；`tracked.py` 在无 git 的目录走 exit 2 并说明「判不了，
  不是『没有排除任何东西』」。

另：本批提交后要把 `go125` 再快进合回 main，并在**主树**跑 `make check-all` + `make fmt`
确认那三条 ERROR 真的消失、派生索引不再变脏；那一步的数子记在收尾门记录里。

commit：基准 `f608aeb`（本批提交即它的下一条）。

---

追计（实测之后，数字以 `20261028T171644Z-harness-lands-on-main.md` 为准）：上面「WARN 主树
6 → 5」算错了，现场是 **6 → 7**。错在把「三条折叠成一条」当成净减一条——被折的那三条在 ERROR 档，
WARN 档只会长出折叠后的那一条 `SEC005`。ERROR 3 → 0 与「无新增欠账」两条仍然成立；发现数合计 9 → 7。
主树实测：`make check-all` = 0 ERROR / 7 WARN、`make fmt`/`vet`/`build`/`test`/`ignored`/`init` 全部
exit 0、`git status --short` 为空（派生索引里 `.deploy` 命中 0 次）。
