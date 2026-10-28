"""commit：提交信息是不是「一件事 + 动宾短语」。

两条边各有分工，别把它们混成一个：
  * **commit-msg 钩子**是真正的门——消息还没落定，改一行就完事，所以这里判的是 ERROR；
  * **本域在 verify 里判 HEAD**（已经提交的那条）。HEAD 已经写进历史，改它的代价是重写历史，
    比一条措辞欠账贵得多，所以这里只报 WARN，作用是「别忘了，下一条按规矩写」。
  把 verify 侧也做成 ERROR，会得到一个永远在报旧账、又无法在不破坏历史的前提下修掉的门禁——
  那种门禁的结局是被 `--no-verify` 绕过去。

判据都是启发式，写明白它们能判什么、判不了什么：
  MSG001  标题为空，或只有「update / fix / 修改」这类没有宾语的动词
  MSG002  标题超过 subject_max_chars：一行说不完一件事，本来就是该拆的信号
  MSG003  标题里两个及以上「，」子句：并列了两个动作（WARN，可能只是补充说明）
  MSG004  正文出现并列信号词（顺带、另外、同时、此外、顺便）
  MSG005  拿不到消息（没有 git、空仓库、文件读不动）——0 样本不等于合规
"""

import re
import subprocess
from pathlib import Path

from scopes.common import add, num, rel_to

NAME = "commit"

PLAN = "一次提交一件事：标题是动宾短语、不并列、不超长；正文出现「顺带/另外/同时」就是该拆的信号"
REFLECT = ("MSG001", "MSG002", "MSG003", "MSG004", "MSG005")

# 没有宾语的裸动词：说了「改」，没说改什么
BARE_SUBJECTS = ("update", "fix", "bug", "wip", "tmp", "修改", "优化", "调整", "提交", "更新", "杂项", "整理")
# 并列信号词：出现在正文里 = 这次提交里还夹了第二件事
BUNDLED_WORDS = ("顺带", "顺便", "另外", "此外", "同时")
SUBJECT_CLAUSES = re.compile(r"，")
WHITESPACE = re.compile(r"\s+")
DEFAULT_SUBJECT_MAX = 50


def split_message(message):
    """标题 + 正文（git 的惯例：第一个空行之前是标题）。"""
    body_start = message.find("\n\n")
    if body_start < 0:
        return message.strip(), ""
    subject = message[:body_start].strip()
    body = message[body_start + 2:].strip()
    return subject, body


def check_message(message, emit, max_chars=DEFAULT_SUBJECT_MAX):
    """把一条消息判成若干条发现。`emit(code, line, message)` 由调用方给：钩子那边落 ERROR，
    verify 这边落 WARN——判据同一套，处置不同（分工见模块开头）。"""
    subject, body = split_message(message)
    if not subject:
        emit("MSG001", 1, "提交信息是空的：没有一句话说明这次改了什么")
        return
    if subject.strip().lower() in BARE_SUBJECTS:
        emit("MSG001", 1, f"标题「{subject}」只有动词没有宾语：读不出这次动了什么，"
                                 "也不要在 revert 时靠它猜")
    if num(max_chars) and max_chars > 0 and len(WHITESPACE.sub("", subject)) > max_chars:
        emit("MSG002", 1, f"标题 {len(WHITESPACE.sub('', subject))} 字，超过 {max_chars}："
                                 "一行说不完一件事，通常就该拆成两个提交")
    clauses = len(SUBJECT_CLAUSES.findall(subject))
    if clauses >= 2:
        emit("MSG003", 1, f"标题里有 {clauses + 1} 个由「，」连接的子句：并列可能是两件事，"
                                 "人读一遍确认；说不完就拆")
    hits = [w for w in BUNDLED_WORDS if w in body]
    if hits:
        emit("MSG004", 1, f"正文出现并列信号词 {hits}：那是「顺带做了第二件事」的字面形状。"
                                 "拆成两个提交，别把无关改动混进这一轮")


def head_message(root):
    """HEAD 的完整提交信息；没有 git 或还没有提交时返回 None。"""
    proc = subprocess.run(["git", "-C", str(root), "log", "-1", "--pretty=%B"],
                          check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    return proc.stdout or None


def run(ctx, findings):
    root = Path(ctx["root"])
    message = head_message(root)
    if message is None:
        ctx.setdefault("not_applicable", []).append(f"{NAME}(拿不到 HEAD 的提交信息)")
        add(findings, "ERROR", NAME, rel_to(root, root / ".git"), 1, "MSG005",
            "读不到 HEAD 的提交信息（不是 git 仓库，或一个提交都还没有）："
            "「判不了」要报出来，不能因为扫不到就当合规")
        return
    quality = ctx.get("quality") or {}
    max_chars = quality.get("subject_max_chars", DEFAULT_SUBJECT_MAX)
    # WARN 而不是 ERROR：HEAD 已经落定，改它要重写历史——那比一条措辞欠账贵。
    # 真正的门在 .harness/git-hooks/commit-msg（同一套 check_message，判 ERROR）。
    # 这里报的是「存量措辞账」：看得见、不阻断、不计进账本（账本只登记 ERROR）。
    check_message(message, lambda code, line, msg: add(
        findings, "WARN", NAME, "HEAD", line, code,
        f"{msg}（HEAD 已提交，改它要重写历史，所以只报不拦；下次由 commit-msg 钩子拦在落笔时）"),
        max_chars)
