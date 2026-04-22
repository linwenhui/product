# 每日文章生成系统 - 免手动授权配置指南

## 问题

每次运行 `run-with-claude.sh` 时，Claude Code 都会请求授权才能使用 WebSearch 等工具。

## 解决方案（已测试有效）

### 方案 1：使用 --allowed-tools 参数（推荐）

在脚本中使用 `--allowed-tools` 参数预先授权特定工具。这是最安全的方式。

修改后的 `run-with-claude.sh` 已使用此方式：

```bash
claude \
  --allowed-tools "WebSearch,Bash,Write,Read,Edit,Glob,Grep,BatchWrite" \
  "请完成以下任务..."
```

### 方案 2：用户级权限配置

编辑 `~/.claude/settings.json`，添加：

```json
{
  "permissions": {
    "defaultMode": "auto"
  }
}
```

这会让 Claude Code 在 auto 模式下自动决定何时请求授权。

### 方案 3：cron 定时任务配置（用于生产环境）

在 crontab 中使用：

```bash
# 每天 6:00 执行
0 6 * * * CLAUDE_PERMISSION_MODE=default \
    cd /path/to/daily-article-automation && \
    python3 daily-article.py >> logs/cron.log 2>&1
```

## 注意事项

### root 用户限制

`--dangerously-skip-permissions` 和 `bypassPermissions` 模式在 root 用户下无法使用，这是 Claude Code 的安全限制。

**解决方法**：
1. 使用 `--allowed-tools` 参数
2. 或在非 root 用户下运行

### 需要的工具列表

运行每日文章生成系统需要以下工具权限：

- `WebSearch` - 搜索热点话题和资料
- `Bash` - 执行 shell 命令
- `Write` - 写入文件
- `Read` - 读取文件
- `Edit` - 编辑文件
- `Glob` - 文件搜索
- `Grep` - 内容搜索
- `BatchWrite` - 批量写入

## 已更新的脚本

`run-with-claude.sh` 已更新为使用 `--allowed-tools` 参数，无需额外配置即可使用。

## 快速测试

```bash
cd daily-article-automation
./run-with-claude.sh
```

如果仍然看到授权请求，检查：
1. 用户级配置文件 `~/.claude/settings.json` 中 `permissions.defaultMode` 设置
2. 是否在 root 用户下运行（root 用户有限制）

## 故障排查

### 问题：仍然提示授权

**原因**：某些技能可能调用未授权的工具

**解决**：
```bash
# 添加更多工具到允许列表
claude --allowed-tools "WebSearch,Bash,Write,Read,Edit,Glob,Grep,BatchWrite,Agent" "..."
```

### 问题：cron 任务不执行

**原因**：环境变量未正确设置

**解决**：
```bash
# 在 crontab 中
0 6 * * * PATH=/usr/local/bin:/usr/bin:/bin \
    CLAUDE_CONFIG_DIR=/home/user/.claude \
    cd /path/to/daily-article-automation && \
    python3 daily-article.py
```

## 安全建议

1. **只授权必要的工具**：不要使用 `*` 或过宽的权限
2. **限制 Bash 命令**：使用 `Bash(git:*)` 限制特定命令
3. **定期审查日志**：检查工具调用记录
4. **生产环境使用沙箱**：在隔离环境中运行

## 完整示例

```bash
#!/bin/bash
# run-with-claude.sh (简化版)

set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

# 热点聚合和话题选择
python3 daily-article.py --step 1 --step 2 || true

# 读取话题
TOPIC=$(grep "^topic:" article/*/selected_topic.md 2>/dev/null | head -1 | cut -d: -f2 | tr -d ' ')

# 使用 --allowed-tools 运行 Claude Code
claude \
  --allowed-tools "WebSearch,Bash,Write,Read,Edit" \
  "请关于\"$TOPIC\"撰写一篇公众号文章..."
```

## 联系支持

- 项目日志：`logs/daily-article.log`
- Claude Code 文档：https://docs.anthropic.com/claude-code
