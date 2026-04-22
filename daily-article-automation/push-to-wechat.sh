#!/bin/bash
# 微信公众号文章推送脚本
# 将今日生成的 3 篇文章推送到微信公众号

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
fi

# 获取今日文章目录
DATE_STR=$(date +%Y-%m-%d)
ARTICLE_DIR="$SCRIPT_DIR/article/$DATE_STR"
FORMATTED_DIR="$ARTICLE_DIR/formatted"
IMGS_DIR="$ARTICLE_DIR/imgs"

echo ""
echo "========================================"
echo "微信公众号文章推送"
echo "========================================"
echo ""
echo "文章目录：$ARTICLE_DIR"
echo ""

# 检查文章文件
if [ ! -d "$FORMATTED_DIR" ]; then
    echo "✗ 错误：formatted 目录不存在"
    exit 1
fi

# 遍历 formatted 目录中的文章
for article_file in "$FORMATTED_DIR"/*-formatted.md; do
    if [ -f "$article_file" ]; then
        filename=$(basename "$article_file")
        echo ""
        echo "----------------------------------------"
        echo "推送文章：$filename"
        echo "----------------------------------------"

        # 提取文章信息
        title=$(grep "^title:" "$article_file" | head -1 | cut -d: -f2- | tr -d ' "'"'"')
        summary=$(grep "^summary:" "$article_file" | head -1 | cut -d: -f2- | tr -d ' "'"'"')

        echo "  标题：$title"
        echo "  摘要：$summary"

        # 使用 baoyu-post-to-wechat skill 推送
        echo ""
        echo "  正在调用 baoyu-post-to-wechat skill..."

        claude -p \
            --allowed-tools "Bash,Write,Read" \
            --model "qwen3.5-plus" \
            "请使用 baoyu-post-to-wechat skill 推送这篇文章到微信公众号草稿箱：

文章文件：$article_file
图片目录：$IMGS_DIR

要求：
1. 使用 API 方式发布（非浏览器）
2. 保存为草稿（draft 模式）
3. 自动匹配文章中的图片
4. 设置合适的封面图

环境变量：
WECHAT_APP_ID=$WECHAT_APP_ID
WECHAT_APP_SECRET=${WECHAT_APP_SECRET:0:10}...

请执行推送并告诉我结果（media_id 或 draft_id）。" 2>&1 | head -30

        echo ""
        echo "  ✓ 推送完成"
    fi
done

echo ""
echo "========================================"
echo "全部推送完成！"
echo "========================================"
echo ""
echo "查看草稿：https://mp.weixin.qq.com"
echo "路径：内容管理 → 草稿箱"
echo ""
