# 规范：规则 ↔ 断言对照表

这是 `AGENTS.md`「硬规则」的执行侧台账：一条规则要么有断言，要么写明「无断言」+ 强度来源。
要么有断言要么没人守——写「应该」而没人检查，等于没写。

阈值与路径都在 `.harness/config.json`（单一来源），本文件不重复数字。

## 已注册的域

| 域 | 管什么 | 快/慢 | 文件 |
| --- | --- | --- | --- |
| `entry` | 入口文件、目录地图、派生索引 | 快 | `scripts/scopes/entry.py` |
| `cmd` | 命令表 ↔ Makefile target ↔ 脚本文件三方对账 | 快 | `scripts/scopes/cmd.py` |
| `workflow` | 流程层：flow.json 的阶段/门径/转移 ↔ Makefile，skills 声明 ↔ 磁盘双向，契约六问 | 快 | `scripts/scopes/workflow.py` |
| `commit` | 提交信息：一件事、动宾短语、不并列。钩子判 ERROR，本域判 HEAD 为 WARN | 快 | `scripts/scopes/commit.py` |
| `hooks` | 每个域的 `PLAN`/`REFLECT` 与 scopes/ 源码逐条对账 | 快 | `scripts/scopes/hooks.py` |
| `budget` | 工具层按角色的行数额度 | 快 | `scripts/scopes/budget.py` |
| `modules` | 功能模块 ↔ `app/admin/router.go` 双向对账 | 快 | `scripts/scopes/modules.py` |
| `secret` | 凭据入库、弱默认、本地覆盖文件 | 快 | `scripts/scopes/secret.py` |
| `stale` | swagger 三方一致、web 产物引用、生成物时效 | 快 | `scripts/scopes/stale.py` |
| `state` | 状态层是真的：看板形状与闭集、完成态可核验证据、INDEX 与现算一致 | 快 | `scripts/scopes/state.py` |
| `worktree` | 一个任务一棵树是真的：树—分支—看板三边对得上，收尾不半途 | 快 | `scripts/scopes/worktree.py` |
| `build` | go build / vet / gofmt / go 指令 / 证据时效 | 慢 | `scripts/scopes/build.py` |
| `baseline` | 账本格式、豁免保质期、总数只减不增 | 快 | `scripts/scopes/baseline.py` |

每个域一份反向语料：`scripts/tests/cases/<域>.py`。`reverse.py` 的 `coverage()` 机器判两件事——
注册域没有语料文件是失败，`REFLECT` 里的 code 既没样本又没进该域的 `UNCOVERED` 也是失败。

## 规则 ↔ 断言

