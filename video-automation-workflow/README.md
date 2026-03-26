# 视频自动化工作流

> 从创意到发布，10 分钟完成视频制作

## 快速开始

### 1. 安装依赖

```bash
cd video-automation-workflow

# 使用 uv (推荐)
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env`：

```bash
cp .env.example .env
```

#### 方式 A：使用当前 ClaudeCode 的 API 配置 (推荐)

如果你在当前环境中使用 Claude Code，它已经配置了 API 代理，可以直接使用：

```bash
# .env 文件中设置
ANTHROPIC_BASE_URL=https://worklink.yealink.com/llmproxy/anthropic
CLAUDE_MODEL=claude-sonnet-4-20250514
```

不需要设置 `CLAUDE_API_KEY`，代理模式会自动处理认证。

#### 方式 B：使用你自己的 Claude API Key

```bash
CLAUDE_API_KEY=sk-ant-api03-...
```

#### 方式 C：使用其他服务商

```bash
# 豆包 Seedream (画面生成)
ARK_API_KEY=
SEEDREAM_BASE_URL=
SEEDREAM_IMAGE_MODEL=doubao-seedream-4.0

# Azure TTS (配音) - 需要有效的 API Key
AZURE_API_KEY=...
AZURE_REGION=eastasia
```

**注意**：TTS 代理（`OPENAI_BASE_URL`）需要浏览器 Cookie 认证，目前建议使用 gTTS 作为备用方案。

### 3. 运行工作流

```bash
# 测试配置
python3 test_config.py

# 测试 Claude API 连接
python3 test_claude.py

# 测试完整工作流（推荐先测试）
python3 test_workflow.py

# 运行完整工作流
python3 run_workflow.py --topic "时间管理技巧"

# 指定标题和描述
python3 run_workflow.py --topic "AI 工具" --title "我的第一个 AI 视频" --description "详细描述"

# 使用预设音色配置
python3 run_workflow.py --topic "知识分享" --config config/male-voice.yaml   # 男声
python3 run_workflow.py --topic "情感故事" --config config/female-voice.yaml # 女声
```

**输出目录：**
- `output/script.md` - 生成的脚本
- `output/scene_*.png` - 生成的画面
- `output/voiceover.mp3` - 生成的配音
- `output/output.mp4` - 最终视频

## 项目结构

```
video-automation-workflow/
├── config/
│   ├── config.yaml         # 主配置文件
│   ├── kimi.yaml           # Kimi 配置示例
│   └── .env.example        # 环境变量示例
├── scripts/
│   └── script_template.txt # 脚本模板
├── assets/
│   └── bgm.mp3             # 背景音乐 (可选)
├── output/                  # 输出目录
│   ├── script.md           # 生成的脚本
│   ├── scene_001.png       # 生成的画面
│   ├── voiceover.mp3       # 生成的配音
│   └── output.mp4          # 最终视频
├── tmp/                     # 临时文件
├── run_workflow.py         # 主脚本
├── requirements.txt        # Python 依赖
└── README.md               # 本文档
```

## 工作流说明

### Step 1: 脚本生成

使用 AI 大模型生成短视频脚本：

**支持平台：**
- Claude (推荐)
- OpenAI GPT
- Kimi 月之暗面

**配置方式：**
```yaml
script:
  provider: "claude"
  api_key: "${CLAUDE_API_KEY}"
  template: "scripts/script_template.txt"
```

### Step 2: 画面生成

使用 AI 绘画生成视频画面：

**支持平台：**
- 豆包 Seedream (推荐，通过火山引擎 ARK)
- FLUX (通过 inference.sh)
- 通义千问 DashScope

**配置方式：**
```yaml
visuals:
  provider: "seedream"
  api_key: "${ARK_API_KEY}"
  style: "cartoon style, bright colors"
  resolution: "1080x1920"
```

### Step 3.5: 字幕生成（可选）

自动生成 SRT 字幕并嵌入到视频中：

**配置方式：**
```yaml
subtitles:
  enabled: true  # 是否启用字幕
  font: "SimHei"      # 字体（需要系统安装）
  size: 24            # 字号
  color: "&HFFFFFF"   # 颜色（白色）
  border_color: "&H000000"  # 边框颜色（黑色）
  border_size: 2      # 边框大小
  margin_v: 20        # 垂直边距
```

**支持字体：**
- Linux: `SimHei`, `WenQuanYi Micro Hei`, `Noto Sans CJK SC`
- macOS: `PingFang SC`, `Heiti SC`
- Windows: `SimHei`, `Microsoft YaHei`

**输出文件：**
- `tmp/subtitles.srt` - SRT 字幕文件
- 视频中嵌入硬编码字幕

### Step 4: 视频合成

**支持平台：**
- OpenAI TTS (推荐，6 种音色可选)
- Azure Cognitive Services (中文自然)
- gTTS (Google TTS，备用方案)

**音色选择：**

