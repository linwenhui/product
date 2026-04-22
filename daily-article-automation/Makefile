# Daily Article Automation - Makefile
# 常用命令快捷方式

.PHONY: help install test dry-run draft-only full-run clean logs setup-cron

PYTHON := python3
PIP := pip3
SCRIPT_DIR := $(shell pwd)

help: ## 显示帮助信息
	@echo "每日自动公众号文章生成系统"
	@echo ""
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## 安装依赖
	@echo "安装 Python 依赖..."
	$(PIP) install -r requirements.txt --quiet
	@echo "✓ 依赖安装完成"

setup: install ## 初始化设置
	@echo "初始化项目..."
	@mkdir -p logs article
	@if [ ! -f config.yaml ]; then \
		cp config.example.yaml config.yaml; \
		echo "✓ 配置文件已创建 (config.yaml)"; \
	else \
		echo "✓ 配置文件已存在"; \
	fi
	@echo "✓ 初始化完成"

test: ## 测试运行 (dry-run 模式)
	@echo "运行测试 (dry-run 模式)..."
	$(PYTHON) daily-article.py --dry-run

dry-run: test ## 测试运行 (dry-run 模式) 的别名

draft-only: ## 生成草稿模式 (不发布)
	@echo "生成草稿模式..."
	$(PYTHON) daily-article.py --draft-only

full-run: ## 完整运行 (自动发布)
	@echo "完整运行模式..."
	$(PYTHON) daily-article.py

step-%: ## 运行特定步骤 (例：make step-1)
	@echo "运行步骤 $*..."
	$(PYTHON) daily-article.py --step $*

logs: ## 查看最新日志
	@echo "查看最新日志 (Ctrl+C 退出)..."
	tail -f logs/daily-article.log

logs-cron: ## 查看 cron 日志
	@echo "查看 cron 日志..."
	tail -f logs/cron.log

clean: ## 清理生成的文件
	@echo "清理生成的文件..."
	rm -rf article/*/ranked_topics.json
	rm -rf article/*/selected_topic.md
	rm -rf article/*/*.md
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -f .coverage
	@echo "✓ 清理完成"

setup-cron: ## 配置 cron 定时任务
	@echo "配置 cron 定时任务..."
	@bash install-cron.sh

check-env: ## 检查环境变量
	@echo "检查环境变量..."
	@if [ -f ".baoyu-skills/.env" ]; then \
		echo "✓ .baoyu-skills/.env 存在"; \
		grep -q "WECHAT_APP_ID" .baoyu-skills/.env && echo "✓ WECHAT_APP_ID 已配置"; \
		grep -q "WECHAT_APP_SECRET" .baoyu-skills/.env && echo "✓ WECHAT_APP_SECRET 已配置"; \
	else \
		echo "! .baoyu-skills/.env 不存在"; \
	fi

status: ## 显示系统状态
	@echo "系统状态:"
	@echo "----------"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "配置：$$(test -f config.yaml && echo '✓ 存在' || echo '✗ 不存在')"
	@echo "日志：$$(ls -la logs/ 2>/dev/null | wc -l) 个文件"
	@echo "文章：$$(ls -la article/ 2>/dev/null | wc -l) 个目录"
	@echo ""
	@echo "最近生成的文章:"
	@ls -lt article/*/ 2>/dev/null | head -5 || echo "(无)"

# 开发相关
lint: ## 代码检查
	@echo "代码检查..."
	@python3 -m py_compile daily-article.py hot_topic_aggregator.py
	@python3 -m py_compile scripts/*.py
	@echo "✓ 代码检查通过"

format: ## 格式化代码
	@echo "格式化代码..."
	@command -v black >/dev/null 2>&1 || $(PIP) install black --quiet
	@black daily-article.py hot_topic_aggregator.py scripts/*.py
	@echo "✓ 代码格式化完成"

test-unit: ## 运行单元测试
	@echo "运行单元测试..."
	@command -v pytest >/dev/null 2>&1 || $(PIP) install pytest --quiet
	@pytest -v
