"""entry：入口文件自己站不站得住。

夹具 ROOT_OK 是「合规入口」的最小形态：目录地图与磁盘双向对得上、每条硬规则都指向真 scope。
八个 code 各造一条违规，最后拿它做正对照——只有反例没有正例，判不出这条断言是不是永远在报。
"""

from scopes import entry as sc_entry
from support import codes_of, ctx_for, new_root

NAME = "entry"

ROOT_OK = """<!-- agents: scope=. parent= -->
# x

## 目录地图

```text
app       ok
.harness  ok
```

## 硬规则

1. 规则一。`scope=modules`
"""


def guide_survives_clean_checkout():
    """在「带 .go/ 模块缓存的树」上生成索引，再拿到「干净检出」上判新鲜度。

    2026-10-28 实测到的故障：`make guide` 把 `.go`、`.go/pkg` 两条写进派生索引，换一棵没有
    缓存的检出（临时树 `e38496c`）ENT007 当场判「索引过期」——派生数据在两台机器上长得不一样，
    而这条域的存在理由就是「只有生成与校验共用一份实现才算派生」。
    """
    with_cache = new_root({"AGENTS.md": ROOT_OK, "app/main.go": "package main\n",
                           ".go/pkg/mod/x.go": "package x\n"})
    sc_entry._fix_guide(with_cache)
    index = (with_cache / ".harness/codebase-guide/index.json").read_text(encoding="utf-8")
    clean = new_root({"AGENTS.md": ROOT_OK, "app/main.go": "package main\n"})
    target = clean / ".harness/codebase-guide/index.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(index, encoding="utf-8")
    findings = []
    sc_entry.run(ctx_for(clean), findings)
    return bool(codes_of(findings))


def cases():
    out = []
    root = new_root({"AGENTS.md": "没有 header\n"})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT001", "根入口没有 header", "ENT001" in codes_of(f)))
    root = new_root({
        "AGENTS.md": ROOT_OK,
        "app/AGENTS.md": "<!-- agents: scope=app parent=nope -->\n# x\n",
        "app/main.go": "package main\n",
    })
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT002", "子入口 parent 指向不存在的目录", "ENT002" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK + "\n" * 200})
    f = []
    sc_entry.run(ctx_for(root, {"agents_max_lines": 20}), f)
    out.append(("ENT003", "入口超行数上限", "ENT003" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK, "extra/x.go": "package x\n"})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT004", "磁盘有目录但地图没有", "ENT004" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK.replace("`scope=modules`", "没有载体")})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT005", "硬规则既没 scope 也没写「无断言」", "ENT005" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK.replace("scope=modules", "scope=ghost")})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT006", "标注了未注册的 scope", "ENT006" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT007", "派生索引不存在", "ENT007" in codes_of(f)))
    root = new_root({"README.md": "x\n"})
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT008", "一个 AGENTS.md 都没扫到", "ENT008" in codes_of(f)))
    root = new_root({"AGENTS.md": ROOT_OK, "app/main.go": "package main\n"})
    sc_entry._fix_guide(root)
    f = []
    sc_entry.run(ctx_for(root), f)
    out.append(("ENT00n", "正对照：合规入口不该报任何 entry 发现", bool(codes_of(f))))
    out.append(("ENT007b", "正对照：带 .go/ 缓存的树上生成的索引，干净检出也认它新鲜",
                guide_survives_clean_checkout()))
    return out
