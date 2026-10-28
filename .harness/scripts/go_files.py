"""列出真正属于本仓库的 .go 文件——「哪些文件算源码」只此一处。

两个坑都在这七行里：

1. `rglob("*.go")` 与 `find -name '*.go'` 都匹配**目录**（`.go` 就是模块缓存本身，
   某个包也可能叫 `nested.go/`）。目录进了 `gofmt -l` 的参数，gofmt 会递归进去，
   把 303M 依赖源码的语法错误报成自己的失败（退出码 2），门禁再把环境的脏读成
   「工具链不可用」。所以先 `is_file()`。
2. 本地产物目录的清单在 `scopes/common.py` 的 `LOCAL_ARTIFACTS`，别处不许再抄一份
   （含 shell 里的 `-not -path`）。判定时看**整条路径的每一段**，只看父目录会漏掉
   根上那个 `.go` 自己。

Makefile 的 `fmt` 与本仓库的 `build` scope 都走这里：一条命令和一个门禁各算一遍的
清单迟早漂移，漂移的形态就是「make fmt 红了但 make check 绿」。
"""

import sys
from pathlib import Path

from scopes.common import in_local_artifact


def go_files(root):
    files = []
    for path in sorted(Path(root).rglob("*.go")):
        rel = path.relative_to(root)
        if not path.is_file() or in_local_artifact(rel.parts):
            continue
        files.append(rel.as_posix())
    return files


def main(argv):
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd().resolve()
    files = go_files(root)
    if not files:
        print("排除本地产物目录后没有 .go 可判——这不是通过", file=sys.stderr)
        return 2
    print(" ".join(files))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
