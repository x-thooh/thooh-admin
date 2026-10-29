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
