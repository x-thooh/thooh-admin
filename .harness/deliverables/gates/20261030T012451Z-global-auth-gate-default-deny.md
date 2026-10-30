# 门记录 20261030T012451Z — 全局鉴权门：默认要 token（T-27 验收）

批次：只做一类事——**把「每个模块自己挂鉴权」换成「入口全局挂一次，公开面显式列出」**。
改的是 4 个文件：新增 `app/core/utils/jwt/gate.go`，`app/core/routers/routers.go` 里挂上，
`jwt.go` 的 `JWTAuthMiddleware` 收敛成 `Gate()` 的别名，`app/admin/router.go` 里按组挂的那处删掉。

## 验收口径（看板 T-27 原文）

> sys/user、sys/config、sys/role、tool/* 等所有 modules 端点都不需要 token 就能 CRUD……
> 做法：modules 各组统一挂鉴权，公开面（登录、验证码、pub 下的免鉴权项）显式列白名单，别靠「没挂」来放行。

## 为什么不是「逐个模块挂」

原样写法是 `r := e.Group("/sys/user"); r.Use(jwt.JWTAuthMiddleware())`。这种姿势下，
**新增一个模块 = 默认免鉴权**，而且没人会报错——就是 T-27 的成因本身。反过来写（全局默认要 token，
免鉴权的面必须在 `gate.go` 里点名）才是「忘了写」会暴露、「写上了」才放行的方向。

## 现场前提

`docker compose build webapp && docker compose up -d webapp`（`make up` 不重建镜像，改完 .go 必须 build）。
容器 `thooh-go`，库是 T-20 那轮按 dump 重建的 `thooh-mysql` 卷，9 个用户。

## 实测矩阵（base http://127.0.0.1:8080）

### 免 token

```text
$ for p in / /index /dashboard /admin/ /sys/user /pub/user /tool/dict; do curl -s -o /dev/null -w '%-12s %{http_code} %{content_type}\n' $B$p; done
  /            200 text/html        （SPA 回落页）
  /index       200 application/json （登录前打的，57B）
  /dashboard   200 application/json 39B = {"code":401,"msg":"令牌不能为空"}   # 数据请求没 token，挡下
  /admin/      200 text/html 12301B （静态前端）
  /sys/user    200 {"code":401,"msg":"令牌不能为空"}
  /pub/user    200 {"code":401,"msg":"令牌不能为空"}
  /tool/dict   200 {"code":401,"msg":"令牌不能为空"}

$ curl -s -X POST -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin123"}' $B/login
  {"code":200,...,"token":"eyJ..."}   token_len=260        # 登录仍在门内可达
$ curl -s $B/login                                    # GET /login
  404 page not found      # 公开面放行到了路由层，没有 GET 处理器——这是既有事实，非本轮改动
```

### 带 token

```text
$ curl -s -H "Authorization: Bearer $T" "$B/sys/user?pageNum=1&pageSize=2"
  {"code":200,"msg":"成功","data":{"currentPage":1,"pageSize":2,"totalPages":5,"total":9,
   "rows":[{"id":"u1","name":"管理员","username":"admin","password":"$2a$10$...
$ curl -s -H 'Authorization: Bearer abc.def.ghi' "$B/sys/user?pageNum=1"
  {"code":401,"msg":"认证失败"}
$ curl -s -H "Authorization: Bearer $T" $B/dashboard
  404 text/plain          # 带 token 的未知路径仍是 NoRoute（Accept 不含 text/html，不回落页面）
```

### 回归项：SPA 刷新（本轮踩到并修掉的）

```text
$ curl -s -H 'Accept: text/html' $B/dashboard
  <!DOCTYPE html><html><head><meta charset=utf-8>...     # 回落页拿回来了
$ curl -s -H 'Accept: text/html' "$B/sys/user?pageNum=1"
  {"code":401,"msg":"令牌不能为空"}                        # 伪造 Accept 打已注册路径，仍挡
```

第一版门只按路径白名单放行，实测发现 SPA 刷新被挡：`GET /dashboard` 带 `Accept: text/html`
返回的是 `{"code":401,"msg":"令牌不能为空"}` 而不是回落页（全局中间件在 `r.NoRoute` 链上也会跑）。
当时想过「凡 `Accept: text/html` 都算导航」这一种修法——那等于让客户端用一个请求头决定要不要鉴权，
写的时候就否掉了。落下来的 `isPageNavigation()` 要 GET + `Accept: text/html` +
`ctx.FullPath() == ""`（没命中任何注册路由，最终走 `r.NoRoute` 回落页）三条都成立才放行。
这一条**在装好之后被真验过**：伪造 `Accept: text/html` 打已注册的 `/sys/user` 仍是 401，
`/dashboard` 带同一个头仍是回落页。规矩写进 lessons L-18。

## 工具链

```text
$ gofmt -l app/core/utils/jwt/     → 空
$ go build ./...                   → exit 0
$ make index                       → wrote .harness/INDEX.md（改 INDEX 前先派生，STATE007）
$ make check-all                   → 0 ERROR, 1 WARN（STL004 swagger paths 为空，既有）
$ make selftest                    → 违规样本 104 条、正对照 20 条、判不了 0 条；覆盖 13 域、缺口 0 条
```

## 提交这一刀自己被 T-26 拦过一次

第一次 `git commit` 时 pre-commit 报
`WKT004 树 T-20 的分支是 'task/T-27'`——假阳性，钩子把 `GIT_DIR`/`GIT_INDEX_FILE` 传给了
读兄弟树的 git 调用。这一棵树的脚本里还没有修复，所以只能先把 `task/T-27` 快进到 main
（main 已含 T-26 的 `gitenv.clean()`），再提交。绕开这一步的写法是 `--no-verify`，没用：
真修的是门禁本身，见门记录 20261030T014137Z。快进前把这份看板备份到
`/tmp/t27-board-20261030.json`，快进后按条目补回 T-31..T-34（主树那份不含这四条）。

## 本轮没做到与故意没做

- **门本身没有断言守着**：`r.Use(jwt.Gate())` 这行以后被删掉，`go build` 与 `make check` 都不会报，
  整套 modules 静默回到免鉴权。已登记 T-32（拟 GTE001，域 modules）。
- **带 token ≠ 按那个人来答**：`modules/pub/api.go:40 GetUser` 把身份写死成 `u1/admin`，
  `:60 GetMenus` 的 SQL 没有角色过滤。门只解决了「谁能进来」，没解决「进来看什么」。已登记 T-33。
- **响应体漏口令散列**：实测 `/sys/user` 的 rows 里带 `"password":"$2a$10$..."`。已登记 T-31。
- 白名单里 `/auth/login`、`/auth/code`、`/auth/logout` 三项**实测没有对应路由**：
  `grep -rn '"/auth' app/ modules/` 只在 gate.go 自己命中，`web/` 里也没有调用。它们是 RuoYi 血统的抄件。
  `/old`、`/protocol.html` 是真注册了的（`app/html/router.go:21,22`），保留。
  本轮**故意不裁**这三项——移动端的接口约定不在仓库里，裁错了是装好的 App 白屏，不是一句 grep 能兜住的
  后果；登记 T-34 等确认后再删。
- 实测 `/logout` 真删会话：`redis-cli --scan --pattern 'go_login_tokens:*'` 3 → 2 个键，
  退出后用同一个 token 打 `/sys/user` 得到 `{"code":401,"msg":"认证失败"}`。
- 未测：密码连续错误 5 次锁定（`pwdErrCntCache`）在新门下的行为。
- 未测：角色级授权（`sys_role_api`）——本轮只验「有没有 token」，没验「这个 token 能不能碰这条 API」。
