# 每日文章生成系统 - TOP3 热点话题版本

每日自动从各大平台聚合热点话题，按**时事**、**科技**、**民生**三个分类整理出讨论热度最高的 3 个话题，生成图文并茂的公众号文章并发布。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    本地 Cron (每天 6:00)                      │
│                  0 6 * * * python daily-article.py          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 热点聚合 (Hot Topic Aggregator)                     │
│  - 小红书热搜 (xiaohongshu MCP)                             │
│  - 微博热搜 (Web Scraping)                                  │
│  - 知乎热榜 (Web Scraping)                                  │
│  - Twitter/X 趋势 (WebSearch)                               │
│  - 输出：ranked_topics.json                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: 选择 TOP3 话题 (按分类)                              │
│  - 时事：政治、国际、社会、政策                              │
│  - 科技：AI、技术、互联网、创新                              │
│  - 民生：生活、健康、教育、就业                              │
│  - 输出：selected_topics.md                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: 资料搜集 (Parallel WebSearch)                       │
│  - 为每个话题并行搜索多个来源                               │
│  - 获取最新数据、图片、引用源                               │
│  - 输出：research_materials/research_summary.md             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: 文章撰写 (wechat-article-writer × 3)               │
│  - 为每个话题撰写一篇 1000-1500 字文章                        │
│  - 故事化开头，带情感色彩                                   │
│  - 结构：效果展示 → 问题描述 → 步骤教学 → 升华总结           │
│  - 输出：article/yyyy-MM-dd/{category}_{slug}.md            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: 格式化优化 (baoyu-format-markdown × 3)             │
│  - 添加 frontmatter (title, summary, cover)                 │
│  - 优化排版：段落、加粗、列表、表格                         │
│  - 输出：formatted/{category}_{slug}-formatted.md           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 6: 生成配图 (baoyu-image-gen × 3)                     │
│  - 使用 SEEDREAM 模型生成封面图 + 内文插图                    │
│  - 每个话题 3-5 张插图 + 1 张封面                              │
│  - 输出：article/yyyy-MM-dd/imgs/                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 7: 发布到微信 (baoyu-post-to-wechat × 3)              │
│  - 调用 API 方式发布（无需浏览器）                           │
│  - 自动设置评论开关、粉丝限制                               │
│  - 支持草稿模式或自动发布                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 8: 通知与日志                                          │
│  - 发送成功/失败通知（微信/邮件/钉钉）                      │
│  - 记录日志到 logs/daily-article.log                        │
│  - 失败时自动重试（最多 3 次）                                │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 安装依赖

```bash
cd daily-article-automation
pip install -r requirements.txt
```

### 2. 检查环境配置

确保以下环境变量已配置（在 `.baoyu-skills/.env` 中）：

```bash
# 微信公众号配置
WECHAT_APP_ID=wxf6a3acdaf4a9dd40
WECHAT_APP_SECRET=10fc656b53434df11e72443551386e6d

# SEEDREAM 图片生成配置
SEEDREAM_BASE_URL=https://worklink.yealink.com/llmproxy/v1
SEEDREAM_IMAGE_MODEL=doubao-seedream-4.0
ARK_API_KEY=your-ark-api-key
```

### 3. 配置文件

编辑 `config.yaml`：

```yaml
article:
  target_length: 1200        # 文章目标字数
  image_density: "balanced"  # 配图密度：minimal/balanced/rich
  auto_publish: false        # false=存草稿，true=自动发布
  categories:                # 分类配置
    - name: "时事"
      keywords: ["政治", "国际", ...]
    - name: "科技"
      keywords: ["AI", "科技", ...]
    - name: "民生"
      keywords: ["生活", "健康", ...]

hot_topics:
  top_per_category: 1        # 每个分类选取的话题数量
```

### 4. 测试运行

#### Dry Run 模式（不实际操作）

```bash
python daily-article.py --dry-run
```

#### 仅执行特定步骤

```bash
# 仅获取热点
python daily-article.py --step 1

# 仅选择话题
python daily-article.py --step 2

# 仅撰写文章
python daily-article.py --step 4
```

#### 端到端测试（生成草稿）

```bash
python daily-article.py --draft-only
```

### 5. 使用 Claude Code 增强版

```bash
./run-with-claude.sh
```

### 6. 配置 Cron 定时任务

