"""注册表：本仓库有哪些 scope，按什么顺序跑。

单独一个文件，是为了让 `verify.py` 只做调度。清单与调度分家之后，
「加一个域」= 加一个文件 + 在这里加一行，不需要动调度逻辑。

顺序 = 跑的顺序（输出还会按 severity/scope/line/code 再排序）。
`baseline` 必须最后：它读其它域已经报出来的 findings。
"""

from scopes import baseline, budget, build, cmd, commit, entry, hooks, modules, secret, stale, state, workflow

SCOPES = (
    entry,
    commit,
    cmd,
    workflow,
    hooks,
    budget,
    modules,
    secret,
    stale,
    state,
    build,
    baseline,
)
