# 门记录 20261029T012600Z — 配置只写形状：凭据从入库文件里拿出来（T-19a）

批次：只做一类事——让 `config.yaml` 不再携带任何值，值由环境变量注入；顺带把「配置加载失败」
这句话变成人看得懂的话。不含 compose、不含 mysql 连接失败（那是 T-19b/T-19c）。

## 为什么现在必须做这件事

私有化交付的前提是「客户环境 ≠ 开发环境」。盘点（2026-10-29）出的事实是：全仓没有环境变量入口
（`common/config/app_config.go` 只认 `-f` 一个 yaml），所以任何一份能跑的 `config.yaml` 都必须
带着真凭据；带着真凭据的文件要么入库（SEC001/SEC002 那三条账就是这么来的），要么像 `.deploy/`
那样被 `.*` 排除在仓库外——后者意味着**干净 clone 起不来**。两个方向都通向这一条改动。

## 改了什么

- `expandEnv()`：逐行展开 `${NAME}` 与 `${NAME:-默认}`。三个坑都各钉了一条测试：
  ① `${NAME:-}` 是「明写允许空」（没开的从库密码），和「没给默认」不是一回事，判据是 `:-` 在不在，
  不是捕获串空不空；② 注释里的示例不算引用（第一版实测把 `${NAME}` 当变量，报出 missing = VAR、NAME，
  等于说明书写得越全越起不来）；③ 裸 `$` 一律不碰（`os.ExpandEnv` 那种语义会吞掉密码里的 `$`）。
- 缺必填变量时**一次报全**：`启动失败：这些环境变量没给值 → THOOH_DB_PW, THOOH_JWT_SECRET`。
- 四个失败点从 `panic(R.ReturnFailMsg(…))` 改成 `log.Fatalf`。理由不是风格：实测
  `panic(结构体值)` 在 Go 1.25 运行时的输出是 `panic: (R.Result) 0x427d49071170`，
  **消息文本一个字都不出现在 stderr**——「配置文件不存在」这种最常见的部署错误一直是哑的。
- `config.yaml`：`jwt.secret`、两处 db 密码、xxl-job 三个口令字段换成 `${THOOH_*}`；host/port/
  dbname/端口这类环境坐标保留 `:-默认`，所以本地 `go run` 与容器各用各的值、共用同一份形状。
  `log.filePath` 原来写死 `D:\\ruoyi\\log`，改成 `${THOOH_LOG_PATH:-./log}`——Linux 上那是死路径。
- `common/config/app_config_test.go`：本仓第一批 Go 单元测试（7 个形状 + 1 个裸 `$` 守卫）。

## 实测

```text
$ go build -o /tmp/t19bin . && /tmp/t19bin
2026-10-29 09:16:36 启动失败：这些环境变量没给值 → THOOH_DB_PW, THOOH_JWT_SECRET。…     exit 1
$ THOOH_DB_PW=… THOOH_JWT_SECRET=… THOOH_DB_PORT=3399 /tmp/t19bin
[error] failed to initialize database, got error dial tcp 127.0.0.1:3399: connect: connection refused
主数据库连接失败: dial tcp 127.0.0.1:3399: connect: connection refused
panic: runtime error: invalid memory address or nil pointer dereference
	pkg/mysql/mysql.go:115                                                        ← T-19b 的现场
$ go test ./common/config/            ok  0.457s                                 exit 0
$ make check                          0 ERROR, 2 WARN                             exit 0
$ make check-all                      含慢域（go build/vet/gofmt）同过             exit 0
```

反向验证（改坏一处，看测试是否立刻红）：把 `strings.Contains(ref, ":-")` 换成 `groups[2] != ""`，
`go test` 立刻三条 FAIL（`明写空默认是允许空` / `缺必填要点名` 两处），改回即绿。

## 账本口径变化（BASE014 当场报出来的）

`config.yaml` 不再携带高熵值之后，SEC001 那条发现**不再存在**，于是它盖的那条豁免成了空账：

```text
$ make check（改前，任务树）  1 ERROR(WKT002), 1 WARN + config.yaml 的 SEC001（基线内 1 条）/SEC002 ×3
$ make check（改后）          0 ERROR, 2 WARN：STL004 + BASE014「账本比现状多 1 条」
```

处理：删掉 `accepted.json` 里那条 `config.yaml / SEC001:高熵密钥入库 jwt.secret`（原 `review_by`
2026-11-28）。刷新前后条数：账本（baseline 0 条 + accepted 1 条）= 1 → 0，现状发现数 0，
当前 ERROR 0 条——满足 BASE014 要求的「先确认当前 ERROR 全是同一批老账」（没有 ERROR，条件空成立）。

**这不等于问题解决**：那个值仍然在 git 历史里（`156f892` 及更早的 `config.yaml`），仍然被客户现网
与 `.deploy/config.yaml` 使用。断言只看工作树文件，看不到历史值，所以这条从「盖章豁免」改成
「看板上的账」——T-6 的 detail 已改写，标准表的「判不了」新增一行说明为什么机器管不到它。
写在这里是因为它的形状危险：**发现消失 ≠ 风险消失**，拿前者当后者就是自我消账。

## 边界

- 端口、host、dbname 留默认值是有意的：它们不是凭据，且「同一份文件在本地和容器里都能跑」靠的就是默认。
- 本次没动 `.deploy/`（那台机器的本地状态，入库等于把真凭据写进仓库）；也没动 `mise.toml` 的
  `GOSUMDB = "off"`（T-4，安全决策归人）。
- 依赖连不上时的 nil panic 只是被复现、被记录，没在这一批修（T-19b）。
