"""stale：生成物（swagger）与注解、前端产物三方一致。

STL003 造不出样本：它要「docs 落后 N 天」，那得跨天提交。本文件不造时间机器（不 mock 时钟、
不把 mtime 改到过去），所以在这里明写判不了，由 coverage() 记账，而不是悄悄少一条样本。
"""

from scopes import stale as sc_stale
from support import codes_of, ctx_for, new_root

NAME = "stale"

UNCOVERED = (
    ("STL003", "要跨天提交才能造出「docs 落后 N 天」；本文件不造时间机器。人判：跑过一次 swag init 再补样"),
)

SWAG_JSON = '{"swagger": "2.0", "info": {"title": "%s", "version": "v1"}, "host": "127.0.0.1:8080", "basePath": "/", "paths": {}}'
SWAG_YAML = 'swagger: "2.0"\ninfo:\n  title: %s\n  version: v1\nhost: 127.0.0.1:8080\nbasePath: /\npaths: {}\n'
MAIN_GO = 'package main\n\n// @title vben-go 接口文档\n// @version v1\n// @host 127.0.0.1:8080\n// @BasePath /\n\nfunc main() {}\n'


def cases():
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
