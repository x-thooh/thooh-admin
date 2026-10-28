"""build: 编译、静态检查与「结论有没有留痕」。

这是慢域（config.json 的 `slow_scopes`），默认 `make check` 跳过，`make check-all` 才跑。
跳过时调度器会明说跳了哪几个域——**跳过不等于通过**。

  BLD001  一条构建证据都没有（`.harness/deliverables/evidence/` 为空）
  BLD002  最近一次证据之后，.go / go.mod / go.sum 又变了——那份结论已经过期
  BLD003  `go build` 或 `go vet` 失败
  BLD004  判不了：Go 工具链/git 不可用，或排除本地产物目录后没有 .go 可扫——报 WARN 并登记
          not_applicable，不冒充绿（断言坑 #11 的另一半）
  BLD005  `gofmt -l` 有输出——本仓库提交前必须已过 gofmt
  BLD006  go.mod 的 `go` 指令低于 config.json 的 `go_version_min`

BLD002 为什么单独存在：BLD003 每次现跑，看起来「不需要留痕」。但一次现跑的结果只活在
那条命令的输出里——换会话、换机器就没了（本仓库 2026-10-28 的教训：规则写了、
`go vet` 从没跑过，6 处 printf 缺陷静默存在）。有账才能证明「什么时候是绿的」。
"""

import re
import subprocess
from pathlib import Path

import go_files as gofiles
from .common import add, quality_get, rel_to

NAME = "build"
PLAN = "慢域：go.mod 的工具链下限、`go build` / `go vet` 是否真的跑过并留下带 commit 的证据、" \
    "证据是否过期、gofmt 是否干净"
REFLECT = ("BLD001", "BLD002", "BLD003", "BLD004", "BLD005", "BLD006")
GO_TOUCHED = ("*.go", "go.mod", "go.sum")
EVIDENCE_GLOB = "verify-*.txt"
EVIDENCE_COMMIT_RE = re.compile(r"^#\s*commit:\s*([0-9a-f]{7,40})", re.M)
GO_DIRECTIVE_RE = re.compile(r"^go\s+(\d+)\.(\d+)(?:\.\d+)?\s*$", re.M)


def sh(argv, cwd):
    try:
        p = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=900)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, str(exc)
    return p, (p.stdout or "") + (p.stderr or "")


def head(text_, n=6):
    lines = [ln for ln in text_.splitlines() if ln.strip()]
    return " | ".join(lines[:n]) if lines else "(无输出)"


def newest_evidence(root):
    d = Path(root) / ".harness" / "deliverables" / "evidence"
    files = sorted(d.glob(EVIDENCE_GLOB)) if d.is_dir() else []
    if not files:
        return None, None
    latest = files[-1]
    try:
        m = EVIDENCE_COMMIT_RE.search(latest.read_text(encoding="utf-8"))
    except OSError:
        m = None
    return latest, (m.group(1) if m else None)


def check_gomod(root, quality, findings):
    minimum = str(quality_get(quality, "go_version_min", "") or "").strip()
    gm = Path(root) / "go.mod"
    if not gm.is_file():
        add(findings, "ERROR", NAME, "go.mod", 1, "BLD006", "go.mod 不存在")
        return
    try:
        text = gm.read_text(encoding="utf-8")
    except OSError as exc:
        add(findings, "ERROR", NAME, "go.mod", 1, "BLD006", f"读不了：{exc}")
        return
    m = GO_DIRECTIVE_RE.search(text)
    if not m:
        add(findings, "ERROR", NAME, "go.mod", 1, "BLD006",
            "go.mod 里没有 `go 1.x` 指令——工具链版本无从判定")
        return
    if not minimum:
        return
    want = [int(x) for x in minimum.split(".")]
    have = [int(m.group(1)), int(m.group(2))]
    if have < want[: len(have)]:
        add(findings, "ERROR", NAME, "go.mod", 1, "BLD006",
            f"go.mod 声明 go {m.group(1)}.{m.group(2)}，低于要求的 {minimum}")


