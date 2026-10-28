# 门记录 20261028T165106Z — `make fmt` 与门禁共用同一份源码清单（scope=build/cmd）

批次：只改「哪些 `.go` 算本仓库源码」这一处落点——新增 `scripts/go_files.py`（唯一实现 + CLI），
`scopes/build.py` 删掉自己的 `go_files()` 改 import 它，Makefile 的 `fmt` 不再用 `find` 抄一份
排除清单，语料加 `BLD005c`，文档同步 standards/decisions/lessons/board。没动业务代码，没动 `.go` 文件。

命令：`make check-all` + `make fmt` + `make selftest`
退出码：0 / 0 / 0

改前基准（上一条提交 `2fbf78b`，同一棵树、同一份磁盘）：

```text
$ make check-all
0 ERROR, 5 WARN  (scopes: entry, commit, cmd, workflow, hooks, budget, modules, secret, stale, state, worktree, build, baseline; mode: normal)

$ make fmt
.go/pkg/mod/gorm.io/gorm@v1.24.0/schema/relationship.go
.go/pkg/mod/gorm.io/gorm@v1.24.0/statement.go
make: *** [fmt] Error 2
```

这两行放一起才是本批的全部问题：**门禁全绿，而 `make help` 里的一条命令是坏的**。
`find . -name '*.go' -not -path './.go/*'` 排掉了缓存的子孙，却把 `.go` 这个目录本身交给了
`gofmt -l`，gofmt 收到目录会递归进去（现测：清单 181 项，其中 1 项是目录）。
T-12 那份门记录写「清单只此一处」，当时只收了 Python 侧——这是它自己欠的一句，见 lessons L-8。

改后：`make check-all` = `0 ERROR, 5 WARN`（计数未变，成员也未变：SEC001 基线内 1 条、
SEC002 3 条、STL004 1 条），`make fmt` = `exit 0` 且无输出，`make selftest` = 违规样本 100 条、
正对照 19 条、判不了 0 条、缺口 0 条。证据文件 `.harness/deliverables/evidence/verify-20261028T165150Z.txt`。

新欠逐条：**没有新增 ERROR，也没有新增 WARN。** 唯一数字变化是 selftest 的违规样本
99 → 100（新增 `BLD005c`），那是语料不是欠账。

上升归因：无上升（ERROR 0 → 0，WARN 5 → 5）。

判不了：`stale:swagger 时效`（与基准同）——这不是通过。本批另登记两类：

- `go_files.py` 清单为空时 `exit 2` 并打印「这不是通过」，`check_gofmt` 侧对应 BLD004 +
  `build:gofmt` 登记；现树 180 个文件，这一支只在夹具里造（空夹具实测 exit=2）。
- **人判、无断言**的一条：`make help` 里每条命令是否跑得通。`cmd` 域只判 target ↔ 命令表
  一一对应，不执行命令——所以 `make fmt` 坏了它看不见。写进 standards.md 的「判不了」表，
  不拿弱断言假装守住。

自查（反向验证，当场真做过）：

- `BLD005c` 有力气：把 `is_file()` 那一筛摘掉做成坏版本，同一夹具（`nested.go/bad.go` 未格式化）
  报出 `[(BLD005, nested.go/bad.go), (BLD005, nested.go/bad.go)]`——目录进清单后 gofmt 递归，
  同一个文件报两遍，样本预期 `[path…] == ["nested.go/bad.go"]` 转红。
- `gofmt -l` 的参数在改后是明确文件清单，实测 `exit 0`；改前 `find` 版实测 `Error 2`。
- 清单只此一处：`go_files.py` 引 `common.in_local_artifact`，Makefile 里不再出现
  `-not -path`；shell 侧那份抄本删除后，`grep -rn "not -path" Makefile` = 0 命中。
- 额度：`scopes/common.py` 416/420，所以实现放脚本侧而不是塞进 common（BUDGET001 会当场报）。
  `go_files.py` 46 行、`scopes/build.py` 减到 168 行，都在 scripts/scopes 档额度内。

commit：基准 `2fbf78b`（本批提交即它的下一条）。
