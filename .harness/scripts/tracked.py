"""「git 会不会带走这条路径」——只此一处。

磁盘上存在 ≠ 仓库内容。本仓库的现场：`.deploy/`（部署侧本地放的配置与口令）被 `.gitignore`
排除，`secret` 域按磁盘扫，就把它里面的真凭据报成 SEC001「高熵密钥**入库**」——那不会入库，
而这条 ERROR 会拦下主树以后每一次提交。同一件事的另一面：`make guide` 把 `.deploy` 写进派生
索引，换一棵没有那个目录的检出，「生成」与「校验」看到的就不是同一张磁盘（lessons L-6 讲过
`.go/` 缓存，这次漂的是 gitignore，机制一模一样）。

所以「什么算仓库内容」有两个问题、两个家：机器本地产物在 `scopes/common.py` 的
`LOCAL_ARTIFACTS`（名字可预测，不需要 git）；用户自己排除掉的在 git 的 ignore 规则里
（只有 git 知道答案）。两边都是**只此一处**，别处 import。

没有 git 时（导出的裸目录、语料夹具）不假装知道：返回原因，调用方按「判不了」登记，
保守地把所有文件当候选——宁可多报，不许因为读不到规则就静默少扫（断言坑 #11）。
"""

import subprocess
import sys
from pathlib import Path

GIT_ARGS = ("ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z")


def ignored(root):
    """返回 (被 ignore 规则排除的相对路径集合, 判不了的原因)。

    `--directory` 把整棵被忽略的子树折成一条，避免在 1.5G 的模块缓存上逐文件询问；
    条目以 `/` 结尾，这里去掉，交给 `is_ignored` 按前缀逐段比对。
    """
    try:
        p = subprocess.run(["git", "-C", str(root), *GIT_ARGS],
                           capture_output=True, text=True, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return frozenset(), f"git 不可用：{exc}"
    if p.returncode != 0:
        return frozenset(), f"git ls-files --ignored 退出码 {p.returncode}"
    return frozenset(n.rstrip("/") for n in p.stdout.split("\0") if n), None


def is_ignored(parts, names):
    """路径的每一段前缀都查一次：`.deploy/config.yaml` 的规则可能只写到目录那一层。"""
    for i in range(1, len(parts) + 1):
        if "/".join(parts[:i]) in names:
            return True
    return False


def main(argv):
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd().resolve()
    names, problem = ignored(root)
    if problem:
        print(f"{problem}——判不了，不是「没有排除任何东西」", file=sys.stderr)
        return 2
    print("\n".join(sorted(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
