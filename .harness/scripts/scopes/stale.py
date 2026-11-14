"""stale: swagger 与前端产物——「生成的东西有没有跟着变」。

  STL001  swagger 元数据三方不一致：main.go 的 `@title/@version/...` ↔ swagger.json ↔ swagger.yaml
  STL002  `web/admin/index.html` 引用的静态资源在磁盘上不存在——按 `r.Static()` 的挂载表解析
  STL003  带 `@Router` 注解的源文件比 docs/ 新——产物过期。超过 `stale_days_error` 天报 ERROR，
          否则 WARN（限时而非禁止）
  STL004  swagger `paths` 为空：文档里一条接口都没有（WARN，说明生成没跑或注解全缺）
  STL005  一个产物都没扫到（路径写错、web/ 改名）——扫不到与全绿同形（断言坑 #11）

STL003 在注解集为空时登记 `not_applicable` 而不是「通过」：本仓库目前 0 条 `@Router`，
重新生成 swagger 是空转，拿「docs 比源码旧 260 天」当 ERROR 是假信号——会逼人把
一条判不了的事情修成看起来修好了。判不了就说判不了。

STL002 为什么要读 `r.Static()` 而不是硬编码 `/admin → web/admin`：挂载表在源码里，
硬编码等于把同一件事判两遍（还会在下次改路由时静默失效）。
"""

import datetime
import re
import subprocess
from pathlib import Path

import ageing

from .common import add, go_files, quality_get

NAME = "stale"
PLAN = "会过期的引用：前端产物里被 `r.Static()` 挂载的资产还存不存在、swagger 三份元数据" \
    "（注解 / docs.go / json / yaml）是否互相一致、文档时效是否越过告警线"
REFLECT = ("STL001", "STL002", "STL003", "STL004", "STL005")
ANNOTATION_KEYS = {"title": "@title", "version": "@version", "description": "@description",
                   "host": "@host", "basePath": "@BasePath"}
STATIC_MOUNT_RE = re.compile(r'\.Static\(\s*"([^"]+)"\s*,\s*".?/?([^"]*)"')
ASSET_RE = re.compile(r"""(?:src|href)=("([^"]+)"|'([^']+)'|([^ >]+))""")
# 条件注释里的引用（`<!--[if lt IE 11]>…/html/ie.html…<![endif]-->`）今天没有浏览器会去取，
# 判它等于把「死代码里的一条路径」算成页面故障。先剥注释，再判真正会被发起的请求。
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
ROUTER_ANNOTATION = "@Router"
MOUNT_FILE = "app/core/routers/routers.go"


def sh(argv, cwd):
    try:
        p = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, str(exc)
    return p, (p.stdout or "") + (p.stderr or "")


def annotations_of_main(root):
    out = {}
    path = Path(root) / "main.go"
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        for key, marker in ANNOTATION_KEYS.items():
            if stripped.startswith(f"// {marker} "):
                out[key] = stripped[len(marker) + 3:].strip()
    return out


def json_meta(data):
    info = (data or {}).get("info") or {}
    return {
        "title": str(info.get("title", "")),
        "version": str(info.get("version", "")),
        "description": str(info.get("description", "")),
        "host": str((data or {}).get("host", "")),
        "basePath": str((data or {}).get("basePath", "")),
    }


def yaml_meta(text):
    """生成物是扁平的两档 YAML，按 key 取标量够用；不做通用 YAML 解析。"""
    out = {}
    for key in ("title", "version", "description", "host", "basePath"):
        m = re.search(rf"^ {{0,2}}{re.escape(key)}:\s*(.*)$", text, re.M)
        if m:
            out[key] = m.group(1).strip().strip('"')
    return out


def mounts(root, findings):
    table = []
    path = Path(root) / MOUNT_FILE
    if not path.is_file():
        add(findings, "WARN", NAME, MOUNT_FILE, 1, "STL005",
            "找不到静态挂载声明，STL002 只能按 web/ 直读判")
        return table
    for url, dir_ in STATIC_MOUNT_RE.findall(path.read_text(encoding="utf-8", errors="replace")):
        table.append((url, Path(root) / dir_))
    table.sort(key=lambda kv: -len(kv[0]))
    return table


def resolve(ref, table, root):
    """返回 (磁盘路径, 是否判得了)。"""
    for url, base in table:
        if url != "/" and ref.startswith(url.rstrip("/") + "/"):
            return base / ref[len(url.rstrip("/")) + 1:], True
    if ref.startswith("/"):
        return Path(root) / ref.lstrip("/"), True
    return None, False


