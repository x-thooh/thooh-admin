# `specs/notes/` — 模块级决策的三种状态

**状态是位置，不是字段**：一篇笔记同时只属于一个目录——`proposed/`（还想做）、
`implemented/`（已经落地，且落地的样子写清楚了）、`rejected/`（决定不做，理由比结论重要）。
全仓级决策（`scope: *`）不进这里，进 `.harness/memory/decisions.md`；域不是一个目录树，
两处都建就是两个事实源。

规矩四条：

1. **一片一决策**。一篇笔记只回答一个问题；回答两个的那篇，第二个从来没人读。
2. **每篇必有「不显然之处」**。写得出让任何人都同意的话不用记——那是常识，不是决策。
3. **移动即状态变化**，改目录名不改正文；从 `proposed/` 移进 `implemented/` 时补一行
   `Landed:` 日期与证据（commit 或文件路径）。
4. **作废不删**：被推翻的移到 `rejected/` 并在文首写 `Supersedes:` / `Superseded-by:`，
   「当初为什么这么定」是这一层唯一的存在理由。

模板在 `.harness/stack-templates/note.md`。
