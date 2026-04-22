#!/bin/bash
# 配图生成恢复脚本
# 用于为已生成的文章补全配图

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 加载环境变量
ENV_FILE=""
if [ -f ".baoyu-skills/.env" ]; then
    ENV_FILE=".baoyu-skills/.env"
elif [ -f "../.baoyu-skills/.env" ]; then
    ENV_FILE="../.baoyu-skills/.env"
elif [ -f "$HOME/.baoyu-skills/.env" ]; then
    ENV_FILE="$HOME/.baoyu-skills/.env"
fi

if [ -n "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    echo "✓ 环境变量已加载：$ENV_FILE"
else
    echo "⚠ 警告：未找到 .baoyu-skills/.env 文件"
    exit 1
fi

# 检查 ARK_API_KEY
if [ -z "$ARK_API_KEY" ]; then
    echo "✗ 错误：ARK_API_KEY 未设置"
    exit 1
fi
echo "✓ ARK_API_KEY 已配置：${ARK_API_KEY:0:10}..."

# 获取今日文章目录
DATE_STR=$(date +%Y-%m-%d)
ARTICLE_DIR="$SCRIPT_DIR/article/$DATE_STR"

if [ ! -d "$ARTICLE_DIR" ]; then
    echo "✗ 错误：文章目录不存在 $ARTICLE_DIR"
    exit 1
fi

echo "✓ 文章目录：$ARTICLE_DIR"

# 查找格式化后的文章
FORMATTED_DIR="$ARTICLE_DIR/formatted"
IMGS_DIR="$ARTICLE_DIR/imgs"
mkdir -p "$IMGS_DIR"

echo ""
echo "开始生成配图..."
echo "========================================"

# 遍历 formatted 目录中的文章
if [ -d "$FORMATTED_DIR" ]; then
    for article_file in "$FORMATTED_DIR"/*-formatted.md; do
        if [ -f "$article_file" ]; then
            filename=$(basename "$article_file" -formatted.md)
            echo ""
            echo "处理：$filename"

            # 提取文章标题作为 prompt
            title=$(grep "^title:" "$article_file" | head -1 | cut -d: -f2- | tr -d ' "'"'"'')
            if [ -z "$title" ]; then
                title="科技风格插图"
            fi

            echo "  标题：$title"
            echo "  生成封面图..."

            # 调用 baoyu-image-gen 生成封面图
            claude -p \
                --allowed-tools "Bash,Write,Read" \
                --model "qwen3.5-plus" \
                "请使用 baoyu-image-gen skill 为文章生成封面图：
- 文章标题：$title
- 输出目录：$IMGS_DIR
- 文件名：${filename}-cover.jpg
- 风格：科技插画风格
- 尺寸：1024x1024

使用环境变量：
SEEDREAM_BASE_URL=$SEEDREAM_BASE_URL
ARK_API_KEY=${ARK_API_KEY:0:10}...

请生成图片并保存到指定目录。" 2>&1 | head -20
        fi
    done
else
    echo "✗ 错误：未找到 formatted 目录"
    exit 1
fi

echo ""
echo "========================================"
echo "配图生成完成！"
echo "查看图片：ls -la $IMGS_DIR"
