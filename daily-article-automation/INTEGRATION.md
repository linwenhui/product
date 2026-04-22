# 集成指南 - Claude Code Skills

本文档说明如何将每日文章生成系统与 Claude Code Skills 集成，实现完全自动化的文章撰写和发布。

## 集成架构

```
┌─────────────────────────────────────────────────────────────────┐
│  daily-article.py (主编排脚本)                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1-2: Python 原生实现                                       │
│    └── 热点聚合 + 话题选择                                       │
│                                                                 │
│  Step 3-7: 调用 Claude Code Skills                              │
│    ├── WebSearch (资料搜集)                                     │
│    ├── wechat-article-writer (文章撰写)                         │
│    ├── baoyu-format-markdown (格式化)                           │
│    ├── baoyu-article-illustrator (配图)                         │
│    └── baoyu-post-to-wechat (发布)                              │
│                                                                 │
│  Step 8: Python 原生实现                                         │
│    └── 通知与日志                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 方法一：使用 Claude Code CLI (推荐)

### 3.1 安装 Claude Code

```bash
npm install -g @anthropics/claude-code
```

### 3.2 创建 Skill 调用脚本

创建 `scripts/invoke-skills.sh`：

```bash
#!/bin/bash
# 调用 Claude Code Skills 完成文章生成

ARTICLE_FILE="$1"
TOPIC="$2"

# 调用 wechat-article-writer
claude --prompt "请用 wechat-article-writer skill 撰写一篇关于\"$TOPIC\"的公众号文章
要求：
- 1000-1500 字
- 故事化开头，带情感色彩
- 结构：效果展示 → 问题描述 → 步骤教学 → 升华总结
- 生成 5 个爆款标题
- 输出文件：$ARTICLE_FILE"

# 调用 baoyu-format-markdown
claude --prompt "请用 baoyu-format-markdown skill 格式化文章：$ARTICLE_FILE"

# 调用 baoyu-article-illustrator
claude --prompt "请用 baoyu-article-illustrator skill 为文章生成配图
文件：${ARTICLE_FILE%.md}-formatted.md
密度：balanced
风格：tech-explainer"

# 调用 baoyu-post-to-wechat
claude --prompt "请用 baoyu-post-to-wechat skill 发布文章到微信
文件：${ARTICLE_FILE%.md}-formatted.md
模式：draft"
```

### 3.3 修改 daily-article.py

在 `daily-article.py` 中调用脚本：

```python
def step4_write_article(self, topic_data: dict, research_data: dict) -> dict:
    """Step 4: 文章撰写 (使用 wechat-article-writer skill)"""
    # ... 现有代码 ...

    # 调用 Claude Code
    script_path = self.base_dir / "scripts" / "invoke-skills.sh"
    subprocess.run(
        ["bash", str(script_path), str(article_file), topic_str],
        check=True,
        capture_output=True
    )
```

## 方法二：使用 Claude Code API

### 4.1 配置 API

```bash
export ANTHROPIC_API_KEY=your_api_key
```

### 4.2 创建 API 调用模块

创建 `scripts/claude_api_client.py`：

```python
#!/usr/bin/env python3
"""
Claude Code API Client
调用 Claude Code 完成文章生成任务
"""

import os
import asyncio
from typing import Optional

class ClaudeCodeClient:
    """Claude Code API 客户端"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

    async def invoke_skill(self, skill_name: str, prompt: str, output_file: str = None):
        """
        调用 Skill

        Args:
            skill_name: Skill 名称
            prompt: 提示词
            output_file: 输出文件路径

        Returns:
            执行结果
        """
        # 使用 Anthropic SDK
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)

        # 构建完整提示（包含 skill 指令）
        full_prompt = f"""<skill>{skill_name}</skill>

{prompt}

请按照 skill 定义的流程执行任务。
"""

        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": full_prompt}]
        )

        result = response.content[0].text

        # 保存到文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)

        return result

    async def write_article(self, topic: str, research_file: str, output_file: str):
        """调用 wechat-article-writer skill"""
        prompt = f"""
请撰写一篇关于"{topic}"的公众号文章。

要求：
- 1000-1500 字
- 故事化开头，带情感色彩（兴奋/焦虑/好奇）
- 结构：效果展示 → 问题描述 → 步骤教学 → 升华总结
- 生成 5 个爆款标题备选
- 参考资料：{research_file}

输出文件：{output_file}
"""
        return await self.invoke_skill("wechat-article-writer", prompt, output_file)

    async def format_markdown(self, article_file: str, output_file: str):
        """调用 baoyu-format-markdown skill"""
        prompt = f"""
请格式化这篇文章：{article_file}

要求：
- 添加 frontmatter (title, summary, cover)
- 优化排版：段落、加粗、列表、表格
- 输出文件：{output_file}
"""
        return await self.invoke_skill("baoyu-format-markdown", prompt, output_file)

    async def generate_images(self, article_file: str, image_dir: str, density: str = "balanced"):
        """调用 baoyu-article-illustrator skill"""
        prompt = f"""
请为这篇文章生成配图：{article_file}

要求：
- 配图密度：{density}
- 生成封面图 + 内文插图 (3-5 张)
- 输出目录：{image_dir}
"""
        return await self.invoke_skill("baoyu-article-illustrator", prompt)

    async def publish_wechat(self, article_file: str, draft_mode: bool = True):
        """调用 baoyu-post-to-wechat skill"""
        mode = "draft" if draft_mode else "publish"
        prompt = f"""
请发布这篇文章到微信公众号：{article_file}

