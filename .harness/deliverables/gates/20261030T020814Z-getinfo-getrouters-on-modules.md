# 门记录 20261030T020814Z — getInfo / getRouters 改挂 modules（T-28 验收）

批次：只做一类事——**把「我是谁、我能进哪些页」这两条接口从旧 RuoYi 模型搬到 dump 口径**，
入口注册一并改挂。代码 3 个文件（`modules/auth/{api,service,vo}.go`、`app/admin/router.go`），
数据 1 行（`thooh-go.sql` 的 `sys_role_actor`）。

## 验收口径（看板 T-28 原文）

> /login 拿到真 token（user_id=u1、dept_id=o1000），带它打 /getInfo 不返回 401（证明鉴权通过），
> 但 handler 里 panic「获取用户信息失败」……在 modules 里实现 getInfo（用户 + roles + permissions）
> 与 getRouters（菜单树），再把这两条从旧实现摘掉。前端 web/admin 读的是顶层 user/roles/permissions，契约要照旧。

## 现场前提

不重起一套（`thooh-mysql` 卷是共享的，两个 mysqld 挂同一个数据目录会把库写坏），改法是把本轮
代码单独编一个镜像，挂到主树那套的网络上跑第二个 webapp：

```
docker build -t thooh:t28 .                                  # exit 0，日志 /tmp/t28-image-build.log
docker run -d --name thooh-t28 --network thooh-admin_default \
  --env-file <主树>/.env -e THOOH_DB_HOST=mysql -e THOOH_REDIS_HOST=redis \
  -p 8081:8080 -v $PWD/config.yaml:/data/app/config.yaml:ro thooh:t28
```

主树那套（:8080）原样没动，测完这个容器 `docker rm -f thooh-t28` 就回到改前。

## 一、契约是先读前端读什么，再决定返回什么形状

不是照旧实现抄一遍字段名就完事，`web/admin` 与 `web/mobile` 的产物里逐条找过读取点：

- `GetInfo` action：`n.user.avatar`、`i.userId`、`i.userName`、`i.nickName`、`n.roles`、`n.permissions`
  ——**顶层平铺**，包一层 `data` 就两边一起白屏（所以 `UserVo` 只是 `user` 那一段的类型）。
- `GenerateRoutes`：读 `n.data` 当路由数组，按键 `component=="Layout"` 找布局、按 `children` 有无决定嵌套。
- mobile 个人中心：`e.user.nickName / .sex / .email / .phonenumber`。

`hidden`/`noCache` 两个布尔的取向照 `app/admin/model/system/sysMenu.go` 的旧实现（`Hidden = visible=="1"`、
`NoCache = is_cache=="1"`），落到 dump 列上就是 `hidden = shtag != 1`、`noCache = catag == 1`。
`catag` 的取向有两处独立佐证：DDL 注释「缓存标记」+ `modules/pub/vo.go` 对同一个值写的注释
「设置为 true 则不会被 keep-alive 缓存」，而种子里 `catag=1` 的正好全是 `*/edit`、`*/view` 这类详情页——
按「详情页不进缓存」解释得通，就按这个写。

## 二、超管走数据，不在 Go 里写死

实测（改前）：`sys_role_actor` 里 `u1` 一行没有（只有 `1:u2..u5`、`2:u6..u9`），而 `sys_role` 里 1 号是
「管理员 / 拥有所有权限」。也就是登录发得出 token，但 roles/permissions 全空、菜单树零棵。
旧实现是靠 `userId == 1` 特判给 `["admin"]` 与 `["*:*:*"]`——那是 RuoYi 的 int 主键时代的写法，
在这套 varchar(36) 口径里没有对应物。这一轮补的是数据：

```sql
INSERT INTO `sys_role_actor` VALUES (1, 'u1');
```

两边都验过，不是只改了文件：

- 现库：`INSERT` 后 `select ... where aid='u1'` → `1:u1`。
- 出货路径（把改过的 dump 当空库重建）：`mysql dump_check < thooh-go.sql` → **exit 0**、
  `/tmp/t28-dump-import.log` 里 `grep -c ERROR` = 0、`information_schema.tables` 计 41 张、
  `sys_role_actor where aid='u1'` 计 1 行。

## 三、实测矩阵（base http://127.0.0.1:8081）

