# 踩坑记忆

一条一个坑，三段缺一不可：现象 / 根因 / 落成的断言。**没有第三条的条目不算记忆**——
那只是抱怨。落成的断言要么指向 `scripts/scopes/` 里的一个 code，要么在 `AGENTS.md`
的「人判项」里写明强度来源。

## L-1 工作树被会话外的进程整体重写

- 现象：会话进行中，主树 456 个受版本控制文件里有 337 个变成 0 字节、`start.sh` 与 `vben-go.sql`
  整个消失；`git status` 从 clean 变成 `1 A / 2 D / 341 M`。所有文件 mtime 挤在同一秒。
- 根因：`mise.toml` 把 `GOPATH` 指到 `<repo>/.go`（274 MB / 11306 文件），同机还有 GoLand
  （fsnotifier 挂在本项目）与并行 agent 应用；`.git` 对象库多出 10743 个悬空 blob，全是 module 缓存内容。
  即「工具把依赖缓存当成仓库内容索引了一遍」之后又重写了工作树。
- 断言：**无断言、人判**。判据是本仓库开工前重新跑一次现场核对：
  `git ls-files | while read -r f; do [ -s "$f" ] || echo x; done | wc -l` 必须为 0。
  「所有文件 mtime 同一秒」是基准作废的信号；此时不许 `git restore` 覆盖现场。

## L-2 规则写了但工具从没跑过

- 现象：仓库有 20 个模块、`go.mod` 声明 1.18 起就存在，但 `_test.go` 为 0、无 Makefile、无 CI、
  无 lint 配置；升级到 1.25 后 `go vet` 一次报出 6 条真缺陷（丢信号、日志丢失参数、3 处
  `string(int64)` 产出乱码 rune）。
- 根因：「能编译」被当成了「没问题」。没有共有门径，就没有人跑 vet，也没有任何断言会发现没人跑。
- 断言：`BLD003`（go_build / go_vet 必须 pass）、`BLD005`（gofmt 违规即 ERROR），
  证据由 `make evidence` 产出并带 commit，过期由 `BLD002` 拦下。

## L-3 反向测试全绿，但脚本作为命令是坏的

- 现象：`make selftest` 39 条样本符合预期，同一次 `make guide` 却把索引写进了
  `--root/.harness/codebase-guide/index.json`（凭空多出一个叫 `--root` 的目录），
  `make evidence` 的 `# 工作区：` 行报 `[: too many arguments`，`make fix` 报
  `fatal: Unimplemented pathspec magic '_'`。
- 根因：反向测试直接调 scope 的函数，绕过了 CLI 层；Makefile 用 `--root X` 调 `gen_guide.py`，
  而它只收位置参数；`git status --porcelain -- :!x/` 的短形式排除路径在 Apple Git 2.50.1 上
  不被接受；证据里的工作区判定把多行 `status` 塞进了 `[ -z ]`。断言测的是判断逻辑，接线没人管。
- 断言：无机器断言，靠两条约定——命令层改动后必须**逐个 target 空跑一次**（本轮已修
  `gen_guide.py` 接受 `--root`、`git_clean` 改用 `:(exclude)`、工作区判定改成单条变量）；
  `make check` 里 0 ERROR 不等于 `make check-all`/`make evidence`/`make fix` 可用。
  后来 `scope=cmd` 落地，CMD003 判「Makefile 指向磁盘上不存在的脚本」——引用的**存在性**有了断言，
  「调用能跑通」（参数形状）仍然只靠上面那条约定，没人替它兜底。

## L-4 `make init` 改的是整个仓库的钩子，不只是这个工作树

- 现象：在 worktree `go125` 里跑 `make init` 之后，`git config --show-origin core.hooksPath`
  显示的是 `/…/thooh-admin/.git/config`——主树也拿到了同一条设置。
- 根因：`core.hooksPath` 不是 worktree-local 的键，写它等于改共享 config。主树当时还没有
  `.harness/`，实测（临时仓库）确认钩子目录不存在时 `git commit` 静默通过：不报错，也没有门禁。
- 断言：无机器断言。约定是 `make init` 必须打印出被改的 origin 文件，让跑的人看见「这次改的是
  共享配置」；主树合并 go125 之前，那边的提交不受门禁保护——这是已知缺口，不当成已上锁。

## L-5 两字母的 code 前缀，对账那头看不见

- 现象：新建 `workflow` 域时 code 起成 `WF001`。`make selftest` 23 条样本全绿、`coverage()`
  也说「缺口 0 条」，但 `make check` 一跑就报 10 条 HOOK003「登记了 WF001，但源码里没有它」。
- 根因：`hooks` 的源码扫描按 `\b[A-Z]{3,6}[0-9]{3}\b` 认 code，两字母前缀根本不匹配；
  而 selftest 读的是模块的 `REFLECT` 元组，不经这个正则。两条路一条看得见一条看不见，
  「样本全绿」就给一条从没被对账过的登记开了绿灯。
