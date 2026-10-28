<!-- agents: scope=common parent= -->
# common/ — 配置与跨层小工具

- `common/config/app_config.go`：`config.yaml` 的结构体镜像，加一个 yaml 键必须加一个
  `yaml:"..."` 字段，两边一起改。无断言（人判）：读不进去的键会静默取零值，
  只有跑起来才看得出——`config` 的键与 yaml 一一对应的断言列在第二期。
- `common/r/`：统一响应（`r.go`）、分页与树。handler 返回走这里，不要在模块里手搓
  `c.JSON` 的错误结构。无断言（人判）：写法统一属于约定，机器判不了语义。
- `common/json/timex`、`boolx`：时间/布尔的宽松反序列化，前端传 "true"/空串都靠它们兜。
- `common/utils/id.go`：编号生成器。

密钥相关：`common/config` 里的 `jwt.secret` 从 `config.yaml` 读，值**不许**出现在代码、
注释、提交信息或 `.harness/deliverables/` 里。`scope=secret`
