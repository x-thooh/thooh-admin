"""secret：密钥与弱口令入库。

SEC003 需要一次真的 `git add`（判的是「进没进版本控制」），git 不可用时如实报「判不了」——
返回 None 而不是 True：环境缺件不是通过。
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
    return out