模式：{mode}
使用 API 方式发布（非浏览器）
"""
        return await self.invoke_skill("baoyu-post-to-wechat", prompt)


async def main():
    """测试"""
    client = ClaudeCodeClient()

    # 示例：撰写文章
    result = await client.write_article(
        topic="AI 绘画新玩法",
        research_file="research.md",
        output_file="article.md"
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

### 4.3 集成到 daily-article.py

```python
from scripts.claude_api_client import ClaudeCodeClient

class DailyArticleAutomation:
    def __init__(self, ...):
        # ... 现有代码 ...
        self.claude_client = ClaudeCodeClient()

    async def step4_write_article(self, ...):
        await self.claude_client.write_article(...)

    async def step5_format_markdown(self, ...):
        await self.claude_client.format_markdown(...)

    async def step6_generate_images(self, ...):
        await self.claude_client.generate_images(...)

    async def step7_publish_wechat(self, ...):
        await self.claude_client.publish_wechat(...)

    def run(self, ...):
        asyncio.run(self._run_async())

    async def _run_async(self):
        # 异步执行各步骤
        ...
```

## 方法三：使用 MCP 协议

如果 Claude Code 支持 MCP (Model Context Protocol)，可以创建一个 MCP Server：

### 5.1 创建 MCP Server

```python
# mcp_server.py
from mcp.server import Server
from mcp.types import Tool

server = Server("daily-article-mcp")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="fetch-hot-topics",
            description="从多平台获取热点话题"
        ),
        Tool(
            name="write-article",
            description="使用 wechat-article-writer skill 撰写文章"
        ),
        # ... 其他工具
    ]

@server.call_tool()
async def call_tool(name: str, args: dict):
    if name == "fetch-hot-topics":
        aggregator = HotTopicAggregator()
        topics = aggregator.fetch_all()
        return {"topics": [asdict(t) for t in topics]}
    elif name == "write-article":
        # 调用 Claude Code skill
        ...
```

### 5.2 配置 MCP

在 Claude Code 配置中添加：

```json
{
  "mcpServers": {
    "daily-article": {
      "command": "python",
      "args": ["/cv5/linwh/ClaudeCode/claudecode_test/daily-article-automation/mcp_server.py"]
    }
  }
}
```

## 完整自动化流程

### 6.1 创建一键运行脚本

```bash
#!/bin/bash
# run-full-automation.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "每日文章自动生成系统"
echo "========================================"
echo ""

# Step 1-2: 获取热点并选择话题
echo "Step 1-2: 热点聚合 + 话题选择..."
python3 daily-article.py --step 1 --step 2

# Step 3-7: 调用 Claude Code Skills
echo ""
echo "Step 3-7: 调用 Claude Code Skills..."

ARTICLE_DATE=$(date +%Y-%m-%d)
ARTICLE_DIR="$SCRIPT_DIR/article/$ARTICLE_DATE"
TOPIC_FILE="$ARTICLE_DIR/selected_topic.md"

# 提取话题
TOPIC=$(grep "^topic:" "$TOPIC_FILE" | cut -d: -f2 | tr -d ' ')

echo "今日话题：$TOPIC"

# 使用 Claude Code 完成剩余步骤
claude --prompt "
请按照以下步骤完成文章生成：

1. 资料搜集：使用 WebSearch 搜索\"$TOPIC\"的相关资料
2. 文章撰写：使用 wechat-article-writer skill
3. 格式化：使用 baoyu-format-markdown skill
4. 配图：使用 baoyu-article-illustrator skill
5. 发布：使用 baoyu-post-to-wechat skill (draft 模式)

工作目录：$ARTICLE_DIR
"

# Step 8: 发送通知
echo ""
echo "Step 8: 发送通知..."
python3 scripts/notify-wechat.py --method wechat --title "文章已生成" --content "《$TOPIC》已完成"

echo ""
echo "========================================"
echo "✅ 文章生成完成！"
echo "========================================"
echo ""
echo "文章路径：$ARTICLE_DIR"
echo "查看草稿：https://mp.weixin.qq.com"
```

### 6.2 配置 Cron

```bash
# 编辑 crontab
crontab -e

# 添加（每天 6:00 执行）：
0 6 * * * /cv5/linwh/ClaudeCode/claudecode_test/daily-article-automation/run-full-automation.sh >> /cv5/linwh/ClaudeCode/claudecode_test/daily-article-automation/logs/automation.log 2>&1
```

## 环境变量配置

创建 `.env` 文件：

```bash
# Claude Code API
ANTHROPIC_API_KEY=sk-ant-api03-...

# WeChat API (已在 .baoyu-skills/.env 中)
WECHAT_APP_ID=wxf6a3acdaf4a9dd40
WECHAT_APP_SECRET=10fc656b53434df11e72443551386e6d

# 图片生成
SEEDREAM_BASE_URL=https://worklink.yealink.com/llmproxy/v1
ARK_API_KEY=3a763260-cb88-4645-86ca-4b25983e8fbb

# 通知配置
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=...
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_password
```

## 故障排查

### 检查 Skill 是否可用

```bash
# 列出可用 skills
claude --list-skills

# 或查看 skill 目录
ls -la .skills/utility/
```

### 查看日志

```bash
# 查看最新日志
tail -f logs/daily-article.log
tail -f logs/cron.log
```

### 手动执行单个 Skill

```bash
# 测试 wechat-article-writer
claude --prompt "请用 wechat-article-writer skill 写一篇关于 AI 的短文"

# 测试 baoyu-post-to-wechat
claude --prompt "请用 baoyu-post-to-wechat skill 检查发布权限"
```

## 最佳实践

1. **先测试后发布**: 使用 `--draft-only` 模式先验证文章质量
2. **人工审核**: 建议每天早上检查草稿箱后再发布
3. **监控日志**: 定期检查日志，确保系统正常运行
4. **备份配置**: 定期备份 `.env` 和 `config.yaml`
5. **技能更新**: 定期检查 skill 更新，保持兼容性
