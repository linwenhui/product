#!/usr/bin/env python3
"""
Video Automation Workflow - Main Script
视频自动化工作流主脚本

Usage:
    python run_workflow.py --topic "你的视频主题"
    python run_workflow.py --config config/config.yaml --topic "你的主题"
"""

import os
import sys
import json
import time
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 检查依赖
try:
    import yaml
    import click
    import requests
    from openai import OpenAI
except ImportError as e:
    print(f"缺少依赖：{e}")
    print("请先安装：pip install pyyaml click requests python-dotenv openai")
    sys.exit(1)


class ScriptGenerator:
    """脚本生成器 - 使用 Claude/OpenAI 生成短视频脚本"""

    # 默认模型配置
    DEFAULT_MODELS = {
        "claude": "qwen3.5-plus",
        "openai": "gpt-4o",
        "kimi": "moonshot-v1-8k",
    }

    def __init__(self, config: dict):
        self.config = config
        self.provider = config.get("provider", "claude")
        self.base_url = config.get("base_url")
        self.model = config.get("model")
        self.api_key = self._get_api_key()
        self.client = self._create_client()

    def _get_api_key(self) -> str:
        """获取 API Key"""
        provider_map = {
            "claude": ["CLAUDE_API_KEY", "ANTHROPIC_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "kimi": ["KIMI_API_KEY"],
        }
        env_vars = provider_map.get(self.provider, ["CLAUDE_API_KEY"])

        # 尝试多个环境变量
        api_key = ""
        for env_var in env_vars:
            api_key = os.getenv(env_var)
            if api_key:
                break

        # 如果仍为空，尝试配置文件
        if not api_key:
            config_key = self.config.get("api_key", "")
            if config_key.startswith("${") and config_key.endswith("}"):
                var_name = config_key[2:-1]
                api_key = os.getenv(var_name, "")
            else:
                api_key = config_key

        if not api_key:
            # Claude 特殊处理：如果没有 API Key 但有 base_url，可能是代理模式
            if self.provider == "claude" and self.base_url:
                print("  提示：使用代理 URL 模式，可能不需要 API Key")
                return "dummy-key-for-proxy"
            raise ValueError(f"缺少 API Key，请设置环境变量 {env_vars[0]}")
        return api_key

    def _get_base_url(self) -> str:
        """获取 API Base URL"""
        # 优先级：config > 环境变量 > 默认值
        if self.base_url:
            return self.base_url

        if self.provider == "claude":
            # 尝试 Anthropic 代理配置
            proxy_url = os.getenv("ANTHROPIC_BASE_URL")
            if proxy_url:
                return proxy_url
            # 尝试 ClaudeCode 配置
            proxy_url = os.getenv("CLAUDE_API_BASE_URL")
            if proxy_url:
                return proxy_url
            return None  # 使用官方 API
        elif self.provider == "kimi":
            return os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
        return None

    def _get_model(self) -> str:
        """获取模型名称"""
        if self.model:
            return self.model

        # 尝试环境变量
        model_env = os.getenv(f"{self.provider.upper()}_MODEL")
        if model_env:
            return model_env

        # 返回默认模型
        return self.DEFAULT_MODELS.get(self.provider, "gpt-4o")

    def _create_client(self):
        """创建 API 客户端"""
        base_url = self._get_base_url()
        model = self._get_model()

        if self.provider == "claude":
            from anthropic import Anthropic
            kwargs = {"api_key": self.api_key}
            if base_url:
                kwargs["base_url"] = base_url
            print(f"  Claude 配置：model={model}, base_url={base_url or 'default'}")
            return Anthropic(**kwargs)
        elif self.provider == "openai":
            kwargs = {"api_key": self.api_key}
            if base_url:
                kwargs["base_url"] = base_url
            return OpenAI(**kwargs)
        elif self.provider == "kimi":
            return OpenAI(api_key=self.api_key, base_url="https://api.moonshot.cn/v1")
        else:
            # 默认使用 OpenAI 兼容接口
            kwargs = {"api_key": self.api_key}
            if base_url:
                kwargs["base_url"] = base_url
            return OpenAI(**kwargs)

    def generate(self, topic: str, template_path: Path) -> str:
        """生成脚本"""
        # 读取模板
        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在：{template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # 构建提示词
        prompt = template.replace("{TOPIC}", topic)
        prompt = prompt.replace("{AUDIENCE}", "普通大众")
        prompt = prompt.replace("{STYLE}", "知识分享")

        print(f"使用 {self.provider} 生成脚本...")

        if self.provider == "claude":
            model = self._get_model()
            response = self.client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            script = response.content[0].text
        else:
            model = self._get_model()
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096
            )
            script = response.choices[0].message.content

        return script

    def generate(self, topic: str, template_path: Path) -> str:
        """生成脚本"""
        # 读取模板
        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在：{template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # 构建提示词
        prompt = template.replace("{TOPIC}", topic)
        prompt = prompt.replace("{AUDIENCE}", "普通大众")
        prompt = prompt.replace("{STYLE}", "知识分享")

        print(f"使用 {self.provider} 生成脚本...")

        if self.provider == "claude":
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            script = response.content[0].text
        else:
            response = self.client.chat.completions.create(
                model="gpt-4o" if self.provider == "openai" else "moonshot-v1-8k",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096
            )
            script = response.choices[0].message.content

        return script


class VisualGenerator:
    """画面生成器 - 使用 AI 绘画生成视频画面"""

    def __init__(self, config: dict, working_dir: Path, temp_dir: Path):
        self.config = config
        self.provider = config.get("provider", "seedream")
        self.style = config.get("style", "cartoon style, bright colors")
        self.resolution = config.get("resolution", "1920x1080")
        self.working_dir = working_dir
        self.temp_dir = temp_dir
        self.api_key = self._get_api_key()

    def _get_api_key(self) -> str:
        """获取 API Key"""
        api_key = os.getenv("ARK_API_KEY") or os.getenv("SEEDREAM_API_KEY") or self.config.get("api_key", "")

        # 处理 ${VAR} 格式
        if api_key.startswith("${") and api_key.endswith("}"):
            var_name = api_key[2:-1]
            api_key = os.getenv(var_name, "")

        if not api_key:
            raise ValueError("缺少 ARK_API_KEY 或 SEEDREAM_API_KEY")
        return api_key

    def _parse_scenes(self, script: str) -> list:
        """从脚本中提取画面描述"""
        scenes = []
        lines = script.split("\n")
        for i, line in enumerate(lines):
            if "画面描述：" in line or "画面描述:" in line:
                # 使用正则分割（支持中文和英文冒号）
                parts = re.split(r'[:：]', line, maxsplit=1)
                if len(parts) >= 2:
                    desc = parts[1].strip()
                    # 移除可能的 markdown 代码块标记
                    desc = desc.strip('`"\'')
                    if desc and not desc.startswith("【") and not desc.startswith("["):
                        scenes.append(desc)
        return scenes

    def _build_prompt(self, scene_desc: str) -> str:
        """构建绘画提示词"""
        base_prompt = f"{scene_desc}, {self.style}, high quality, detailed"
        return base_prompt

    def generate_batch(self, script: str) -> list:
        """批量生成画面"""
        scenes = self._parse_scenes(script)
        if not scenes:
            print("警告：未从脚本中提取到画面描述，使用默认场景")
            scenes = ["一个简洁的封面画面，扁平化设计"]

        print(f"检测到 {len(scenes)} 个场景，开始生成画面...")

        output_files = []
        for i, scene in enumerate(scenes, 1):
            print(f"\n生成场景 {i}/{len(scenes)}: {scene[:50]}...")
            prompt = self._build_prompt(scene)

            output_file = self._generate_image(prompt, f"scene_{i:03d}")
            if output_file:
                output_files.append(str(output_file))

        return output_files

    def _generate_image(self, prompt: str, filename: str) -> Path:
        """生成单张图片"""
        if self.provider == "seedream":
            return self._generate_seedream(prompt, filename)
        elif self.provider == "flux":
            return self._generate_flux(prompt, filename)
        elif self.provider == "dashscope":
            return self._generate_dashscope(prompt, filename)
        else:
            return self._generate_seedream(prompt, filename)

    def _generate_seedream(self, prompt: str, filename: str) -> Path:
        """使用豆包 Seedream 生成图片"""
        base_url = os.getenv("SEEDREAM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        model = os.getenv("SEEDREAM_IMAGE_MODEL", "doubao-seedream-4-0")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 解析分辨率
        width, height = 1920, 1080
        if "x" in self.resolution:
            width, height = map(int, self.resolution.split("x"))

        payload = {
            "model": model,
            "prompt": prompt,
            "size": f"{width}x{height}",
            "stream": False
        }

        response = requests.post(
            f"{base_url}/images/generations",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        image_url = result["data"][0]["url"]

        # 下载图片
        img_response = requests.get(image_url, timeout=30)
        output_path = self.working_dir / f"{filename}.png"
        with open(output_path, "wb") as f:
            f.write(img_response.content)

        print(f"  → {output_path}")
        return output_path

    def _generate_flux(self, prompt: str, filename: str) -> Path:
        """使用 FLUX 生成图片"""
        # 使用 inference.sh CLI
        try:
            cmd = [
                "infsh", "app", "run", "falai/flux-dev-lora",
                "--input", json.dumps({"prompt": prompt})
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # 解析输出获取图片 URL
            # 简化处理，实际需要根据 infsh 输出格式解析
            print(f"  FLUX 生成完成 → {self.working_dir / f'{filename}.png'}")
            return self.working_dir / f"{filename}.png"
        except Exception as e:
            print(f"  FLUX 生成失败：{e}")
            return None

    def _generate_dashscope(self, prompt: str, filename: str) -> Path:
        """使用通义千问生成图片"""
        api_key = os.getenv("DASHSCOPE_API_KEY", self.api_key)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "wanx2.1-t2i-turbo",
            "input": {"prompt": prompt},
            "parameters": {
                "size": "1920*1080",
                "n": 1
            }
        }

        # 提交任务
        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers=headers,
            json=payload,
            timeout=60
        )
        result = response.json()

        # 获取图片 URL
        image_url = result["output"]["results"][0]["url"]

        # 下载图片
        img_response = requests.get(image_url, timeout=30)
        output_path = self.working_dir / f"{filename}.png"
        with open(output_path, "wb") as f:
            f.write(img_response.content)

        print(f"  → {output_path}")
        return output_path


class AudioGenerator:
    """配音生成器 - 使用 OpenAI TTS / Azure TTS 生成语音"""

    def __init__(self, config: dict, working_dir: Path, temp_dir: Path,
                 resolution: str = "1920x1080", subtitle_config: dict = None):
        self.config = config
        self.voice = config.get("voice", "zh-CN-YunxiNeural")
        self.rate = config.get("rate", 1.0)
        self.volume = config.get("volume", 1.0)
        self.bgm_config = config.get("bgm", {})
        self.working_dir = working_dir
        self.temp_dir = temp_dir

        # 分辨率和字幕配置（用于动态计算字幕最大字符数）
        self.resolution = resolution
        self.subtitle_config = subtitle_config or {}
        self.subtitle_font = self.subtitle_config.get("font", "SimHei")
        self.subtitle_size = self.subtitle_config.get("size", 8)
        self.subtitle_margin_v = self.subtitle_config.get("margin_v", 50)

        # 动态计算每行最大字符数
        self.max_chars_per_line = self._calculate_max_chars()

        # TTS 提供商选择：openai_tts 或 azure
        self.provider = config.get("provider", "openai_tts")

        # OpenAI TTS 配置
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or config.get("api_key", "")
        self.openai_tts_model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        self.openai_tts_voice = config.get("tts_voice", "alloy")

        # Azure TTS 配置
        self.azure_api_key = os.getenv("AZURE_API_KEY")
        self.azure_region = os.getenv("AZURE_REGION", "eastasia")

        # 处理 ${VAR} 格式
        if self.openai_api_key.startswith("${") and self.openai_api_key.endswith("}"):
            var_name = self.openai_api_key[2:-1]
            self.openai_api_key = os.getenv(var_name, "")
        if self.azure_api_key and self.azure_api_key.startswith("${") and self.azure_api_key.endswith("}"):
            var_name = self.azure_api_key[2:-1]
            self.azure_api_key = os.getenv(var_name, "")

    def _calculate_max_chars(self) -> int:
        """根据图像宽度和字体大小计算每行最大字符数"""
        # 解析分辨率
        try:
            width, height = self.resolution.split('x')
            video_width = int(width)
        except:
            video_width = 1920

        # 字体大小
        font_size = self.subtitle_size

        # 中文字体大致是正方形，每个字宽度约等于字体大小
        # 考虑左右边距（各 50 像素）和安全边距
        safe_margin = 50  # 左右安全边距
        available_width = video_width - 2 * safe_margin

        # 计算最大字符数（向下取整，保留 1 像素余量）
        max_chars = int(available_width / font_size)

        # 限制范围：最少 10 字，最多 25 字
        return max(10, min(25, max_chars))

    def _parse_dialogue(self, script: str) -> list:
        """从脚本中提取台词"""
        dialogues = []
        lines = script.split("\n")
        for line in lines:
            if "台词：" in line:
                dialogue = line.replace("台词：", "").strip()
                if dialogue:
                    dialogues.append(dialogue)
        return dialogues

    def _parse_script_with_scenes(self, script: str) -> list:
        """从脚本中提取场景和台词（用于生成字幕）"""
        scenes = []
        lines = script.split("\n")
        current_scene = {}

        for line in lines:
            line = line.strip()
            if line.startswith("【") and "】" in line:
                # 新场景开始
                # 跳过【标题】行，它不是场景
                if "标题" in line:
                    continue
                if current_scene:
                    scenes.append(current_scene)
                current_scene = {"title": line.strip("[]")}
            elif line.startswith("台词：") or line.startswith("台词:"):
                # 使用正则分割支持中文和英文冒号
                if ":" in line or "：" in line:
                    parts = re.split(r'[:：]', line, maxsplit=1)
                    current_scene["dialogue"] = parts[1].strip() if len(parts) >= 2 else line[3:].strip()
                else:
                    current_scene["dialogue"] = line[3:].strip()
            elif line.startswith("画面描述：") or line.startswith("画面描述:"):
                # 使用正则分割支持中文和英文冒号
                if ":" in line or "：" in line:
                    parts = re.split(r'[:：]', line, maxsplit=1)
                    current_scene["visual"] = parts[1].strip() if len(parts) >= 2 else line[4:].strip()
                else:
                    current_scene["visual"] = line[4:].strip()

        if current_scene and current_scene.get("dialogue"):
            scenes.append(current_scene)

        return scenes

    def _split_dialogue(self, dialogue: str) -> list:
        """将长台词按标点符号分割成多个句子

        只按标点分割，保持句子完整性
        """
        # 支持中文和英文标点：， 。 ？ ！ , . ? ! ； ; ： :
        chinese_punct = '，。？！；：、'
        english_punct = ',.!?;:'
        all_punct = chinese_punct + english_punct

        # 构建正则表达式字符类
        punct_pattern = f'([{re.escape(all_punct)}])'
        parts = re.split(punct_pattern, dialogue)

        sentences = []
        current = ""
        for part in parts:
            if not part:
                continue
            # 判断是否为标点
            if part in all_punct:
                current += part
                sentences.append(current)
                current = ""
            else:
                current = part
        if current:
            sentences.append(current)

        return sentences if sentences else [dialogue]

    def generate_srt(self, script: str, audio_duration: float, output_path: Path) -> str:
        """生成 SRT 字幕文件 - 按标点分割后的句子为单位"""
        scenes = self._parse_script_with_scenes(script)

        if not scenes:
            print("  警告：无法从脚本中提取台词生成字幕")
            return ""

        # 提取所有台词并按标点分割成句子
        all_sentences = []
        for scene in scenes:
            dialogue = scene.get("dialogue", "")
            if dialogue:
                # 按标点分割成多个句子
                sentences = self._split_dialogue(dialogue)
                for sent in sentences:
                    all_sentences.append({
                        'text': sent,
                        'chars': len(sent)
                    })

        # 计算总字符数（用于时长分配）
        total_chars = sum(s['chars'] for s in all_sentences)

        print(f"  检测到 {len(all_sentences)} 个句子（按标点分割），根据 {self.resolution} 分辨率计算时长...")

        # 生成 SRT 字幕
        srt_content = ""
        current_time = 0.0
        subtitle_index = 1

        for sent_data in all_sentences:
            text = sent_data['text']
            chars = sent_data['chars']

            # 按字符比例分配时长
            if total_chars > 0:
                duration = audio_duration * (chars / total_chars)
            else:
                duration = audio_duration / len(all_sentences)

            start_time = current_time
            end_time = current_time + duration

            # 转换为 SRT 时间格式
            start_str = self._format_srt_time(start_time)
            end_str = self._format_srt_time(end_time)

            # 添加字幕条目
            srt_content += f"{subtitle_index}\n"
            srt_content += f"{start_str} --> {end_str}\n"
            srt_content += f"{text}\n\n"

            subtitle_index += 1
            current_time = end_time

        # 保存 SRT 文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        print(f"  → {output_path}")
        return str(output_path)

    def generate_scene_durations(self, script: str, audio_duration: float, num_images: int) -> list:
        """生成每个场景的时长分配（用于图片切换同步）

        返回：每张场景图片应该显示的时长列表
        """
        scenes = self._parse_script_with_scenes(script)

        if not scenes:
            print("  警告：无法从脚本中提取场景")
            return [audio_duration / num_images] * num_images

        # 提取所有台词并计算每个场景的字符数
        scene_chars = []
        for scene in scenes:
            dialogue = scene.get("dialogue", "")
            chars = len(dialogue) if dialogue else 0
            scene_chars.append(chars)

        # 计算总字符数
        total_chars = sum(scene_chars)

        # 按字符比例分配音频时长到每个场景
        scene_durations = []
        for chars in scene_chars:
            if total_chars > 0:
                duration = audio_duration * (chars / total_chars)
            else:
                duration = audio_duration / len(scenes)
            scene_durations.append(duration)

        print(f"  检测到 {len(scenes)} 个场景，按字符比例分配时长")

        # 如果场景数与图片数一致，直接返回
        if len(scene_durations) == num_images:
            return scene_durations

        # 如果场景数 > 图片数，合并场景时长
        if len(scene_durations) > num_images:
            merged_durations = []
            scenes_per_image = len(scene_durations) / num_images
            for i in range(num_images):
                start_idx = int(i * scenes_per_image)
                end_idx = int((i + 1) * scenes_per_image)
                duration = sum(scene_durations[j] for j in range(start_idx, min(end_idx, len(scene_durations))))
                merged_durations.append(duration)
            # 确保总时长匹配
            total_assigned = sum(merged_durations)
            if merged_durations and total_assigned < audio_duration:
                merged_durations[-1] += audio_duration - total_assigned
            return merged_durations

        # 如果场景数 < 图片数，补充剩余图片时长
        if len(scene_durations) < num_images:
            total_assigned = sum(scene_durations)
            remaining = audio_duration - total_assigned
            remaining_images = num_images - len(scene_durations)
            # 将剩余时长平均分配给多余图片
            extra_duration = remaining / remaining_images if remaining_images > 0 else 0
            while len(scene_durations) < num_images:
                scene_durations.append(extra_duration)
            return scene_durations

        return scene_durations

    def _format_srt_time(self, seconds: float) -> str:
        """将秒数转换为 SRT 时间格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def generate(self, script: str, audio_duration: float = 0) -> dict:
        """生成配音和字幕"""
        dialogues = self._parse_dialogue(script)
        if not dialogues:
            print("警告：未从脚本中提取到台词")
            return {}

        print(f"检测到 {len(dialogues)} 句台词，开始生成配音...")
        print(f"TTS 提供商：{self.provider}, 模型：{self.openai_tts_model}")

        # 保存台词文件
        dialogue_file = self.temp_dir / "dialogue.txt"
        with open(dialogue_file, "w", encoding="utf-8") as f:
            f.write("\n".join(dialogues))
        print(f"台词已保存到：{dialogue_file}")

        # 生成音频
        output_file = self.working_dir / "voiceover.mp3"

        # 根据 provider 选择 TTS 引擎
        if self.provider == "edge":
            self._generate_edge_tts(dialogues, output_file)
        elif self.provider == "openai_tts":
            success = self._generate_openai_tts(dialogues, output_file)
            if not success:
                print("  OpenAI TTS 失败，尝试 edge-tts...")
                self._generate_edge_tts(dialogues, output_file)
        elif self.provider == "azure":
            self._generate_azure_tts(dialogues, output_file)
        else:
            # 默认使用 edge-tts
            self._generate_edge_tts(dialogues, output_file)

        # 添加背景音乐
        if self.bgm_config.get("enabled", False):
            bgm_file = self.bgm_config.get("file", "assets/bgm.mp3")
            bgm_volume = self.bgm_config.get("volume", 0.3)
            self._add_background_music(output_file, bgm_file, bgm_volume)

        print(f"配音已保存到：{output_file}")

        # 获取音频时长
        if audio_duration <= 0:
            audio_duration = self._get_audio_duration(output_file)

        # 生成 SRT 字幕
        srt_file = self.temp_dir / "subtitles.srt"
        srt_path = self.generate_srt(script, audio_duration, srt_file)

        result = {
            "audio": str(output_file),
            "duration": audio_duration,
            "subtitles": srt_path if srt_path else ""
        }

        return result

    def _generate_openai_tts(self, texts: list, output_path: Path) -> bool:
        """使用 OpenAI 兼容 TTS API 生成音频"""
        try:
            from openai import OpenAI

            # 创建客户端
            client = OpenAI(
                api_key=self.openai_api_key,
                base_url=self.openai_base_url
            )

            print(f"  使用 OpenAI TTS: {self.openai_tts_model}, voice={self.openai_tts_voice}")

            # 合并所有台词
            full_text = "\n".join(texts)

            # 调用 TTS API
            response = client.audio.speech.create(
                model=self.openai_tts_model,
                voice=self.openai_tts_voice,
                input=full_text,
                response_format="mp3"
            )

            # 保存音频
            with open(output_path, "wb") as f:
                f.write(response.content)

            print(f"  → {output_path}")
            return True

        except Exception as e:
            print(f"  OpenAI TTS 失败：{e}")
            return False

    def _generate_azure_tts(self, texts: list, output_path: Path):
        """使用 Azure TTS 生成音频"""
        # Azure TTS 备用方案
        if not self.azure_api_key:
            print("  Azure TTS 未配置 API Key，使用 edge-tts 备用方案")
            self._generate_edge_tts(texts, output_path)
            return

        url = f"https://{self.azure_region}.tts.speech.microsoft.com/cognitiveservices/v1"

        headers = {
            "Ocp-Apim-Subscription-Key": self.azure_api_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
            "User-Agent": "VideoWorkflow/1.0"
        }

        # 合并文本为 SSML
        full_ssml = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">'
        full_ssml += f'<voice name="{self.voice}">'

        for text in texts:
            # 转义特殊字符
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            full_ssml += f'<break time="200ms"/>{text}'

        full_ssml += '</voice></speak>'

        response = requests.post(url, headers=headers, data=full_ssml.encode('utf-8'), timeout=120)

        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"  → {output_path}")
        else:
            print(f"  Azure TTS 失败：{response.status_code} {response.text}")
            self._generate_edge_tts(texts, output_path)

    def _generate_edge_tts(self, texts: list, output_path: Path):
        """使用 edge-tts (Microsoft Edge 免费 TTS) 生成音频，支持多音色"""
        try:
            import asyncio
            import edge_tts

            # 合并所有台词
            full_text = "\n".join(texts)

            # 获取配置的音色，默认使用中文男声
            voice = self.voice if hasattr(self, 'voice') and self.voice else 'zh-CN-YunxiNeural'
            print(f"  使用 edge-tts 生成，voice={voice}...")

            # 使用 edge-tts 生成音频
            communicate = edge_tts.Communicate(full_text, voice)
            asyncio.run(communicate.save(str(output_path)))

            print(f"  → {output_path}")
            return True

        except Exception as e:
            print(f"  edge-tts 失败：{e}")
            return self._generate_gtts(texts, output_path)

    def _generate_gtts(self, texts: list, output_path: Path):
        """gTTS 备用方案 - 不支持音色切换"""
        try:
            from gtts import gTTS

            # 合并所有台词
            full_text = "。".join(texts)

            print("  使用 gTTS (Google TTS) 生成（不支持音色切换）...")

            # 创建 gTTS 对象（中文）
            tts = gTTS(text=full_text, lang="zh-CN")

            # 保存音频
            tts.save(str(output_path))

            print(f"  → {output_path}")
            return True

        except Exception as e:
            print(f"  gTTS 失败：{e}")
            return False

    def _get_audio_duration(self, audio_path: Path) -> float:
        """获取音频时长（秒）"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except Exception as e:
            print(f"  获取音频时长失败：{e}，使用默认时长 60 秒")
            return 60.0

    def _add_background_music(self, voiceover: Path, bgm: str, volume: float):
        """添加背景音乐"""
        bgm_path = Path(bgm)
        if not bgm_path.exists():
            print(f"  背景音乐文件不存在：{bgm_path}")
            return

        output_file = self.temp_dir / "voiceover_with_bgm.mp3"

        # 使用 FFmpeg 混合音频
        cmd = [
            "ffmpeg", "-y",
            "-i", str(voiceover),
            "-i", str(bgm_path),
            "-filter_complex", f"[0:a]volume=1[a0];[1:a]volume={volume}[a1];[a0][a1]amix=inputs=2:duration=first",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(output_file)
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            # 替换原文件
            shutil.move(output_file, voiceover)
            print(f"  已添加背景音乐")
        except Exception as e:
            print(f"  添加背景音乐失败：{e}")


class VideoAssembler:
    """视频合成器 - 使用 FFmpeg 合成视频"""

    def __init__(self, config: dict, working_dir: Path, temp_dir: Path):
        self.config = config
        self.working_dir = working_dir
        self.temp_dir = temp_dir
        self.resolution = config.get("resolution", "1920x1080")
        self.fps = config.get("fps", 30)
        self.crf = config.get("crf", 23)
        self.codec = config.get("codec", "libx264")
        # 字幕配置
        self.subtitles_enabled = config.get("subtitles", {}).get("enabled", True)
        self.subtitle_font = config.get("subtitles", {}).get("font", "Noto Sans CJK SC")
        self.subtitle_size = config.get("subtitles", {}).get("size", 8)
        self.subtitle_color = config.get("subtitles", {}).get("color", "&HFFFFFF")
        self.subtitle_border_color = config.get("subtitles", {}).get("border_color", "&H000000")
        self.subtitle_border_size = config.get("subtitles", {}).get("border_size", 2)
        self.subtitle_margin_v = config.get("subtitles", {}).get("margin_v", 50)

    def assemble(self, images: list, audio: str, subtitles: str = "", image_durations: list = None) -> str:
        """合成视频"""
        if not images:
            print("错误：没有图片文件")
            return ""
        if not audio or not Path(audio).exists():
            print("错误：没有音频文件")
            return ""

        print(f"使用 {len(images)} 张图片和音频合成视频...")

        output_file = self.working_dir / "output.mp4"

        # 计算每张图的持续时间
        total_duration = self._get_audio_duration(audio)

        # 检查字幕文件
        has_subtitles = subtitles and Path(subtitles).exists()

        # 使用传入的图片时长分配，或从字幕解析，或平均分配
        if image_durations:
            # 使用传入的时长分配（基于场景）
            durations = image_durations
            print(f"使用场景时长分配：{[f'{d:.2f}s' for d in durations]}")
        elif has_subtitles and self.subtitles_enabled:
            print(f"嵌入字幕：{subtitles}")
            print(f"  字体：{self.subtitle_font}, 大小：{self.subtitle_size}, 颜色：{self.subtitle_color}")
            # 从字幕文件解析每个句子的时长，用于图片切换同步
            durations = self._parse_subtitle_durations(subtitles, len(images))
            print(f"根据字幕时长分配 {len(durations)} 个时间段")
        else:
            # 平均分配时长
            durations = [total_duration / len(images)] * len(images)
            print(f"每张图片显示时长：{durations[0]:.1f}秒")
            if has_subtitles and not self.subtitles_enabled:
                print("字幕文件存在但未启用（config 中 subtitles.enabled=false）")

        # 创建 FFmpeg 命令
        cmd = self._build_ffmpeg_cmd(images, audio, output_file, durations, subtitles if has_subtitles and self.subtitles_enabled else "")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                print(f"  FFmpeg 错误：{result.stderr}")
                return ""

            print(f"  → {output_file}")
            return str(output_file)

        except subprocess.TimeoutExpired:
            print("  FFmpeg 超时")
            return ""
        except Exception as e:
            print(f"  合成失败：{e}")
            return ""

    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长（秒）"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except Exception as e:
            print(f"  获取音频时长失败：{e}，使用默认时长 30 秒")
            return 30.0

    def _parse_subtitle_durations(self, subtitles_path: str, num_images: int) -> list:
        """从字幕文件解析每个句子的时长，并映射到图片

        返回每张图片应该显示的时长列表
        """
        # 读取字幕文件
        with open(subtitles_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析 SRT 字幕，提取每个字幕的起止时间
        pattern = r'\d+\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})'
        matches = re.findall(pattern, content)

        if not matches:
            print(f"  警告：无法从字幕文件解析时长，使用平均分配")
            return [60.0 / num_images] * num_images

        # 计算每个字幕段落的时长和累计时间
        subtitle_segments = []
        for start_str, end_str in matches:
            start = self._parse_srt_time(start_str)
            end = self._parse_srt_time(end_str)
            duration = end - start
            subtitle_segments.append({
                'start': start,
                'end': end,
                'duration': duration
            })

        # 计算总时长
        total_duration = sum(seg['duration'] for seg in subtitle_segments)

        # 将字幕时间段映射到图片
        # 假设每张图片对应一个场景/段落，每个段落可能包含多个字幕句子
        num_segments = len(subtitle_segments)

        if num_images >= num_segments:
            # 图片数量 >= 字幕段落数：每张图片对应一个字幕段落
            image_durations = []
            for i in range(num_images):
                if i < num_segments:
                    image_durations.append(subtitle_segments[i]['duration'])
                else:
                    # 多余的图片：分配剩余时长或平均时长
                    remaining = total_duration - sum(image_durations)
                    remaining_images = num_images - len(image_durations)
                    if remaining_images > 0:
                        image_durations.append(remaining / remaining_images)
                    else:
                        image_durations.append(1.0)
            return image_durations
        else:
            # 图片数量 < 字幕段落数：多张图片合并时长
            # 计算每张图片应该覆盖多少字幕段落
            segments_per_image = num_segments / num_images
            image_durations = []

            for i in range(num_images):
                start_idx = int(i * segments_per_image)
                end_idx = int((i + 1) * segments_per_image)

                # 累加该图片覆盖的所有字幕段落的时长
                duration = sum(subtitle_segments[j]['duration'] for j in range(start_idx, min(end_idx, num_segments)))
                image_durations.append(duration)

            # 确保总时长匹配
            total_assigned = sum(image_durations)
            if total_assigned < total_duration and image_durations:
                # 将剩余时长分配给最后一张图片
                image_durations[-1] += total_duration - total_assigned

            return image_durations

    def _parse_srt_time(self, time_str: str) -> float:
        """解析 SRT 时间格式为秒数"""
        # 格式：HH:MM:SS,mmm
        parts = time_str.replace(',', '.').split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    def _build_ffmpeg_cmd(self, images: list, audio: str, output: Path, img_durations: list, subtitles: str = "") -> list:
        """构建 FFmpeg 命令"""
        # 支持每张不同的显示时长
        if isinstance(img_durations, list):
            durations = img_durations
        else:
            # 兼容旧的单个时长参数
            durations = [img_durations] * len(images)

        # 创建图片列表文件（使用绝对路径）
        list_file = self.temp_dir / "images.txt"
        with open(list_file, "w") as f:
            for i, img in enumerate(images):
                # 转换为绝对路径
                img_path = Path(img)
                if not img_path.is_absolute():
                    img_path = Path.cwd() / img_path
                f.write(f"file '{img_path}'\n")
                # 每张图设置对应的 duration
                duration = durations[i] if i < len(durations) else durations[-1]
                f.write(f"duration {duration:.3f}\n")
            # 最后一张图片需要重复一次（FFmpeg concat 特性）
            last_img = Path(images[-1])
            if not last_img.is_absolute():
                last_img = Path.cwd() / last_img
            f.write(f"file '{last_img}'\n")

        # 构建视频滤镜
        vf_filters = [f"scale={self.resolution.replace('x', ':')}", f"fps={self.fps}"]

        # 添加字幕滤镜
        if subtitles:
            # 转义字幕文件路径中的冒号和引号
            subs_path_escaped = subtitles.replace(":", r"\:").replace("'", r"\'")
            # 字幕样式：底部中间对齐，大字体
            # Alignment=2: 底部中间 (Anchored)
            # MarginV=50: 从底部向上 50 像素
            # FontSize: 根据分辨率计算
            width, height = self.resolution.split('x')
            font_size = int(self.subtitle_size) if self.subtitle_size else int(width) // 24
            style = f"FontName={self.subtitle_font},FontSize={font_size},PrimaryColour=&H00FFFFFF,SecondaryColour=&H00000000,OutlineColour=&H00000000,BackColour=&H00000000,Outline={self.subtitle_border_size},MarginV={self.subtitle_margin_v},BorderStyle=1,Alignment=2,Blur=1"
            vf_filters.append(f"subtitles='{subs_path_escaped}':force_style='{style}'")

        vf_string = ",".join(vf_filters)

        # 构建命令
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-i", audio,
            "-c:v", self.codec,
            "-crf", str(self.crf),
            "-preset", "medium",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-vf", vf_string,
            "-shortest",
            "-movflags", "+faststart",
            str(output)
        ]

        return cmd


class VideoPublisher:
    """视频发布器 - 自动发布到平台"""

    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", False)
        self.platforms = config.get("platforms", [])
        self.schedule = config.get("schedule", "18:00")
        self.tags = config.get("default_tags", [])

    def publish(self, video: str, title: str = "", description: str = ""):
        """发布视频"""
        if not self.enabled:
            print("自动发布未启用")
            print(f"视频文件：{video}")
            return

        print(f"开始发布到 {len(self.platforms)} 个平台...")

        for platform in self.platforms:
            print(f"\n发布到 {platform}...")

            if platform == "douyin":
                self._publish_douyin(video, title, description)
            elif platform == "bilibili":
                self._publish_bilibili(video, title, description)
            elif platform == "video_account":
                self._publish_video_account(video, title, description)
            else:
                print(f"  不支持的平台：{platform}")

    def _publish_douyin(self, video: str, title: str, description: str):
        """发布到抖音"""
        print("  抖音发布需要使用抖音开放平台 API 或浏览器自动化")
        print("  推荐工具：Playwright, Selenium")
        # 实际实现需要抖音开放平台权限
        # https://open.douyin.com/

    def _publish_bilibili(self, video: str, title: str, description: str):
        """发布到 B 站"""
        print("  B 站发布需要使用 B 站开放平台 API 或浏览器自动化")
        print("  推荐工具：bilibili-toolkit, Playwright")
        # 实际实现需要 B 站 Cookie 或 API 权限

    def _publish_video_account(self, video: str, title: str, description: str):
        """发布到视频号"""
        print("  视频号发布需要使用微信开放平台 API 或浏览器自动化")
        print("  推荐工具：Playwright, 微信小店开放接口")


class VideoWorkflow:
    """视频自动化工作流主类"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化工作流"""
        # 加载环境变量
        load_dotenv(".env")
        load_dotenv(Path.home() / ".baoyu-skills" / ".env")

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.working_dir = Path(self.config.get("advanced", {}).get("working_dir", "./output"))
        self.temp_dir = Path(self.config.get("advanced", {}).get("temp_dir", "./tmp"))
        self.retry_count = self.config.get("advanced", {}).get("retry_count", 2)
        self._ensure_dirs()

        # 初始化各组件
        self.script_gen = ScriptGenerator(self.config.get("script", {}))
        self.visual_gen = VisualGenerator(
            self.config.get("visuals", {}),
            self.working_dir,
            self.temp_dir
        )
        self.audio_gen = AudioGenerator(
            self.config.get("audio", {}),
            self.working_dir,
            self.temp_dir,
            resolution=self.config.get("export", {}).get("resolution", "1920x1080"),
            subtitle_config=self.config.get("subtitles", {})
        )
        self.video_asm = VideoAssembler(
            self.config.get("export", {}),
            self.working_dir,
            self.temp_dir
        )
        self.publisher = VideoPublisher(self.config.get("publish", {}))

    def _load_config(self) -> dict:
        """加载配置文件"""
        if not self.config_path.exists():
            print(f"配置文件不存在：{self.config_path}")
            return self._get_default_config()

        with open(self.config_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析环境变量替换 ${VAR} 和 ${VAR:-default}
        content = self._expand_env_vars(content)

        import yaml
        return yaml.safe_load(content)

    def _expand_env_vars(self, content: str) -> str:
        """展开环境变量替换"""
        def replace_var(match):
            var_expr = match.group(1)
            # 处理 ${VAR:-default} 格式
            if ":-" in var_expr:
                var_name, default = var_expr.split(":-", 1)
                return os.getenv(var_name, default)
            # 处理 ${VAR} 格式
            else:
                return os.getenv(var_expr, match.group(0))

        # 替换所有 ${VAR} 和 ${VAR:-default}
        pattern = r'\$\{([^}]+)\}'
        return re.sub(pattern, replace_var, content)

    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            "script": {"provider": "claude", "template": "scripts/script_template.txt"},
            "visuals": {"provider": "seedream", "style": "cartoon style"},
            "audio": {"provider": "azure", "voice": "zh-CN-YunxiNeural"},
            "export": {"resolution": "1920x1080", "fps": 30, "crf": 23},
            "publish": {"enabled": False},
            "advanced": {"working_dir": "./output", "temp_dir": "./tmp"}
        }

    def _ensure_dirs(self):
        """确保目录存在"""
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate_script(self, topic: str) -> str:
        """Step 1: 生成脚本"""
        print("\n" + "=" * 50)
        print("Step 1: 生成脚本")
        print("=" * 50)

        for attempt in range(1, self.retry_count + 1):
            try:
                template_path = Path(self.config["script"]["template"])
                script = self.script_gen.generate(topic, template_path)

                # 保存脚本
                script_file = self.working_dir / "script.md"
                with open(script_file, "w", encoding="utf-8") as f:
                    f.write(script)

                print(f"脚本已保存到：{script_file}")
                print(f"\n脚本预览（前 500 字）：")
                print("-" * 30)
                print(script[:500])
                print("...")

                return script

            except Exception as e:
                print(f"  尝试 {attempt}/{self.retry_count} 失败：{e}")
                if attempt == self.retry_count:
                    raise

        return ""

    def generate_visuals(self, script: str) -> list:
        """Step 2: 生成画面"""
        print("\n" + "=" * 50)
        print("Step 2: 生成画面")
        print("=" * 50)

        for attempt in range(1, self.retry_count + 1):
            try:
                images = self.visual_gen.generate_batch(script)
                print(f"成功生成 {len(images)} 张画面")
                return images
            except Exception as e:
                print(f"  尝试 {attempt}/{self.retry_count} 失败：{e}")
                if attempt == self.retry_count:
                    raise

        return []

    def generate_audio(self, script: str, audio_duration: float = 0) -> dict:
        """Step 3: 生成配音和字幕"""
        print("\n" + "=" * 50)
        print("Step 3: 生成配音")
        print("=" * 50)

        for attempt in range(1, self.retry_count + 1):
            try:
                result = self.audio_gen.generate(script, audio_duration)
                return result
            except Exception as e:
                print(f"  尝试 {attempt}/{self.retry_count} 失败：{e}")
                if attempt == self.retry_count:
                    raise

        return {}

    def assemble_video(self, images: list, audio: str, subtitles: str = "", script: str = "", audio_duration: float = 0) -> str:
        """Step 4: 合成视频"""
        print("\n" + "=" * 50)
        print("Step 4: 合成视频")
        print("=" * 50)

        for attempt in range(1, self.retry_count + 1):
            try:
                # 如果有脚本，根据场景生成图片时长分配
                image_durations = None
                if script and images:
                    # 使用实际音频时长
                    if audio_duration <= 0:
                        audio_duration = self.video_asm._get_audio_duration(audio)
                    image_durations = self.audio_gen.generate_scene_durations(script, audio_duration, len(images))
                    print(f"图片切换时长分配：{[f'{d:.2f}s' for d in image_durations]}")

                video = self.video_asm.assemble(images, audio, subtitles, image_durations)
                return video
            except Exception as e:
                print(f"  尝试 {attempt}/{self.retry_count} 失败：{e}")
                if attempt == self.retry_count:
                    raise

        return ""

    def run(self, topic: str, title: str = "", description: str = "", skip_visuals: bool = False, skip_script: bool = False):
        """运行完整工作流"""
        print("\n" + "=" * 60)
        print("视频自动化工作流")
        print("=" * 60)
        print(f"主题：{topic}")
        if skip_script:
            print("模式：跳过脚本生成，使用现有脚本")
        if skip_visuals:
            print("模式：跳过画面生成，使用现有图片")
        print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        start_time = time.time()

        try:
            # Step 1: 生成脚本（或跳过）
            if skip_script:
                print("\n" + "=" * 50)
                print("Step 1: 使用现有脚本")
                print("=" * 50)
                script_file = self.working_dir / "script.md"
                if script_file.exists():
                    script = script_file.read_text(encoding='utf-8')
                    print(f"读取脚本：{script_file}")
                else:
                    print("警告：现有脚本不存在，重新生成...")
                    script = self.generate_script(topic)
            else:
                script = self.generate_script(topic)

            # Step 2: 生成画面（或跳过）
            if skip_visuals:
                print("\n" + "=" * 50)
                print("Step 2: 使用现有图片")
                print("=" * 50)
                images = sorted([str(p) for p in self.working_dir.glob('scene_*.png')])
                if images:
                    print(f"使用 {len(images)} 张现有图片")
                else:
                    print("警告：未找到现有图片，重新生成...")
                    images = self.generate_visuals(script)
            else:
                images = self.generate_visuals(script)

            # Step 3: 生成配音和字幕
            audio_result = self.generate_audio(script)
            audio = audio_result.get("audio", "")
            subtitles = audio_result.get("subtitles", "")
            audio_duration = audio_result.get("duration", 0)

            # Step 4: 合成视频（嵌入字幕）
            video = self.assemble_video(images, audio, subtitles, script, audio_duration)

            # Step 5: 发布
            if video:
                self.publisher.publish(video, title or topic, description)

            elapsed = time.time() - start_time

            print("\n" + "=" * 60)
            print("工作流执行完成!")
            print("=" * 60)
            print(f"输出目录：{self.working_dir}")
            print(f"耗时：{elapsed:.1f}秒")
            print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            if video:
                print(f"\n最终输出：{video}")
            if subtitles:
                print(f"字幕文件：{subtitles}")

        except Exception as e:
            print("\n" + "=" * 60)
            print("工作流执行失败!")
            print("=" * 60)
            print(f"错误：{e}")
            sys.exit(1)


@click.command()
@click.option("--topic", required=True, help="视频主题")
@click.option("--config", default="config/config.yaml", help="配置文件路径")
@click.option("--title", default="", help="视频标题（可选，默认使用主题）")
@click.option("--description", default="", help="视频描述（可选）")
@click.option("--skip-visuals", is_flag=True, help="跳过画面生成，使用现有图片")
@click.option("--skip-script", is_flag=True, help="跳过脚本生成，使用现有脚本")
def main(topic: str, config: str, title: str, description: str, skip_visuals: bool, skip_script: bool):
    """视频自动化工作流入口"""
    workflow = VideoWorkflow(config)
    workflow.run(topic, title, description, skip_visuals=skip_visuals, skip_script=skip_script)


if __name__ == "__main__":
    main()
