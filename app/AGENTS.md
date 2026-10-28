<!-- agents: scope=app parent= -->
# app/ — 框架层

- `app/core/`：启动、配置加载、中间件、静态挂载。`app/core/routers/routers.go` 里的
  `r.Static("/admin", "./web/admin")` 一类的挂载表是**前端产物的解析依据**，改它要连着
  判 `web/` 的引用是否还在。`scope=stale`
- `app/admin/router.go`：路由聚合，手写、无生成。加模块 = 在这里加 import + `alias.Init(e)`。
  `scope=modules`
- `app/admin/{api,model,router,service}/`：系统自带的管理与监控接口，跟 `modules/` 的
  业务模块不是一类东西，**不要**指望它们出现在模块对账里（模块根只有 `modules/` 与
  `admin/`，见 `.harness/config.json` 的 `module_roots`）。
- `app/html/`：gin 的 HTML 模板与 `createRender()`。

依赖方向现状（不是愿望）：`pkg/` 反向 import 了 `vben/app/...`，所以
「pkg 不许依赖 app」这条现在写不成断言。要收敛先立单独一轮，
记进 `.harness/memory/decisions.md`。

改中间件或启动顺序后跑 `make check-all`——编译是唯一能证明挂载点没被改坏的东西。
