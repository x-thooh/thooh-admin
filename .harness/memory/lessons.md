# 踩坑记忆

一条一个坑，三段缺一不可：现象 / 根因 / 落成的断言。**没有第三条的条目不算记忆**——
那只是抱怨。落成的断言要么指向 `scripts/scopes/` 里的一个 code，要么在 `AGENTS.md`
的「人判项」里写明强度来源。

## L-1 工作树被会话外的进程整体重写

- 现象：会话进行中，主树 456 个受版本控制文件里有 337 个变成 0 字节、`start.sh` 与 `vben-go.sql`
  整个消失；`git status` 从 clean 变成 `1 A / 2 D / 341 M`。所有文件 mtime 挤在同一秒。
- 根因：`mise.toml` 把 `GOPATH` 指到 `<repo>/.go`（274 MB / 11306 文件），同机还有 GoLand
  （fsnotifier 挂在本项目）与并行 agent 应用；`.git` 对象库多出 10743 个悬空 blob，全是 module 缓存内容。
  即「工具把依赖缓存当成仓库内容索引了一遍」之后又重写了工作树。
- 断言：**无断言、人判**。判据是本仓库开工前重新跑一次现场核对：
  `git ls-files | while read -r f; do [ -s "$f" ] || echo x; done | wc -l` 必须为 0。
  「所有文件 mtime 同一秒」是基准作废的信号；此时不许 `git restore` 覆盖现场。

## L-2 规则写了但工具从没跑过

- 现象：仓库有 20 个模块、`go.mod` 声明 1.18 起就存在，但 `_test.go` 为 0、无 Makefile、无 CI、
  无 lint 配置；升级到 1.25 后 `go vet` 一次报出 6 条真缺陷（丢信号、日志丢失参数、3 处
  `string(int64)` 产出乱码 rune）。
- 根因：「能编译」被当成了「没问题」。没有共有门径，就没有人跑 vet，也没有任何断言会发现没人跑。
- 断言：`BLD003`（go_build / go_vet 必须 pass）、`BLD005`（gofmt 违规即 ERROR），
  证据由 `make evidence` 产出并带 commit，过期由 `BLD002` 拦下。

## L-3 反向测试全绿，但脚本作为命令是坏的

- 现象：`make selftest` 39 条样本符合预期，同一次 `make guide` 却把索引写进了
  `--root/.harness/codebase-guide/index.json`（凭空多出一个叫 `--root` 的目录），
  `make evidence` 的 `# 工作区：` 行报 `[: too many arguments`，`make fix` 报
  `fatal: Unimplemented pathspec magic '_'`。
- 根因：反向测试直接调 scope 的函数，绕过了 CLI 层；Makefile 用 `--root X` 调 `gen_guide.py`，
  而它只收位置参数；`git status --porcelain -- :!x/` 的短形式排除路径在 Apple Git 2.50.1 上
  不被接受；证据里的工作区判定把多行 `status` 塞进了 `[ -z ]`。断言测的是判断逻辑，接线没人管。
- 断言：无机器断言，靠两条约定——命令层改动后必须**逐个 target 空跑一次**（本轮已修
  `gen_guide.py` 接受 `--root`、`git_clean` 改用 `:(exclude)`、工作区判定改成单条变量）；
  `make check` 里 0 ERROR 不等于 `make check-all`/`make evidence`/`make fix` 可用。
  第二期把「Makefile 里出现的每个脚本调用都能跑通」做成 `scripts` 域的断言。


