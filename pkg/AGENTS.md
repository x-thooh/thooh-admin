<!-- agents: scope=pkg parent= -->
# pkg/ — 独立工具包

`mysql`、`redis`、`cache`、`logs`、`middleware`、`scheduler`、`strcase`、`ristretto`。
这里放**与业务无关**的连接、缓存与中间件；`pkg/mysql/mysql.go` 的 `sync.Once` 与连接池
参数来自 `common/config`，改池子大小先改 `config.yaml` 的 `max_*_conn`，别在这里写死。

依赖方向现状（不是愿望）：`pkg/` 里有文件 import `vben/app/...` 与
`vben/app/admin/model/...`，所以「pkg 不许依赖 app」这条只能等人先把反向依赖清掉，
再写成断言。清了之后要在 `.harness/memory/decisions.md` 立一条并给 `scope=` 名字。无断言（人判）

改这里的文件必须跑 `make check-all`：`go vet` 在本轮抓到过 printf 参数用错
（`log.Printf("…:", err)` 少动词、`log.Printf(v)` 无格式串）、`string(int64)` 被当成
数字转字符串。这类错误编译通过、运行时才难看。`scope=build`
