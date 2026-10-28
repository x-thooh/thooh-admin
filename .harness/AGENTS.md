<!-- agents: scope=.harness parent= -->
# .harness/ — agent 工程层

| 子目录 | 层 | 能不能手改 |
| --- | --- | --- |
| `scripts/verify.py`、`registry.py` | 执行 | 能（改域 = 加文件 + 在 registry 加一行） |
| `scripts/scopes/<域>.py` | 执行 | 能，每个 code 必须在 `specs/standards.md` 有行 |
| `scripts/tests/reverse.py` | 执行 | 能，新域必须带至少一个违规样本 |
| `config.json` | 执行 | 能（阈值与模块根的唯一来源） |
| `git-hooks/` | 执行 | 能，装法是 `make init` 设 `core.hooksPath` |
| `specs/standards.md` | 知识 | 能（规则↔断言对照表，含「无断言」列） |
| `codebase-guide/index.json` | 知识 | **禁手改**：派生数据，`make fix` / `make guide` 重建（ENT007） |
| `baseline.txt`、`accepted.json` | 状态 | 能，但只减不增（BASE013），豁免要理由 + 负责人 + 复查日期 |
| `deliverables/`、`tasks/`、`memory/` | 状态 | 能；`memory/` 只 `remember`，作废不删 |

三条自家规矩：

1. 加断言的同时加反向样本；两者不同批提交等于没提交。`scope=baseline`（账本只减不增
   会间接逼你处理新报出来的欠账）其余靠 `make selftest`。无断言（人判）：脚本没法替你
   证明「这条断言真的会报」。
2. `--fix` 只重建派生数据，不写理由、不选版本、不改业务代码。`scope=entry`
3. 判不了就登记 `not_applicable`，输出里必须与「通过」分开。扫到 0 个样本要报错。
   `scope=modules`（MOD005 是本仓第一条 0 样本守卫，新域照抄它）

命令一律从仓库根的 `Makefile` 走，这里没有第二条入口。
