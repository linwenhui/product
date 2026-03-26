# TTS 音色配置指南

## OpenAI TTS 音色 (6 种)

| 音色 | 性别 | 特点 | 适用场景 |
|------|------|------|----------|
| `alloy` | 中性 | 平衡自然 | 通用场景 |
| `echo` | 男声 | 沉稳有力 | 知识分享、新闻播报 |
| `fable` | 男声 | 温暖叙事 | 故事讲述、情感内容 |
| `onyx` | 男声 | 深沉磁性 | 品牌宣传、专业内容 |
| `nova` | 女声 | 清脆活力 | 轻松内容、产品介绍 |
| `shimmer` | 女声 | 温柔甜美 | 亲和力内容、客服 |

### 配置示例

```yaml
audio:
  provider: "openai_tts"
  tts_voice: "echo"  # 男声
```

## Azure TTS 中文音色

### 女声

| 音色 | 特点 | 适用场景 |
|------|------|----------|
| `zh-CN-XiaoxiaoNeural` | 温柔知性 | 情感内容、有声书 |
| `zh-CN-XiaoyiNeural` | 青春活力 | 轻松内容、广告 |
| `zh-CN-XiaohanNeural` | 温暖亲切 | 客服、教育 |
| `zh-CN-XiaomengNeural` | 甜美可爱 | 儿童内容 |
| `zh-CN-XiaomoNeural` | 成熟稳重 | 正式场合 |
| `zh-CN-XiaoqiuNeural` | 专业干练 | 商务内容 |
| `zh-CN-XiaoxuanNeural` | 温柔平和 | 舒缓内容 |
| `zh-CN-XiaoyanNeural` | 清晰明亮 | 新闻播报 |
| `zh-CN-XiaochenNeural` | 热情活力 | 营销内容 |
| `zh-CN-XiaoruiNeural` | 沉稳大气 | 正式场合 |

### 男声

| 音色 | 特点 | 适用场景 |
|------|------|----------|
| `zh-CN-YunxiNeural` | 沉稳有力 | 知识分享 (默认) |
| `zh-CN-YunjianNeural` | 运动活力 | 体育内容 |
| `zh-CN-YunhaoNeural` | 温暖亲切 | 教育内容 |
| `zh-CN-YunzeNeural` | 成熟稳重 | 商务场合 |
| `zh-CN-YunxiaNeural` | 青春阳光 | 轻松内容 |
| `zh-CN-YunyangNeural` | 专业清晰 | 新闻播报 |

### 配置示例

```yaml
audio:
  provider: "azure"
  voice: "zh-CN-XiaoxiaoNeural"  # 女声
  # voice: "zh-CN-YunxiNeural"  # 男声
```

## gTTS (Google TTS)

gTTS 目前仅支持默认音色，无法指定具体声音。

```yaml
audio:
  provider: "gtts"  # 自动使用 Google TTS
```

## 快速选择

**想要男声：**
```yaml
audio:
  tts_voice: "echo"  # OpenAI TTS (沉稳男声)
  # 或
  voice: "zh-CN-YunxiNeural"  # Azure TTS (沉稳男声)
```

**想要女声：**
```yaml
audio:
  tts_voice: "nova"  # OpenAI TTS (活力女声)
  # 或
  voice: "zh-CN-XiaoxiaoNeural"  # Azure TTS (温柔女声)
```

## 试听建议

由于不同 TTS 服务的音色不同，建议：

1. 先用短文本测试（如"你好，这是一个测试"）
2. 选择最符合你内容风格的音色
3. 固定下来作为默认配置

## 语速和音量调节

```yaml
audio:
  rate: 1.0    # 语速：0.5(慢) - 2.0(快)
  volume: 1.0  # 音量：0.0(静音) - 2.0(最大)
```

- 语速建议：0.9-1.2 之间
- 音量建议：0.8-1.2 之间
