# 门记录 20261029T015228Z — 能跑的编排提级进仓库（T-19c）

批次：只做一类事——让**干净 clone 能一条命令起整套**。镜像、编排、环境变量样例、配置路径这四件
都属于这一条。不含 README 部署段与离线交付（下一批），不含列名漂移（T-20）。

## 为什么现在必须做

D-20 盘点出的形状：仓库里那份 `docker-compose.yml` 只有 webapp 一个服务、`Dockerfile` 是
`COPY main`（要求宿主先 `go build -o main .`）且不挂配置，裸跑必读不到 config.yaml；
真能用的那份写在 `.deploy/proof.yml`，被 `.gitignore` 的 `.*` 排除在仓库外。
于是「能跑」和「在仓库里」是两件事——客户拿到的是后者。

## 改了什么

- `Dockerfile`：改成两段。编译段 `golang:1.26-alpine`（`go mod download` 单独一层，改一行代码不必重下模块），
  运行段 `alpine:3.20` + `ca-certificates`/`tzdata`（DSN 里 `loc=Local`，缺时区表会把本地时间读成 UTC）。
  加 `EXPOSE 8080`。不再 `COPY main`：忘了编就把上一个陈旧二进制烘进镜像，现场看不出来；
  现在客户机只需要 docker。删掉的 `ln -sf /dev/stdout /data/app/service.log` 全仓没有任何代码写这个文件。
- `.dockerignore`（新增，必须显式入库——见下）：排掉 `.go/`（实测 303M 的模块缓存，
  不打掉的话一次 `docker build` 把它整个传进上下文；与 lessons L-1 同一个坑）、
  `config.yaml` 与 `.env`（客户改过的配置带真凭据，不该烘进镜像层）。
- `docker-compose.yml`：三件一起——`webapp` + `mysql:8.0`（initdb 挂 `thooh-go.sql`、命名卷、healthcheck）
  + `redis:7-alpine`（healthcheck）。要点四条：
  - 凭据 `${VAR:?必填…}`：不给就**拒绝启动并点名**，应用在启动路径上也是同样口径（T-19a/T-19b）。
  - healthcheck 用 `CMD-SHELL` 里的 `$$MYSQL_ROOT_PASSWORD`，不让 compose 插值——
    写进 test 字符串等于在 `docker inspect` 上留一份明文副本。
  - mysql 与 redis 不写 `ports`：只有 webapp 对外可达。
  - 宿主机端口用 `THOOH_PUBLIC_PORT`，容器内固定 8080。一个变量担两个含义就会互相打脸
    （改了它就同时改了应用监听端口，映射跟着错位）。
  - 配置以**只读卷**挂进去，镜像里没有 `config.yaml`：烘一份进去就是第二个事实源。
- `.env.example`（新增）+ `.gitignore`：`.*` 会顺手吃掉 `.dockerignore` 和 `.env.example`，
  必须加 `!.dockerignore` / `!.env.example` 两条例外才真能入库——这一条不写出来就会「文件在磁盘上、
  仓库里没有」。（`.env` 本身仍被忽略：`git check-ignore -v .env` → `.gitignore:23:.*`。）
- `main.go`：补 `flag.Parse()`。`-f` 原本注册了却从不解析，实测改前 `-f /tmp/none/x.yaml` 的报错仍指向
  `./config.yaml`，容器里靠 `WORKDIR` 侥幸能用。
- `Makefile` + `AGENTS.md` 命令表：`up`/`down` 的说明改成「整套」，新增 `logs`（起不来的原因在容器日志里）。
  帮助文本里不写未注册的 `docker compose` 子命令——清卷这类破坏性动作留在 README，不做成 target，
  免得门禁下的 agent 顺手跑。

## 实测（全部真容器、真 HTTP）