| # | 规则 | 断言 | 严重度 | 反向样本 |
| --- | --- | --- | --- | --- |
| 1 | 命令只从 `Makefile` 走 | `scope=cmd`：CMD001 表里有 target 里没有、CMD002 target 有表里没登记、CMD003 Makefile 指向不存在的脚本、CMD004 脚本既不当命令也不被引用、CMD005 样本为 0 或缺输入 | ERROR | CMD001–CMD005（各一条独立夹具）+ CMD00n 三方一致正对照 |
| 2 | 模块要在两处登记 | `scope=modules`：MOD001 未注册、MOD002 死引用、MOD003 只 import 不挂、MOD004 形状不完整、MOD005 样本为 0 | ERROR | `make selftest`：MOD001–MOD005、MOD003c（注释里的挂载不算）、MOD00n 正对照 |
| 2a | 全局鉴权门不能被删或挪后 | `scope=modules`：GTE001（`r.Use(jwt.Gate())` 缺失或在 html/admin.Routers 之后） | ERROR | `make selftest`：GTE001（注释掉）、GTE001b（顺序颠倒）、GTE001n 正对照 |
| 3 | 提交前 `make check` 退出码 0；合并前 `make check-all` | `scope=build`：BLD003 编译/vet 失败、BLD005 未 gofmt；BLD001/BLD002 证据缺失与过期为 WARN（留痕是流程账，不当提交门）。`.harness/git-hooks/pre-commit` 由 `make init` 通过 `core.hooksPath` 装上，跑快域 | ERROR / WARN | BLD003、BLD005、BLD001、BLD002 + 两条正对照 |
| 4 | go 指令不低于 `go_version_min` | `scope=build`：BLD006 | ERROR | BLD006 + BLD006n |
| 5 | 密钥与本地覆盖配置不入库 | `scope=secret`：SEC001 高熵、SEC002 弱默认（WARN）、SEC003 覆盖文件被跟踪、SEC004 样本为 0、SEC005 高熵键只在 gitignore 排除的本地文件里（WARN，点名不判入库） | ERROR / WARN | SEC001、SEC001b（未跟踪且没被排除→仍算入库）、SEC002、SEC003、SEC004、SEC005 + SEC00n（`${...}` 占位符不报） |
| 6 | 生成物跟着源码走 | `scope=stale`：STL001 三方元数据一致、STL002 产物引用齐全、STL003 时效（限时）、STL004 paths 空（WARN）、STL005 样本为 0 | ERROR / WARN | STL001、STL002、STL004、STL005、STL00n。**STL003 无样本**：要跨天提交才造得出来，见下「判不了」 |
| 7 | 账本只减不增、豁免要盖章 | `scope=baseline`：BASE011 格式/必填、BASE012 过期、BASE013 上升、BASE014 可刷新（WARN） | ERROR / WARN | BASE011、BASE011b、BASE012、BASE013 + BASE00n 零基线正对照 |
| 8 | 入口与磁盘对齐 | `scope=entry`：ENT001/002 header、ENT003 行数、ENT004 地图双向、ENT005 规则无载体、ENT006 未注册 scope、ENT007 派生索引、ENT008 样本为 0 | ERROR | ENT001–ENT008 + ENT00n 正对照 |
| 9 | 结论 = 命令 + 退出码 + 完整输出 | `scope=build`：BLD001/BLD002 管证据在不在、新不新；证据内容本身是不是真的判不了（脚本不能替人相信一句话） | WARN | BLD001、BLD002 |
| 10 | 一次一类修改；一个任务一棵树，看板先登记再开树 | `scope=worktree`：WKT001 任务已 done 而树还在（收尾做了一半；**按「这份工作合进主树没有」分两档**——还没合进去是 ERROR，done 与未落地互相矛盾、撤它就是删掉没做的事；已合进去只 WARN，因为提交途中的树本来就是 dirty，把「脏」也当 ERROR 会把「标记 done 再提交」这一步自己挡在门外）、WKT002 树在看板里没人登记或任务还挂 open/blocked（顺序反了）、WKT004 树的分支既不是 `task/<id>` 也不是目录名。**判不了**：「忘了开树」（任务可能在别人机器上做）、「改前 `git status` 干净」 | ERROR / WARN | WKT001（已合并 → WARN 且消息点名 `make task-done`）、WKT001b（已合并但还有没提交的东西 → 仍 WARN，消息要点名那笔改动）、WKT001c（未合并 → ERROR）、WKT002（无对应任务 + status=open 两式）、WKT003、WKT004 + WKT00n 树—分支—看板对齐正对照 |
| 11 | 判不了就说判不了 | 各域的样本守卫（MOD005 / SEC004 / STL005 / ENT008 / CMD005 / MSG005）+ `not_applicable` 清单；BLD004 两条分支——Go 工具链缺失、排除本地产物后没有 .go 可判——都走 WARN 并登记 | ERROR / WARN | 每条样本守卫都在 selftest 里单独造一例「目录为空」；BLD004 造得出「没有 .go」这一支，「工具链缺失」那一支故意不造（等于依赖坏环境） |
| 12 | 一次提交说一件事 | `scope=commit`：MSG001 空标题或裸动词、MSG002 超 `subject_max_chars`、MSG003 标题并列（两个及以上「，」子句）、MSG004 正文出现顺带/另外/同时/此外、MSG005 拿不到消息。同一份 `check_message` 由 `commit-msg` 钩子在落笔时判 ERROR | WARN（钩子侧 ERROR） | MSG001–MSG005 + MSG00n 合规消息正对照 |
| 13 | 一次修改走五段，每段有过法 | `scope=workflow`：FLOW001 flow.json 缺/坏/stages 空、FLOW002 阶段与 REQUIRED_STAGES 不齐、FLOW003 阶段既无 gate 又无 manual、FLOW004 门径不是 Makefile 的 target（含 Makefile 读不到）、FLOW005 转移表空/指向不存在的阶段/没写条件/非末阶段无出口、FLOW006 声明账本缺或一条没声明、FLOW007 声明未装机、FLOW008 装机未声明、FLOW009 SKILL.md 三条验收缺一、FLOW010 契约六问缺一 | ERROR | FLOW001–FLOW010（各一条独立夹具，含三条 FLOW005 变体与两条 FLOW006 变体）+ FLOW00n 最小仓库正对照 |
| 14 | 状态层是事实：闭集取值、完成态带证据、INDEX 只派生 | `scope=state`：STATE001 看板缺/坏/tasks 空、STATE002 条目缺必填或 `updated` 坏/在未来、STATE003 status/priority 越出闭集或 blocked 没写等什么、STATE004 id 重复、STATE005 done 无证据或证据格式不认识、STATE006 证据核验失败（无 git 时 WARN + 判不了）、STATE007 INDEX 与现算不一致（`--fix` 可重建）、STATE008 看板过期（30 天 WARN、两倍 ERROR） | ERROR / WARN | STATE001–STATE008（含两条 STATE002 变体、三条 STATE003 变体、STATE006 的 path/commit 两式）+ STATE00n 现算 INDEX 正对照 |

