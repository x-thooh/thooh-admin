"""commit：提交信息的启发式判据。

MSG001–004 直接喂字符串给 `check_message`（判据是纯函数，不需要造仓库）；
MSG005 要「拿不到消息」，所以造一个不是 git 仓库的临时根。

正对照那条用的是本仓库真用过的合规写法——拿自己已经写过的消息当夹具，
判据哪天变严了会立刻打在熟悉的句子上，比编一句假话更容易看出问题。
"""

from scopes import commit as sc_commit
from support import codes_of, ctx_for, new_root

NAME = "commit"

OK_MESSAGE = "新增 cmd 域：入口命令表、Makefile target 与脚本文件三方对账\n\n" \
             "硬规则原来靠人判，挂上断言后当场报出 5 条未登记的 target。\n"


def fires(message, limit=50):
    hit = []
    sc_commit.check_message(message, lambda code, line, msg: hit.append(code), limit)
    return hit


def cases():
    out = []
    out.append(("MSG001", "标题只有动词没有宾语", "MSG001" in fires("update\n")))
    out.append(("MSG001b", "整条消息是空的", "MSG001" in fires("\n\n")))
    out.append(("MSG002", f"标题 {len('x' * 60)} 字，超过额度", "MSG002" in fires("修复" + "x" * 55 + "\n\n正文")))
    out.append(("MSG003", "标题里三个由「，」连接的子句",
                "MSG003" in fires("改这里，再改那里，最后补个测试\n\n正文")))
    out.append(("MSG004", "正文出现「顺带」", "MSG004" in fires("修好登录\n\n顺带把首页配色也调了")))
    out.append(("MSG002b", "正对照：同一条消息把额度调大后不该再报 MSG002",
                "MSG002" in fires("修复" + "x" * 55 + "\n\n正文", 200)))

    root = new_root({})
    f = []
    sc_commit.run(ctx_for(root), f)
    out.append(("MSG005", "拿不到 HEAD 的提交信息（不是 git 仓库）", "MSG005" in codes_of(f)))

    out.append(("MSG00n", "正对照：合规消息不报任何东西", bool(fires(OK_MESSAGE))))
    return out
