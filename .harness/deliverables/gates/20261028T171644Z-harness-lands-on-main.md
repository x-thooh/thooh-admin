# 门记录 20261028T171644Z — harness 落在主树上：合回之后的实测（scope=entry/secret/cmd/worktree）

批次：只做一类事——把任务树 `go125` 快进合回 `main`，然后在**主树**跑一遍实测。没动任何脚本逻辑；
落盘的只有状态层三样：本记录、从主树搬过来的那次证据文件、看板 `T-2` 划 done（外加批 D 记录的一条
实测追计，见「上升归因」）。这一步的存在理由写在 lessons L-9：**不许在任务树里宣布完成**。

命令（全部在主树 `/Users/thooh/Sites/github.com/x-thooh/thooh-admin` 跑，`main` = `156f892`）：

```text
$ make check-all     0 ERROR, 7 WARN (scopes: entry, commit, cmd, workflow, hooks, budget,
                     modules, secret, stale, state, worktree, build, baseline; mode: normal)
                     判不了（1）: stale:swagger 时效                     exit 0
$ make selftest      违规样本 102 条、正对照 20 条、判不了 0 条
                     覆盖：注册域 13 个、语料文件 13 个、缺口 0 条        exit 0
$ make init          钩子装好、状态目录建好、索引重算、selftest 跑完       exit 0
                     —— 跑完 git status --short 为空：派生索引不再变脏
$ make ignored       .deploy  .go  .idea                                  exit 0
$ make fmt | vet | build | test | check | check-json                       六条全部 exit 0
$ grep -c deploy .harness/codebase-guide/index.json  →  0
```

证据：`path:.harness/deliverables/evidence/verify-20261028T171443Z.txt`（头部 `# commit: 156f892`、
`# 工作区：` 为空 = 当场干净）。这份文件是主树产出的，所以它的数字只属于主树。

改前基准（主树 `f608aeb`，原样抄自 `20261028T170822Z-repo-content-per-git.md`，不重述）：
`3 ERROR, 6 WARN`，三条 ERROR 全在被 `.gitignore` 排除的 `.deploy/config.yaml`；同一次 `make init`
把 `.deploy` 写进派生索引，`git status --short` 出现 ` M .harness/codebase-guide/index.json`。

新欠逐条：**没有新增 ERROR**。WARN 多出一条，点名：`secret .deploy/config.yaml:15 SEC005`
「3 个高熵键在 gitignore 排除的本地文件里」——它不是新债，是那三条 SEC001 换了口径落进 WARN 档。

上升归因：ERROR 3 → 0；WARN 6 → 7（+1 就是上面那条 SEC005：三条高熵键折成一条点名到文件的 WARN，
`.deploy` 原有的那条 SEC002 一字未动，主树独有的这条以前被三条 ERROR 盖着、现在单独成条）。
发现数合计 9 → 7。
**批 D 门记录里预估的「WARN 主树 6 → 5」算错了**：它把「三条折叠成一条」当成净减，忘了被折的三条
在 ERROR 档、WARN 档只会多出折叠后的那一条。已在那条记录补追计，当场数字以本记录为准。

判不了：`stale:swagger 时效`（与基准同）。批 D 新增的 `secret:gitignore 判定` 在主树**没触发**——
那里有 git，这条分支的现场得靠语料（`SEC005` 夹具用真 `git init`）。`cmd` 域判不了「`make help`
里每条命令跑得通」：上面点名跑了 10 条（check-all / check / check-json / selftest / init / ignored /
fmt / vet / build / test），其余逐条写明——`evidence` 跑过（就是那份文件）、`commit-msg` 见下面
反向验证、`fix` 与 `init` 重复未跑、`task-new`/`task-done`/`task-list` 是收尾动作本记录之后执行、
`go-all` 等于 build+vet 已分别跑过、`up`/`down` 要起 docker（归 T-3 的账）、`clean` 会删掉主树 1.5G
的 `.go/` 缓存，破坏性动作不在本批。

反向验证「装好了」（T-2 验收的第三条，光「合了」不算装好）：`core.hooksPath` 是仓库级设置、值
`.harness/git-hooks` 是相对路径，所以每棵树跑自己那份钩子——主树以前没有那个目录，钩子被 git 静默
跳过（lessons L-4），这就是 T-2 的全部风险。现在实测一次：在临时分支 `harness-hook-probe` 上

```text
$ git commit --allow-empty -m "测试钩子有没有真的装上 …（正文含「顺带」）"   exit 1
check_commit：.git/COMMIT_EDITMSG 的提交信息有问题：
  MSG004  正文出现并列信号词 ['顺带']
$ git rev-parse --short HEAD   →  156f892        # 提交没进去
$ git checkout main && git branch -D harness-hook-probe   # 探针分支删掉，主树未动
```

pre-commit 在同一次尝试里也跑了（输出 `0 ERROR, 7 WARN`），拦人的是 commit-msg 那一步；两步都在
主树生效。探针全程在临时分支上做，`main` 一个字节没动。

commit：上面那批数字量在 `main` = `156f892` 的那一刻；本记录写在任务树 `cc864b4` 之上，随收尾提交
一起快进进 `main`（顺序见下）。

边界：板上还开着 `T-1`（schema 漂移）、`T-3`（compose）、`T-4`（GOSUMDB=off）、`T-5`（swagger）、
`T-6`（凭据）、`T-7`（retro/round），`T-9` blocked 带 `waiting_on`。那些是业务与部署侧的账，不属于
「harness 工程层补全」这一条。

