#!/usr/bin/env python3
"""
测试完整配音生成
Test Full Audio Generation
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(".env")

# 导入工作流模块
from run_workflow import AudioGenerator

def test_audio_generation():
    """测试完整音频生成"""
    print("=" * 50)
    print("测试完整配音生成")
    print("=" * 50)

    # 测试台词
    test_dialogues = [
        "你好，这是一个测试。",
        "今天天气不错，希望你能听到我的声音。",
        "这是第三句话，用于测试多句台词的合并。",
        "最后一句，谢谢你的收听！"
    ]

    working_dir = Path("output")
    temp_dir = Path("tmp")
    working_dir.mkdir(exist_ok=True)
    temp_dir.mkdir(exist_ok=True)

    config = {
        "provider": "openai_tts",
        "tts_voice": "alloy",
        "bgm": {"enabled": False}
    }

    generator = AudioGenerator(config, working_dir, temp_dir)

    output_file = working_dir / "test_voiceover.mp3"

    print(f"\n生成 {len(test_dialogues)} 句台词的配音...")

    # 保存台词文件
    dialogue_file = temp_dir / "test_dialogue.txt"
    with open(dialogue_file, "w", encoding="utf-8") as f:
        f.write("\n".join(test_dialogues))
    print(f"台词已保存到：{dialogue_file}")

    # 生成音频
    try:
        # 直接使用内部方法
        success = generator._generate_openai_tts(test_dialogues, output_file)

        if not success:
            print("\nOpenAI TTS 失败，使用 gTTS 备用方案...")
            generator._generate_local_tts(test_dialogues, output_file)

        # 检查输出文件
        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"\n✓ 配音生成成功!")
            print(f"输出文件：{output_file}")
            print(f"文件大小：{file_size / 1024:.1f} KB")
            return True
        else:
            print("\n✗ 配音生成失败：没有输出文件")
            return False

    except Exception as e:
        print(f"\n✗ 配音生成失败：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_audio_generation()
    sys.exit(0 if success else 1)
