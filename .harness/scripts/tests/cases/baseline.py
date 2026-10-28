"""baseline：老账账本与豁免表的保质期、只减不增。

BASE013 要拿 git HEAD 里的旧账本作比，所以样本里真跑一次 `git commit`；没有 git 就报判不了。
BASE014（条数下降 → 提示可刷新）用「账本里有一条现状里根本不存在的账」造出来——
那正是「老账修掉了」在数据上的形状。
"""

import json

from scopes import baseline as sc_baseline
from support import codes_of, ctx_for, git, new_root

NAME = "baseline"


def cases():
    out = []
    root = new_root({
        ".harness/baseline.txt": "secret\tconfig.yaml\t指纹\t不是数字\n",
        ".harness/accepted.json": "[]",
    })
    f = []
    sc_baseline.run(ctx_for(root), f)
    out.append(("BASE011", "账本行格式坏（条数不是正整数）", "BASE011" in codes_of(f)))

    root = new_root({
        ".harness/accepted.json": json.dumps([{"scope": "secret", "path": "a", "fingerprint": "SEC001:x",
                                               "count": 1, "reason": "", "owner": "", "review_by": "2020-01-01"}]),
    })
    f = []
    sc_baseline.run(ctx_for(root), f)
    out.append(("BASE011b", "豁免缺理由与负责人", "BASE011" in codes_of(f)))

    root = new_root({
        ".harness/accepted.json": json.dumps([{"scope": "secret", "path": "a", "fingerprint": "SEC001:x",
                                               "count": 1, "reason": "存量", "owner": "thooh",
                                               "review_by": "2020-01-01"}]),
    })
    f = []
    sc_baseline.run(ctx_for(root), f)
    out.append(("BASE012", "豁免已过期", "BASE012" in codes_of(f)))

    root = new_root({"go.mod": "module x\n"})
    ok, _ = git(root, "init", "-q")
    if ok:
        (root / ".harness").mkdir(parents=True, exist_ok=True)
        (root / ".harness/baseline.txt").write_text("# 注释\n")
        (root / ".harness/accepted.json").write_text(json.dumps([
            {"scope": "secret", "path": "config.yaml", "fingerprint": "SEC001:x", "count": 1,
             "reason": "存量", "owner": "thooh", "review_by": "2999-01-01"}]))
        git(root, "add", ".")
        git(root, "commit", "-q", "-m", "ledger 1")
        (root / ".harness/accepted.json").write_text(json.dumps([
            {"scope": "secret", "path": "config.yaml", "fingerprint": "SEC001:x", "count": 1,
             "reason": "存量", "owner": "thooh", "review_by": "2999-01-01"},
            {"scope": "secret", "path": "config.yaml", "fingerprint": "SEC001:y", "count": 2,
             "reason": "又盖一条", "owner": "thooh", "review_by": "2999-01-01"}]))
        f = []
        sc_baseline.run(ctx_for(root), f)
        out.append(("BASE013", "账本总数上升", "BASE013" in codes_of(f)))
    else:
        out.append(("BASE013", "git 不可用，这一条判不了", None))

    root = new_root({".harness/baseline.txt": "secret\tgone.py\tSEC001:不在现状里\t3\n"})
    f = []
    sc_baseline.run(ctx_for(root), f)
    out.append(("BASE014", "账本比现状多：老账修掉了一部分", "BASE014" in codes_of(f)))

    root = new_root({})
    f = []
    sc_baseline.run(ctx_for(root), f)
    out.append(("BASE00n", "正对照：零基线不报任何东西", bool(codes_of(f))))
    return out
