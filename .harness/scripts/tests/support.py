"""反向语料的公共脚手架：临时仓库、ctx、git 包装。

只放跨域重复的几件事。域内的夹具（entry 的 `ROOT_OK`、stale 的 `SWAG_JSON` 等）留在各自的
`cases/<域>.py` 里——夹具跟着样本走，改样本时才看得见哪个夹具还管用。

额度：本目录整体算「语料」档（`budget` 域的 `tests/` 前缀），因为反向样本天生比实现长；
但一域一文件，谁都别想再靠「大家都塞进同一个文件」把额度熬没。
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
CASE_DIR = HERE / "cases"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from registry import SCOPES as REGISTERED  # noqa: E402
import gitenv  # noqa: E402

# 清单从 registry 取，不在语料里再抄一份：抄的那份在别人加一个 scope 的当场就过期。
# 上一版把 6 个名字写死在 reverse.py 里，后来加了 hooks 与 budget 两个域，selftest 一声没吭。
REGISTRY = tuple(mod.NAME for mod in REGISTERED)


def new_root(files):
    root = Path(tempfile.mkdtemp(prefix="vben-reverse-"))
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def ctx_for(root, quality=None):
    return {
        "root": str(root),
        "strict": False,
        "quality": quality or {},
        "selected": REGISTRY,
        "registry": REGISTRY,
    }


def codes_of(findings):
    return [f.code for f in findings]


def git(root, *argv):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t")
    p = subprocess.run(["git", "-C", str(root), *argv], capture_output=True, text=True, env=env)
    return p.returncode == 0, (p.stdout or "") + (p.stderr or "")


def git_text(root, *argv):
    """取一条 git 命令的 stdout（rev-parse 之类）；失败返回 None，不抛。"""
    ok, out = git(root, *argv)
    return out.strip() if ok else None