def check_meta(root, quality, findings):
    import json

    json_rel = str(quality_get(quality, "swagger_json", "docs/swagger.json"))
    yaml_rel = str(quality_get(quality, "swagger_yaml", "docs/swagger.yaml"))
    jp, yp = Path(root) / json_rel, Path(root) / yaml_rel
    if not jp.is_file() and not yp.is_file():
        add(findings, "ERROR", NAME, json_rel, 1, "STL005",
            f"swagger 产物一个都没有（{json_rel} / {yaml_rel}）")
        return
    jm = {}
    if jp.is_file():
        try:
            jm = json_meta(json.loads(jp.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            add(findings, "ERROR", NAME, json_rel, 1, "STL001", f"swagger.json 解析失败：{exc}")
    ym = yaml_meta(yp.read_text(encoding="utf-8", errors="replace")) if yp.is_file() else {}
    am = annotations_of_main(root)
    sources = {"main.go": am, json_rel: jm, yaml_rel: ym}
    for key in ANNOTATION_KEYS:
        vals = {name: meta[key] for name, meta in sources.items() if meta and key in meta}
        distinct = {v for v in vals.values() if v}
        if len(distinct) > 1:
            worst = max(vals, key=lambda n: len(vals[n]))
            detail = "、".join(f"{n}={vals[n]!r}" for n in sorted(vals))
            add(findings, "ERROR", NAME, json_rel if json_rel in vals else MOUNT_FILE, 1, "STL001",
                f"{key} 三方不一致（{detail}）；以 main.go 注解为准重新生成，最完整的是 {worst}")
    if jp.is_file():
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
        except ValueError:
            return
        if not (data.get("paths") or {}):
            add(findings, "WARN", NAME, json_rel, 1, "STL004",
                "swagger paths 为空：文档里没有一条接口，多半是注解缺失或没跑 swag init")


def check_assets(root, quality, findings):
    index_rel = str(quality_get(quality, "web_index", "web/admin/index.html"))
    index = Path(root) / index_rel
    if not index.is_file():
        add(findings, "ERROR", NAME, index_rel, 1, "STL005",
            f"前端入口产物 {index_rel} 不存在——web/ 改名或配置写错")
        return
    table = mounts(root, findings)
    text = HTML_COMMENT.sub("", index.read_text(encoding="utf-8", errors="replace"))
    refs = set()
    for m in ASSET_RE.finditer(text):
        ref = m.group(2) or m.group(3) or m.group(4) or ""
        if not ref.startswith("/") or ref.startswith("//"):
            continue  # 内联脚本里的 href=f;var 之类不算引用
        refs.add(ref)
    if not refs:
        add(findings, "WARN", NAME, index_rel, 1, "STL005",
            "入口 HTML 里没解析到任何以 / 开头的资源引用——检查正则还是检查产物")
    for ref in sorted(refs):
        target, ok = resolve(ref, table, root)
        if not ok or target is None:
            continue
        if not target.exists():
            add(findings, "ERROR", NAME, index_rel, 1, "STL002",
                f"引用 {ref} 但磁盘上没有 {target.relative_to(root)}——构建产物与静态挂载表脱节")


def check_swag_staleness(root, quality, findings, na):
    warn_days = int(quality_get(quality, "stale_days_warn", 7))
    error_days = int(quality_get(quality, "stale_days_error", 14))
    src_hits = [p for p in go_files(Path(root)) if ROUTER_ANNOTATION in p.read_text(encoding="utf-8", errors="replace")]
    if not src_hits:
        na.append("stale:swagger 时效")
        return
    # docs 目录有未提交改动 = 正在重新生成；提交前 git log 还是旧时间，拿它判过期会误拦本次提交
    pd, dirty_out = sh(["git", "status", "--porcelain", "--", "docs"], root)
    if pd is None or dirty_out.strip():
        return
    p, out = sh(["git", "log", "-1", "--format=%ct", "--", "docs"], root)
    if p is None or p.returncode != 0 or not out.strip():
        na.append("stale:swagger 时效")
        return
    docs_ts = int(out.splitlines()[0])
    p2, out2 = sh(["git", "log", "-1", "--format=%ct", "--", *{str(x.relative_to(root)) for x in src_hits}], root)
    if p2 is None or p2.returncode != 0 or not out2.strip():
        na.append("stale:swagger 时效")
        return
    src_ts = int(out2.splitlines()[0])
    days = ageing.age_days(docs_ts, src_ts)
    if days < warn_days:
        return
    cfg = datetime.date.fromtimestamp(docs_ts).isoformat()
    add(findings, "ERROR" if days >= error_days else "WARN", NAME,
        str(quality_get(quality, "swagger_json", "docs/swagger.json")), 1, "STL003",
        f"{len(src_hits)} 个文件带 @Router，但 docs/ 最后一次生成在 {cfg}（落后 {days} 天）："
        "跑 swag init 重新生成")


def run(ctx, findings):
    root = Path(ctx["root"])
    quality = ctx.get("quality") or {}
    na = ctx.setdefault("not_applicable", [])
    check_meta(root, quality, findings)
    check_assets(root, quality, findings)
    check_swag_staleness(root, quality, findings, na)
