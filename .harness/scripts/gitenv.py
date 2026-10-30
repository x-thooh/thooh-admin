"""gitenv：把「读哪个仓库」这几个环境变量摘干净，交给要跨树跑的 git 调用。

为什么需要它（看板 T-26，2026-10-30 实测）：pre-commit / commit-msg 钩子里，git 会给子进程
导出 `GIT_DIR`、`GIT_INDEX_FILE`、`GIT_WORK_TREE`、`GIT_COMMON_DIR`，指向**正在提交的那棵树**。
harness 的脚本按设计要读**别的**树（worktree 域逐个对账兄弟任务树、`make task-done` 要判断
另一棵树落没落地），用的却是 `git -C <别的路径>`。`-C` 只改工作目录，HEAD 与索引由 `GIT_DIR`
/`GIT_INDEX_FILE` 决定，于是从任务树提交时读兄弟树，拿到的是自己这棵树的分支——WKT004 报出
一条根本不存在的「树与分支对不上」，把提交挡在门外；同一形状的 `GIT_INDEX_FILE=.git` 还会让
`git status` 直接 `fatal: .git/index: index file open failed: Not a directory`（lessons L-15）。

只摘这七个：它们决定「这个进程读哪个仓库」。`GIT_AUTHOR_*`/`GIT_COMMITTER_*` 不动——它们只影响
写入，而反向测试的夹具正靠它们造提交；`GIT_CONFIG_*` 也不动，摘了会把用户的配置一起丢掉。

不该用的地方：单棵树内部自己的 git 调用（钩子里 root 就是被提交的那棵树，环境指哪儿就读哪儿，
本来就是对的）。判断标准只有一条——**这个调用的目标路径是否可能不等于当前进程的仓库**。
"""

import os

# 决定「读哪个仓库」的变量；摘自 gitcli(7) 的仓库定位那一组
LEAKED = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
)


def clean(base=None):
    """返回一份去掉了 LEAKED 的环境字典副本；base 给了就在它上面摘。"""
    env = dict(os.environ if base is None else base)
    for name in LEAKED:
        env.pop(name, None)
    return env
