# 唯一命令入口。
#
# 规则与断言都在 `.harness/` 里，但**怎么跑**只在这张表里。人不该记住
# `python3 .harness/scripts/verify.py --all --scope=build` 这种串：记不住就会跳过，
# 跳过了门禁就不存在。未在这里注册的脚本一律不许当命令用。
#
# 环境变量在本文件里钉死，不依赖开发者 shell：
#   GOPATH 在仓库外。它一旦落进仓库，模块缓存就会被 `git add -A` 收走，
#   .git 里会留下上万个游离对象（本仓库 2026-10-28 踩过，见 .harness/memory/lessons.md L-1）。

ROOT := $(patsubst %/,%,$(dir $(realpath $(firstword $(MAKEFILE_LIST)))))
HARNESS := $(ROOT)/.harness
SCRIPTS := $(HARNESS)/scripts
VERIFY := $(SCRIPTS)/verify.py
REVERSE := $(SCRIPTS)/tests/reverse.py
GEN_GUIDE := $(SCRIPTS)/gen_guide.py
DISCOVERY := $(SCRIPTS)/discovery.py
CHECK_COMMIT := $(SCRIPTS)/check_commit.py
WT := $(SCRIPTS)/wt.py
GO_FILES := $(SCRIPTS)/go_files.py
TRACKED := $(SCRIPTS)/tracked.py
RETRO := $(SCRIPTS)/retro.py
PY ?= python3

export GOPATH := $(HOME)/.go
export GOMODCACHE := $(GOPATH)/pkg/mod
export GOPROXY := https://goproxy.cn,direct
export GOFLAGS := -buildvcs=false

.DEFAULT_GOAL := help
.PHONY: help init check check-all check-json check-strict fix guide index ignored evidence retro selftest commit-msg \
	task-new task-done task-list build vet fmt test go-all up down clean

help: ## 列出可用命令
	@echo "用法：make <目标>"
	@grep -hE '^[a-z0-9-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk -F'## ' '{split($$1,a,":"); printf "  %-12s %s\n", a[1], $$2}'
	@echo ""
	@echo "  check-all 会连同慢域（build：go build + go vet）一起跑，默认 check 跳过它"

init: ## 装 git 钩子、建状态目录、生成代码库索引
	@git -C $(ROOT) config core.hooksPath .harness/git-hooks
	@echo "hooksPath 写在 $$(git -C $(ROOT) config --show-origin --get core.hooksPath | cut -f1)" \
		"——它是仓库级设置，同仓库的其它 worktree 一起受影响"
	@chmod +x $(HARNESS)/git-hooks/pre-commit $(HARNESS)/git-hooks/commit-msg
	@mkdir -p $(HARNESS)/deliverables/evidence $(HARNESS)/tasks
	@$(PY) $(GEN_GUIDE) --root $(ROOT)
	@$(PY) $(DISCOVERY) --root $(ROOT)
	@echo "init 完成：hooksPath=.harness/git-hooks，索引与 INDEX.md 已重建"
	@$(MAKE) --no-print-directory selftest

check: ## 跑门禁（跳过慢域）
	@$(PY) $(VERIFY) --root $(ROOT)

check-all: ## 跑门禁，含慢域
	@$(PY) $(VERIFY) --root $(ROOT) --all

check-json: ## 跑门禁，输出原始计数
	@$(PY) $(VERIFY) --root $(ROOT) --all --json

check-strict: ## 跑门禁，示例数据按 ERROR 处理
	@$(PY) $(VERIFY) --root $(ROOT) --all --strict

fix: ## 只修派生数据（需工作区干净），修完自动重跑
	@$(PY) $(VERIFY) --root $(ROOT) --all --fix

guide: ## 重新生成 .harness/codebase-guide/（派生，禁手改）
	@$(PY) $(GEN_GUIDE) --root $(ROOT)

index: ## 重新生成 .harness/INDEX.md（派生：下一步、没人守的规则、流程装机状态）
	@$(PY) $(DISCOVERY) --root $(ROOT)

