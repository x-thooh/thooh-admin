<!-- agents: scope=tests parent= -->
# tests/ — 测试

本仓库现在**没有** Go 测试（目录是空的）。这里只写规则，不假装已有覆盖：

- 新增测试写 `*_test.go`，放在被测包内；跨包集成测试放本目录并带 `package tests_test`。
  无断言（人判）：测试写没写只有 `go test` 知道，而 `go test ./...` 对空包是静默通过。
- `make test` 跑 `go test ./...`；它不在门禁里（本仓库当前无测试，纳入门禁等于给绿灯）。
  一旦有第一条真测试，把它加进 `.harness/scripts/scopes/` 并在
  `.harness/specs/standards.md` 占一行。
- 手工 curl/postman 脚本不要放这里，放 `docs/` 或 issue 里。
