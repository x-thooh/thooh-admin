# 门记录 20261030T011406Z — 登录拿到真 token（T-20 第一刀验收）

批次：只做一类事——**把登录入口切到 dump 口径的那套并真实现它**。代码在 `84cbd72`（modules 接管登录）
与 `6f83899`（dump 补验证码开关），这一篇记的是「切完之后，真打一次得到什么」。

## 验收口径（看板 T-20 原文）

> 跑在 T-19 起起来的那套容器上，/login 返回 200 且 sys_config/mon_job 相关接口不再报 Unknown column。

## 现场前提

两套实现并挂在一个 gin engine 上：`app/admin/{api,model}` 是 RuoYi 血统（`user_id int`、`config_key`、
`sys_job`），`modules/` 已是 dump 口径（`id varchar(36)`、`kenam`、`mon_job`）。负责人定的路线是
**入口切到 modules 那套**；前提是 modules/auth 的登录得先真做出来——原样它是一个桩
（`accessToken="11233"`，不查库不验口令，见 lessons L-16）。

## 实测：干净库 + 真请求

```text
# 库按改过的 dump 重建（卷 thooh-mysql 是本轮 make up 造的，没有别的数据）
$ docker compose down -v && make up
  Container t-20-redis-1 Healthy / Container t-20-mysql-1 Healthy / Container thooh-go Started   exit 0
$ docker compose build webapp && docker compose up -d webapp
  Image thooh:1.0.0 Built                                                                        exit 0
  # 注意：make up 不重建镜像，改完 .go 必须 build 一次，否则跑的是旧二进制
  #（本轮第一次 make up 后 /login 仍报 config_key，就是旧镜像）

$ curl -s -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin123"}' \
    http://127.0.0.1:8080/login
  {"code":200,"data":{"access_token":"eyJ...","expire_in":43200},"msg":"登录成功","token":"eyJ..."}
  顶层键: ['code','data','msg','token']    data 键: ['access_token','expire_in']
  # 两套前端各有各的读法：web/admin 读顶层 .token，web/mobile 读 data.access_token（grep 量出来的）

$ python3 -c '解码 JWT' → claims: {"user_id":"u1","dept_id":"o1000","user_name":"admin","exp":1793365878,"iss":"thooh-go","uuid":"cfce05f1-..."}

$ T=$(取上面那个 token)
$ curl -s -H "Authorization: Bearer $T" http://127.0.0.1:8080/getInfo
  （响应体为空，不是 401）——鉴权中间件放行了，掉进旧实现：容器日志 panic: {500 获取用户信息失败 <nil>}
$ curl -s -H "Authorization: Bearer 瞎写的" http://127.0.0.1:8080/getInfo
  {"code":401,"msg":"认证失败"}                          # 假 token 确实被挡，不是「谁来都过」

$ docker exec t-20-redis-1 redis-cli --scan --pattern 'go_login_tokens:*'
  go_login_tokens:d535c433-d3fe-11f1-861e-12bf57931e75
  go_login_tokens:cfce05f1-d3fe-11f1-861e-12bf57931e75   # 会话真写进 redis，中间件按它判存活
$ docker exec t-20-mysql-1 mysql ... -e "select username,himsg,lotim from \`thooh-go\`.mon_login_log order by id desc limit 2"
  admin  登录成功  2026-10-30 01:11:27.771000
  admin  登录成功  2026-10-30 01:11:18.758000             # 登录日志写的是 dump 里真存在的表

$ docker logs --since 6m thooh-go | grep -c "Unknown column 'config_key'"
  0                                                     # T-19 留下的那条 1054 在登录链上没了
```

## 门禁

```text
$ go build ./...            exit 0（只有 gopsutil 的 cgo 弃用告警，存量）
$ make check-all            0 ERROR, 1 WARN（WARN 是存量 STL004：swagger paths 为空）
$ make selftest             违规样本 104 条、正对照 20 条、判不了 0 条，缺口 0 条
```

## 本轮没做到与故意没做

- `mon_job` 那条**没修**：旧 cron 在启动期查 `sys_job`（表不存在），每启动一次掉一条 Error 1146——
  登记成 T-29，不在这一刀的口径里。
- `getInfo` / `getRouters` 仍走旧实现，真 token 过了鉴权却在 handler 里 panic——登记成 T-28。
- 出错落库仍写 `sys_oper_log`（dump 里是 `mon_oper_log`），一次报错连带一次 panic——登记成 T-30。
- `modules/` 全套 CRUD 端点在鉴权外（全仓 `Use(` 零命中）——这条是安全硬伤，登记成 T-27，
  本轮没动，因为「给 modules 加鉴权」与「接管登录」是两类改动。
- 未实测的两条：`web/mobile` 对 `data.access_token` 的解包路径只按 grep 结果推断，没跑过真前端；
  密码错误锁定的 `maxRetryCount` 链路（连续错 5 次）没实测，只做了代码接线的搬运。
- 旧 `LoginHandler` / `CaptchaImageHandler` / `LogoutHandler` 只是**摘了挂载**没删，等 T-20e 退役账一起清。
