"""四段落点的登记表与对账。

每个 scope 必须自己说清两件事：`PLAN`（这个域在动手前管什么）、`REFLECT`（它在复盘时能报哪些
code）。本域把这张表与源码逐条对账——**漏登记、多登记、空登记都报**，因为「规则写了但工具从没
跑过」是本仓库真踩过的坑（见 .harness/memory/lessons.md L-2）。

为什么集中在这一个文件里读，而不是让每个 scope 自带两个函数：额度（BUDGET001）只减不增，
多数 scope 已贴着线；集中登记不动额度，而且「登记了却没实现」这种半真半假的账，
比空函数更容易被逐条对账抓出来。

可测性：`reconcile()` 与 `check_registration()` 都接受注入的模块清单与目录，`run()` 只负责
从真实仓库取它们。反向样本要造的是一棵假的 scopes/ 树，不是假的 registry import。
"""

import inspect
import re
from pathlib import Path

from scopes.common import add, rel_to

NAME = "hooks"

PLAN = "动手前每个域说清自己管什么（PLAN）、复盘时能报哪些 code（REFLECT）；这张表与 scopes/ 源码逐条对账"
REFLECT = ("HOOK001", "HOOK002", "HOOK003", "HOOK004", "HOOK005")

CODE_RE = re.compile(r"\b([A-Z]{3,6}[0-9]{3})\b")
# 不是 scope，但里面的 code 字面量同样算「有人宣称会报这条」
SHARED_FILES = ("common.py",)
# 对账时按模块名（p.stem）比；按 "common.py" 比会漏排除，把共享 helper 当成没注册的域
NOT_SCOPES = {"__init__", *(name[:-3] for name in SHARED_FILES if name.endswith(".py"))}


def scopes_dir(root=None):
    """优先用被检仓库自己的 scopes/，退回到本文件所在目录。

    绝对路径：verify 可以从任何 cwd 调用，相对路径会扫到错的目录。
    """
    if root is not None:
        cand = Path(root) / ".harness" / "scripts" / "scopes"
        if cand.is_dir():
            return cand
    return Path(__file__).resolve().parent


def source_codes(path):
    """文件里出现过的 code 字面量。整行 `#` 注释剥掉，其余原样——
    注释里点名的 code 如果没人认领，那本来就是一条该报的裂缝。
    """
    codes = set()
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return codes
    for line in lines:
        if line.strip().startswith("#"):
            continue
        codes.update(CODE_RE.findall(line))
    return codes


def module_source(mod):
    return Path(getattr(mod, "SOURCE", None) or inspect.getfile(mod))


def registry_of():
    """延迟 import：registry.py 会 import 本模块，模块级 import 会绕成环。"""
    import registry

    return registry.SCOPES, registry


def reconcile(root, sd, mods, registry_rel, findings):
    """registry.py 的清单 ↔ scopes/ 目录的模块，双向比对。

    多一个（目录里有但没注册）= 这个域永远不会被跑到；少一个（注册了但文件没了）= 调度直接崩。
    """
    files = {p.stem for p in Path(sd).glob("*.py") if p.stem not in NOT_SCOPES}
    if not mods:
        add(findings, "ERROR", NAME, registry_rel, 1, "HOOK001", "registry.SCOPES 是空的：一个域都没跑")
        return
    registered = {mod.NAME for mod in mods}
    for missing in sorted(files - registered):
        add(
            findings,
            "ERROR",
            NAME,
            rel_to(root, Path(sd) / f"{missing}.py"),
            1,
            "HOOK001",
            f"scope {missing} 在 scopes/ 里但没进 registry.SCOPES：这条断言从没被执行过",
        )
    for ghost in sorted(registered - files):
        add(
            findings,
            "ERROR",
            NAME,
            registry_rel,
            1,
            "HOOK001",
            f"registry 里有 {ghost}，但 scopes/{ghost}.py 不存在：调度会 import 失败",
        )


def check_registration(mods, root, sd, findings):
    """PLAN/REFLECT 非空 → 登记的 code 真在源码里 → 源码里的 code 都登记了 → 没有孤儿。"""
    all_registered = set()
    for mod in mods:
        all_registered |= set(getattr(mod, "REFLECT", None) or ())

    shared_codes = set()
    for name in SHARED_FILES:
        shared_codes |= source_codes(Path(sd) / name)

    for mod in mods:
        rel = rel_to(root, module_source(mod))
        plan = getattr(mod, "PLAN", None)
        reflect = getattr(mod, "REFLECT", None)
        if not (isinstance(plan, str) and plan.strip()):
            add(findings, "ERROR", NAME, rel, 1, "HOOK002", f"{mod.NAME}: PLAN 缺失或为空——这个域管什么没说清")
        if not (isinstance(reflect, tuple) and reflect):
            add(findings, "ERROR", NAME, rel, 1, "HOOK002", f"{mod.NAME}: REFLECT 缺失或为空——它能报哪些 code 没说清")
            continue
        own = source_codes(module_source(mod))
        for code in reflect:
            if code not in own and code not in shared_codes:
                add(
                    findings,
                    "ERROR",
                    NAME,
                    rel,
                    1,
                    "HOOK003",
                    f"{mod.NAME} 登记了 {code}，但源码里没有它：登记了不会报的账等于假账",
                )
        for code in sorted(own - set(reflect)):
            # 跨域引用（secret 提到 baseline 的 BASE012）不是本域的输出，不算漏登记
            if code in all_registered or code in shared_codes:
                continue
            add(
                findings,
                "ERROR",
                NAME,
                rel,
                1,
                "HOOK004",
                f"{mod.NAME} 源码里会报 {code}，但没进 REFLECT：加了没人知道",
            )

    for name in SHARED_FILES:
        path = Path(sd) / name
        if not path.is_file():
            continue
        for code in sorted(source_codes(path) - all_registered):
            add(
                findings,
                "ERROR",
                NAME,
                rel_to(root, path),
                1,
                "HOOK005",
                f"{name} 提到 {code}，但没有任何 scope 认领它：这是一条没人实现的规则",
            )


def run(ctx, findings):
    root = Path(ctx["root"])
    sd = scopes_dir(root)
    mods, registry_module = registry_of()
    registry_rel = rel_to(root, Path(inspect.getfile(registry_module)))
    reconcile(root, sd, mods, registry_rel, findings)
    check_registration(mods, root, sd, findings)
