# 门记录 20261029T013600Z — 依赖连不上时要说得出原因（T-19b）

批次：只做一类事——把「连不上 mysql / redis」从 nil panic 改成一次性可读退出。不含 compose 与
Dockerfile（T-19c），不含列名漂移（T-20），也不在这批动 `-f`（下面登记了发现）。

## 为什么现在必须做

私有化交付里客户现场第一批故障一定是「依赖没起来」或「地址写错」。上一批实测到的形状是（见
20261029T012600Z）：

```text
主数据库连接失败: dial tcp 127.0.0.1:3399: connect: connection refused
panic: runtime error: invalid memory address or nil pointer dereference
	pkg/mysql/mysql.go:115
```

原因那行有，但它是 `log.Printf` 之后 `return`——函数照样让调用方拿到东西，紧接着的 nil 解引用
把整段输出压成一次崩溃；而崩溃里既没有地址也没有库名。更要紧的是这条路径由 `sync.Once` 守着，
只可能走到一次：一旦走岔，进程要么带 nil 连接继续活着，要么在完全无关的代码位置上炸。

## 改了什么

- `pkg/mysql/mysql.go`
  - `connectMysql()` 现在返回 `error`，不再「打完日志就 return」。
  - 新增 `target`（user/password/host/port/dbName）：`dsn()` 带密码，`label()` 只带
    `user@host:port/dbname`。错误消息一律只用 `label()`——这一行会进容器 stdout，可能被采集留档。
  - 抽出 `open(role, target, logger)`：主从两处原本各抄一遍 DSN、`gorm.Open`、连接池设置，
    其中主库那条 `db.DB()` 失败的日志写成了「获取从数据库SQL DB失败」。现在一处、带角色前缀。
  - 修掉一个真 bug：从库关闭时 `currentDB` 被留成 nil，`MysqlDb(true)` 拿到 nil 连接、用到才炸。
    现在默认「当前库 = 主库」，开从库才切过去。
  - `MysqlDb()` 首次连接失败走 `log.Fatalf("启动失败：%v", err)`。
- `pkg/redis/redis.go`：`connectRedis()` 返回 `error`，`panic(re.Err())` 换成带 `host:port` 的
  一条消息 + `Client()` 里 `log.Fatalf`；密码只进 `redis.Options`，不进消息。
- `pkg/mysql/mysql_test.go`、`pkg/redis/redis_test.go`：本仓第 2、3 个 Go 单测。断言的是两件事——
  错误里必须有 `主库 thooh@127.0.0.1:<端口>/<库名>` 和底层 `connection refused`，且**不能有密码**。
  端口用「先 `net.Listen` 占一个再放开」拿到（回环上的空闲端口立刻 ECONNREFUSED），不硬编码。

## 实测

```text
$ make test      ok github.com/x-thooh/thooh-admin/pkg/mysql  1.624s
                 ok github.com/x-thooh/thooh-admin/pkg/redis  2.151s        exit 0
$ make vet       go vet exit=0
$ make fmt       （无输出，已格式化）
$ go build -o /tmp/t19b-main .                                               exit 0
$ cd /tmp/t19b-run && /tmp/t19b-main          # 配置指向一个已放开的回环端口
2026-10-29 09:34:51 启动失败：主库 thooh@127.0.0.1:49575/thooh-go 连不上：dial tcp 127.0.0.1:49575: connect: connection refused
                                                          退出码=1  panic 行数=0  密码出现次数=0
$ make check-all 0 ERROR, 2 WARN                                             exit 0
```

两条 WARN 都不是这一批引入的：`STL004`（swagger paths 为空，全库 `@Router` 缺失）与 `BLD002`
（证据文件比现有 Go 源码旧——本批又改了 .go，攒到 T-19 收尾时用 `make evidence` 一起刷，
现在刷完下一批立刻又旧）。

反向验证（把实现改坏，看测试是否立刻红）：

```text
① label() → dsn()（密码进错误消息）
   FAIL：错误消息漏出了密码 + 缺 "thooh@127.0.0.1:49295/thooh-go"
② open() 里 gorm.Open 失败改成 return &gorm.DB{}, nil（把错误咽掉）
   FAIL：连不上的库必须返回错误，不能把 nil 连接交给调用方
```

两条都立刻红，改回即绿。还原用 `cp /tmp/*.bak`，不用 `git checkout --`：见 lessons L-13。

## 为什么是「一次性退出」而不是把 error 往上抛

`MysqlDb()` 有 260 个调用点（`grep -rn "MysqlDb(" `，排除 `.go/` 缓存与 pkg/mysql 自身），
`redis.Client()` 有 5 个。逐个改成返回 `(x, err)` 是一轮独立的重构，且大多数调用点本来就不检查错误。
这一批要的是「起不来的话说人话」，所以：
- 连接层返回 error（可测、可单测里直接断）；
- 只有 `MysqlDb()` / `Client()` 这两个入口把 error 变成 `log.Fatalf`。

`log.Fatalf` 而不是 panic：panic 在启动路径上给出的是运行时栈，在请求路径上会被 gin 的 Recovery
咽成一个 500——两种都比退出难查。密码不回显，因为退出码 + 一行原因已经够定位。

## 边界与后续

- 连不上库时进程退出，`restart: always` 的容器会崩溃循环。这是刻意的：日志里每一轮都是同一句原因，
  比「进程活着但每个请求都 500」好查。健康检查与 compose 侧的重启策略归 T-19c。
- **新发现（归 T-19c 收）**：`main.go:23` 注册了 `-f` 却从不调 `flag.Parse()`，全仓没有一处调用。
  实测 `-f /nonexistent/x.yaml` 的报错仍然指向 `./config.yaml`——这个 flag 是摆设，本地靠工作目录
  侥幸能用，容器里就得靠 `WORKDIR` 撞上。已写进看板 T-19 的 detail，配置路径要和 compose 一起定。
- 本批不判「库连上了但表/列对不上」（T-20 的验收），也不判 `ConnMaxLifetime` 配置项被忽略
  （代码写死 `time.Hour`，与 `config.Database.ConnMaxLifetime` 各算各的）。