- 断言：`HOOK003` 本身——它就是为「登记了不会报的账」写的，这次是它第一次在**新域落地当天**
  抓到东西。命名规矩进 `.harness/AGENTS.md` 自家规矩第 4 条与 `standards.md` 的「工具层自家规矩」
  表下说明；放宽正则被否：`GB001`、`ID001` 这类 token 会一起被抓进来，换来一批假阳性。

## L-6 「排除哪些目录」抄了四份，最少的那份决定故障长什么样

- 现象：`make check-all` 在当前树报 0 ERROR，同一份 `e38496c` 在临时检出的干净树上报
  ENT007「派生索引过期」；另外 `gofmt` 那条一路报 BLD004「工具链不可用」，可 `go build`/`go vet`
  明明跑得好。两个症状看着没关系，根子是同一个：这棵树里有一个 303M 的 `.go/` 模块缓存。
- 根因：排除清单存在四份各写各的——`common.GUIDE_IGNORE`（缺 `.go`）、`entry.SKIP_DIRS`（有）、
  `secret.SKIP_PARTS`（有）、`git_clean` 的 volatile（有）。少一份就少一类东西被当成本地内容：
  `GUIDE_IGNORE` 缺 `.go` ⇒ 派生索引写进 `.go`、`.go/pkg` 两条 ⇒ 换一棵没有缓存的检出，
  「生成」与「校验」看到的磁盘不一样 ⇒ ENT007。`gofmt -l .` 没有排除任何目录 ⇒ 退出码 2
  来自依赖源码 ⇒ 环境的脏被报成代码的错。
- 断言：合并成 `common.LOCAL_ARTIFACTS` 一份，五个使用点都走它。反向样本
  `ENT007b`（在带缓存的树上生成索引，拿到干净检出上判新鲜度必须合格）与 `BLD005b`
  （缓存里未格式化的依赖源码不算本仓库欠账）钉住这条；`ENT007` 本身早就在判，
  只是过去只有「带缓存的树」能看见它——**派生数据可复现**要靠跨树样本才算守住。

## L-7 `rglob("*.go")` 也匹配目录，`.go` 自己就是第一个受害者

- 现象：把 gofmt 改成「只扫仓库自己的 .go」后，第一版仍把 `.go` 当成一个待格式化文件报出来；
  `BLD005b` 与 `BLD004` 两条样本当场不符合预期。
- 根因：`Path.rglob("*.go")` 按名字模式匹配**任何**路径项，目录也算；写排除时习惯只看父目录段
  （`rel.parts[:-1]`），根上那个 `.go` 目录没有父段，于是漏网。两个小坑叠在一起，症状却是
  「排除清单明明生效了，怎么还有缓存里的东西」。
- 断言：`go_files()` 先 `is_file()` 再按**全路径段**判本地产物。反向样本就是上面那两条
  （`BLD004`/`BLD005b`），它们既是修好的证明，也是这条坑的常驻看门人。




## L-8 「清单只此一处」写早了：第六份抄本在 Makefile 的 `find` 里

- 现象：L-6 把五处 Python 收成一份 `LOCAL_ARTIFACTS`，门记录里落下「清单只此一处」。紧接着
  同一轮回归跑 `make fmt`，它照样炸——退出码 2，报的还是 `.go/pkg/mod/gorm.io/…` 那些依赖源码。
- 根因两条，都是老坑换工具再犯：
  1. Makefile 里 `gofmt -l $(find . -name '*.go' -not -path './.go/*')` 是第六份抄本。
     `-not -path './.go/*'` 排掉缓存的**子孙**，可 `find -name '*.go'` 也匹配 `.go` 这个**目录本身**
     （L-7 讲的正是这件事），而 gofmt 收到目录会递归进去——排除清单写对了也没用。
  2. 「收清单」只收了 Python 侧，因为验证跑的是 `make check` 与 `make selftest`，不是
     `make help` 里的每一条命令。L-3（反向测试全绿，脚本作为命令是坏的）的镜像故障第二次发生，
     而且这次是我自己在门记录里把话说满。
- 断言：`scripts/go_files.py` 成为「哪些 `.go` 算本仓库源码」的唯一实现（先 `is_file()`，再按
  整条路径段引 `LOCAL_ARTIFACTS`），Makefile 的 `fmt` 与 `build` scope 都调它；清单为空时脚本
  exit 2 并把「判不了」说在前面，不交给 gofmt 读 stdin。反向样本 `BLD005c` 钉住目录不混进清单
  （混进去时 gofmt 递归，同一个文件报两遍）。
- **没断言的那半**：`make fmt` 作为命令能不能跑，机器判不了——`cmd` 域只判 target 与命令表
  一一对应，不执行命令。所以规矩写进 `standards.md`：改清单或改工具层，`make help` 列出的命令
  逐条跑一遍；这一条同时进「判不了」表，别拿弱断言假装守住。