| OpenAI TTS | 性别 | 特点 | Azure TTS 备用 |
|------------|------|------|---------------|
| `echo` | 男声 | 沉稳有力 | zh-CN-YunxiNeural |
| `onyx` | 男声 | 深沉磁性 | zh-CN-YunzeNeural |
| `fable` | 男声 | 温暖叙事 | zh-CN-YunhaoNeural |
| `nova` | 女声 | 清脆活力 | zh-CN-XiaoxiaoNeural |
| `shimmer` | 女声 | 温柔甜美 | zh-CN-XiaomengNeural |
| `alloy` | 中性 | 平衡自然 | zh-CN-XiaohanNeural |

**配置方式：**
```yaml
audio:
  provider: "openai_tts"
  tts_voice: "echo"  # 男声：echo/onyx/fable, 女声：nova/shimmer
  # 或
  provider: "azure"
  voice: "zh-CN-YunxiNeural"  # 男声
  # voice: "zh-CN-XiaoxiaoNeural"  # 女声
```

**预设配置：**
- `config/male-voice.yaml` - 男声配置（沉稳有力）
- `config/female-voice.yaml` - 女声配置（温柔知性）

详见：[config/TTS_VOICES.md](config/TTS_VOICES.md)
- 本地 pyttsx3 (备用方案)

**配置方式：**
```yaml
audio:
  provider: "azure"
  api_key: "${AZURE_API_KEY}"
  voice: "zh-CN-YunxiNeural"
  bgm:
    enabled: true
    file: "assets/bgm.mp3"
    volume: 0.3
```

### Step 4: 视频合成

使用 FFmpeg 合成视频：

- 自动拼接画面
- 对齐配音
- 添加转场效果
- 混合背景音乐

**配置方式：**
```yaml
export:
  resolution: "1080x1920"
  fps: 30
  crf: 23
  codec: "libx264"
```

### Step 5: 自动发布 (可选)

发布到多个平台：

- 抖音
- B 站
- 视频号

**配置方式：**
```yaml
publish:
  enabled: false
  platforms:
    - "douyin"
    - "bilibili"
  schedule: "18:00"
```

## 配置说明

### config.yaml 完整示例

```yaml
# 脚本生成
script:
  provider: "claude"
  api_key: "${CLAUDE_API_KEY}"
  template: "scripts/script_template.txt"
  default_duration: 60

# 画面生成
visuals:
  provider: "seedream"
  api_key: "${ARK_API_KEY}"
  style: "cartoon style, bright colors, clean composition"
  images_per_scene: 1
  resolution: "1080x1920"

# 配音
audio:
  provider: "azure"
  api_key: "${AZURE_API_KEY}"
  voice: "zh-CN-YunxiNeural"
  volume: 1.0
  rate: 1.0
  bgm:
    enabled: true
    file: "assets/bgm.mp3"
    volume: 0.3

# 输出
export:
  resolution: "1080x1920"
  fps: 30
  codec: "libx264"
  crf: 23

# 发布
publish:
  enabled: false
  platforms:
    - "douyin"
    - "bilibili"
    - "video_account"
  schedule: "18:00"
  default_tags:
    - "AI 视频"
    - "自动化"

# 高级
advanced:
  working_dir: "./output"
  temp_dir: "./tmp"
  log_level: "info"
  retry_count: 2
  keep_intermediates: false
```

## API Key 获取指南

### Claude API
1. 访问 https://console.anthropic.com/
2. 注册账号并绑定支付方式
3. 创建 API Key

### 豆包 Seedream (火山引擎 ARK)
1. 访问 https://console.volcengine.com/ark
2. 注册火山引擎账号
3. 创建应用并获取 API Key
4. 使用 `doubao-seedream-4-0` 模型

### Azure Cognitive Services
1. 访问 https://portal.azure.com/
2. 创建 Cognitive Services 资源
3. 选择 Speech 服务
4. 获取 Key 和 Region

### OpenAI API
1. 访问 https://platform.openai.com/
2. 注册账号并绑定支付方式
3. 创建 API Key

## 常见问题

### Q: 如何修改视频风格？

编辑 `config/config.yaml` 中的 `visuals.style` 字段：

```yaml
visuals:
  style: "realistic, cinematic lighting"  # 写实电影感
  # 或
  style: "minimalist, flat design"  # 极简扁平
  # 或
  style: "anime style, vibrant colors"  # 动漫风格
```

### Q: 如何批量生成？

创建主题列表文件，然后循环调用：

```bash
# topics.txt
时间管理技巧
AI 工具教程
效率提升方法

# 批量运行
while read topic; do
  python run_workflow.py --topic "$topic"
done < topics.txt
```

### Q: 如何添加自己的背景音乐？

1. 将音乐文件放到 `assets/bgm.mp3`
2. 修改配置：
```yaml
audio:
  bgm:
    enabled: true
    file: "assets/my_music.mp3"
    volume: 0.3
```

### Q: 视频合成失败怎么办？

检查 FFmpeg 是否安装：
```bash
ffmpeg -version
```

如未安装，请安装：
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
apt-get install ffmpeg
```

### Q: 如何调整视频分辨率？

修改配置：
```yaml
export:
  resolution: "1920x1080"  # 横屏
  # 或
  resolution: "1080x1920"  # 竖屏
  # 或
  resolution: "1080x1080"  # 正方形
```

## 依赖要求

- Python 3.8+
- FFmpeg (视频合成)
- FFprobe (音频时长检测)

## 许可证

MIT License