## 工具层自家规矩 ↔ 断言

这几条管的是 harness 自己，不面向业务代码，所以不占上面「硬规则」的编号——但一样要有断言。

| 规矩 | 断言 | 严重度 | 反向样本 |
| --- | --- | --- | --- |
| 每个域必须说清自己管什么（`PLAN`）与能报哪些 code（`REFLECT`），且与源码逐条一致 | `scope=hooks`：HOOK001 registry ↔ scopes/ 双向、HOOK002 空登记、HOOK003 登记了源码里没有的、HOOK004 源码会报但没登记、HOOK005 共享 helper 提到没人认领的 code | ERROR | HOOK001/001b/001c、HOOK002、HOOK003、HOOK004、HOOK005 + HOOK00n 干净树正对照 |
| 加断言的同时加语料；注册域不许没有 `cases/<域>.py` | `make selftest` 的 `coverage()`（不是 scope：它判的是语料库自己，找不到「违规仓库」去扫） | selftest 退出码 1 | 由 reverse.py 自检：删一个 `cases/<域>.py` 立刻红 |
| 工具层文件按角色有行数额度，超限即该拆 | `scope=budget`：BUDGET001 超额度、BUDGET002 额度表坏或样本为 0 | ERROR | BUDGET001、BUDGET002、BUDGET002b（0 样本）+ BUDGET00n 正对照 |
| 本地产物目录（`.go/` 缓存、`node_modules/`、`__pycache__/`…）只有一份清单：`scopes/common.py` 的 `LOCAL_ARTIFACTS`，`build_guide` / `entry` / `secret` / `git_clean` / `go_files` 都走它。shell 里的 `find … -not -path` 也算一份抄本——收了五处、漏了第六处，现场见 lessons L-8 | 间接由 ENT007 判（派生索引在「有缓存的树」与「干净检出」上必须一致）与 BLD004/BLD005 判（gofmt 不许扫进依赖源码，也不许在没得扫时沉默） | ERROR / WARN | ENT007b（跨树复现正对照）、BLD005b（缓存里的依赖不算欠账）、BLD004（排除后无 .go 可判） |
| 「哪些 `.go` 算本仓库的源码」只有一份实现：`scripts/go_files.py`（先 `is_file()` 再按整条路径段排除）。Makefile 的 `fmt` 与 `build` scope 都调它——一条命令和一个门禁各算一遍，漂移的形态就是「`make fmt` 红了但 `make check` 绿」 | `scope=build`：BLD004（清单为空 = 判不了，不沉默）、BLD005（未格式化） | ERROR / WARN | BLD005c（`nested.go/` 目录里那个文件只报一次：目录本身没混进清单）、BLD004 + BLD005n/BLD005b 正对照 |
| 「这条路径 git 会不会带走」只有一份答案：`scripts/tracked.py`（问 `git ls-files --others --ignored --exclude-standard --directory`）。派生索引与被排除文件的密钥判定都问它；读不到 ignore 规则（没有 git）时一律当会入库，并登记 `secret:gitignore 判定` 为判不了 | `scope=entry`：ENT007 判两台机器看到的磁盘是否同一张；`scope=secret`：SEC005 把「不入库但本地是真凭据」点名而不是沉默 | ERROR / WARN | ENT007c（带 gitignore 本地目录的树上生成索引，没有它的检出也认它新鲜）、SEC005 + SEC001b（未跟踪但没被排除的仍算入库） |
| 「这份工作落地了没有」只有一处判定：`wt.py` 的 `tree_state()`（工作区干净吗、HEAD 已合进主树吗）。`make task-done` 两条都要（脏就不许撤），WKT001 只按第二条分档——CLI 与门禁各算一遍的漂移形态就是「脚本说可以撤、门禁说这是欠账」，本批现场是撤树这一步在门禁里根本走不通（lessons L-10）。读不出来时两个布尔给 `None`，门禁按 ERROR 走，不许冒充已落地那一档 | `scope=worktree`：WKT001 按「已合并」分档，「还有没提交的」只写进消息 | ERROR / WARN | WKT001（已合并 → WARN）、WKT001b（已合并但没提交 → 仍 WARN 且消息点名那笔改动）、WKT001c（未合并 → ERROR）；把档位钉死成单一档、或假装 `tree_state` 永远返回「干净 + 已合并」，对应样本立刻变红 |
| 「跨树读 git」只有一份环境：`scripts/gitenv.py` 的 `clean()` 剥掉 `GIT_DIR`/`GIT_INDEX_FILE`/`GIT_WORK_TREE`/`GIT_COMMON_DIR`/`GIT_OBJECT_DIRECTORY`/`GIT_ALTERNATE_OBJECT_DIRECTORIES`/`GIT_NAMESPACE`。`wt.git()`（worktree 域与 `make task-new`/`task-done` 唯一的 git 入口）带上它；`wt.git_raw()` 保留不 scrub 的原样，只给反向样本用（T-26、lessons L-15 的两次命中分别是「判不了」与「假阳性 WKT004」） | selftest 语料钉住：`WKT004e` 证明不 scrub 时读到的是主树的分支，`WKT00n4` 证明钩子环境下读兄弟树一条不报；把 `wt.git()` 的 `env=` 摘掉，`WKT00n4` 当场变红（2026-10-30 实测） | ERROR（拦提交） | WKT004e（泄漏是真的）、WKT00n4（正对照：scrub 在位时一条不报） |

