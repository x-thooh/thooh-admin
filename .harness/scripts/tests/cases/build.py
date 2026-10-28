"""build：编译、格式、证据时效。

慢域按函数取样（`check_gomod` / `check_gofmt` / `check_compile` / `check_evidence`），
不去跑整条 `run()`——那要把 go 工具链真的叫起来，selftest 就变成 build 了。
BLD004（工具链缺失）故意不造样本：环境故障不是违规，造它等于让 selftest 依赖一个坏环境。
"""

from scopes import build as sc_build
from support import codes_of, ctx_for, git, git_text, new_root

NAME = "build"

UNCOVERED = (
    ("BLD004", "工具链缺失 = 环境故障，故意造它等于让 selftest 依赖一个坏环境"),
)


def cases():
    out = []
    quality = {"go_version_min": "1.25", "go_src": "."}
    root = new_root({"go.mod": "module x\n\ngo 1.18\n"})
    f = []
    sc_build.check_gomod(root, quality, f)
    out.append(("BLD006", "go 指令低于要求版本", "BLD006" in codes_of(f)))

    root = new_root({"go.mod": "module x\n\ngo 1.25\n"})
    f = []
    sc_build.check_gomod(root, quality, f)
    out.append(("BLD006n", "正对照：达标版本不报", bool(codes_of(f))))

    root = new_root({"go.mod": "module x\n\ngo 1.25\n",
                     "bad.go": "package x\n\nfunc F() int {\nreturn 1\n}\n"})
    f = []
    sc_build.check_gofmt(root, f)
    out.append(("BLD005", "未过 gofmt（函数体没缩进）", "BLD005" in codes_of(f)))

    root = new_root({"go.mod": "module x\n\ngo 1.25\n", "ok.go": "package x\n\nfunc F() int { return 1 }\n"})
    f = []
    sc_build.check_gofmt(root, f)
    out.append(("BLD005n", "正对照：已格式化不报", bool(codes_of(f))))

    root = new_root({"go.mod": "module x\n\ngo 1.25\n", "bad.go": "package x\n\nfunc F() { undefined() }\n"})
    findings = []
    na = []
    sc_build.check_compile(root, quality, findings, na)
    got = codes_of(findings)
    if "BLD004" in got:
        out.append(("BLD003", "go 工具链不可用，这一条判不了", None))
    else:
        out.append(("BLD003", "编译不过", "BLD003" in got))

    root = new_root({"go.mod": "module x\n\ngo 1.25\n"})
    f = []
    sc_build.check_evidence(root, f, [])
    out.append(("BLD001", "一条证据都没有", "BLD001" in codes_of(f)))

    root = new_root({"go.mod": "module x\n\ngo 1.25\n", "a.go": "package x\n"})
    ok, _ = git(root, "init", "-q")
    if ok:
        git(root, "add", ".")
        git(root, "commit", "-q", "-m", "one")
        first = git_text(root, "rev-parse", "HEAD")
        (root / "b.go").write_text("package x\n")
        git(root, "add", ".")
        git(root, "commit", "-q", "-m", "two")
        ev = root / ".harness/deliverables/evidence"
        ev.mkdir(parents=True, exist_ok=True)
        (ev / "verify-1.txt").write_text(f"# commit: {first}\n旧结论\n")
        f = []
        sc_build.check_evidence(root, f, [])
        out.append(("BLD002", "证据之后源码又提交了", "BLD002" in codes_of(f)))
    else:
        out.append(("BLD002", "git 不可用，这一条判不了", None))
    return out
