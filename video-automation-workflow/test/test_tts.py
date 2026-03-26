#!/usr/bin/env python3
"""
测试 OpenAI TTS 代理连接
Test OpenAI TTS Proxy Connection
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(".env")

def test_openai_tts():
    """测试 OpenAI TTS 连接"""
    print("=" * 50)
    print("测试 OpenAI TTS 连接")
    print("=" * 50)

    # 获取配置
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("OPENAI_API_KEY", "proxy-mode")
    model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    voice = "alloy"

    print(f"\n配置信息:")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    print(f"  Voice: {voice}")
    print(f"  API Key: {'已设置' if api_key and api_key != 'proxy-mode' else '代理模式'}")

    try:
        from openai import OpenAI

        # 创建客户端
        client = OpenAI(api_key=api_key, base_url=base_url)

        # 测试文本
        test_text = "你好，这是一个测试。今天天气不错，希望你能听到我的声音。"

        print(f"\n生成 TTS 音频...")
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=test_text,
            response_format="mp3"
        )

        # 保存音频
        output_path = Path("output/test_tts.mp3")
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"\n✓ TTS 生成成功!")
        print(f"输出文件：{output_path}")

        # 显示文件信息
        file_size = output_path.stat().st_size
        print(f"文件大小：{file_size / 1024:.1f} KB")

        return True

    except Exception as e:
        print(f"\n✗ TTS 生成失败：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_openai_tts()
    exit(0 if success else 1)