code 的命名本身也是一条规矩：**3–6 个大写字母 + 三位数字**（`hooks` 的 `CODE_RE` 就按这个匹配）。
两字母前缀（试过 `WF001`）不会被源码扫描看见——登记了、源码里也有，但对账那头是瞎的，
于是 `FLOWxxx` 这种改名比放宽正则更省事：正则一放宽，`GB001`、`ID001` 之类也会被抓进来。

## 判不了（不是通过）

| 情形 | 现在怎么处理 |
| --- | --- |
| `@Router` 注解为 0（当前全库如此） | STL003 登记 `stale:swagger 时效` 为判不了，不拿「docs 比源码旧」当 ERROR |
| `--scope baseline` 单查 | 上游没跑，降级与新欠判不了；调度器输出里明说 |
| 没有 git（导出、裸文件目录） | BASE013、BLD002、STL003 全报 WARN + 判不了；STATE006 的 `commit:` 证据同此处理 |
| 拿不到 worktree 清单，或某棵树读不出分支 | WKT003 报 WARN 并登记 `worktree:…` 为判不了——有树却对不上账时不许沉默 |
| 树 done 而这份工作有没有落地读不出来（树的 HEAD 读不出、`merge-base` 失败） | 登记 `worktree:…` 为判不了，同时**按 ERROR** 报 WKT001：判不了不许冒充「已落地」那一档。这一支没在语料里造假夹具（要故意把 git 弄坏），靠当场替换 `tree_state` 复现，数字记在本批门记录 |
| WKT001 的 WARN 档（这份工作已落地，只差撤树）要不要按「限时而非禁止」升成 ERROR | 现在不升：这一域没有年龄事实源——树的 HEAD 提交时间量的是活儿什么时候做完，不是任务什么时候被判定结束；看板条目也没有 done_at。`stale` 与 `state` 已各算一份天数，再算就是第三处抄本。欠账挂看板 T-15 |
| 一条门禁给出的出路到底走不走得通 | 判不了：机器能判「消息里有没有 code」，判不了「照着消息做能不能做完」。本批就是靠这条人判抓出来的——WKT001 让人「撤树或改回 doing」，而那两步各自被别的门禁挡住。做法写进 lessons L-10：新加或收紧断言时，把它给的两条出路真走一遍 |
| 已经提交进历史里的凭据 | 判不了：`secret` 扫的是工作树里的文件，看不到 `git log` 里被删掉的旧版本。`config.yaml` 的 `jwt.secret` 在 T-19a 换成 `${THOOH_JWT_SECRET}` 之后，SEC001 那条发现就消失了——**发现消失不等于风险消失**，那个值仍在历史与客户现网里。做法是轮换 + 让现存 token 失效，账挂看板 T-6；不拿「文件干净了」当「密钥安全了」 |
| `wt.py` 的写路径（`task_new` 有没有把状态写到被读取的那一份） | 判不了：`tests/cases/` 喂的是 scope 的 `run(ctx, findings)`，不是命令级夹具；给 `wt.py` 建一套端到端夹具的成本不抵收益。落法是当场用真 git 仓库跑一遍并把输出写进门记录（现场：T-21），靠 lessons L-12 那条人判规矩 |
| 新写一处 `subprocess` 直接调 `git -C` 而没走 `gitenv.clean()` | 判不了：现在的语料钉的是 `wt.git()` 这一个入口，钉不住「别人另写一个」。做法登记成 T-35（拟一条静态断言扫 `.harness/scripts/**/*.py` 里带 `"git", "-C"` 的调用，要求同一语句里有 `env=gitenv.clean()`，或在紧邻注释里写明这是单仓库内的调用） |
| 排除本地产物目录后没有 .go 可判 | BLD004 报 WARN 并登记 `build:gofmt`；「扫到 0 个文件」与「格式全对」长得一模一样 |
| 慢域被跳过 | 打印「已跳过慢域（N）：build——不是通过」，退出码不受影响 |
| `make help` 里每条命令是否真的跑得通 | `cmd` 域只判 target 与命令表一一对应，不执行命令——判不了。做法是人逐条跑（改清单或改工具层之后必跑，lessons L-8 的现场就是 `make fmt` 炸而门禁全绿）；不拿「有 target」当「能跑」 |