## L-9 「入库」的主语是 git，不是磁盘：合回主树才炸出来的三条 ERROR

- 现象：任务树里连过三批、`make check-all` 稳定 `0 ERROR / 5 WARN`，快进合进 main 之后
  当场 3 条 SEC001「高熵密钥入库」——全在 `.deploy/config.yaml`。那个目录被 `.gitignore`
  的 `.*` 排除，只存在于主树（部署侧本地放的配置与口令），任务树里根本没有它。
  同一次 `make init` 又重算出多一条 `.deploy` 的派生索引：提交上去，下一棵没有它的检出
  立刻 ENT007——和 L-6 完全同一个机制，只是这次漂的不是机器缓存，是用户自己排除的东西。
- 根因：`secret` 与 `gen_guide` 都按**磁盘上有什么**扫，而这两条断言的主语其实是
  **git 会带走什么**。「不入库」的东西报成「入库」，后果不只是吵：主树以后每一次提交都被
  这条 ERROR 拦住，门禁从此变成要绕过的东西。
- 断言：仓库内容有两半、各自一个家——机器本地产物在 `common.LOCAL_ARTIFACTS`（名字可预测），
  用户排除的在 `scripts/tracked.py`（只有 git 知道答案，用 `ls-files --others --ignored
  --exclude-standard --directory` 一次问完）。读不到 ignore 规则时（没有 git）一律当会入库，
  并登记 `secret:gitignore 判定` 为判不了——宁可多报，不许静默少扫。反向样本 `ENT007c`
  （带 gitignore 本地目录的树生成索引，没有它的检出也认它新鲜）与 `SEC005`（不判入库但要
  点名），外加 `SEC001b` 钉住反方向：未跟踪但没被排除的文件仍然算入库。
- **流程教训**：不许在任务树里宣布完成。任务树看不到主树的本地目录，正如干净检出看不到
  `.go/` 缓存——合回 main 之后必须在主树再跑一次全量，那才是这套门禁真正的落点。

## L-10 门禁不许堵住它自己指的路；而「脏」在 pre-commit 里永远为真

- 现象：看板把 T-2 写成 done 的当场 `make check` = 1 ERROR / exit 2，消息给两条出路
  「要么撤树（make task-done），要么把任务改回 doing」。两条各自走不通：撤树要求看板已 done 且
  已合并，而「已 done」得先提交才算数，提交要过这条钩子——**这条断言要求的状态，正是它自己判的
  违规**。照消息试了一遍：`task-done` 回「看板里还是 doing」，改回 done 又撞 ERROR。
- 根因一（分档）：一种 code 收进了两种严重度不同的状态。真正会丢活儿的是**这份工作还没合进
  主树**；已经合进去、只剩一条 `git worktree remove` 是收尾的必经中间态，不是欠账。
- 根因二（更便宜也更贵的一层）：第一版按「干净 + 已合并」分档，测的时候当场被推翻——钩子跑在
  **staged 状态**下，`git status --porcelain` 必然非空，于是「脏」这一档会把每一次「把任务标成
  done」的提交都拦死。教训：**门禁里的每个输入都要问一句「它在钩子那一刻是什么值」**；磁盘上
  读得到的事实不等于当时成立的事实。
- 断言：两份事实只在 `wt.py` 的 `tree_state()` 算一次（`make task-done` 两条都要，WKT001 只看
  merged），档位错了就是 L-6/L-8 那一类「脚本放行、门禁拦截」。反向样本 WKT001（已合并 → WARN）、
  WKT001b（已合并但没提交 → 仍 WARN，消息点名那笔改动）、WKT001c（未合并 → ERROR）；力气当场量过：
  档位钉死 ERROR → WKT001/001b 红，钉死 WARN → WKT001c 红，假装 `tree_state` 永远返回干净+已合并
  → WKT001b/001c 红。
- **一般化的规矩（人判，机器判不了）**：新加或收紧一条门禁时，把它给的两条出路**各真跑一遍**，
  包括在钩子生效的那一刻跑。「按它说的做，能不能做到」判不了，所以只写在 lessons 与 standards
  的「判不了」表里，靠人在反思段走一遍，不拿弱断言假装守住。

## L-11 destructive 命令做到一半失败，比一开始就失败更糟

- 现象：`make task-done TASK=go125` 回 `删树失败：… Permission denied`（exit 2），但这时
  `git worktree list` 已经没有这棵树、目录还在磁盘上；在树里跑任何 git 命令都是
  `fatal: not a git repository: …/.git/worktrees/go125`。三条出路全断：`task-done` 再跑说「这里没有树」，
  `scope=worktree` 报 ERROR 说「判不了，先别撤树」（它判的是磁盘上有个目录），主树钩子因此拦住
  之后每一次提交。人工 `chmod -R u+rwX` + `rm -rf` + `git worktree prune` 才清掉。
