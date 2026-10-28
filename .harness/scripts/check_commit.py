#!/usr/bin/env python3
"""提交信息的两个调用面共用一份判据。

判据在 `scopes/commit.py`（`check_message`），本文件只做「取一条消息、跑判据、给退出码」：

  * `.harness/git-hooks/commit-msg` 传 `--message-file .git/COMMIT_EDITMSG`，
    这时候违规是 ERROR——消息还没落定，改一行就完事；
  * `make commit-msg` 不带参数，判 HEAD，只报不拦（HEAD 已提交，改它要重写历史）。

两个面共用一份判据，是为了不让「提交时的规矩」和「复盘时的规矩」漂成两套。

退出码：0 = 没问题；1 = 有违规；2 = 拿不到消息（判不了，不冒充通过）。
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from scopes import commit as sc_commit  # noqa: E402

EXEMPT_PREFIXES = ("merge ", "revert ", "fixup! ", "squash! ")


def limit_of(root):
    try:
        cfg = json.loads((Path(root) / ".harness/config.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return sc_commit.DEFAULT_SUBJECT_MAX
    return cfg.get("subject_max_chars", sc_commit.DEFAULT_SUBJECT_MAX)


def main(argv=None):
    ap = argparse.ArgumentParser(description="判一条提交信息：一件事、动宾短语、不并列")
    ap.add_argument("--root", default=None, help="仓库根；不给就用本文件所在仓库")
    ap.add_argument("--message-file", default=None,
                    help="git 交给 commit-msg 钩子的那个文件；不给则判 HEAD")
    args = ap.parse_args(argv)

    root = Path(args.root) if args.root else HERE.parents[1]
    if args.message_file:
        try:
            message = Path(args.message_file).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"check_commit：读不了 {args.message_file}（{exc}）——判不了就不放行", file=sys.stderr)
            return 2
        origin = args.message_file
    else:
        message = sc_commit.head_message(root)
        origin = "HEAD"
        if message is None:
            print("check_commit：拿不到 HEAD 的提交信息（不是 git 仓库，或还没有提交）：判不了",
                  file=sys.stderr)
            return 2

    subject, _ = sc_commit.split_message(message)
    if subject.strip().lower().startswith(EXEMPT_PREFIXES):
        # git 自己写的标题（合并、回滚、fixup）不按「一件事」判：它的格式不由我们决定
        print(f"check_commit：「{subject[:40]}」由 git 生成，不适用格式判据，放行")
        return 0

    found = []
    sc_commit.check_message(message, lambda code, line, msg: found.append((code, msg)),
                            limit_of(root))
    if not found:
        return 0
    print(f"check_commit：{origin} 的提交信息有问题：", file=sys.stderr)
    for code, msg in found:
        print(f"  {code}  {msg}", file=sys.stderr)
    print("  改标题，或把夹在里面的第二件事拆成单独一轮。", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