## 账本

- `.harness/baseline.txt`：首版为空（零基线）。bootstrap 当天的 ERROR 要么修掉，要么逐条进 `accepted.json`。
- `.harness/accepted.json`：`scope`/`path`/`fingerprint`/`count`/`reason`/`owner`/`review_by` 全必填。
  指纹 = `code:` + 消息里数字抹成 `#`；改消息措辞等于作废一条已盖章的豁免（BASE012/BASE011 会追）。
- 现存 0 条。原有的一条（`config.yaml` 的 `jwt.secret`，SEC001 高熵入库）在 T-19a 之后**没有对应的
  发现了**，于是刷掉（前后条数 1 → 0，写在门记录 20261029T012600Z）。刷它是因为豁免的前提没了，
  不是因为密钥问题解决了——轮换与历史值仍挂看板 T-6，见上「判不了」表。

## 第二期不做的事（写明，避免当成已完成）

- `retro`/`round` 复盘脚本（事实底板：数字先算，AI 只在数字上写；环比 ERROR 与手册行数）：
  第三期，已作为 `T-7` 进看板。
- 流程层与状态层已上线：`workflow/flow.json` + `skills` 双向对账（`scope=workflow`）、
  看板 + 派生 INDEX（`scope=state`）、门记录与笔记模板（`stack-templates/`）、
  决策三态目录（`specs/notes/{proposed,implemented,rejected}/`）、
  任务级隔离 `make task-new`/`task-done`/`task-list`（`scope=worktree`）。
- 提交信息钩子已上线（`git-hooks/commit-msg` + `scope=commit`）；没上线的是**历史扫描**：
  本域只判 HEAD，不回头改旧提交——重写历史的代价高于一条措辞欠账。
- 「文档点名的路径必须存在」这类断言：本仓库大量反引号写的是**目标代码**路径，
  按仓库根判会产出一批语义正确的误报，只保留链接与 code/scope 名的检查。