- 根因：`git worktree remove` **先删注册表、后删目录**，而 Go 把模块缓存目录建成 0555 只读
  （GOPATH 在树内，实测 2516 个 `-type d ! -perm -u+w`）。脚本把这条命令的退出码当成「要么全做
  要么没做」，事实是它能把仓库状态切成「一半是树、一半不是」。
- 断言：**部分无断言**。已落地的牙齿是批 E 的 fail-closed——`tree_state()` 读不出来时报 ERROR
  并登记 `not_applicable`，所以这个态是被门禁发现的（当场就发现了），没有冒充「安全那一档」。
  还缺的那半（认出「`.git` 文件在但 admin 目录没了」= 孤儿树，并打印真能跑的出路）登记成 **T-17**。
- 一般化的规矩（人判）：调任何会改两边状态（版本控制 + 磁盘）的命令之前，先问「它中途失败会留下
  什么态，我的脚本认不认这个态」。凡是「先做 A 再做 B、失败只报一句」的步骤，都要在失败分支里
  重读一次现场，而不是拿调用前的判断继续说话。

## L-12 状态文件在每个工作树里各有一份：写事实要写到被读取的那一份

- 现象：`make task-new TASK=T-19` 报「看板里 T-19：open → doing」（exit 0），紧接着在这棵树里
  `make check` = 1 ERROR / exit 2：WKT002「任务还挂 open，树却已开起来」。脚本说写完的事实，
  门禁说根本没写。
- 根因：`.harness/tasks/board.json` 是被版本控制的文件，**每个工作树一份拷贝**；`mark_doing(root)`
  写的是主树那份，`git worktree add` 从 base 检出的树里那份仍是 open，而 scope 读的是
  `ctx.root` 之下自己那份。脚本「成功」的语义只覆盖了一半的物理事实。
- 断言：无机器断言（`scope=worktree` 判得出这个态、但判不了脚本写没写对副本）；落法是
  `task_new` 对 `root` 与 `target` 各调一次 `mark_doing`，验证写在门记录
  20261029T012021Z：真 git 夹具里两份看板都翻成 doing。
- 一般化的规矩（人判）：脚本要落一个「会被别处的门禁读」的事实之前，先问**那个门禁在哪个文件系统
  上读**——主树、任务树、还是 CI 的干净检出。多副本状态文件的写操作，要么每个副本都写，
  要么明确「本脚本不写状态」。

## L-13 变异测试的还原手段必须对得上「改动提交过没有」：`git checkout --` 会抹掉未提交的实现

- 现象：给 `open()` 做反向验证（`label()` → `dsn()`，看密码断言会不会红）之后，用
  `git checkout -- pkg/mysql/mysql.go` 还原。结果还原到了**提交前的旧实现**——本轮还没提交的
  全部改动被 HEAD 覆盖，`git status --porcelain` 只剩 `?? mysql_test.go`，看上去像「这个任务没做过」。
  是重写文件时才暴露的，代价是一次完整的重打。
- 根因：`git checkout -- <path>` 的语义是「回到 index/HEAD」，而变异前的工作区**本来就领先 HEAD**；
  「变异前」和「HEAD」不是同一个态。和 L-11 同族：把破坏性命令当成可逆。
- 断言：无机器断言（门禁只看磁盘与 HEAD 是否一致，看不见「刚被覆盖的是未提交工作」）。
  落法是流程规矩：改坏之前 `cp` 一份到 `/tmp/xxx.bak`，还原用 `cp` 回来（本批实测第二次变异就是这么做的，
  还原后 `go test` 立刻回到 ok）；还原之后立刻 `git status --porcelain` 对一眼改动清单还是不是预期的那几个文件。
- 一般化的规矩（人判）：任何「临时改坏以验证牙齿」的步骤，先问**当前工作区是不是 HEAD**——
  是，`checkout`/`restore` 才等于还原；不是，只有复制备份这一条路。

## L-14 起得来不等于跑得对：验收要真打一个业务端点，报错路上会掉出新账

- 现象：T-19 的编排补完、`docker compose ps` 三个容器全 healthy 之后，随手打了一次 `POST /login`，
  于是当场看见五笔坐在代码前看不见的账：`server.logLevel` 是死配置（每条 SQL 打 stdout）、
  启动即 `AutoMigrate` 改客户库、业务错误靠 `panic` 传（每次失败一整屏 goroutine dump）、
  报错写日志那张表在库里不存在（`Error 1146: sys_oper_log doesn't exist`）、
  改 `.env` 口令与卷里口令不一致的那条路径存在（这条故意没实测，要删卷）。
  前三笔各自登记成 T-23 / T-24 / T-25，第四笔成了 T-20 列名漂移的现场证据。
