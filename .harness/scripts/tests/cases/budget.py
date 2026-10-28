"""budget：工具层按角色的行数额度。

这个域的样本有一条自我指涉：本目录（`tests/`）就是它管的语料档。当初 `reverse.py` 长到 620 行
被 BUDGET001 拦下，治法是拆文件（就是你现在看到的这个目录），不是调大额度——调额度等于把新欠盖章。
"""

from scopes import budget as sc_budget
from support import codes_of, ctx_for, new_root

NAME = "budget"


def cases():
    out = []
    root = new_root({".harness/scripts/scopes/big.py": "".join(f"print({i})\n" for i in range(25))})
    f = []
    sc_budget.run(ctx_for(root, {"budget": {"scopes": 10}}), f)
    out.append(("BUDGET001", "域文件超过该档额度", "BUDGET001" in codes_of(f)))

    root = new_root({".harness/scripts/x.py": "print(1)\n"})
    f = []
    sc_budget.run(ctx_for(root, {"budget": {"ghost": 10, "corpus": 0}}), f)
    out.append(("BUDGET002", "额度表里有不认识的档位，或有非正数", "BUDGET002" in codes_of(f)))

    root = new_root({})
    f = []
    sc_budget.run(ctx_for(root), f)
    out.append(("BUDGET002b", "一个脚本都没扫到（0 样本 ≠ 全绿）", "BUDGET002" in codes_of(f)))

    root = new_root({".harness/scripts/scopes/ok.py": "print(1)\n"})
    f = []
    sc_budget.run(ctx_for(root), f)
    out.append(("BUDGET00n", "正对照：额度内的文件不报", bool(codes_of(f))))
    return out
