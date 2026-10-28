# 流程：加一个业务模块

**适用**：在 `modules/` 下新增一个业务模块（一张表 + 一组接口），或给已有模块加子路由。
**不适用**：只改框架层（`app/`）、只改配置、只改前端产物——那些各有自己的入口。

本流程的存在理由：这个仓库里「漏登记路由」是**静默失败**——编译照过、`make check` 里的
modules 域会报，但没人跑它就一路带到线上。所以每一步后面都挂一条命令。

## 什么时候跑

- 使用者说「加一个 XX 模块 / 把 XX 表做成接口」时。
- 从 `make check` 报出 MOD001（目录在但没注册）或 MOD002（注册了但目录不在）时——那是本流程
  第 2、3 步没走完的现场。
- 不跑的情形：只是改现有模块的内部逻辑，不动目录与路由表。

## 怎么跑

前置：`git status` 干净，且当前在任务自己的 worktree 里（不在主干上直接改）。
下面的命令全部从仓库根的 `Makefile` 走——本文件不是第二条入口。

1. **定形状**。一个模块目录 = `api.go` + `model.go` + `router.go` + `func Init(e *gin.Engine)`。
   先照着 `modules/demo/` 抄，别自创文件名——`MOD004` 判的就是这四件套齐不齐。
2. **建目录并写代码**。模型的结构体 tag 决定 `docs/` 里的 swagger；注解写完再第 5 步统一生成。
3. **登记路由**（本仓库唯一的第二条修改点）：`app/admin/router.go` 里加 import，并加
   `<alias>.Init(e)`。**只 import 不挂**会被 `MOD003` 报出来；注释掉的挂载不算。
4. **跑快域**：`make check`。modules 段必须 0 条，否则第 2、3 步有一步没走完。
5. **重生生成物**：`swag init`（产出 `docs/`）与 `make guide`（产出 `codebase-guide/`）。
   生成物禁手改；`STL001` 会比对 `docs/swagger.json` 的 `paths` 与源码里的 `@Router`。
6. **跑慢域**：`make check-all`（`go build` + `go vet` + gofmt + 证据时效）。
7. **提交**：一次提交一件事，标题是动宾短语。`commit-msg` 钩子会判 `MSG001`–`MSG004`。

## 怎么验证装好了

跑完做一次反向验证，确认第 3 步的登记不是嘴上说说（三步都要真跑，别只看前两行）：

1. 删掉 `app/admin/router.go` 里的 `<alias>.Init(e)` 一行 → `make check` **必须**报 MOD003
   （只 import 不挂）。
2. 连 import 一起删 → `make check` **必须**报 MOD001（目录在、注册表里没有）。
3. 把两行改回去再跑一次 → modules 段**必须**回到 0 条。

判不了的情形：`make check` 一个模块都没扫到时报 MOD005（0 样本守卫）——那是「没检查」，
不是「检查通过」。

## 相关断言

`scope=modules`（MOD001–MOD005）、`scope=stale`（STL001 swagger 与 `@Router` 一致）、
`scope=cmd`（这里用到的命令必须在 `Makefile` 与根 `AGENTS.md` 的命令表里对得上）。