- 根因：健康检查与端口通只证明「进程活着」，不证明「一次真实请求走完全程」。
  而错误处理链本身是代码里最少被读的那一段——只有失败真发生一次，它才会开口。
- 断言：`scope=state`/`scope=stale` 都判不了业务可达性；这一条**无机器断言**，是流程规矩：
  验收段的门径不能停在 `make check-all` 绿，要包含一次针对真实端点的请求，
  并把这次请求里出现的每一条新错误当场登记（要么进看板，要么写进「故意没实测」）。
- 一般化的规矩（人判）：凡是「部署形状改完了」这一类交付，验收命令里必须有一条打到业务端的 curl，
  它的输出原样进门记录。绿色的门禁 + 一个 500 的响应，比全绿但没人打过更要紧。

## L-15 脚本换目录跑 git，却没换掉钩子留下的环境：同一磁盘态在 shell 里读得到、在提交里读不到

- 现象：主树提交 T-19 收尾时，pre-commit 里的 `make check` 报
  「读不了 …/thooh-admin-wt/T-19 的工作区：fatal: .git/index: index file open failed: Not a directory」，
  ERROR 拦下提交；同一时刻在 shell 里跑 `make check`，那棵树读得好好的，只按「已 done 已合并」报 WARN。
  两个结果差在一个进程环境变量上，不是磁盘状态。
- 复现（最小夹具，2026-10-29）：主仓库 + 一棵 linked 树，`GIT_INDEX_FILE=.git git -C <树> status`
  → 原样报那句 `index file open failed: Not a directory`；`GIT_DIR=<主仓库>/.git` 同样加进去复现不出。
  原因是那棵树根目录的 `.git` 是一个**文件**，相对路径按新的 cwd 解析后就成了 `.git/index` 这个「目录下的文件」。
- 根因：`.harness/scripts/wt.py` 的 `git()` 只传 `-C <路径>` 换工作目录，子进程继承了调用方的
  git 环境。git 的 pre-commit 钩子会导出 `GIT_INDEX_FILE`（staged 与 worktree 两套索引要分开）
  与 `GIT_DIR`/`GIT_WORK_TREE`/`GIT_COMMON_DIR`（指向**正在提交的那棵树**），
  于是「读别的工作树」这件事在钩子里必然出错——而失败被包装成「判不了」，看着像磁盘态坏了，实际是调用姿势错。
- 二次命中（2026-10-30，T-27 提交当场）：同一根因换了表现。从任务树 `task/T-27` 提交时，
  `git -C …/T-20 rev-parse --abbrev-ref HEAD` 回的是 `task/T-27`，WKT004 报出一条根本不存在的
  「树与分支对不上」，把提交拦下。`GIT_DIR` 钉住 HEAD 的来源，`-C` 只改 cwd——这一次连「判不了」都不报，
  直接假阳性，比第一次更难认：现象指向另一棵树的磁盘状态，而那棵树自己跑一遍什么事没有。
- 断言：已修（T-26）。跨树读走 `.harness/scripts/gitenv.py` 的 `clean()`，`wt.git()` 带上它；
  `wt.git_raw()` 保留「不 scrub」的原样，只给反向样本用来证明泄漏是真的。selftest 里有两条：
  `WKT004e`（不 scrub 读到主树分支——泄漏成立）与 `WKT00n4`（钩子环境下读兄弟树仍一条不报）。
  把 scrub 摘掉后 `WKT00n4` 立刻「不符合」，实测过，正对照不是空转。
  仍未覆盖的：谁新写一个 `subprocess` 直接调 `git -C` 而不 scrub，没有静态断言会报——登记成 T-35。
- 一般化的规矩（人判）：跨目录调外部命令时，「换 cwd」不等于「换个起点」——那条命令还带着父进程的 env。
  只要脚本会去读**别的**仓库/工作树，就要先问它继承了什么环境变量；反过来，凡是「同一件事在交互 shell 里过、
  在钩子里不过」的报障，第一刀砍环境变量，别去动磁盘。

## L-16 「新那套」是按目录认出来的，不是按函数体：模块存在不等于功能实现

- 现象：仓库里有两套后台实现并挂一个 gin engine——`app/admin/{api,model}` 是 RuoYi 血统
  （`user_id int`、`config_key`、`sys_job`），`modules/` 已经是 dump 口径（`id varchar(36)`、`kenam`、`mon_job`）。
  按「口径」选 modules 没错，但 modules/auth/api.go 的 `Login` 是个桩：硬编码 `accessToken="11233"`，
  不查用户、不验口令、不发 JWT；全仓 `modules/` 搜不到一处 `CreateToken` 或 `PasswordVerify`。
  如果只把 `/login` 改挂过去，验收会拿到一个「200 且带 token」的响应，而那个 token 谁都过不了中间件。
- 根因：目录名与模型口径证明的是「数据结构对齐到哪套」，不证明「业务逻辑搬到哪套」。
  切换入口这类决定按目录来做最省事，也最容易把「看起来有」当成「能用」。
