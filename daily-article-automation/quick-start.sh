#!/bin/bash
# Quick Start Script - 快速测试每日文章生成系统

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "每日自动公众号文章生成系统"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误：未找到 Python 3${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python: $(python3 --version)"

# 检查配置文件
if [ ! -f "config.yaml" ]; then
    echo -e "${YELLOW}!${NC} 配置文件不存在，创建示例配置..."
    cp config.example.yaml config.yaml
fi
echo -e "${GREEN}✓${NC} 配置文件：config.yaml"

# 检查依赖
echo ""
echo "检查依赖..."
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "安装 PyYAML..."
    pip3 install pyyaml --quiet
fi
echo -e "${GREEN}✓${NC} Python 依赖已安装"

# 显示菜单
echo ""
echo "请选择运行模式:"
echo "  1) Dry Run 模式 (测试，不实际操作)"
echo "  2) 生成草稿模式 (存为草稿，不发布)"
echo "  3) 仅获取热点"
echo "  4) 仅执行特定步骤"
echo "  5) 完整运行 (自动发布)"
echo ""

read -p "请输入选项 [1-5]: " -n 1 -r
echo

case $REPLY in
    1)
        echo ""
        echo "运行 Dry Run 模式..."
        python3 daily-article.py --dry-run
        ;;
    2)
        echo ""
        echo "运行生成草稿模式..."
        python3 daily-article.py --draft-only
        ;;
    3)
        echo ""
        echo "获取热点..."
        python3 daily-article.py --step 1
        ;;
    4)
        echo ""
        read -p "请输入步骤编号 (1-8): " step
        python3 daily-article.py --step "$step"
        ;;
    5)
        echo ""
        echo -e "${YELLOW}警告：此模式将自动发布文章到微信公众号！${NC}"
        read -p "确认继续？[y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 daily-article.py
        else
            echo "已取消"
            exit 0
        fi
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "运行完成!"
echo "========================================"
echo ""
echo "查看生成的文件:"
echo "  cd article/$(date +%Y-%m-%d)/"
echo "  ls -la"
echo ""
echo "查看日志:"
echo "  tail -f logs/daily-article.log"
echo ""
