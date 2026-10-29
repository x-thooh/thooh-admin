# 门记录 20261029T020216Z — 干净 clone 真起得来整套（T-19d 验收）

批次：只做一类事——**验收**。代码改动在 `340206f`（README 部署段）与 `ce57b94`（编排提级）里，
这一篇记的是「按 README 从一个干净 clone 走一遍，得到什么」。

## 验收口径（看板 T-19 原文）

> 干净 clone 起容器，mysql 与 redis 健康检查通过，/login 不再 nil panic 而是给出可读的 SQL 错误。

## 实测：从任务树另起一份干净 clone

```text
$ make down                      # 任务树那套先停：容器与网络清掉，卷 thooh-mysql 留着
$ git clone --branch task/T-19 <任务树> /tmp/t19d-clone
  340206f 部署段进 README：一条命令起整套，说清缺什么与为什么
$ cd /tmp/t19d-clone && ls -a    # 仓库内容就是这些：Dockerfile docker-compose.yml config.yaml
                                 # .env.example .dockerignore thooh-go.sql web/ ...（无 .deploy、无真凭据）
$ cp <任务树的 .env> .env        # 客户自己填的那一个文件，仓库里没有，这是唯一的额外输入
$ make up
  Container t19d-clone-redis-1 Healthy / Container t19d-clone-mysql-1 Healthy
  Container thooh-go Started                                                            exit 0
$ docker compose ps
  mysql  Up (healthy)   redis  Up (healthy)   webapp  Up
$ curl -X POST -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin123"}' \
    http://127.0.0.1:8080/login
  {"code":500,"msg":"Error 1054: Unknown column 'config_key' in 'where clause'"}
$ docker images thooh --format '{{.CreatedSince}}'
  10 minutes ago        # 镜像被复用，clone 里没有重编
$ docker compose down && rm -rf /tmp/t19d-clone
```

三条口径逐条对上：容器起来（`up -d` exit 0）、两个依赖都 healthy（healthcheck 真的在把关，
webapp 是等它们绿了才起）、`/login` 给的是**一条可读的 SQL 错误**而不是 nil panic，
且进程没退、容器没重启（`RestartCount=0`）。这条做完 `/login` 仍拿不到 200 的业务结果——
列名漂移归 T-20，这是 D-20 里定好的顺序。

## 跑起来才看见的账（坐在代码前想不出来）

T-19c 记了两笔（T-23 `server.logLevel` 没人读、T-24 启动即 AutoMigrate）。这一批又看见三笔：

1. **业务错误靠 `panic` 传**（T-25）。登录失败的日志形状是：
   ```text
   2026/10/29 01:59:11 panic: {500 Error 1054: Unknown column 'config_key' in 'where clause' <nil>}
   goroutine 30 [running]:  runtime/debug.Stack() … app/core/utils/error/Recover.go:24 …
   ```
   `app/core/utils/error/Recover.go:19-30` 把 panic 恢复成 HTTP 200 + JSON，
   代价是每次业务失败打一整屏 goroutine dump。客户端看到的 `msg` 是对的，
   但「错误即 panic」这条路会把真崩溃混在噪声里。
   与 D-21 同族：那批里 `panic(R.Result)` 只打出地址，这条恰好打得出来——同一个值两种命运，
   正因为不可预期，才更不该拿 panic 当返回通道。
2. **错误日志本身又炸一次**：`Error 1146: Table 'thooh-go.sys_oper_log' doesn't exist`
   （同一处 Recover 里写库）。这是 T-20 清单里 `sys_oper_log ↔ mon_oper_log` 漂移的现场证据，
   记下来是因为它发生在**报错的路上**：报错了却报不出来，最难查的就是这种。
3. **compose 会因 `.env` 变化重建容器**：改一个变量 `make up` 就重建，
   而 mysql 的口令只在卷为空时生效——「改了 `.env` 的口令但库里还是旧口令」这条路径存在。
   **本批没实测**：验证它要 `down -v` 删库，是破坏性动作，且这台机器上的卷是多棵树共用的。

## 边界（写清哪些是实测、哪些是依据）

- 「`thooh-go.sql` 只在数据卷为空时执行」写在 compose 注释与 README 里，依据是 mysql 官方镜像的
  initdb 语义，**不是本批实测**（同上，要删卷才能验）。第一次起时 `Volume thooh-mysql Created`
  之后库里确有表，只能算旁证。
- `docker save` 三个镜像约 1.2GB 是按 `docker images` 的体积推的；实测只做了 webapp 单独一轮
  `save（22M）→ rmi → load`，输出 `Loaded image: thooh:1.0.0`。
- 内网 GOPROXY 与 `GOSUMDB`（T-4）、历史密钥轮换（T-6）、`mise.toml` 在未信任目录里会让
  `make` 直接失败（现场：`/private/tmp/t19d-clone/mise.toml ... not trusted`）——
  最后这条是客户机真会撞上的：`make` 走 mise 的 shim。本批只在 README 用 `make`，
  没有替它做判定，登记在这里因为它属于「命令入口」而不是部署编排。

## 数字

```text
$ make selftest    违规样本 104 / 正对照 20 / 判不了 0 / 缺口 0        exit 0
$ make evidence    .harness/deliverables/evidence/verify-20261029T020328Z.txt
                   # 命令：make check-all  # commit: 340206f  # 工作区：dirty（就是本批未提交的那几份文档）
                   0 ERROR, 1 WARN（STL004 swagger paths 为空）      exit 0
$ make check-all   同上：0 ERROR, 1 WARN                              exit 0
```

工作区标 dirty 是因为证据要在文档落笔之前跑；合回 main 之后会从干净的主树再存一份，那份才是这轮的最终证据。