- 断言：**无机器断言**。`scope=modules` 判的是目录形状（api/model/router + `func Init`），形状齐了但函数是桩它判不出。
  人判的规矩：凡「把入口从 A 切到 B」，切换前要在 B 里读到三样东西——真实的数据访问、真实的安全校验、
  真实的返回值来源；任一样缺失就先把它做出来再切，或明写「本次只换壳，验收不许打这个端点」。
- 顺带记一条同族实测：`modules/` 下 grep `Use(` 零命中，整套 CRUD 端点在鉴权外（登记成 T-27）。
  「新那套」在口径上是对的、在防护上是空的——按目录挑实现时这两件事要分开量。

## L-17 兄弟树开在「主树未提交的那份看板」之后：新检出的树天生看不到，门禁就冲它报 WKT002

- 现象（2026-10-30，T-26 树里 `make check-all`）：报 `WKT002 任务 T-27 还是 open，树 T-27 却已经开起来`。
  磁盘上 T-27 确实在干活，看板里也确实是 doing——只不过写在**主树的工作区**与 T-27 自己那份里，
  而 T-26 这份是 `git worktree add` 从 `main` 的 HEAD 检出的，HEAD 里没有这次改动。
- 根因：`task_new` 按 L-12 的修法给「主树 + 新树」各写一次看板，但主树那次写**没跟着提交**。
  被版本控制的状态文件有两个维度：一份拷贝（L-12）和一份拷贝的**哪个版本**（这条）。
  两棵树同时开着时，每一棵的 `make check` 都会拿自己那份旧看板去对磁盘上的兄弟树，
  于是兄弟树的存在本身就是违规——这不是假阳性，是真的「事实没能抵达被读取的那份」。
- 今天的落法（人工对齐）：在 T-26 树里把 T-27 写成 `doing` + `worktree=T-27` 再跑门禁。
  改的是看板，不是磁盘——磁盘上那棵树是真的在干活，抹不平。
- 该加的断言：登记成 T-36。两条路选一条：
  ①`make task-new` 收尾时检查主树看板是否干净（脏就拒绝开树，或者由脚本把这一条状态提交进 main），
  让「开树」这个动作对兄弟树是**可见的**；
  ②把「哪棵树开着」这类运行时状态从被版本控制的 `board.json` 里挪出去（`git worktree list` 现算），
  看板只留计划与证据。②更干净，但 WKT002 的判据要跟着重写，别顺手做。

## L-18 按请求头放行等于按客户端的意愿放行：免鉴权判据里必须有一条是「服务端自己知道的」

- 现象（装好之后验的，不是踩过的坑）：全局门要救 SPA 刷新——浏览器地址栏刷新 `/dashboard`
  得拿到 `web/admin/index.html`，而 gin 的全局中间件在 `r.NoRoute` 链上也会跑，第一版按路径白名单
  把这次刷新挡成了 `{"code":401,"msg":"令牌不能为空"}`。最省事的写法是「`Accept` 含 text/html 就算导航」，
  在纸上就能判死：那等于让客户端用一个请求头决定要不要鉴权，任何脚本给已注册的 CRUD 端点补一个头
  就免 token 读全库。落下来的写法要 GET + `Accept: text/html` + `ctx.FullPath() == ""` 三条都成立，
  验收时把被保护的 `/sys/user` 伪造成公开请求的形状打一次——仍是 401；同一个头打 `/dashboard` 仍是回落页。
- 根因：`Accept` 是**客户端可控**的信号。它可以当放行的*必要条件*，永远不该单独当充分条件。
  默认拒绝的门里，每条放行判据至少要有一条来自服务端自己的事实——这里用的是
  `ctx.FullPath() == ""`（gin 在没命中任何注册路由时才给空串），它是路由表的产物，伪造不了。
- 断言：**无机器断言**。`scope=modules` 判目录形状，判不出一条放行条件的成色；
  门本身被删掉也没人报（登记成 T-32）。人判的规矩：写任何「免鉴权」判据时，把每一条标成
  「客户端可控」或「服务端可控」，全条都是前者的判据不许进白名单分支；
  验收时对被保护端点**伪造成公开请求的形状**（补上那个头）打一次，看还是不是 401。
  本轮实测留档：`/sys/user` 带 `Accept: text/html` 仍是 401，`/dashboard` 带它仍回落页面。
- 同族的一条留给下一轮：`/pub/user`、`/pub/menus` 现在要 token 了，但 handler 里身份写死 u1/admin、
  菜单不带角色过滤（登记成 T-33）。「谁能进来」和「进来看什么」是两道门，装上第一道容易让人以为装完了。

## L-19 接口 200 只证明后端认了，不证明前端起得来：契约验收的终点是页面，不是响应体

