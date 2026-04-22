# 部署检查清单 (CHECKLIST.md)

## 部署前检查

### 环境准备

- [ ] Python 3.10+ 已安装
- [ ] pip3 已安装
- [ ] Node.js 已安装（用于 Claude Code CLI）
- [ ] Claude Code 已安装 (`npm install -g @anthropics/claude-code`)

### 配置文件

- [ ] `.baoyu-skills/.env` 存在且包含有效凭证
- [ ] `config.yaml` 已创建并配置正确
- [ ] `requirements.txt` 依赖已安装 (`make install`)

### 环境变量检查

运行以下命令检查：

```bash
make check-env
```

 expected output:
```
检查环境变量...
✓ .baoyu-skills/.env 存在
✓ WECHAT_APP_ID 已配置
✓ WECHAT_APP_SECRET 已配置
```

### 功能测试

#### 1. Dry Run 测试

```bash
make test
```

期望结果：
- [ ] 无 Python 错误
- [ ] 成功获取热点话题
- [ ] 成功创建选题文件
- [ ] 成功创建文章目录结构

#### 2. 热点聚合测试

```bash
make step-1
```

期望结果：
- [ ] 获取到至少 4 个热点
- [ ] 热点按得分排序
- [ ] 保存到 `ranked_topics.json`

#### 3. 完整流程测试

```bash
make draft-only
```

期望结果：
- [ ] 生成文章 Markdown 文件
- [ ] 生成格式化后的文件
- [ ] 创建 imgs 目录

### Cron 配置

#### 安装定时任务

```bash
make setup-cron
```

期望结果：
- [ ] Cron 任务安装成功
- [ ] 日志文件创建成功

#### 验证 Cron

```bash
# 查看已安装的 cron
crontab -l

# 应该看到类似：
0 6 * * * cd /cv5/linwh/ClaudeCode/claudecode_test/daily-article-automation && python3 daily-article.py >> logs/cron.log 2>&1
```

### 通知配置

#### 微信通知

- [ ] 公众号已配置模板消息
- [ ] 接收者用户 ID 已配置

#### 钉钉通知（可选）

- [ ] 钉钉机器人已创建
- [ ] Webhook URL 已配置到环境变量

```bash
export DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=..."
```

#### 邮件通知（可选）

- [ ] SMTP 服务器配置正确
- [ ] 邮件账号密码已配置

### 监控与日志

#### 日志检查

```bash
# 查看最新日志
tail -100 logs/daily-article.log

# 查看 cron 日志
tail -100 logs/cron.log
```

确认：
- [ ] 日志正常输出，无 ERROR 级别错误
- [ ] 每日文章生成时间符合预期

#### 告警配置

- [ ] 失败通知已测试
- [ ] 接收人能正常收到通知

## 生产环境部署

### 服务器要求

- [ ] 稳定的网络连接
- [ ] 24 小时运行
- [ ] 足够的磁盘空间（至少 1GB）
- [ ] 已配置防火墙规则

### 备份策略

- [ ] 每日备份 `.env` 文件
- [ ] 每周备份文章目录
- [ ] 每月备份配置文件

### 监控告警

- [ ] 服务器监控已配置
- [ ] 进程守护（systemd/supervisor）
- [ ] 磁盘空间监控

### 安全加固

- [ ] `.env` 文件权限设置为 600
- [ ] 限制日志文件访问权限
- [ ] 定期更新依赖包

## 验收标准

### 功能验收

- [ ] 每天 6:00 自动触发
- [ ] 获取至少 5 个热点话题
- [ ] 生成 1000-1500 字文章
- [ ] 生成封面图 + 至少 2 张内文插图
- [ ] 成功发布到微信公众号（或存为草稿）
- [ ] 失败时发送通知并重试

### 性能验收

- [ ] 单次运行时间 < 10 分钟
- [ ] API 调用成功率 > 95%
- [ ] 系统可用性 > 99%

### 质量验收

- [ ] 文章内容连贯、无明显错误
- [ ] 配图质量符合要求
- [ ] 排版美观、易于阅读

## 问题排查

### 常见问题

#### 1. Python 依赖缺失

```bash
make install
```

#### 2. 配置文件不存在

```bash
cp config.example.yaml config.yaml
```

#### 3. 环境变量缺失

编辑 `.baoyu-skills/.env`，确保包含：

```bash
WECHAT_APP_ID=...
WECHAT_APP_SECRET=...
```

#### 4. Cron 未执行

```bash
# 检查 cron 服务
systemctl status cron

# 查看 cron 日志
grep CRON /var/log/syslog | tail -20
```

#### 5. 文章发布失败

- 检查 API 凭证是否有效
- 检查网络连接
- 切换到 browser 模式重试

## 维护计划

### 每日

- [ ] 检查日志，确认正常运行
- [ ] 查看生成的文章质量

### 每周

- [ ] 分析热点话题准确性
- [ ] 调整评分算法参数

### 每月

- [ ] 更新依赖包
- [ ] 审查安全设置
- [ ] 备份重要数据

### 每季度

- [ ] 评估系统性能
- [ ] 优化热点源
- [ ] 更新文档

## 联系方式

遇到问题请查看：
- README.md - 项目说明
- INTEGRATION.md - 集成指南
- logs/daily-article.log - 运行日志
