#!/usr/bin/env python3
"""反向测试调度器：每条断言都要真的会报。

为什么必须有这套东西：一条从未触发过的断言与「没有断言」是同一件事，但它更坏——它给绿灯。
本仓库 2026-10-28 的教训之一就是 `go vet` 写在文档里、从没跑过，6 处 printf 缺陷静默存在
（`.harness/memory/lessons.md` L-2）。

做法：在临时目录里造一个**最小违规仓库**，直接调那个域的函数，看预期的 code 有没有报出来；
能 cheap 造出「正对照」的一并造——只有反例没有正例，判不出这条断言是不是永远在报。

语料按域放在 `cases/<域>.py`（一域一文件），本文件只做三件事：发现语料、跑、核覆盖。
它自己也曾把 8 个域装进一个 620 行的文件，`BUDGET001` 当场拦下——那个文件已经大到没人会
通读，于是「某个域一条样本都没有」这种事反而看不见。所以 coverage() 是这套语料的地基：
加域不写样本，这里就红。

判不了的事写清楚，不冒充通过：造不出样本的 code 在各自的 `cases/<域>.py` 里进 `UNCOVERED`。

用法：make selftest
"""

import argparse
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for _p in (str(HERE), str(HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from registry import SCOPES as REGISTERED  # noqa: E402
from support import CASE_DIR, REGISTRY  # noqa: E402


def load_cases():
    """按文件名发现语料：`cases/<域>.py` 里必须有 NAME 与 cases()。

    不写死清单——写死的清单正是上一版 reverse.py 的毛病：加一个域，没人想起来改这里。
    """
    mods = []
    for path in sorted(CASE_DIR.glob("*.py")):
        if path.stem == "__init__":
            continue
        mod = importlib.import_module(f"cases.{path.stem}")
        if mod.NAME != path.stem:
            raise SystemExit(f"{path} 的 NAME={mod.NAME!r} 与文件名不符：语料按文件名发现，名字要一致")
        mods.append(mod)
    return mods


def coverage(case_mods, results):
    """覆盖棘轮：每个注册域都要有语料，每个 REFLECT code 都要有样本或明写判不了。"""
    problems = []
    names = {mod.NAME for mod in case_mods}
    for missing in sorted(set(REGISTRY) - names):
        problems.append(f"注册域 {missing} 没有反向语料：它的断言从没被验证过")
    for extra in sorted(names - set(REGISTRY)):
        problems.append(f"语料 {extra} 对应的域已不在 registry 里：它在测一个不存在的域")
    sampled = {code for _scope, code, _what, _fired in results}
    declared = {(mod.NAME, code) for mod in case_mods for code, _why in getattr(mod, "UNCOVERED", ())}
    for mod in REGISTERED:
        for code in getattr(mod, "REFLECT", None) or ():
            if code in sampled or (mod.NAME, code) in declared:
                continue
            problems.append(f"{mod.NAME}/{code} 既没样本也没进 UNCOVERED：这条断言从没生效过")
    for scope, code in sorted(declared):
        if scope not in set(REGISTRY):
            problems.append(f"UNCOVERED 里的 {scope} 已不是注册域：免责条要跟着域一起删")
        elif code in sampled:
            problems.append(f"UNCOVERED 说 {scope}/{code} 判不了，但已经有样本了：删掉这条免责")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="反向测试：每条断言都要真的会报")
    ap.add_argument("--root", default=None, help="只为与 Makefile 统一接口而收，本脚本不读仓库")
    ap.parse_args(argv)

    case_mods = load_cases()
    results, failures = [], []
    for mod in case_mods:
        for code, what, fired in mod.cases():
            results.append((mod.NAME, code, what, fired))
            expect_fire = not what.startswith("正对照")
            if fired is not None and fired != expect_fire:
                failures.append((mod.NAME, code, what))
    gaps = coverage(case_mods, results)

    for scope, code, what, fired in results:
        expect = "不会报" if what.startswith("正对照") else "会报"
        if fired is None:
            state = "判不了"
        elif (fired and expect == "会报") or (not fired and expect == "不会报"):
            state = "符合"
        else:
            state = "不符合"
        print(f"{state:<7} {scope:<9} {code:<9} 预期{expect:<4} {what}")
    print()
    for mod in case_mods:
        for code, why in getattr(mod, "UNCOVERED", ()):
            print(f"未造样本  {mod.NAME:<9} {code:<9} {why}")
    print()
    violations = [r for r in results if not r[2].startswith("正对照")]
    controls = [r for r in results if r[2].startswith("正对照")]
    skipped = sum(1 for _s, _c, _w, x in results if x is None)
    print(f"违规样本 {len(violations)} 条、正对照 {len(controls)} 条、判不了 {skipped} 条")
    print(f"覆盖：注册域 {len(REGISTRY)} 个、语料文件 {len(case_mods)} 个、缺口 {len(gaps)} 条")
    for problem in gaps:
        print(f"SELFTEST FAIL 覆盖：{problem}")
    for scope, code, what in failures:
        print(f"SELFTEST FAIL {scope}/{code}：样本表现与预期不符（{what}）")
    if failures or gaps:
        return 1
    if skipped:
        print("有样本判不了（环境缺 git/go）——这不是通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