| 场景 | 结果 |
| --- | --- |
| `POST /login` admin | token 长度 260 |
| `GET /getInfo` 带 u1 token | code 200；`user.userId=u1`、`userName=admin`、`nickName=管理员`、`phonenumber=13812345678`、`email=thooh@qq.com`、`sex=1`、`createTime=2026-01-20 15:03:01`、`dept={id:o1000,name:XX科技}`；`roles=[管理员]`；`permissions` 57 条 |
| `GET /getInfo` 无 token | `{"code":401,"msg":"令牌不能为空"}` |
| `GET /getInfo` 坏 token | `{"code":401,"msg":"认证失败"}`（getRouters 同） |
| `GET /getRouters` 带 u1 token | code 200；4 棵顶层：`/sys`[11]、`/mon`[7]、`/tool`[7]、`/bpm`[9]，目录 `component=Layout`、`alwaysShow=true`、`redirect=noRedirect`；子页 `hidden` 与 `noCache` 按种子对得上（`user/edit` hidden=true noCache=true） |
| 换一个人（u6 / zl，角色 2） | `roles=[普通用户]`、`permissions` 3 条、树只剩 `/bpm`[9] —— 权限确实按人给，不是写死 |
| 响应体搜口令 | `getInfo` 全文搜 `password` 无（`UserVo` 是逐字段点名取的，不是把 `SysUser` 整个 Marshal；列表接口那条还欠着，T-31） |
| SPA 深链回归 | `GET /dashboard` 带 `Accept: text/html` → 200、12301B 首页（T-27 的页面导航豁免没被这两条改挂碰坏） |

## 四、浏览器里真点一遍（接口通 ≠ 页面起得来）

`mcp browser-use` 打开 :8081/login，填 admin/admin123 提交 → 落在 `/admin/index`，侧边栏 menubar
四条子菜单；读 Vuex 落值：

```
user: id=u1  name=admin  nickName=管理员  avatar=/admin/static/img/profile.473f5971.jpg  roles=[管理员]  permissions=57 条
permission.sidebarRouters 顶层: 系统管理[11] 监控中心[7] 辅助工具[7] 流程管理[9]
```

`user.id` 之前是 `undefined`（旧实现压根没给 `userId` 这个键），现在落到了 `u1`。

## 五、顺手去掉的那层缓存

改挂前这两条是 `e.GET("getInfo", handlerFunc, api.GetInfoHandler)`，`handlerFunc` 是
`cache.CacheByRequestURI(memoryStore, 2*time.Second)`——**按 URI 缓存 2 秒，键里不分用户**。
`/getInfo` 的响应是「这个人是谁、能进哪些页」，同窗口内第二个登录的人会拿到第一个人的身份。
新写法不带它（`gin-cache` 仍被 `app/html/router.go` 用着，依赖没变成孤儿）。
这一条是照代码推断去掉的，**没做对照实测**：旧 handler 在两条路径上都 panic，拿不到可比的响应体，
造不出「A 的身份发给 B」的现场。改完后同 token 连打两次是两次真查库（1.9ms / 1.5ms，无缓存命中）。

## 工具链

```
make fmt          → 无输出（gofmt 干净；先 gofmt -w 了 modules/auth/vo.go 的结构体对齐）
make build        → go build exit=0
make vet          → go vet exit=0
make index        → exit=0（STATE007：看板 T-28 改 doing 后 INDEX 与现算不一致，按规矩走派生）
make check        → 0 ERROR, 1 WARN（STL004 swagger 空），exit=0
make check-all    → 0 ERROR, 1 WARN，exit=0
make selftest     → 违规样本 105 条、正对照 21 条、判不了 0 条；覆盖 13 域，缺口 0
```

## 本轮没做到与故意没做

- **菜单里的 `comp` 与前端产物里的模块名对不上，页面点不开**。浏览器控制台实测
  `Error: Cannot find module './sys/user/index'`；`web/admin/static/js/app.*.js` 的懒加载上下文键是
  `./system/user/index`、`./monitor/online/index`、`./tool/gen/index` 这一套 RuoYi 目录名，
  dump 的 `sys_menu.comp` 是 `sys/user/index`、`mon/online/user/index`、`tool/code/index`。
  getRouters 的活到此为止（树按人给到了、路由建出来了），改名是数据还是重建前端二选一，登记 T-37。
- 前端 `v-hasPermi` 用的权限字符是 `system:user:edit` 这一套，dump 的 `sys_api.perm` 是 `sys:user:edit`；
  两边一个字母之差，按钮全隐。登记 T-38。
- 角色 1「拥有所有权限」实际只授了 38/42 菜单、57/73 接口，缺的正好是「使用案例」整块；
  旧实现靠 `*:*:*` 是全给。要不要在数据里表达 superadmin，登记 T-39。
- 旧的 `api.GetInfoHandler` / `api.GetRoutersHandler` 留在原地不删——按目录退役（T-20e），
  零散删函数会让「还剩多少没退」判不出来。
- mobile 端只核对了它读的键名（`user.nickName/.sex/.email/.phonenumber`），没真跑一遍 H5。
- `dept` 直接回 `sys_org` 这一行（`id/name/tier/...`），不包装成 RuoYi 的 `deptId/deptName`：
  实测 `web/admin` 产物里 `deptName` 出现 0 次，没有读取点就不发明键名。
