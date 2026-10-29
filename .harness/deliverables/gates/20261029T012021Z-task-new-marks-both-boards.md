# 门记录 20261029T012021Z — 开树时两份看板都要写（T-21，scope=worktree）

批次：工具层一处缺陷。`make task-new` 把 `doing` 只写进**主树**那份看板，而新树从 base 检出的
那份还写 `open`；树自己的门禁读的是树里那份，于是 WKT002「任务还挂 open，树却已开起来」当场拦住
这棵树的第一次提交。现场：2026-10-29 开 T-19 之后，树里 `make check` = 1 ERROR / exit 2。

改前的实测（就在 T-19 树里）：

```text
$ make task-new TASK=T-19（主树）      已开：…/thooh-admin-wt/T-19（分支 task/T-19，自 main）
                                       看板里 T-19：open → doing，worktree 填 T-19        exit 0
$ make check（树内）                   ERROR worktree .:1 WKT002 任务 T-19 还是 open，树 T-19
                                       却已经开起来：顺序反了            1 ERROR, 1 WARN   exit 2
```

根因形状：`board.json` 是**每个工作树各一份的磁盘状态**，不是仓库级服务。`mark_doing(root, …)`
只写 `root`，等于「脚本写了一份事实，门禁在另一份上读它」。这与 lessons L-10 是同一家族（门禁不许
堵住它自己指的路），但机制不同：那条是档位判错，这条是**写错了副本**。

修法：`task_new` 里 `mark_doing(root, …)` 之后对 `target` 再写一次——同一个事实（这条现在是
doing、它的树是这个 id）本来就在两边都成立；输出文案改成「两份看板（主树与树内）」。

改后的实测，用真 git 仓库夹具（`/tmp/wt-fixture`，`git init` + 一次提交 + 调 `wt.task_new`）：

```text
exit 0
已开：/private/tmp/wt-fixture/repo-wt/T-1（分支 task/T-1，自 main）
两份看板（主树与树内）里 T-1：open → doing，worktree 填 T-1
主树看板: status=doing worktree=T-1
树内看板: status=doing worktree=T-1
```

回到 T-19 树里：用修好的 `wt.mark_doing` 把这一次补写上（正是脚本本该做的事），`make index` 之后
`make check` = 0 ERROR / 2 WARN（STL004 + BASE014），exit 0。

没做的：夹具没进 `tests/cases/worktree.py`——那一域语料喂的是 scope 的 `run()`，不是 `wt.py` 的
写路径；给 `wt.py` 建命令级夹具要再造一套夹具框架，收益不抵成本。所以这条靠本记录里那两次实测
留痕，人判（见 standards「判不了」表里「一条门禁给出的出路走不走得通」那一行）。

T-19 的 `doing` 与 `worktree` 字段随本批一起入库；看板里新增 T-21 记这次缺陷（done，证据指向本文件）。
