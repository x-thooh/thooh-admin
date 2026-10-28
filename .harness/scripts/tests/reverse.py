#!/usr/bin/env python3
"""反向测试：每条断言都要真的会报。

为什么必须有这个文件：一条从未触发过的断言与「没有断言」是同一件事，但它更坏——
它给绿灯。本仓库 2026-10-28 的教训之一就是 `go vet` 写在文档里、从没跑过，
6 处 printf 缺陷静默存在（`.harness/memory/lessons.md` L-2）。

做法：在临时目录里造一个**最小违规仓库**，直接调那个 scope 的函数，看预期的 code
有没有报出来。每个已注册 scope 至少一条；能 cheap 造出「正对照」的也一并造——
只有反例没有正例，判不出「这条断言是不是永远在报」。

判不了的事写清楚，不冒充通过（STL003 的时间差分支要跨天提交，这里不造）。

用法：make selftest
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from scopes import baseline as sc_baseline  # noqa: E402
from scopes import build as sc_build  # noqa: E402
from scopes import entry as sc_entry  # noqa: E402
from scopes import modules as sc_modules  # noqa: E402
from scopes import secret as sc_secret  # noqa: E402
from scopes import stale as sc_stale  # noqa: E402

REGISTRY = ("entry", "modules", "secret", "stale", "build", "baseline")
UNCOVERED = [
    ("stale", "STL003", "要跨天提交才能造出「docs 落后 N 天」；本文件不造时间机器。人判：跑过一次 swag init 再补样"),
    ("build", "BLD004", "工具链缺失 = 环境故障，故意造它等于让 selftest 依赖一个坏环境"),
]


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


# --- 入口 --------------------------------------------------------------------

ROOT_OK = """<!-- agents: scope=. parent= -->
# x

## 目录地图

```text
app       ok
.harness  ok
```

## 硬规则