- 现象：T-28 把 getInfo/getRouters 改挂到 dump 口径后，curl 矩阵全对——u1 回 57 条权限、
  树 4 棵 34 个子页、无 token 401、换 u6 只剩 /bpm。浏览器真登录一次才看见第二类账：
  Vuex 里 `user.id=u1`、侧边栏四条都出来了（这些确实过了），但点进 `/admin/sys/user` 控制台报
  `Cannot find module './sys/user/index'`；再 grep 前端产物，`v-hasPermi` 要的是
  `system:user:edit`，`sys_api.perm` 给的是 `sys:user:edit`——57 条权限一条也匹配不上，按钮全隐。
  两处都是数据/产物对不上，接口侧一个错都不报。
- 根因：契约有两端。curl 只能证明「我发的形状前端读得了」这一半（顶层 user/roles/permissions 读到了），
  证明不了「前端拿着这份数据下一步要做什么」——它拿 `comp` 去查自己的模块表，拿 `permissions` 去比硬编码
  在 bundle 里的字符串。这两个查找目标都不在我改的代码里，所以在我的验收口径外面。
- 断言：**无机器断言**。`scope=modules` 判目录形状，`scope=stale` 判 docs/web 跟着源码走，
  没有一条断言能把「`sys_menu.comp` 里的值在 web/admin 产物的模块表里存在」钉住——产物是压缩后的
  单行 js，判得了但要写解析器。人判的规矩：改任何「前端要读」的接口，验收里必须有一条**浏览器实测**
  （真登录、真点进去、读一次 store 落值），并把这次这类账登记成任务
  （本轮留 T-37 模块名、T-38 权限字符、T-39 角色覆盖）。只给 curl 表不说页面状态的交付，算没说完成。
- 可复用的正面写法：把「前端读什么」先 grep 出来再决定返回什么形状（本轮 `dept` 就因此不包装成
  `deptId/deptName`——产物里 `deptName` 出现 0 次，没有读取点就不发明键名）。

## L-20 覆盖关账：任务登记会过时，收口前先问「它是不是已经被别的任务做掉了」

- 现象：2026-11-14 用 subagent 清看板前盘账，18 条 open 里有 5 条疑似被更早的修复覆盖：
  T-3（compose 缺 mysql/redis）、T-22（task-new 弄脏主树看板）、T-1/T-29/T-30（列名/表名漂移）。
- 结论与证据：
  - T-3 → T-19 的 compose 提级（`ce57b94`）已补齐 mysql/redis/healthcheck/卷，划 done。
  - T-22 → T-36 的 `task_new` 现在开树后把主树看板提交进 main（`.harness/scripts/wt.py` 的
    `git commit ... -- BOARD_REL`），主树不再有未提交的 doing，划 done（`ba40fee`）。
  - T-1/T-29/T-30 的「列名/表名漂移」是 T-20（app/admin/model 以 dump 为准重写）的子集，
    保留 open 归 T-20 那棵树一起收；T-29 的「补 job 模块或摘掉启动注册」、T-30 的
    「Recover 改调 modules/mon/oper + 拆 panic」是独立工作，归业务批次单独做。
- 根因：看板是登记时点的快照，任务之间会互相吞并（一个「列名重写」吃掉三张「某表列名不一致」的小账）。
  开干前不做覆盖关账，就会在已修好的地方重做一遍、甚至双写冲突。
- 人判的规矩：清看板前先按「改动文件域」聚类，对每条 open 问一句「它改的文件，最近有没有别的提交已经动过」；
  动过就先看那个提交是否已覆盖本任务，覆盖了就划 done 并引证据，别机械地每条都开一棵树。

## L-21 用 subagent 批量清看板：覆盖关账、同域串行、残留另立账

