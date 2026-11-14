<div align="center"><h1 align="center">thooh-go</h1></div>
<div align="center"><h3 align="center">一个开箱即用的通用开发平台GO语言版</h3></div>

# 🍿 相关地址

* PC端体验地址 ：[http://8.153.168.178/](http://8.153.168.178/)
* 移动端体验地址 ：[http://8.153.168.178/app/](http://8.153.168.178/app/)
* 联系方式（加微信后可找小狐狸拉进交流群）：

![输入图片说明](https://gitee.com/thooh/thooh-app/raw/master/docs/wx.jpg "微信联系方式")


# 🍟 概述
* 前端采用Vue3、Element Plus，基于thooh5前端项目修改。
* 后端参考学习的`乐观开发者`的 [https://gitee.com/OptimisticDevelopers/Ruoyi-Go](https://gitee.com/OptimisticDevelopers/Ruoyi-Go)
* 后端采用go & gin & Jwt & gorm & mysql & copier & redis & gin-cache && xxl-job。
* 权限认证使用OAuth2 & Jwt，支持多终端认证系统。
* 支持加载动态权限菜单，多方式轻松权限控制。


# ⚡ 快速启动（本机开发）

需要 Go 1.26+。`config.yaml` 里只有**形状**，值一律从环境变量注入——所以本机跑之前要先给两条必填：

```bash
go mod tidy

# 两条必填（口令自己生成，别用示例值）
export THOOH_DB_PW="$(openssl rand -base64 24 | tr -d '=+/')"
export THOOH_JWT_SECRET="$(openssl rand -base64 48 | tr -d '\n/+=')"

# 依赖：用你本机已有的 mysql(3306) 与 redis(6379)，或显式指到别处
# 库表：新建数据库 thooh-go（默认名，可用 THOOH_DB_NAME 改），导入根目录的 thooh-go.sql
go run main.go              # 默认读 ./config.yaml；-f 可指到别处
```

没给必填变量时会直接退出并点名缺哪个，这是刻意的（不带着弱口令起服务）。

`make up` 起的那套依赖**不发布宿主机端口**（见下面部署段），所以本机 `go run` 连不到它；
要在容器里跑后端就走 `make up`。

命令入口只有 `Makefile` 那张表，门禁与检查见 `AGENTS.md` 与 `.harness/`。

# 🔒 私有化部署（一台机器起整套）

`docker-compose.yml` 里是三件：`webapp` + `mysql:8.0`（自动导入 `thooh-go.sql`）+ `redis:7-alpine`。
客户机**只需要 docker**，不需要 Go——编译在镜像里做（`Dockerfile` 的 build 段）。

```bash
# 1) 填凭据（.env 被 gitignore 排除，永远不入库）
cp .env.example .env
# 编辑 .env，至少填这两条：
#   THOOH_DB_PW=<openssl rand -base64 24>
#   THOOH_JWT_SECRET=<openssl rand -base64 48>

# 2) 升级已有库前先跑 `make migrate`（服务启动不再自动改表）；全新库由 thooh-go.sql 导入

# 2b) 起整套（首次会构建镜像；mysql 与 redis 的 healthcheck 都过了才起 webapp）
make up            # 没有 make 就用：docker compose -f docker-compose.yml up -d

# 3) 验证：三个容器都在，webapp 活着
docker compose ps
make logs          # 起不来的原因就在这一屏里

# 4) 停（数据留在卷 thooh-mysql 里）
make down
```

## 需要哪些变量

| 变量 | 必填 | 默认（compose 里） |
| --- | --- | --- |
| `THOOH_DB_PW` | 是 | 无——没给时 compose 拒绝启动并点名 |
| `THOOH_JWT_SECRET` | 是 | 无，同上；换了它现存 token 全部失效 |
| `THOOH_DB_HOST` / `THOOH_DB_PORT` | 否 | `mysql` / `3306`（compose 内网服务名） |
| `THOOH_DB_NAME` / `THOOH_DB_USER` | 否 | `thooh-go` / `root` |
| `THOOH_REDIS_HOST` / `THOOH_REDIS_PORT` / `THOOH_REDIS_PW` | 否 | `redis` / `6379` / 空 |
| `THOOH_PUBLIC_PORT` | 否 | `8080`（只改宿主机端口，容器内仍是 8080） |
| `THOOH_RUN_MODE` / `THOOH_LOG_LEVEL` | 否 | `release` / `info` |

语法：`config.yaml` 里 `${NAME}` 必填、`${NAME:-默认}` 可空；注释里的 `${...}` 是文档，不会被当成引用。

## 凭据在哪里

- 仓库里的 `config.yaml` 只有形状，没有值。
- 值只在 `.env`（被 `.gitignore` 排除）与容器环境变量里。
- 镜像里**没有** `config.yaml`：它由 compose 以只读卷挂进去（`.dockerignore` 也把它排掉，
  免得客户改过的配置被烘进镜像层）。
- 健康检查用容器自己的 `$MYSQL_ROOT_PASSWORD`，不让 compose 插值——否则 `docker inspect` 上会留一份明文。

## 数据、迁移与升级

- `thooh-go.sql` 只在数据卷为空时执行。改了 dump 要先清卷（下面这条**会删库**，确认过再跑）：

  ```bash
  docker compose -f docker-compose.yml down -v
  ```

- 启动时 `app/admin/router.go` 会对 `sys_group`、`sys_group_cate`、`sys_group_actor` 三张表跑
  `AutoMigrate`（每次 boot 都可能改表）。备份与升级口径见看板 T-24。

## 离线交付（内网机器不能上网）

在一台能上网的机器上构建，再把镜像搬进去：

```bash
docker compose -f docker-compose.yml build
docker save thooh:1.0.0 mysql:8.0 redis:7-alpine -o thooh-images.tar   # 约 1.2GB（单独的 webapp 实测 22M）
# 拷 thooh-images.tar 与仓库（含 .env）到内网机器
docker load -i thooh-images.tar
make up
```

镜像都在了，`make up` 不会再触发构建。Go 模块的离线来源（内网 GOPROXY 与校验库）见看板 T-4。

## 起不来时先看这三条

| 输出 | 意思 | 出路 |
| --- | --- | --- |
| `required variable THOOH_DB_PW is missing a value: 必填…` | `.env` 没填或没导出 | 填 `.env`；compose 与 `up` 都会点名同一个变量 |
| `启动失败：这些环境变量没给值 → THOOH_DB_PW, THOOH_JWT_SECRET` | 本机 `go run` 前没给值 | 显式 `export`，清单见上表 |
| `启动失败：主库 root@127.0.0.1:3306/thooh-go 连不上：dial tcp: connect: connection refused` | 依赖没起来或地址写错 | `docker compose ps` 看 health；`make logs` 看完整原因。消息里只有地址，不含口令 |

## 现在已知的不通过

按现状如实记（这些不是部署失败，是应用与库里对不上账）：

```bash
curl -X POST -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' http://127.0.0.1:8080/login
# {"code":500,"msg":"Error 1054: Unknown column 'config_key' in 'where clause'"}
```

HTTP 层通了、容器不再崩溃，但 `app/admin/model` 那套旧模型的列名与自带 dump 对不上，
登录因此还拿不到 200 的业务结果——这一轮按「以 dump 为准」重写在看板 T-20。
另两条噪音：`server.logLevel` 目前没接到 gorm 日志（每条 SQL 都打 stdout，T-23）、
启动即 `AutoMigrate`（T-24）。


# 🍖 详细功能

1. 主控面板：控制台页面，可进行工作台，分析页，统计等功能的展示。
2. 部门管理：部门维护，支持多层级结构的树形结构。
3. 用户管理：用户维护，可设置用户部门，岗位，群组，职务，角色，数据权限等。
4. 岗位管理：岗位维护，岗位可作为用户的一个标签，岗位也可与权限等其他功能挂钩。
5. 群组管理：群组维护，群组可设置部门，用户，岗位，用于更广泛的权限设置。
6. 菜单管理：菜单目录，菜单，和按钮的维护是权限控制的基本单位。
7. 角色管理：角色绑定菜单后，可限制相关角色的人员登录系统的功能范围。
8. 字典管理：系统内各种枚举类型的维护。
9. 访问日志：用户的登录和退出日志的查看和管理。
10. 操作日志：用户的操作业务的日志的查看和管理。
11. 定时任务：定时任务的维护，通过cron表达式控制任务的执行频率。
12. 流程引擎：流程图展示，支持驳回、转办、废弃，跳转等功能
13. 在线表单：在线表单设计，配合流程可以实现表单数据流转
14. 消息机制：待办待阅功能，联通钉钉与企业微信接口
15. 代码生成：在线配置，一键生成前后端代码

# ⚡ 近期计划

- [ ] 完善文档
- [ ] 完善工作流

# 💐 特别鸣谢
- 👉 乐观开发者：[https://gitee.com/OptimisticDevelopers/Ruoyi-Go](https://gitee.com/OptimisticDevelopers/Ruoyi-Go)
- 👉 thooh-Admin：[https://vvbin.cn/doc-next](https://vvbin.cn/doc-next)
- 👉 vxe-table：[https://gitee.com/xuliangzhan_admin/vxe-table](https://gitee.com/xuliangzhan_admin/vxe-table)
- 👉 VForm：[https://www.vform666.com](https://www.vform666.com/)

```
如果对您有帮助，点击右上角⭐Star⭐关注 ，感谢支持开源！
```