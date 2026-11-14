#!/usr/bin/env python3
"""复盘事实底板：只算数字，不写结论。

口径：数字先算，AI 只在数字上写。复盘三问的答案（lessons.md）要建立在这里
打印的事实上，而不是凭印象。
"""
import argparse
import json
import re
from pathlib import Path


def lines_of(p):
    try:
        return len(p.read_text(encoding="utf-8").splitlines())
    except OSError:
        return 0


def evidence_errors(p):
    m = re.search(r"(\d+) ERROR, (\d+) WARN", p.read_text(encoding="utf-8"))
    return (int(m.group(1)), int(m.group(2))) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    root = Path(ap.parse_args().root).resolve()
    h = root / ".harness"
    out = []

    ev = sorted((h / "deliverables" / "evidence").glob("verify-*.txt"))
    out.append(f"evidence 份数: {len(ev)}")
    counts = [(p.name, evidence_errors(p)) for p in ev]
    counts = [c for c in counts if c[1]]
    if counts:
        last = counts[-1]
        out.append(f"最近 evidence: {last[0]}  ERROR={last[1][0]} WARN={last[1][1]}")
        if len(counts) > 1:
            prev = counts[-2]
            out.append(f"ERROR 环比: {prev[1][0]} -> {last[1][0]} ({last[1][0] - prev[1][0]:+d})")

    base = h / "baseline.txt"
    n = 0
    if base.exists():
        n = sum(1 for ln in base.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#"))
    out.append(f"baseline 条目数: {n}")

    try:
        tasks = json.loads((h / "tasks" / "board.json").read_text(encoding="utf-8"))["tasks"]
    except (OSError, ValueError, KeyError):
        tasks = []
    by = {}
    for t in tasks:
        by[t.get("status", "?")] = by.get(t.get("status", "?"), 0) + 1
    out.append("看板: " + " ".join(f"{k}={v}" for k, v in sorted(by.items())) + f" total={len(tasks)}")

    lessons = h / "memory" / "lessons.md"
    k = len(re.findall(r"^## L-\d+", lessons.read_text(encoding="utf-8"), re.M)) if lessons.exists() else 0
    out.append(f"lessons 条目数: {k}")

    out.append("手册行数:")
    for p in sorted(root.rglob("AGENTS.md")):
        rel = p.relative_to(root)
        if any(x in rel.parts for x in (".worktrees", "node_modules", ".git")):
            continue
        out.append(f"  {rel}: {lines_of(p)}")
    print("\n".join(out))


if __name__ == "__main__":
    main()
