#!/bin/bash
# Install Cron Job for Daily Article Automation
# 安装每日文章自动生成的定时任务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="daily-article-automation"

echo "========================================"
echo "安装每日文章自动生成 Cron 任务"
echo "========================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 Python 3"
    exit 1
fi
echo "✓ Python 版本：$(python3 --version)"

# 检查配置文件
if [ ! -f "$SCRIPT_DIR/config.yaml" ]; then
    echo "错误：配置文件 config.yaml 不存在"
    exit 1
fi
echo "✓ 配置文件存在"

# 检查依赖
echo ""
echo "检查 Python 依赖..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip3 install -r "$SCRIPT_DIR/requirements.txt" --quiet
    echo "✓ 依赖已安装"
fi

# 创建日志目录
mkdir -p "$SCRIPT_DIR/logs"
echo "✓ 日志目录已创建"

# 显示当前 crontab
echo ""
echo "当前 crontab 配置:"
crontab -l 2>/dev/null || echo "(无配置)"

# 询问是否安装
echo ""
read -p "是否安装每天 6:00 执行的定时任务？[y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消安装"
    exit 0
fi

# 备份现有 crontab
CRON_BACKUP="$HOME/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
crontab -l > "$CRON_BACKUP" 2>/dev/null || true
echo "✓ 已备份现有 crontab: $CRON_BACKUP"

# 添加新任务
CRON_JOB="0 6 * * * cd $SCRIPT_DIR && /usr/bin/env python3 daily-article.py >> $SCRIPT_DIR/logs/cron.log 2>&1"

# 检查是否已存在相同任务
if crontab -l 2>/dev/null | grep -q "daily-article.py"; then
    echo "警告：已存在 daily-article.py 的定时任务"
    read -p "是否替换？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消安装"
        exit 0
    fi
    # 删除旧任务
    crontab -l 2>/dev/null | grep -v "daily-article.py" | crontab -
fi

# 添加新任务
(crontab -l 2>/dev/null | grep -v "daily-article.py"; echo "$CRON_JOB") | crontab -

echo ""
echo "========================================"
echo "✓ Cron 任务安装成功!"
echo "========================================"
echo ""
echo "任务详情:"
echo "  时间：每天早上 6:00"
echo "  命令：python3 daily-article.py"
echo "  日志：$SCRIPT_DIR/logs/cron.log"
echo ""
echo "查看当前 crontab:"
echo "  crontab -l"
echo ""
echo "查看日志:"
echo "  tail -f $SCRIPT_DIR/logs/cron.log"
echo ""
echo "卸载命令:"
echo "  crontab -l | grep -v daily-article | crontab -"
echo ""

# 测试运行
echo "是否立即执行一次测试运行？[y/N] "
read -p "" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "执行测试运行 (dry-run 模式)..."
    cd "$SCRIPT_DIR"
    python3 daily-article.py --dry-run
fi