task-new: ## 给看板里已登记的任务开一棵工作树：TASK=<看板 id>
	@$(PY) $(WT) --root $(ROOT) task-new $(TASK)

task-done: ## 收尾一棵树（干净 + 看板 done + 已合并才动手）：TASK=<看板 id>
	@$(PY) $(WT) --root $(ROOT) task-done $(TASK)

task-list: ## 列出已开的工作树
	@$(PY) $(WT) --root $(ROOT) list

evidence: ## 把一次全量校验的完整输出存成证据
	@mkdir -p $(HARNESS)/deliverables/evidence
	@out=$(HARNESS)/deliverables/evidence/verify-$$(date -u +%Y%m%dT%H%M%SZ).txt; \
	status=$$(git -C $(ROOT) status --porcelain | head -1); \
	{ echo "# 命令：make check-all"; \
	  echo "# UTC：$$(date -u +%Y-%m-%dT%H:%M:%SZ)"; \
	  echo "# commit: $$(git -C $(ROOT) rev-parse HEAD)"; \
	  echo "# 工作区：$${status:+dirty}"; \
	  echo "# 首条未提交改动：$$status"; \
	  echo "# 退出码契约：0 = 无 ERROR，1 = 有 ERROR，2 = 前置条件不满足"; \
	  echo; \
	  $(PY) $(VERIFY) --root $(ROOT) --all; echo "exit=$$?"; } > $$out; \
	tail -3 $$out; echo "已存：$$out"

retro: ## 复盘事实底板：只算数字（ERROR 环比、看板、手册行数），不写结论
	@$(PY) $(RETRO) --root $(ROOT)

selftest: ## 反向测试：每条断言都要真的会报
	@$(PY) $(REVERSE) --root $(ROOT)

commit-msg: ## 判最近一条提交信息「一件事、动宾短语、不并列」（提交时的钩子跑同一套判据）
	@$(PY) $(CHECK_COMMIT) --root $(ROOT)

build: ## go build
	@cd $(ROOT) && go build ./... > /tmp/vben-build.log 2>&1; rc=$$?; \
	if [ $$rc -ne 0 ]; then cat /tmp/vben-build.log; fi; \
	echo "go build exit=$$rc"; exit $$rc

vet: ## go vet
	@cd $(ROOT) && go vet ./... > /tmp/vben-vet.log 2>&1; rc=$$?; \
	if [ $$rc -ne 0 ]; then cat /tmp/vben-vet.log; fi; \
	echo "go vet exit=$$rc"; exit $$rc

fmt: ## 列出未格式化的 .go（只报告，不代改）
	@cd $(ROOT) && files=$$($(PY) $(GO_FILES) $(ROOT)) || \
		{ echo "make fmt：判不了——排除本地产物后没有 .go 可判，这不是通过"; exit 2; }; \
	gofmt -l $$files

ignored: ## 列出被 gitignore 排除的本地路径（门禁判「不入库」时看这张表）
	@$(PY) $(TRACKED) $(ROOT)

test: ## go test
	@cd $(ROOT) && go test ./...

go-all: build vet ## 编译 + 静态检查（慢域，等价于 check-all 里的 build scope）

up: ## 起整套（webapp + mysql + redis；缺凭据时 compose 点名缺哪个）
	@docker compose -f $(ROOT)/docker-compose.yml up -d

down: ## 停整套（mysql 数据留在卷 thooh-mysql 里；清库见 README 部署段）
	@docker compose -f $(ROOT)/docker-compose.yml down

logs: ## 跟 webapp 的日志（起不来的原因在这里）
	@docker compose -f $(ROOT)/docker-compose.yml logs -f webapp

clean: ## 清派生产物（不动状态目录）
	@rm -rf $(HARNESS)/codebase-guide
	@go clean -cache 2>/dev/null || true
	@echo "已清：codebase-guide、go build cache"
