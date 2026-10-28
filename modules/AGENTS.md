<!-- agents: scope=modules parent= -->
# modules/ — 业务功能模块

一个目录 = 一个可挂载的功能模块，四件事同时成立才算数：

1. 目录里有 `api.go`（gin handler）、`model.go`（gorm 模型 + `TableName()`）、
   `router.go`（`func Init(e *gin.Engine)`）。
2. `router.go` 里**只**注册路由，业务写在 `api.go`/`service.go`；`service.go` 可选。
3. `app/admin/router.go` 里 import 这个包并调用 `alias.Init(e)`——两处都要改，
   漏一处编译照过、路由静默不存在。`scope=modules`
4. 模型要进 `mysql.MysqlDb().AutoMigrate(...)`（在 `app/admin/router.go` 末尾）才算迁移；
   全量表结构变更同步 `vben-go.sql`。无断言（人判）：AutoMigrate 覆盖不到的
   索引/约束改动只有 dump 能说清。

注释与用户可见文案一律中文；`err` 不要吞，返回走 `common/r` 的统一结构。
`modules/sys/actor` 这类只有 `model.go` 的目录是共享模型包，不是模块，不判形状。

改完跑 `make check`（modules 域是快域，秒级）。
