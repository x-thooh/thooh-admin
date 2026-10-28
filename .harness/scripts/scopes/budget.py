"""工具层的行数额度。

门禁自己最容易长胖：每加一条断言就往一个文件里塞几行，直到没人敢读它。
所以「文件超额度」必须是断言而不是自觉——本仓库的教训 L-2 就是「规则写了但工具从没跑过」，
而跑不动的工具和没写的工具结局一样。

额度按**角色**分档，不按目录拍平：反向语料（tests/）天生比实现长，共享 helper
（scopes/common.py）天生比单个域长。拿一个数字管三者，结果只能是「一调就全绿、一涨就爆红」。
今天的三档按现状校准，所以它的作用是**棘轮**：新文件必须落在档内，老文件再涨就要归因。

只审 `.harness/scripts/**`：`AGENTS.md` 的行数额度已经由 `entry` 域按
`agents_max_lines` / `sub_agents_max_lines` 判了，同一个文件不许两个域各判一遍。
"""

from pathlib import Path

from scopes.common import add, as_dict, num, quality_get, rel_to

NAME = "budget"

PLAN = "工具层每个文件按角色有行数额度（域 / 调度 / 共享 helper / 反向语料），超限即该拆；额度写在 config.json"
REFLECT = ("BUDGET001", "BUDGET002")

# 每条 = (相对 root 的路径, 档位名)。档位名对应 config.json 的 budget 块。
# 语料按前缀认，不按文件名清单：反向样本拆成一域一文件之后，写死文件名的清单当场就过期。
CORPUS_PREFIX = "tests/"
SHARED = ("scopes/common.py",)
DEFAULTS = {"scopes": 300, "scripts": 300, "shared": 420, "corpus": 500}
IGNORED_PARTS = {"__pycache__"}


def bucket_of(rel):
    """rel 是相对 .harness/scripts/ 的路径。"""
    if rel.startswith(CORPUS_PREFIX):
        return "corpus"
    if rel in SHARED:
        return "shared"
    if rel.startswith("scopes/"):
        return "scopes"
    return "scripts"


def py_files(root):
    base = Path(root) / ".harness" / "scripts"
    if not base.is_dir():
        return base, []
    out = []
    for path in sorted(base.rglob("*.py")):
        if not path.is_file() or IGNORED_PARTS & set(path.parts):
            continue
        out.append((path, path.relative_to(base).as_posix()))
    return base, out


def line_count(path):
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except (OSError, UnicodeDecodeError):
        return 0


def limits_of(quality, findings, root):
    raw = as_dict(quality_get(quality, "budget", {}))
    limits = dict(DEFAULTS)
    bad = []
    for key, value in raw.items():
        if key not in DEFAULTS:
            bad.append(key)
        elif not num(value) or value <= 0:
            bad.append(f"{key}={value!r}")
        else:
            limits[key] = int(value)
    if bad:
        add(
            findings,
            "ERROR",
            NAME,
            ".harness/config.json",
            1,
            "BUDGET002",
            f"budget 块里有不认识或不是正数的档位：{', '.join(sorted(bad))}（可用档位：{', '.join(sorted(DEFAULTS))}）",
        )
    return limits


def run(ctx, findings):
    root = Path(ctx["root"])
    limits = limits_of(ctx.get("quality") or {}, findings, root)
    base, files = py_files(root)
    if not files:
        add(
            findings,
            "ERROR",
            NAME,
            rel_to(root, base),
            1,
            "BUDGET002",
            "没扫到任何脚本（.harness/scripts/**/*.py）：0 个样本和全绿长得一模一样，先确认路径",
        )
        return
    for path, rel in files:
        bucket = bucket_of(rel)
        limit = limits[bucket]
        count = line_count(path)
        if count > limit:
            add(
                findings,
                "ERROR",
                NAME,
                rel_to(root, path),
                count,
                "BUDGET001",
                f"{count} 行，超过「{bucket}」档额度 {limit}：这个文件已经大到没人会通读，"
                "按域拆开后各自配反向样本（不许为了过检查调大额度，那等于把新欠盖章）",
            )