1. 规则一。`scope=modules`
"""


def case_entry():
    out = []
    root = new_root({"AGENTS.md": "没有 header\n"})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT001", "根入口没有 header", "ENT001" in codes_of(f)))
    root = new_root({
        "AGENTS.md": ROOT_OK,
        "app/AGENTS.md": "<!-- agents: scope=app parent=nope -->\n# x\n",
        "app/main.go": "package main\n",
    })
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT002", "子入口 parent 指向不存在的目录", "ENT002" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK + "\n" * 200})
    f = []
    sc_entry.run(ctx_for(root, {"agents_max_lines": 20}), f)
    out.append(("ENT003", "入口超行数上限", "ENT003" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK, "extra/x.go": "package x\n"})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT004", "磁盘有目录但地图没有", "ENT004" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK.replace("`scope=modules`", "没有载体")})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT005", "硬规则既没 scope 也没写「无断言」", "ENT005" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK.replace("scope=modules", "scope=ghost")})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT006", "标注了未注册的 scope", "ENT006" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT007", "派生索引不存在", "ENT007" in codes_of(f)))
    root = new_root({"README.md": "x\n"})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT008", "一个 AGENTS.md 都没扫到", "ENT008" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK, "app/main.go": "package main\n"})
    sc_entry._fix_guide(root)
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT00n", "正对照：合规入口不该报任何 entry 发现", bool(codes_of(f))))
    return out


# --- 模块注册 ----------------------------------------------------------------

GO_MOD = "module vben\n\ngo 1.25\n"
ROUTER_INIT = "package foo\n\nimport \"github.com/gin-gonic/gin\"\n\nfunc Init(e *gin.Engine) {}\n"


def case_modules():
    out = []
    mod = {"modules/foo/router.go": ROUTER_INIT, "modules/foo/api.go": "package foo\n", "go.mod": GO_MOD}
    root = new_root({**mod, "app/admin/router.go": "package admin\n\nfunc Routers() {}\n"})
    f = []
    sc_modules.run(ctx_for(root, {"module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD001", "模块导出 Init 但注册表没 import", "MOD001" in codes_of(f)))

    root = new_root({
        **mod,
        "app/admin/router.go": 'package admin\n\nimport (\n\t"vben/modules/ghost"\n)\n\nfunc Routers() { ghost.Init(nil) }\n',
    })
    f = []
    sc_modules.run(ctx_for(root, {"module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD002", "注册表 import 了不存在的模块路径", "MOD002" in codes_of(f)))

    root = new_root({
        **mod,
        "app/admin/router.go": 'package admin\n\nimport (\n\t"vben/modules/foo"\n)\n\nfunc Routers() { _ = 1 }\n',
    })
    f = []
    sc_modules.run(ctx_for(root, {"module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD003", "import 了但没有 Init 调用", "MOD003" in codes_of(f)))

    root = new_root({
        "modules/bar/api.go": "package bar\n",
        "modules/bar/model.go": "package bar\n",
        "go.mod": GO_MOD,
        "app/admin/router.go": "package admin\n",
    })
    f = []
    sc_modules.run(ctx_for(root, {"module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD004", "有 api.go 却没有 router.go", "MOD004" in codes_of(f)))

    root = new_root({"go.mod": GO_MOD, "modules/foo/router.go": "package foo\n"})
    f = []
    sc_modules.run(ctx_for(root, {"module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD005", "注册表文件不存在", "MOD005" in codes_of(f)))

    root = new_root({"go.mod": GO_MOD, "app/admin/router.go": "package admin\n"})
    f = []
    sc_modules.run(ctx_for(root, {"module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD005b", "模块根下一个 .go 都没有", "MOD005" in codes_of(f)))

    # 断言坑 #13：注释里的挂载不算注册。这一条同时是 MOD003 与「剥注释」的反向样本。
    root = new_root({
        **mod,
        "app/admin/router.go": 'package admin\n\nimport (\n\t"vben/modules/foo"\n)\n\nfunc Routers() {\n\t// foo.Init(e)\n}\n',
    })
    f = []
    sc_modules.run(ctx_for(root, {"module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD003c", "注释里的 foo.Init(e) 不算挂载", "MOD003" in codes_of(f)))

    root = new_root({
        **mod,
        "app/admin/router.go": 'package admin\n\nimport (\n\t"vben/modules/foo"\n)\n\nfunc Routers() { foo.Init(nil) }\n',
    })
    f = []
    sc_modules.run(ctx_for(root, {"module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD00n", "正对照：登记齐全的模块不该报", bool(codes_of(f))))
    return out


# --- 密钥 --------------------------------------------------------------------

def case_secret():
    out = []
    root = new_root({"config.yaml": "jwt:\n  secret: FAKEFAKEFAKE0123456789abcdefghijABCDEFGHIJ0123456789abcdef\n"})
    f = []
    sc_secret.run(ctx_for(root), f)
    out.append(("SEC001", "高熵密钥写在 config.yaml", "SEC001" in codes_of(f)))

    root = new_root({"config.yaml": "database:\n  primary:\n    password: 123456\n"})
    f = []
    sc_secret.run(ctx_for(root), f)
    out.append(("SEC002", "弱默认口令", "SEC002" in codes_of(f)))

    root = new_root({".env": "A=1\n", "readme.md": "x\n"})
    ok, _ = git(root, "init", "-q")
    if ok:
        git(root, "add", ".env")
        f = []
        sc_secret.run(ctx_for(root), f)
        out.append(("SEC003", "本地覆盖文件进了版本控制", "SEC003" in codes_of(f)))
    else:
        out.append(("SEC003", "git 不可用，这一条判不了", None))

    root = new_root({})
    f = []
    sc_secret.run(ctx_for(root), f)
    out.append(("SEC004", "一个候选文件都没有", "SEC004" in codes_of(f)))

    root = new_root({"config.yaml": "jwt:\n  secret: ${JWT_SECRET}\n"})
    f = []
    sc_secret.run(ctx_for(root), f)
    out.append(("SEC00n", "正对照：环境变量占位符不该报 SEC001", "SEC001" in codes_of(f)))
    return out


# --- 生成物 ------------------------------------------------------------------

SWAG_JSON = '{"swagger": "2.0", "info": {"title": "%s", "version": "v1"}, "host": "127.0.0.1:8080", "basePath": "/", "paths": {}}'
SWAG_YAML = 'swagger: "2.0"\ninfo:\n  title: %s\n  version: v1\nhost: 127.0.0.1:8080\nbasePath: /\npaths: {}\n'
MAIN_GO = 'package main\n\n// @title vben-go 接口文档\n// @version v1\n// @host 127.0.0.1:8080\n// @BasePath /\n\nfunc main() {}\n'


def case_stale():
    out = []
    quality = {"swagger_json": "docs/swagger.json", "swagger_yaml": "docs/swagger.yaml",
               "web_index": "web/admin/index.html", "stale_days_warn": 7, "stale_days_error": 14}
    root = new_root({
        "main.go": MAIN_GO,
        "docs/swagger.json": SWAG_JSON % "vben-g 接口文档",
        "docs/swagger.yaml": SWAG_YAML % "vben-go 接口文档",
        "app/core/routers/routers.go": 'package routers\n\nfunc R() { r.Static("/admin", "./web/admin") }\n',
        "web/admin/index.html": '<link href=/admin/static/css/missing.css>',
    })
    f = []
    sc_stale.run(ctx_for(root, quality), f)
    got = codes_of(f)
    out.append(("STL001", "json 的 title 与 main.go/yaml 不一致", "STL001" in got))
    out.append(("STL002", "入口 HTML 引用了不存在的产物", "STL002" in got))
    out.append(("STL004", "paths 为空", "STL004" in got))

    root = new_root({"app/core/routers/routers.go": "package r\n", "main.go": MAIN_GO,
                     "docs/swagger.json": SWAG_JSON % "vben-go 接口文档",
                     "docs/swagger.yaml": SWAG_YAML % "vben-go 接口文档"})
    f = []
    sc_stale.run(ctx_for(root, quality), f)
    out.append(("STL005", "web 入口产物不存在", "STL005" in codes_of(f)))

    root = new_root({
        "main.go": MAIN_GO.replace("// @version v1", "// @version v1\n// @description 同一份"),
        "docs/swagger.json": '{"swagger":"2.0","info":{"title":"vben-go 接口文档","version":"v1","description":"同一份"},"host":"127.0.0.1:8080","basePath":"/","paths":{"/x":{"get":{}}}}',
        "docs/swagger.yaml": 'info:\n  title: vben-go 接口文档\n  version: v1\n  description: 同一份\nhost: 127.0.0.1:8080\nbasePath: /\npaths:\n  /x:\n    get: {}\n',
        "app/core/routers/routers.go": 'package routers\n\nfunc R() { r.Static("/admin", "./web/admin") }\n',
        "web/admin/index.html": '<link href=/admin/static/css/app.aaa.css><script src=/admin/static/js/app.bbb.js>',
        "web/admin/static/css/app.aaa.css": "",
        "web/admin/static/js/app.bbb.js": "",
    })
    f = []
    sc_stale.run(ctx_for(root, quality), f)
    out.append(("STL00n", "正对照：三方一致 + 产物齐全 + 条件注释不参与判定",
                bool([c for c in codes_of(f) if c != "STL004"])))
    return out


# --- 构建 --------------------------------------------------------------------

def case_build():
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


# --- 账本 --------------------------------------------------------------------

def case_baseline():
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
        old = {"secret\tconfig.yaml\tSEC001:x\t1\n", }
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

    root = new_root({})
    f = []
    sc_baseline.run(ctx_for(root), f)
    out.append(("BASE00n", "正对照：零基线不报任何东西", bool(codes_of(f))))
    return out


CASES = [
    ("entry", case_entry),
    ("modules", case_modules),
    ("secret", case_secret),
    ("stale", case_stale),
    ("build", case_build),
    ("baseline", case_baseline),
]


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description="反向测试：每条断言都要真的会报")
    ap.add_argument("--root", default=None, help="只为与 Makefile 统一接口而收，本脚本不读仓库")
    args = ap.parse_args(argv)

    results, failures = [], []
    for scope, fn in CASES:
        for code, what, fired in fn():
            results.append((scope, code, what, fired))
            expect_fire = not what.startswith("正对照")
            if fired is not None and fired != expect_fire:
                failures.append((scope, code, what))
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
    for scope, code, why in UNCOVERED:
        print(f"未造样本  {scope:<9} {code:<9} {why}")
    print()
    violations = [r for r in results if not r[2].startswith("正对照")]
    controls = [r for r in results if r[2].startswith("正对照")]
    skipped = sum(1 for _s, _c, _w, x in results if x is None)
    print(f"违规样本 {len(violations)} 条、正对照 {len(controls)} 条、判不了 {skipped} 条")
    if failures:
        for scope, code, what in failures:
            print(f"SELFTEST FAIL {scope}/{code}：样本表现与预期不符（{what}）")
        return 1
    if skipped:
        print("有样本判不了（环境缺 git/go）——这不是通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