def check_evidence(root, findings, na):
    latest, commit = newest_evidence(root)
    rel = rel_to(root, latest) if latest else ".harness/deliverables/evidence/"
    if latest is None:
        add(findings, "WARN", NAME, rel, 1, "BLD001",
            "没有构建证据：跑 make evidence 存一次全量校验的完整输出")
        return
    p, out = sh(["git", "rev-parse", "HEAD"], root)
    if p is None or p.returncode != 0:
        add(findings, "WARN", NAME, rel, 1, "BLD004", f"git 不可用，判不了证据新旧：{head(out)}")
        na.append("build:证据时效")
        return
    head_sha = out.strip()
    if commit is None:
        add(findings, "WARN", NAME, rel, 1, "BLD002",
            "证据里没有 `# commit:` 行，无法与 HEAD 对照——用 make evidence 重新生成")
        return
    if commit == head_sha:
        return
    # 只比已提交的历史，不查工作区：证据本身就是提交前拍的，把工作区改动算成
    # 「证据过期」会形成死锁（必须先提交才能刷新，必须先刷新才能提交）。
    p2, out2 = sh(["git", "diff", "--name-only", f"{commit}..HEAD", "--", *GO_TOUCHED], root)
    if p2 is None or p2.returncode != 0:
        add(findings, "WARN", NAME, rel, 1, "BLD004",
            f"证据记录的 commit {commit[:8]} 在当前历史里找不到：{head(out2)}")
        na.append("build:证据时效")
        return
    changed = [ln for ln in out2.splitlines() if ln.strip()]
    if changed:
        add(findings, "WARN", NAME, rel, 1, "BLD002",
            f"证据（{latest.name}，commit {commit[:8]}）之后 Go 源码又改了 "
            f"{len(changed)} 处（如 {changed[0]}）：结论过期，重跑 make evidence")


def check_gofmt(root, findings, na):
    # 「哪些 .go 算本仓库的源码」只此一处（scripts/go_files.py）；Makefile 的 fmt 走同一个脚本
    files = gofiles.go_files(root)
    if not files:
        add(findings, "WARN", NAME, ".", 1, "BLD004",
            "排除本地产物目录后没有 .go 可判——这一条判不了，不是通过")
        na.append("build:gofmt")
        return
    p, out = sh(["gofmt", "-l", *files], root)
    if p is None:
        add(findings, "WARN", NAME, ".", 1, "BLD004", f"gofmt 不可用：{out}")
        return
    if p.returncode != 0:
        add(findings, "WARN", NAME, ".", 1, "BLD004", f"gofmt 退出码 {p.returncode}：{head(out)}")
        return
    for rel in (ln.strip() for ln in out.splitlines() if ln.strip()):
        add(findings, "ERROR", NAME, rel, 1, "BLD005", "未过 gofmt：跑 gofmt -w 再提交")


def check_compile(root, quality, findings, na):
    src = Path(root) / str(quality_get(quality, "go_src", ".") or ".")
    p, out = sh(["go", "version"], src)
    if p is None or p.returncode != 0:
        add(findings, "WARN", NAME, "go.mod", 1, "BLD004",
            f"Go 工具链不可用，编译与 vet 判不了：{head(out) or out}")
        na.append("build")
        return
    for argv, code in ((["go", "build", "./..."], "BLD003"), (["go", "vet", "./..."], "BLD003")):
        p2, out2 = sh(argv, src)
        if p2 is None:
            add(findings, "WARN", NAME, "go.mod", 1, "BLD004", f"{argv[1]} 跑不了：{out2}")
            na.append("build")
            continue
        if p2.returncode != 0:
            add(findings, "ERROR", NAME, "go.mod", 1, code,
                f"{' '.join(argv)} 失败（exit {p2.returncode}）：{head(out2)}")


def run(ctx, findings):
    root = Path(ctx["root"])
    quality = ctx.get("quality") or {}
    na = ctx.setdefault("not_applicable", [])
    check_gomod(root, quality, findings)
    check_gofmt(root, findings, na)
    check_evidence(root, findings, na)
    check_compile(root, quality, findings, na)
