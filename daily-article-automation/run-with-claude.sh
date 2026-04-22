#!/bin/bash
# Full Automation with Claude Code - 使用 Claude Code 完成完整流程
# 综合热度 TOP3 话题版本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 加载环境变量（图片生成所需）
# 尝试多个可能的位置
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
    echo "  ARK_API_KEY: ${ARK_API_KEY:0:10}..."
    echo "  SEEDREAM_BASE_URL: $SEEDREAM_BASE_URL"
else
    echo "⚠ 警告：未找到 .baoyu-skills/.env 文件，图片生成可能失败"
fi

echo "========================================"
echo "每日文章生成系统 - Claude Code 增强版"
echo "综合热度 TOP3 话题"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Claude Code
if ! command -v claude &> /dev/null; then
    echo -e "${RED}错误：未找到 Claude Code${NC}"
    echo "请运行：npm install -g @anthropic-ai/claude-code"
    exit 1
fi
echo -e "${GREEN}✓${NC} Claude Code: $(claude --version)"

# 检查配置
if [ ! -f "config.yaml" ]; then
    echo -e "${YELLOW}!${NC} 配置文件不存在，创建示例配置..."
    cp config.example.yaml config.yaml
fi

# 创建目录
mkdir -p logs article

DATE_STR=$(date +%Y-%m-%d)
ARTICLE_DIR="$SCRIPT_DIR/article/$DATE_STR"
mkdir -p "$ARTICLE_DIR"

echo ""
echo "今日日期：$DATE_STR"
echo "文章目录：$ARTICLE_DIR"
echo ""

# Step 1-2: 获取热点并选择话题（使用 Python）
echo -e "${BLUE}Step 1-2: 热点聚合 + 话题选择 (综合热度 TOP3)${NC}"
echo "----------------------------------------"

# 使用 Python 生成热点和话题
python3 -c "
import sys
import json
from pathlib import Path
from datetime import datetime
sys.path.insert(0, '.')
from hot_topic_aggregator import HotTopicAggregator

# Step 1: 获取热点
aggregator = HotTopicAggregator('config.yaml')
topics = aggregator.fetch_all()
date_str = datetime.now().strftime('%Y-%m-%d')
topics_file = Path(f'article/{date_str}/ranked_topics.json')
topics_file.parent.mkdir(parents=True, exist_ok=True)
aggregator.save_to_json(str(topics_file))

# Step 2: 选择综合热度 TOP3 话题 (不限制分类)
top3_topics = topics[:3]
topic_file = Path(f'article/{date_str}/selected_topics.md')

with open(topic_file, 'w', encoding='utf-8') as f:
    f.write(f'''---
generated_at: {datetime.now().isoformat()}
selection_method: \"综合热度排名\"
total_topics: 3
---

# 今日选题：综合热度 TOP3 热点话题

''')
    for i, topic in enumerate(top3_topics, 1):
        f.write(f'''## {i}. {topic.topic}

- **来源**: {topic.source}
- **分类**: {topic.category}
- **热度**: {topic.heat_value}
- **综合得分**: {topic.score}
- **关键词**: {\", \".join(topic.keywords)}
- **链接**: {topic.url}

''')

print('✓ 话题已选择 (综合热度 TOP3):')
for i, topic in enumerate(top3_topics, 1):
    print(f'  {i}. [{topic.category}] {topic.topic} (得分：{topic.score:.3f})')
"

# 读取选题文件
TOPIC_FILE="$ARTICLE_DIR/selected_topics.md"
if [ ! -f "$TOPIC_FILE" ]; then
    echo -e "${RED}错误：选题文件不存在${NC}"
    exit 1
fi

# 提取三个话题
TOPIC1=$(grep -A1 "^## 1\." "$TOPIC_FILE" | grep "## 1\." | sed 's/.*## 1\. //' || echo "")
TOPIC2=$(grep -A1 "^## 2\." "$TOPIC_FILE" | grep "## 2\." | sed 's/.*## 2\. //' || echo "")
TOPIC3=$(grep -A1 "^## 3\." "$TOPIC_FILE" | grep "## 3\." | sed 's/.*## 3\. //' || echo "")

echo ""
echo -e "${GREEN}✓${NC} 今日话题 (综合热度 TOP3):"
[ -n "$TOPIC1" ] && echo "  1. $TOPIC1"
[ -n "$TOPIC2" ] && echo "  2. $TOPIC2"
[ -n "$TOPIC3" ] && echo "  3. $TOPIC3"

# Step 3-7: 使用 Claude Code 完成
echo ""
echo -e "${BLUE}Step 3-7: 使用 Claude Code 完成文章生成${NC}"
echo "----------------------------------------"

# 创建研究材料
RESEARCH_DIR="$ARTICLE_DIR/research_materials"
mkdir -p "$RESEARCH_DIR"
RESEARCH_FILE="$RESEARCH_DIR/research_summary.md"

cat > "$RESEARCH_FILE" << EOF
# 资料搜集：今日 TOP3 热点话题

搜集时间：$(date +%Y-%m-%d\ %H:%M)

## 话题列表
EOF

