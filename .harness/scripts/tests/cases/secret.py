"""secret：密钥与弱口令入库。

SEC003 与 SEC005（还有 SEC001b 那条「未跟踪但没被 ignore」）都要一次真的 `git init`：
它们判的是「git 会不会带走这条路径」。git 不可用时如实报「判不了」——返回 None 而不是
True：环境缺件不是通过。
"""

from scopes import secret as sc_secret
from support import codes_of, ctx_for, git, new_root

NAME = "secret"


def cases():
    out = []
    root = new_root({"config.yaml": "jwt:\n  secret: FAKEFAKEFAKE0123456789abcdefghijABCDEFGHIJ0123456789abcdef\n"})
    f = []
    sc_secret.run(ctx_for(root), f)
    out.append(("SEC001", "高熵密钥写在 config.yaml", "SEC001" in codes_of(f)))

    root = new_root({"config.yaml": "database:\n  primary:\n    password: 123456\n"})
    f = []
    sc_secret.run(ctx_for(root), f)
    out.append(("SEC002", "弱默认口令", "SEC002" in codes_of(f)))

    root = new_root({".env": "A=1\n", "readme.md": "x\n"})
    ok, _ = git(root, "init", "-q")
    if ok:
        git(root, "add", ".env")
        f = []
        sc_secret.run(ctx_for(root), f)
        out.append(("SEC003", "本地覆盖文件进了版本控制", "SEC003" in codes_of(f)))
    else:
        out.append(("SEC003", "git 不可用，这一条判不了", None))

    root = new_root({})
    f = []
    sc_secret.run(ctx_for(root), f)
    out.append(("SEC004", "一个候选文件都没有", "SEC004" in codes_of(f)))

    root = new_root({"config.yaml": "jwt:\n  secret: ${JWT_SECRET}\n"})
    f = []
    sc_secret.run(ctx_for(root), f)
    out.append(("SEC00n", "正对照：环境变量占位符不该报 SEC001", "SEC001" in codes_of(f)))

    # 「入库」的主语是 git 会带走的东西。这一条同时钉住两个方向：被 ignore 的本地部署配置
    # 不算入库（SEC001 不许报，否则主树以后每次提交都被拦），但也不许沉默（SEC005 点名），
    # 而且弱口令那种「形同虚设」照报——它判的是有没有用，不是进不进仓库。
    strong = "FAKEFAKEFAKE0123456789abcdefghijABCDEFGHIJ0123456789abcdef"
    root = new_root({".gitignore": "/deploy/\n",
                     "deploy/config.yaml": f"jwt:\n  secret: {strong}\n"
                                           "database:\n  primary:\n    password: 123456\n"})
    ok, _ = git(root, "init", "-q")
    if ok:
        f = []
        ctx = ctx_for(root)
        sc_secret.run(ctx, f)
        got = codes_of(f)
        out.append(("SEC005", "gitignore 排除的本地文件：不判入库、降级点名、弱口令照报",
                    "SEC005" in got and "SEC001" not in got and "SEC002" in got))
    else:
        out.append(("SEC005", "git 不可用，这一条判不了", None))

    root = new_root({".gitignore": "/deploy/\n", f"config.yaml": f"jwt:\n  secret: {strong}\n"})
    ok, _ = git(root, "init", "-q")
    if ok:
        f = []
        sc_secret.run(ctx_for(root), f)
        out.append(("SEC001b", "没被 ignore 的未跟踪文件仍然算入库（不能收窄成「只判已跟踪的」）",
                    "SEC001" in codes_of(f)))
    else:
        out.append(("SEC001b", "git 不可用，这一条判不了", None))
    return out
