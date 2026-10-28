# 模板：决策笔记（模块级）

复制到 `.harness/specs/notes/proposed/<kebab-标题>.md`。**一片一决策**：能拆成两篇就拆。
全仓级（`scope: *`）的不放这里，进 `.harness/memory/decisions.md`。

```markdown
# 笔记：<一句话标题，是动宾短语或结论，不是「关于 XX 的思考」>

- scope: `<哪个模块或目录>`
- status: proposed | implemented | rejected      # 状态同时由所在目录表达，两处必须一致
- written_by: <session/人名> <YYYY-MM-DD>
- version: 1
- supersedes: <旧笔记路径或 —>
- 看板：`T-<id>`（这条决策落成任务时挂上看板）

## 问题
<是什么在互相矛盾：两个文件、两个约定、还是两个使用者的说法>

## 不显然之处
<只有做过才知道的那一句。写不出来就别写这篇——那是常识，不是决策>

## 提案 / 决定
<方向、代价、被否掉的方案与为什么否>

## 断言载体
<这条定了之后由哪个 code 守着；判不了就写「无断言（人判）」+ 强度来源，别拿弱断言假装守住>
```

落地时：`git mv` 到 `implemented/` 并在文首补 `Landed: YYYY-MM-DD` + 证据
（`commit:<sha>` 或 `path:<存在的文件>`）。被推翻时移到 `rejected/`，**不删**——
「当初为什么这么定」是这一层唯一的存在理由。
