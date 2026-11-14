#!/usr/bin/env python3
"""wt：一个任务一棵树（任务级隔离）。

一次提交是一「轮」，一个任务是一条分支。两者共用一个工作目录，同时做两件事就得 `stash`
——而 stash 是让脚本替人保管未提交的工作，它保管丢了没人发现。所以每个任务开一棵
worktree，主树保持原样；树放在仓库**外面**（同级 `<主树目录名>-wt/<id>`），放里面就会被
一次 `git add -A` 收进提交。

顺序不许颠倒：`task-new` 要求看板里先有这条任务（WKT002 判的就是反过来的那两种），
建成之后它替你把看板写成 `doing` + `worktree=<id>`——这两格是脚本刚造出来的事实，
留给人补就等于让门禁惩罚守流程的人。`task-done` 先确认干净、再确认看板已 done、再确认已合并，
三条都过才动手删树——`git worktree remove` 会把没提交的东西一起丢掉。

用法：make task-new TASK=<看板 id> / make task-done TASK=<看板 id> / make task-list
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import gitenv  # noqa: E402

BOARD_REL = ".harness/tasks/board.json"


def git(root, *argv):
    # 目标路径是**别的树**，所以环境要摘干净：钩子导出的 GIT_DIR/GIT_INDEX_FILE 会让
    # `git -C <别的树>` 读回调用方这棵树的 HEAD（看板 T-26、lessons L-15）
    proc = subprocess.run(
        ["git", "-C", str(root), *argv], check=False, capture_output=True, text=True, env=gitenv.clean()
    )
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def git_raw(root, *argv):
    """T-26 之前的读法：环境照抄，不 scrub。

    只给反向样本用——它的作用是证明「正对照」不是空转：同一棵树、同一条命令，环境里带着
    钩子传下来的 GIT_DIR 就会读回别人的 HEAD。生产代码不许调这个。
    """
    proc = subprocess.run(["git", "-C", str(root), *argv], check=False, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def main_worktree(root):
    """`git worktree list --porcelain` 的第一条 = 主树；任务树放在它的同级。"""
    code, out, err = git(root, "worktree", "list", "--porcelain")
    if code != 0:
        return None, f"拿不到 worktree 清单：{err or '这里不是 git 仓库'}"
    for line in out.splitlines():
        if line.startswith("worktree "):
            return Path(line[len("worktree "):]).resolve(), None
    return None, "worktree 清单里没有 `worktree` 行——判不了，不动手"


def wt_parent(root):
    main, problem = main_worktree(root)
    if problem:
        return None, problem
    return main.parent / f"{main.name}-wt", None


def tree_dir(root, task_id):
    parent, problem = wt_parent(root)
    if problem:
        return None, problem
    return parent / task_id, None


def board_tasks(root):
    try:
        data = json.loads((Path(root) / BOARD_REL).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"读不了看板 {BOARD_REL}：{exc}"
    return [t for t in (data.get("tasks") or []) if isinstance(t, dict)], None


def is_orphan(target):
    """孤儿树：`.git` 指针文件还在，但注册表（gitdir）与树内容（admin/）都没了。

    现场是 `git worktree remove` 删到一半撞上 0555 的 `.go/` 中止：注册表先被删、目录没删完。
    这种残骸里没有任何可丢的工作，是可清理的残骸，不是「判不了」（lessons L-11）。
    """
    dotgit = Path(target) / ".git"
    if not dotgit.is_file() or (Path(target) / "admin").exists():
        return False
    try:
        line = dotgit.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    if not line.startswith("gitdir:"):
        return False
    return not Path(line[len("gitdir:"):].strip()).exists()


def orphan_exit(root, target):
    """残骸的出路：先挪出被扫描的 `-wt/` 父目录（解除拦提交、不删文件），再 prune 失效注册表。"""
    git(root, "worktree", "prune")
    main, _problem = main_worktree(root)
    park = (main.parent if main else Path(target).parent.parent) / f"{Path(target).name}.orphan"
    return (f"{target} 是半途删除留下的残骸（注册表已没、树内容已没）。已 git worktree prune。\n"
            f"出路（只挪不删，事后取证；挪走后 WKT 扫描就看不到它）：\n"
            f"  mv '{target}' '{park}' && git -C '{main or root}' worktree prune")


def tree_state(target, main):
    """量一棵树的收尾条件：返回 (干净吗, 已合进主树吗, 未提交清单, HEAD, 判不了的原因)。

    「收尾做了一半」有两个档位，差别全在这两个布尔上：树里还有没提交的东西、或这份工作还没
    落地，撤它就是丢活儿（ERROR）；两者都过了，剩下的只是忘撤一棵空树（WARN）。读不出来时
    前两项给 None——判不了不许冒充「安全的那一档」。
    """
    if is_orphan(target):
        return True, True, "", "", None
    code, dirty, err = git(target, "status", "--porcelain")
    if code != 0:
        return None, None, "", "", f"读不了 {target} 的工作区：{err or '这里不是 git 工作树'}"
    code, sha, err = git(target, "rev-parse", "HEAD")
    if code != 0:
        return None, None, dirty, "", f"拿不到 {target} 的 HEAD：{err}"
    code, _out, err = git(main, "merge-base", "--is-ancestor", sha, "HEAD")
    if code == 0:
        return not dirty, True, dirty, sha, None
    if code == 1:
        return not dirty, False, dirty, sha, None
    return None, None, dirty, sha, f"判不了 {target}（{sha[:8]}）有没有合进 {main}：{err or 'merge-base 失败'}"


def find_task(tasks, task_id):
    for task in tasks or []:
        if str(task.get("id")) == task_id or str(task.get("worktree") or "") == task_id:
            return task
    return None


def mark_doing(root, task_id):
    """把看板里这条任务写成 doing + worktree=<id>，返回改了什么。

    为什么脚本要动看板：`task-new` 一成功，「有树但任务还挂 open」就是 WKT002 的现场，
    而这个 transient 是脚本自己造的——让人再改一次文件才能过门，等于门禁在惩罚守流程的人。
    这里写的不是判断（不做「这条算完成」那种事），是脚本刚刚做出来的事实。
    """
    path = Path(root) / BOARD_REL
    data = json.loads(path.read_text(encoding="utf-8"))
    entry = find_task(data.get("tasks") or [], task_id)
    was = str(entry.get("status"))
    entry["status"] = "doing"
    entry["worktree"] = task_id
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return was


def task_new(root, task_id):
    tasks, problem = board_tasks(root)
    if problem:
        return 2, problem
    entry = find_task(tasks, task_id)
    if entry is None:
        return 2, (f"看板里没有 {task_id}：先登记要做的事，再开树。\n"
                   "顺序反了的代价是看不见的——树先建起来，做的事就没被记账（WKT002）")
    if str(entry.get("status")) == "done":
        return 2, f"任务 {task_id} 在看板里已经 done：要为别的事开树就再登记一条，别复用完成态的 id"
    target, problem = tree_dir(root, task_id)
    if problem:
        return 2, problem
    if target.exists():
        return 2, f"树已经在：{target}——同一个 id 第二次执行不该再建一遍，先看清它是什么"
    code, base, err = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if code != 0:
        return 2, f"拿不到当前分支：{err}"
    branch = f"task/{task_id}"
    code, _out, err = git(root, "worktree", "add", "-b", branch, str(target), base)
    if code != 0:
        return 1, f"开树失败：{err}"
    was = mark_doing(root, task_id)
    # 树里那份看板一起写：`worktree add` 检出的是 base 的提交，那份看板上这条还挂 open，
    # 而树跑门禁读的是它自己那份。只改主树 = 脚本造出「有树但看板 open」的态，
    # 于是 WKT002 拦住这棵树的第一次提交（现场：2026-10-29 开 T-19）。
    mark_doing(target, task_id)
    # 主树这份 doing 若不提交，之后从 main 开的兄弟树检出时看不到它，门禁报 WKT002（T-36）
    code, _out, err = git(root, "commit", "-m", f"开树 {task_id}：看板划 doing", "--", BOARD_REL)
    if code != 0:
        return 1, f"树已开（{target}），但主树看板提交失败：{err}"
    note = f"两份看板（主树与树内）里 {task_id}：{was} → doing，worktree 填 {task_id}"
    if was == "blocked":
        note += "（这条原来标 blocked；还卡着就别开树，把 waiting_on 改回原状态）"
    return 0, f"已开：{target}（分支 {branch}，自 {base}）\n{note}"


def task_done(root, task_id):
    target, problem = tree_dir(root, task_id)
    if problem:
        return 2, problem
    if not target.is_dir():
        return 2, f"没有这棵树：{target}"
    main, problem = main_worktree(root)
    if problem:
        return 2, problem
    clean, merged, dirty, sha, problem = tree_state(target, main)
    if problem:
        return 2, problem
    if not clean:
        return 1, f"树里有未提交的东西，先提交再收尾（删树会把它们一起丢掉）：\n{dirty}"
    tasks, problem = board_tasks(root)
    if problem:
        return 2, problem
    entry = find_task(tasks, task_id)
    if entry is not None and str(entry.get("status")) != "done":
        return 1, (f"看板里 {task_id} 还是 {entry.get('status')}：先写成 done 并带可核验证据"
                   "（commit:<sha> 或 path:<文件>），否则删掉的树是一条没人认领的账")
    if not merged:
        return 1, (f"{target} 的提交（{sha[:8]}）还没合进主树 {main}："
                   "先合并再删树，顺序反了就把没落地的工作删了")
    if is_orphan(target):
        return 1, orphan_exit(root, target)
    # 先把只读的 `.go/` 模块缓存（0555）放开，否则 remove 删到一半中止、注册表却已先没了
    subprocess.run(["chmod", "-R", "u+rwX", str(target / ".go")], check=False, capture_output=True)
    code, _out, err = git(root, "worktree", "remove", str(target))
    if code != 0:
        subprocess.run(["chmod", "-R", "u+rwX", str(target)], check=False, capture_output=True)
        git(root, "worktree", "prune")
        park = main.parent / f"{target.name}.orphan"
        return 1, (f"删树失败：{err}\n已补 chmod 并 git worktree prune。重跑 make task-done TASK={task_id}，"
                   f"仍不行就把残骸挪出被扫描的目录（只挪不删）：\n"
                   f"  mv '{target}' '{park}' && git -C '{main}' worktree prune")
    git(root, "worktree", "prune")
    return 0, (f"已收尾：{target} 已移除。分支 task/{task_id} 留在仓库里——"
               f"删分支是单独的决定：git branch -d task/{task_id}")


def list_trees(root):
    parent, problem = wt_parent(root)
    if problem:
        return 2, problem
    if not parent.is_dir():
        return 0, f"{parent} 不存在：现在没有任务树"
    names = sorted(p.name for p in parent.iterdir() if p.is_dir())
    return 0, "\n".join(f"{parent / n}" for n in names) or f"{parent} 是空的"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[2]
    if argv[:1] == ["--root"]:
        del argv[0:1]
        if not argv:
            return 2, "用法：wt.py --root <仓库根> <动作> [TASK]"
        root = Path(argv.pop(0)).resolve()
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    action = argv[0]
    if action not in ("task-new", "task-done", "list"):
        return 2, f"未知动作 {action}：可选 task-new / task-done / list"
    if action == "list":
        return list_trees(root)
    if len(argv) < 2:
        return 2, f"用法：wt.py --root <仓库根> {action} <看板 id>（Makefile 里是 TASK=<id>）"
    return (task_new if action == "task-new" else task_done)(root, argv[1])


if __name__ == "__main__":
    exit_code, message = main()
    print(message, file=sys.stdout if exit_code == 0 else sys.stderr)
    sys.exit(exit_code)