```bash
# 编辑 crontab
crontab -e

# 添加以下行（根据实际路径调整）
0 6 * * * cd /cv5/linwh/ClaudeCode/claudecode_test/daily-article-automation && \
    /usr/bin/python3 daily-article.py >> logs/cron.log 2>&1
```

## 文件结构

```
daily-article-automation/
├── daily-article.py           # 主编排脚本
├── hot_topic_aggregator.py    # 热点聚合模块（支持分类）
├── config.yaml                # 配置文件
├── run-with-claude.sh         # Claude Code 增强版脚本
├── README.md                  # 本文档
├── article/                   # 文章输出目录
│   └── yyyy-MM-dd/
│       ├── ranked_topics.json      # 热点排行数据
│       ├── selected_topics.md      # 选定的 TOP3 话题
│       ├── research_materials/     # 研究材料
│       ├── *.md                    # 文章草稿
│       ├── formatted/              # 格式化后的文章
│       └── imgs/                   # 生成的图片
├── logs/
│   └── daily-article.log      # 运行日志
└── scripts/
    ├── claude-skill-invoker.py   # Claude Code Skill 调用器
    ├── notify-wechat.py          # 微信通知
    └── retry-handler.py          # 重试处理
```

## 分类规则

### 时事 (Current Events)
- 关键词：政治、国际、社会、政策、新闻、政府、外交、军事、法律、法规
- 示例：「外交部发布最新政策」「某地出台新规」

### 科技 (Technology)
- 关键词：AI、人工智能、科技、互联网、数码、创新、技术、软件、硬件、芯片
- 示例：「AI 绘画新玩法」「最新芯片技术突破」

### 民生 (Livelihood)
- 关键词：生活、健康、教育、住房、就业、工资、物价、医疗、养老、社保
- 示例：「医保政策新变化」「就业形势分析」

## 使用技能

本系统依赖以下 Claude Code 技能：

| 技能 | 用途 | 调用方式 |
|------|------|----------|
| `wechat-article-writer` | 文章撰写 | Step 4 |
| `baoyu-format-markdown` | 格式化优化 | Step 5 |
| `baoyu-image-gen` | 生成配图 | Step 6 |
| `baoyu-post-to-wechat` | 发布到微信 | Step 7 |
| `WebSearch` | 资料搜集 | Step 3 |
| `xiaohongshu MCP` | 小红书热点 | Step 1 |

## 热点聚合算法

综合得分 = 热度 × 时效性 × 公众号适配度 × 来源权重

| 来源 | 权重 |
|------|------|
| 小红书 | 0.3 |
| 微博 | 0.3 |
| 知乎 | 0.2 |
| Twitter/X | 0.2 |

公众号适配度 boost：
- 包含"教程"、"技巧"、"方法"等关键词 +10%
- 包含"指南"、"神器"、"效率"等关键词 +10%

## 错误处理

### 重试机制

- 最大重试次数：3 次
- 延迟策略：指数退避（60s → 120s → 240s）
- 最大延迟：600 秒

### 失败通知

支持三种通知方式：
- 微信模板消息
- 钉钉机器人
- 邮件

## 验收标准

- [ ] 每天 6:00 自动触发
- [ ] 获取至少 5 个热点话题
- [ ] 按分类输出 TOP3 话题（时事、科技、民生）
- [ ] 为每个话题生成 1000-1500 字文章
- [ ] 为每篇文章生成封面图 + 至少 2 张内文插图
- [ ] 成功发布到微信公众号（草稿箱）
- [ ] 失败时发送通知并重试

## 故障排查

### 热点 API 被封

解决：
1. 检查 IP 是否被封
2. 使用代理池
3. 降低请求频率

### 图片生成失败

解决：
1. 检查 API key 是否有效
2. 检查图片服务状态
3. 降级为无图文章

### 微信 API 调用失败

解决：
1. 检查 AppID/AppSecret 是否正确
2. 检查 access_token 是否过期
3. 切换到浏览器模式发布

### Claude Code 要求授权

解决：
1. 使用 `--allowed-tools` 参数预先授权工具
2. 在 `~/.claude/settings.json` 中设置 `permissions.defaultMode: "auto"`

## 安全注意事项

1. **凭证保护**: `.env` 文件不要提交到 git
2. **API 限流**: 避免短时间内大量请求
3. **内容审核**: 建议先存草稿，人工审核后再发布

## License

MIT
