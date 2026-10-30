# 门记录 20261030T014137Z — 钩子环境不再串台：跨树读 git 走 gitenv（T-26 验收）

批次：只做一类事——**把「脚本读别的仓库/工作树时继承了钩子的 GIT_* 环境」这一类故障修在入口上**，
并给它补上能证伪的样本。改动四处：新增 `.harness/scripts/gitenv.py`、`wt.py` 的 `git()` 带上 scrub
（另留一个 `git_raw()` 给反向样本复刻旧读法）、`tests/support.py` 的夹具 env 也摘、
`tests/cases/worktree.py` 加两条样本。

## 验收口径（看板 T-26 原文）

> 钩子进程里读别的工作树要能读对：`wt.py` 的 `git()` 显式剥 `GIT_DIR`/`GIT_INDEX_FILE`/
> `GIT_WORK_TREE` 等，再给 selftest 加一个「树存在 + 钩子环境」的夹具。

## 触发它的现场（两次命中）

1. 2026-10-29 主树收尾 T-19：pre-commit 里报
   `fatal: .git/index: index file open failed: Not a directory`，同一时刻 shell 里跑 `make check` 读得好好的。
   最小夹具复现：`GIT_INDEX_FILE=.git git -C <树> status` 原样报这句。
2. 2026-10-30 从 `task/T-27` 提交全局鉴权门：pre-commit 报
   `WKT004 树 T-20 的分支是 'task/T-27'`——**假阳性**。`GIT_DIR` 钉住 HEAD 的来源，`-C` 只改 cwd，
   所以从哪棵树提交，读到的都是那棵树的分支。这一次比第一次更坏：不报「判不了」，直接凭空造一条欠账拦提交。

## 修法：只剥「决定读哪个仓库」的那七个

`gitenv.LEAKED` = `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE`、`GIT_COMMON_DIR`、
`GIT_OBJECT_DIRECTORY`、`GIT_ALTERNATE_OBJECT_DIRECTORIES`、`GIT_NAMESPACE`。
`GIT_AUTHOR_*`/`GIT_COMMITTER_*` 不动——只影响写入，反向测试的夹具正靠它们造提交。

判断标准写在 `gitenv.py` 的 docstring 里：**这个调用的目标路径是否可能不等于当前进程的仓库**。
按这条，`wt.git()`（worktree 域逐棵对账、`make task-new`/`task-done` 操作兄弟树）要 scrub；
`scopes/common.py` 的 `git_clean`、`scopes/commit.py` 的 `head_message`、`scopes/state.py` 的 `has_commit`、
`tracked.py` 的 ignore 清单**本轮故意没动**：它们的 target 恒是被检的那棵树，钩子环境指的也是它。
这条「故意」本身是欠账（新写一处 raw 调用没人报），登记成 T-35。

## 实测：样本有牙齿，不是空转

```text
$ make selftest            （修完之后）
  符合  worktree  WKT004e  预期会报    钩子环境串台是真的：带 GIT_DIR 不 scrub 读别的树，拿回主树的分支（T-26）
  符合  worktree  WKT00n4  预期不会报  正对照：环境变量里带着钩子那套 GIT_DIR/GIT_INDEX_FILE，读兄弟树仍要是它自己的分支，一条不报
  违规样本 105 条、正对照 21 条、判不了 0 条
  覆盖：注册域 13 个、语料文件 13 个、缺口 0 条                                   exit 0

# 证伪：把 wt.git() 的 env=gitenv.clean() 摘掉，同一条正对照当场变红
$ python3 - <<删掉 env= 参数>> ; make selftest
  符合      worktree  WKT004e   预期会报   …
  不符合    worktree  WKT00n4   预期不会报 …
  SELFTEST FAIL worktree/WKT00n4：样本表现与预期不符                            exit 1
$ 还原（gitenv.py 里 env=gitenv.clean() 仍在位：True）
```

夹具是真 git：临时主树 `git init -b main` + 一次提交 + `git worktree add -b task/T-1`，
然后把 `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` 设成**主树**的再跑这一域——正是钩子给子进程的形状。

## 顺带掉出来的另一笔账（不是本轮修的）

T-26 树里第一次跑 `make check-all` 报两条 ERROR：除了 INDEX 过期（`make index` 解决），
还有 `WKT002 任务 T-27 还是 open，树 T-27 却已经开起来`。这条**不是**环境串台：T-27 的 doing 真写过，
只是写在主树的工作区里没提交，而 T-26 从 `main` 的 HEAD 检出，天生看不到（lessons L-17）。
本轮把 T-26 这份看板对齐磁盘事实（T-27 → doing + worktree=T-27），机制本身登记成 T-36。

## 工具链

```text
$ make check        → 0 ERROR, 1 WARN（STL004 swagger paths 为空，既有）
$ make check-all    → 0 ERROR, 1 WARN
$ make selftest     → 105 违规样本 / 21 正对照 / 0 判不了 / 0 缺口，exit 0
$ go build ./...    → 本轮没动 .go，不适用（改动全在 .harness/scripts/ 的 Python）
```

## 本轮没做到与故意没做

- 没给「新写一处 raw `git -C`」加静态断言——现在只有 `wt.git()` 这一个入口被样本钉住（T-35）。
- 没动 `common.py`/`commit.py`/`state.py`/`tracked.py` 四处单仓库内的 git 调用，理由见上（T-35 记的是「判不了未来」）。
- 没重做 WKT002 的判据：兄弟树与看板版本的错位（T-36）这轮靠人工对齐 + lessons 兜。
- 没验 CI/干净检出下的形状：本仓库没有 CI，钩子路径只在本地 git 里跑；
  「交互 shell 过、钩子里不过」这一类样本目前只有 selftest 夹具这一个证据面。