撤树三步的真实顺序（比「先提交、再合并、最后撤树」多一步）：**先把任务树上已有的提交快进合进
`main`，再在本树提交收尾**。原因就在批 E 那条分档里——收尾这次提交的内容正是「T-2 划 done」，而它
落笔时树里还没有这笔提交，`tree_state()` 只能看到上一条树 HEAD；只要那条没进主树，量出来就是
「done 但未落地」→ ERROR，钩子把唯一一条出路（撤树）拦在自己门口。所以合在先、记账在后：

```text
$ git -C …/thooh-admin merge --ff-only go125        # 把 cc864b4 落进主树        exit 0
$ make check-all（主树）                             0 ERROR, 7 WARN              exit 0
$ （任务树）T-2 → done + evidence，make index && make check-all
                                                   0 ERROR, 6 WARN              exit 0
     WKT001 落在 WARN 档，消息点名「树里另有没提交的东西…：M .harness/INDEX.md」
$ git commit（收尾）                                 钩子输出 0 ERROR, 6 WARN     exit 0
$ git -C …/thooh-admin merge --ff-only go125        # 落进收尾提交                exit 0
$ make task-done TASK=go125（主树）                  删树失败：Permission denied   exit 2
```

## 追计：撤树这一步真的炸了，而且是半途炸

上面最后一行不是「待跑」，跑完了，结果是**这个脚本目前没有出路的一条路**：

```text
$ make task-done TASK=go125
删树失败：error: failed to delete '/Users/…/thooh-admin-wt/go125': Permission denied
make: *** [task-done] Error 1                                                  exit 2
$ git worktree list
/Users/…/thooh-admin  0e8d6fb [main]        # 注册表里已经没有这棵树
$ ls -d /Users/…/thooh-admin-wt/go125
/Users/…/thooh-admin-wt/go125               # 目录还在，304M
$ git -C /Users/…/thooh-admin-wt/go125 status
fatal: not a git repository: /Users/…/thooh-admin/.git/worktrees/go125
$ make check-all（主树）
ERROR worktree … WKT001  …这份工作有没有落地判不了（读不了 …：fatal: not a git repository…）：
     证明不了它结束，先别撤树                                            1 ERROR, 7 WARN   exit 1
```

根因：`mise.toml` 把 GOPATH 指进树里的 `.go/`，Go 把模块缓存目录建成 **0555 只读**（实测 2516 个
`-type d ! -perm -u+w`）。`git worktree remove` 一边删一遍撞进只读目录就中止，而它**已经先把
`.git/worktrees/go125` 注册表删掉**——于是磁盘上留下一堆「和 `0e8d6fb` 逐字节相同、但 git 不再认识」
的文件。这条状态没有任何一条命令能出去：`task-done` 要求它是工作树（已经不是），WKT001 反过来要求
「先别撤树」（已经撤了一半），钩子因此把主树后续所有提交都拦死。

现场核对（确认没有丢东西，才敢清）：`git rev-parse --short HEAD` 与 `refs/heads/go125` 都是
`0e8d6fb`，`git diff --stat refs/heads/go125 HEAD` 输出 0 行，`git status --porcelain` 0 行；
撤树前最后一次 `git status --short`（在任务树）只剩那 5 个已提交的文件。目录里独有的只有
303M 可重新下载的 `.go/` 缓存和三个空的状态目录（`deliverables/{artifacts,ledgers}`、
`memory/trace`，`find -type f` 为 0 行）。清法是人工两步 + 一条 prune，**这一步是使用者批准之后
做的**（不可逆）：

```text
$ chmod -R u+rwX …/thooh-admin-wt/go125 && rm -rf …/thooh-admin-wt/go125   exit 0
$ git worktree prune                                                        exit 0
$ ls -a …/thooh-admin-wt/                                                   只剩 . 与 ..
```

撤干净之后的主树实测（这才是这套门禁真正的落点，见 lessons L-9）：

```text
$ make check-all   0 ERROR, 7 WARN，判不了（1）: stale:swagger 时效          exit 0
                   WKT001 不再出现；7 条 WARN 与合回那一刻同（SEC005 一条、SEC002 四条、
                   SEC001 基线内一条、STL004 一条）
$ make selftest    违规样本 104 条、正对照 20 条、判不了 0 条
                   覆盖：注册域 13 个、语料文件 13 个、缺口 0 条             exit 0
$ make task-list   /Users/…/thooh-admin-wt 是空的                            exit 0
$ git status --porcelain                                                              0 行
```

证据：`path:.harness/deliverables/evidence/verify-20261029T005554Z.txt`（主树、撤树之后、
`# commit: 0e8d6fb`、工作区为空）。

新欠：ERROR 0 条；WARN 与上表同一条不少（`worktree` 那条 transient 随撤树消失）。
这条缺陷登记成看板 **T-17**（`make task-done` 半途失败后没有出路），坑写在 **lessons L-11**：
「destructive 命令做到一半失败，比一开始就失败更糟——注册表与磁盘各走一半，脚本必须认这个态并给出
能跑的出路」。批 E 那次按 merged 分档的改动救到了这里：fail-closed 报 ERROR 而不是冒充「安全那一档」，
所以现场是被门禁发现的，不是被静默掩盖的。
