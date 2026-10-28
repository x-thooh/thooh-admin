<!-- agents: scope=web parent= -->
# web/ — 前端构建产物

只有产物，没有前端源码：`admin/`（vben 后台 dist）、`mobile/`（uni-app）、
`mobile_old/`、`template/`（代码生成器用的 `.tpl`，被 `app/admin/service/tools/gen.go` 读）。

- `web/admin/index.html` 里 `href=/admin/static/...`、`src=/admin/static/...` 靠
  `app/core/routers/routers.go` 的 `r.Static("/admin", "./web/admin")` 解析。改了挂载前缀
  或换了 dist，两边必须一起改——断言按挂载表逐条查文件在不在。`scope=stale`
- 产物带内容哈希（`app.3bd2cbbb.js`），一次构建全批换名：只替换半个目录 = 白屏。
  所以更新前端要么整目录换，要么不换。无断言（人判）：半个目录长什么样判不完。
- `template/*.tpl` 是**生成器输入**，改它等于改所有以后生成的模块，属单独一轮，
  记进 `.harness/memory/decisions.md`。
- `web/template` 与 `gen.go` 里写的 `view/template` 路径不一致（现存事实）。无断言（人判）：
  生成器只在跑的时候暴露，等第一轮真跑代码生成时再修。