- 现象：一轮 subagent 并行清掉 18 条 open，全过程拦到 5 类问题，都是「并行 + 自动」才暴露的。
- 拦到了什么（复盘三问①）：
  - SEC001 拦真实散列进测试（T-31 回归测试写了 dump 里的 bcrypt，被 pre-commit 拦，改假 fixture）。
  - WKT002 拦并行开树（后开的树看不到先开树的 doing），根因是 task-new 没提交主树看板（T-36），
    补修后 task-new 提交前又漏 make index（STATE007 拦 7 次），再补。
  - STL001/STL003 拦 swagger 重新生成的提交：yaml_meta 正则误读 definitions 的 description；
    STL003 用 git log 时间，docs 未提交时永远是旧的——两者都是 stale.py 缺陷，本轮修掉。
  - T-34 误删白名单：grep `"/auth` 匹配不到 `e.Group("auth")` + `g.POST("/login")` 的拼接路由，
    agent 据此删了 /auth/* 三项。实际 /login（app/admin/router.go:39）是真实入口且白名单里有，
    所以没出事——但「凭拼接 grep 判断路由调用面」本身就是不可靠的判据。
- 漏了什么（②）：T-5（swagger paths 空）第一轮排批次时漏掉，只剩 4 条 open 时才发现；
  两个 subagent 反复卡在「请切换 goal 焦点」的误解上（worker 对 goal 系统的内置反应），T-5 最后主线程直接做完。
- 该加哪条断言（③）：无。这些是流程与静态检查的边界，靠人判。但 T-34 的教训值得一条人判规矩：
  「删鉴权白名单条目」前必须用**真实路由表**（router 注册后的 gin.Routes() 或 grep `Group(`+`POST/GET(` 的拼接）
  核对，不许只用 `grep "/路径"` 就说没有调用面。
- 残留另立账：gen.go 原生 SQL 仍引用 gen_table/gen_table_column（dump 是 tool_code_*，短列名对账没做）；
  sys_user_role/sys_user_post/sys_role_dept 在 dump 无对应表（未定）；modules/mon 缺 job 模块
  （定时任务未注册，只有表名对齐了）。这三笔留在看板 open 或另开任务，不在本轮 T-20 范围。

## L-22 旧表名对账的边界：摘功能要摘干净，grep 清零要覆盖到「间接引用」

- 现象：T-40/T-41 对账 system 模型与 gen.go 的旧表名，两处都差点漏：
  T-41 摘了 gen_table 的生成配置查询，但 `GenDbList` 里 information_schema 查询还有
  `NOT IN (select table_name from gen_table)`（同样是 1146 源，只是藏在「查系统表」的 SQL 里）；
  T-40 摘 sys_role_dept 数据权限，涟漪到 api 层 `roles.go` 的 `GetDeptTreeRole`（保留接口、checkedKeys 回空数组），
  不这样 api 包编译不过。
- 根因：摘一个功能/表时，引用它的点分两类——「显式引用」（grep 表名能扫到的联表）和
  「间接引用」（information_schema 里的子查询、上层接口返回它的数据）。只 grep 表名字面量会漏后者。
- 人判的规矩：旧表名/旧列名对账的收尾自检，除了 `grep 旧表名`，还要 `grep 该表被上层 api/service
  消费的入口`，摘功能时把入口一起处理（保留接口就回空数据并注明，删接口就连调用点一起删）；
  grep 清零必须连 information_schema/原生 SQL 里的表名子查询一起算。
- 补账：T-41 的 decisions 没记（subagent 只改了代码），主线程补了「代码生成器在 tool_code 口径下
  未实现」的说明；这提醒——「自主决策摘功能」类任务，验收时要确认决策写进了 decisions，不只看代码。

## L-23 浏览器实测是唯一能把「接口 200」与「页面能用」分开的手

- 拦到了什么（复盘①）：这一轮浏览器点遍菜单 + 真做 CRUD，抓到 8 类后端缺陷，全是 curl 与
  go build 都测不出来的：legacy 层用 int 主键扫 varchar(36) 的 id（列表全空）、`bit(1)` 列按
  字符串写（1406）、`sys_role`/`sys_menu` 的 bigint 主键没有自增也没人给值（1364）、软删写
  `avtag=0` 但列表不过滤（删了还在）、`sys_role_menu` 写 `where id=`（1054）、空 roleIds 触发
  `Create` 空切片、join 后 `where id` 歧义（1052）、`menu.comp` 指向产物里不存在的模块。
- 漏了什么（②）：两点。一是菜单 25 个自定义模块（`sys/group`、`sys/api`、`tool/num`、
  `tool/oss`、`bpm/*`、`demo/*`）在 `web/admin` 预构建产物里根本没有对应模块，页面点开报
  `Cannot find module`——这不是改数据能解决的，需要前端源码重建，而仓库只有产物、无 `src/`、
  无 `package.json`、无 sourcemap，git 历史里也从未有过。二是软删过滤只补了用户/角色/菜单三处
  列表——复查后订正：公告/字典/岗位用的是硬删除（`Delete`），没有同类漏网，这条判断不成立，
  不要照着去加 `avtag = 1`。
- 该加哪条断言（③）：无机器断言。`scope=modules` 判目录形状，判不出「模型类型与 dump 列类型
  是否匹配」。人判的规矩：以 dump 为准重写模型时，**列名与列类型要一起对**——`varchar(36)` 的
  id 不能留 int，`bit(1)` 不能留 string；这两类错误都不会在编译期或 `go vet` 冒头，只在真正读写
  时炸。可复用的做法：`common/json/bitx` 这种 Scanner/Valuer 类型比在每个调用点手写转换更省，
  它把「dump 的 bit=1 ↔ RuoYi 的 "0"」这对反向口径收在一处。
- 验收口径的教训：`/sys/role` 返回 200 且 body 里有 rows，不等于列名对——旧实现的
  `tools.Fail()` 也返回 200。判断「页面能不能用」必须看浏览器里的表格行数与控制台，不看 HTTP 码。