```text
$ docker compose -f docker-compose.yml config -q      # 没给 THOOH_DB_PW / THOOH_JWT_SECRET
error while interpolating services.webapp.environment.THOOH_JWT_SECRET: required variable
  THOOH_JWT_SECRET is missing a value: 必填：签名密钥，生成：openssl rand -base64 48；换了它现存 token 全部失效
error while interpolating services.mysql.environment.MYSQL_ROOT_PASSWORD: required variable
  THOOH_DB_PW is missing a value: 必填：与 webapp 的 THOOH_DB_PW 同一个值                                    exit 1
$ docker compose -f docker-compose.yml up -d          # 同一套缺变量，起也起不来，消息同上                    exit 1
$ docker compose -f docker-compose.yml build                                                                exit 0
$ make up                                             # 这时磁盘上才有 .env（0600，值不回显）
  Container t-19-redis-1 Healthy / Container t-19-mysql-1 Healthy → Container thooh-go Started                exit 0
$ docker compose ps
  t-19-mysql-1  Up (healthy)   t-19-redis-1  Up (healthy)   thooh-go  Up
$ curl -X POST -d '{"username":"admin","password":"123456"}' http://127.0.0.1:8080/login
  HTTP 200  {"code":500,"msg":"Error 1054: Unknown column 'config_key' in 'where clause'"}
$ make check-all   0 ERROR, 2 WARN → make evidence 之后 0 ERROR, 1 WARN（只剩 STL004）                        exit 0
$ make test        ok pkg/mysql、ok pkg/redis、ok common/config                                              exit 0
$ /tmp/t19c-main -f /tmp/none/x.yaml
  启动失败：配置文件 /tmp/none/x.yaml 不存在（-f 指的路径，或容器里没挂进去）
```

`/login` 这一条就是 T-19 的验收口径：**不再 nil panic，而是一条可读的 SQL 错误**。
容器活着、进程没退、错误以业务码返回——列名漂移的证据留在这里，归 T-20 修。
口令由脚本随机生成写进 `.env`（0600），全程没回显过值。

## 现场看到的两条新账（登记成 T-23 / T-24）

跑起来之后才看见的东西，坐在代码前想不出来：

1. **`server.logLevel` 是死配置**（T-23）。`pkg/mysql/mysql.go:70` 硬编码 `logger.Info`，
   全仓没有任何地方读 `Server.LogLevel`——于是 release 部署把每条 SQL、每次 `information_schema`
   探查和耗时都打在 stdout 上。compose 传的 `THOOH_LOG_LEVEL` 现在也是没人读的值，这一条要么接上、
   要么把键删掉，不许留「配了但不生效」。
2. **启动即 AutoMigrate 改客户库**（T-24）。`app/admin/router.go:118` 每次 boot 都
   `ALTER TABLE sys_group / sys_group_cate / sys_group_actor`（日志里真跑到了）。
   私有化交付里「应用一启动就可能改表」必须进升级/回滚口径，或挪成显式动作——现在它藏在路由注册里。

## 边界

- 容器仍以 root 运行。`pkg/cache/fileCache` 往 `storage/` 写、`logMode: file` 往 `filePath` 写，
  改非 root 要连写入路径一起验，单独一轮。
- redis 不设密码：可达面只有 compose 内网（没发布端口）。客户自带 redis 时用 `THOOH_REDIS_PW`，
  config 侧 `${THOOH_REDIS_PW:-}` 已支持空值。
- mysql 用 root（与 `THOOH_DB_USER` 默认一致）。换非 root 要 `MYSQL_USER` + 授权 + 应用口令三处一起改，
  本批不动，别当成已加固。
- 离线交付（`docker save/load`、内网 GOPROXY 与 `GOSUMDB`，T-4）与 README 部署段归下一批。
- `thooh-go.sql` 只在数据卷为空时执行：改了 dump 不清卷，跑起来的还是旧 schema——这条写在 compose 注释里，
  因为「列名漂移修好了但库里没变」最容易误判成没修好。