[ -n "$TOPIC1" ] && echo "- TOPIC 1: $TOPIC1" >> "$RESEARCH_FILE"
[ -n "$TOPIC2" ] && echo "- TOPIC 2: $TOPIC2" >> "$RESEARCH_FILE"
[ -n "$TOPIC3" ] && echo "- TOPIC 3: $TOPIC3" >> "$RESEARCH_FILE"

cat >> "$RESEARCH_FILE" << EOF

## 搜索查询
EOF

[ -n "$TOPIC1" ] && echo "- $TOPIC1 最新进展 2026" >> "$RESEARCH_FILE"
[ -n "$TOPIC1" ] && echo "- $TOPIC1 教程 技巧" >> "$RESEARCH_FILE"
[ -n "$TOPIC2" ] && echo "- $TOPIC2 最新进展 2026" >> "$RESEARCH_FILE"
[ -n "$TOPIC2" ] && echo "- $TOPIC2 教程 技巧" >> "$RESEARCH_FILE"
[ -n "$TOPIC3" ] && echo "- $TOPIC3 最新进展 2026" >> "$RESEARCH_FILE"
[ -n "$TOPIC3" ] && echo "- $TOPIC3 教程 技巧" >> "$RESEARCH_FILE"

cat >> "$RESEARCH_FILE" << EOF

## 资料内容
〔待 Claude Code WebSearch 填充〕
EOF

echo -e "${GREEN}✓${NC} 研究材料已准备"

# 文章文件（为每个话题生成单独的文章）
FORMATTED_DIR="$ARTICLE_DIR/formatted"
IMGS_DIR="$ARTICLE_DIR/imgs"
mkdir -p "$FORMATTED_DIR" "$IMGS_DIR"

echo ""
echo "开始调用 Claude Code..."
echo ""

# 构建话题列表字符串
TOPICS_LIST=""
[ -n "$TOPIC1" ] && TOPICS_LIST="$TOPICS_LIST
- TOPIC 1: $TOPIC1"
[ -n "$TOPIC2" ] && TOPICS_LIST="$TOPICS_LIST
- TOPIC 2: $TOPIC2"
[ -n "$TOPIC3" ] && TOPICS_LIST="$TOPICS_LIST
- TOPIC 3: $TOPIC3"

# 使用 claude 命令执行 - 通过 stdin 传递 prompt
echo "使用允许工具列表启动 Claude Code..."
echo ""

# 通过 stdin 传递 prompt（使用 cat 避免变量转义问题）
cat <<PROMPT_EOF | claude -p \
  --allowed-tools "WebSearch,Bash,BatchWrite,Write,Read,Glob,Grep" \
  --model "qwen3.5-plus"
请完成以下每日文章生成任务：

今日 TOP3 话题：$TOPICS_LIST

任务列表:
1. 使用 WebSearch 搜索每个话题的最新资料（至少 3 个来源/话题）
2. 将搜索结果补充到：$RESEARCH_FILE
3. 为每个话题使用 wechat-article-writer skill 撰写文章
   - 要求：1000-1500 字/篇，故事化开头
   - 结构：效果展示 → 问题描述 → 步骤教学 → 升华总结
   - 输出目录：$ARTICLE_DIR (文件名包含分类前缀)
4. 使用 baoyu-format-markdown skill 格式化文章
   - 添加 frontmatter (title, summary, cover)
   - 优化排版
   - 输出目录：$FORMATTED_DIR
5. 使用 baoyu-image-gen skill 生成配图
   - 配图密度：balanced
   - 每个话题生成 3-5 张插图 + 1 张封面
   - 输出目录：$IMGS_DIR
6. 使用 baoyu-post-to-wechat skill 保存为草稿（draft 模式）

请按顺序执行以上任务，每完成一步请告诉我进度。
工作目录：$ARTICLE_DIR
PROMPT_EOF

# 检查结果
echo ""
echo "========================================"
if [ -d "$ARTICLE_DIR" ] && [ "$(ls -A $ARTICLE_DIR/*.md 2>/dev/null)" ]; then
    echo -e "${GREEN}✓${NC} 文章已生成：$ARTICLE_DIR"
else
    echo -e "${YELLOW}!${NC} 文章生成失败"
fi

if [ -d "$FORMATTED_DIR" ] && [ "$(ls -A $FORMATTED_DIR/*.md 2>/dev/null)" ]; then
    echo -e "${GREEN}✓${NC} 格式化完成：$FORMATTED_DIR"
else
    echo -e "${YELLOW}!${NC} 格式化未完成"
fi

if [ -d "$IMGS_DIR" ] && [ "$(ls -A $IMGS_DIR 2>/dev/null)" ]; then
    echo -e "${GREEN}✓${NC} 配图已生成：$IMGS_DIR"
else
    echo -e "${YELLOW}!${NC} 配图未生成"
fi


rm /tmp/claude-0/ -rf
rm /tmp/wechat-article-images-* -rf
rm /tmp/run-with-claude-output.log 

echo ""
echo "========================================"
echo "完成！"
echo "========================================"
echo ""
echo "查看草稿：https://mp.weixin.qq.com"
echo "查看日志：tail -f logs/daily-article.log"
echo ""
