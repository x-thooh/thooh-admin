"""modules：模块目录 ↔ 注册表（router.go）双向对账。

MOD003c 是断言坑 #13 的样本：注释里的 `foo.Init(e)` 不算挂载。它同时验两件事——
这条断言会报，且「剥注释」这一步真做了。
"""

from scopes import modules as sc_modules
from support import codes_of, ctx_for, new_root

NAME = "modules"

GO_MOD = "module vben\n\ngo 1.25\n"
ROUTER_INIT = "package foo\n\nimport \"github.com/gin-gonic/gin\"\n\nfunc Init(e *gin.Engine) {}\n"


def cases():
    out = []
    mod = {"modules/foo/router.go": ROUTER_INIT, "modules/foo/api.go": "package foo\n", "go.mod": GO_MOD}
    root = new_root({**mod, "app/admin/router.go": "package admin\n\nfunc Routers() {}\n"})
    f = []
    sc_modules.run(ctx_for(root, {"gate_file": "", "module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD001", "模块导出 Init 但注册表没 import", "MOD001" in codes_of(f)))

    root = new_root({
        **mod,
        "app/admin/router.go": 'package admin\n\nimport (\n\t"vben/modules/ghost"\n)\n\nfunc Routers() { ghost.Init(nil) }\n',
    })
    f = []
    sc_modules.run(ctx_for(root, {"gate_file": "", "module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD002", "注册表 import 了不存在的模块路径", "MOD002" in codes_of(f)))

    root = new_root({
        **mod,
        "app/admin/router.go": 'package admin\n\nimport (\n\t"vben/modules/foo"\n)\n\nfunc Routers() { _ = 1 }\n',
    })
    f = []
    sc_modules.run(ctx_for(root, {"gate_file": "", "module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD003", "import 了但没有 Init 调用", "MOD003" in codes_of(f)))

    root = new_root({
        "modules/bar/api.go": "package bar\n",
        "modules/bar/model.go": "package bar\n",
        "go.mod": GO_MOD,
        "app/admin/router.go": "package admin\n",
    })
    f = []
    sc_modules.run(ctx_for(root, {"gate_file": "", "module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD004", "有 api.go 却没有 router.go", "MOD004" in codes_of(f)))

    root = new_root({"go.mod": GO_MOD, "modules/foo/router.go": "package foo\n"})
    f = []
    sc_modules.run(ctx_for(root, {"gate_file": "", "module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD005", "注册表文件不存在", "MOD005" in codes_of(f)))

    root = new_root({"go.mod": GO_MOD, "app/admin/router.go": "package admin\n"})
    f = []
    sc_modules.run(ctx_for(root, {"gate_file": "", "module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD005b", "模块根下一个 .go 都没有", "MOD005" in codes_of(f)))

    # 断言坑 #13：注释里的挂载不算注册。这一条同时是 MOD003 与「剥注释」的反向样本。
    root = new_root({
        **mod,
        "app/admin/router.go": 'package admin\n\nimport (\n\t"vben/modules/foo"\n)\n\nfunc Routers() {\n\t// foo.Init(e)\n}\n',
    })
    f = []
    sc_modules.run(ctx_for(root, {"gate_file": "", "module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD003c", "注释里的 foo.Init(e) 不算挂载", "MOD003" in codes_of(f)))

    root = new_root({
        **mod,
        "app/admin/router.go": 'package admin\n\nimport (\n\t"vben/modules/foo"\n)\n\nfunc Routers() { foo.Init(nil) }\n',
    })
    f = []
    sc_modules.run(ctx_for(root, {"gate_file": "", "module_roots": ["modules"], "registry_file": "app/admin/router.go"}), f)
    out.append(("MOD00n", "正对照：登记齐全的模块不该报", bool(codes_of(f))))

    gate_q = {"module_roots": ["modules"], "registry_file": "app/admin/router.go"}
    ok = "package r\n\nfunc f() {\n\tr.Use(jwt.Gate())\n\thtml.Routers(r)\n\tadmin.Routers(r)\n}\n"
    bad_order = "package r\n\nfunc f() {\n\thtml.Routers(r)\n\tr.Use(jwt.Gate())\n}\n"
    for code, what, body in (
        ("GTE001", "Gate 被注释掉", ok.replace("\tr.Use", "\t// r.Use")),
        ("GTE001b", "Gate 在 Routers 之后", bad_order),
    ):
        root = new_root({"go.mod": GO_MOD, "app/core/routers/routers.go": body})
        f = []
        sc_modules.run(ctx_for(root, gate_q), f)
        out.append((code, what, "GTE001" in codes_of(f)))
    root = new_root({"go.mod": GO_MOD, "app/core/routers/routers.go": ok})
    f = []
    sc_modules.run(ctx_for(root, gate_q), f)
    out.append(("GTE001n", "正对照：Gate 在 Routers 之前不该报", "GTE001" in codes_of(f)))
    return out
