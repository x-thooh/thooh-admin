"""hooks：四段落点的登记表与源码逐条对账。

这里的样本不造假的 registry import，只造一棵假的 `scopes/` 树：`FakeScope` 带 `SOURCE`，
hooks 域因此不必 `inspect.getfile`，能对着临时目录里的假源码判。
"""

from scopes import hooks as sc_hooks
from support import codes_of, new_root

NAME = "hooks"


class FakeScope:
    """假 scope：hooks 域只读 NAME / PLAN / REFLECT 和 SOURCE 指向的那个文件。"""

    def __init__(self, name, source, plan="管一件事", reflect=()):
        self.NAME = name
        self.SOURCE = str(source)
        self.PLAN = plan
        self.REFLECT = tuple(reflect)


HOOK_TREE = {
    ".harness/scripts/scopes/common.py": "",
    ".harness/scripts/scopes/good.py": 'NAME = "good"\n\nCODE = "GOOD001"\n',
    ".harness/scripts/scopes/orphan.py": 'NAME = "orphan"\n',
}


def cases():
    out = []
    root = new_root(HOOK_TREE)
    sd = root / ".harness/scripts/scopes"
    good = FakeScope("good", sd / "good.py", reflect=("GOOD001",))

    f = []
    sc_hooks.reconcile(root, sd, [], "registry.py", f)
    out.append(("HOOK001", "registry.SCOPES 空：一个域都没跑", "HOOK001" in codes_of(f)))

    f = []
    sc_hooks.reconcile(root, sd, [good], "registry.py", f)
    out.append(("HOOK001b", "scopes/orphan.py 在目录里但没登记", "HOOK001" in codes_of(f)))

    f = []
    sc_hooks.reconcile(root, sd, [good, FakeScope("ghost", sd / "gone.py")], "registry.py", f)
    out.append(("HOOK001c", "登记了 ghost 但没有 scopes/ghost.py", "HOOK001" in codes_of(f)))

    f = []
    sc_hooks.check_registration([FakeScope("empty", sd / "good.py", plan="", reflect=())], root, sd, f)
    got = codes_of(f)
    out.append(("HOOK002", "PLAN 与 REFLECT 都是空的", "HOOK002" in got and got.count("HOOK002") == 2))

    f = []
    sc_hooks.check_registration([FakeScope("good", sd / "good.py", reflect=("GOOD001", "GOOD009"))],
                                root, sd, f)
    out.append(("HOOK003", "登记了 GOOD009 但源码里没它", "HOOK003" in codes_of(f)))

    (sd / "sneaky.py").write_text('NAME = "sneaky"\n\nA = "SNE001"\nB = "SNE002"\n', encoding="utf-8")
    f = []
    sc_hooks.check_registration([FakeScope("sneaky", sd / "sneaky.py", reflect=("SNE001",))], root, sd, f)
    out.append(("HOOK004", "源码会报 SNE002，REFLECT 里没登记", "HOOK004" in codes_of(f)))

    (sd / "common.py").write_text('HINT = "ORG001"\n', encoding="utf-8")
    f = []
    sc_hooks.check_registration([good], root, sd, f)
    out.append(("HOOK005", "common.py 提到 ORG001，没有域认领", "HOOK005" in codes_of(f)))

    # 正对照另起一棵干净树：上面往 sd/ 里写过 sneaky.py 与改了 common.py，复用就把对照片淹了
    clean = new_root({
        ".harness/scripts/scopes/common.py": "",
        ".harness/scripts/scopes/good.py": 'NAME = "good"\n\nA = "GOOD001"\n',
        ".harness/scripts/scopes/tidy.py": 'NAME = "tidy"\n\nB = "TID001"\n',
    })
    csd = clean / ".harness/scripts/scopes"
    mods = [FakeScope("good", csd / "good.py", reflect=("GOOD001",)),
            FakeScope("tidy", csd / "tidy.py", reflect=("TID001",))]
    f = []
    sc_hooks.reconcile(clean, csd, mods, "registry.py", f)
    sc_hooks.check_registration(mods, clean, csd, f)
    out.append(("HOOK00n", "正对照：目录与登记一一对应、code 全认领时不该报", bool(codes_of(f))))
    return out
