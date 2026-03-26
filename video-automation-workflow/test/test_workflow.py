#!/usr/bin/env python3
"""
视频工作流测试脚本
Test Video Workflow - Quick Test
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(".env")

def test_script_generation():
    """测试脚本生成"""
    print("=" * 50)
    print("测试 Step 1: 脚本生成")
    print("=" * 50)

    try:
        from run_workflow import ScriptGenerator

        config = {
            "provider": "claude",
            "base_url": os.getenv("ANTHROPIC_BASE_URL"),
            "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        }

        generator = ScriptGenerator(config)
        template_path = Path("scripts/script_template.txt")

        script = generator.generate("时间管理的 3 个技巧", template_path)

        print("\n✓ 脚本生成成功!")
        print(f"脚本长度：{len(script)} 字")

        # 保存
        output_file = Path("output/test_script.md")
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"已保存到：{output_file}")

        return True

    except Exception as e:
        print(f"\n✗ 脚本生成失败：{e}")
        return False


def test_visual_generation():
    """测试画面生成"""
    print("\n" + "=" * 50)
    print("测试 Step 2: 画面生成")
    print("=" * 50)

    try:
        from run_workflow import VisualGenerator

        config = {
            "provider": "seedream",
            "api_key": os.getenv("ARK_API_KEY"),
            "style": "cartoon style, bright colors",
            "resolution": "1080x1920",
        }

        working_dir = Path("output")
        temp_dir = Path("tmp")
        working_dir.mkdir(exist_ok=True)
        temp_dir.mkdir(exist_ok=True)

        generator = VisualGenerator(config, working_dir, temp_dir)

        # 测试简单提示词
        prompt = "一个简洁的封面画面，扁平化矢量设计，明亮配色"
        print(f"生成测试图片：{prompt}")

        output_path = generator._generate_seedream(prompt, "test_cover")

        if output_path and output_path.exists():
            print(f"\n✓ 画面生成成功!")
            print(f"输出文件：{output_path}")
            return True
        else:
            print("\n✗ 画面生成失败：没有输出文件")
            return False

    except Exception as e:
        print(f"\n✗ 画面生成失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_audio_generation():
    """测试音频生成（仅测试台词提取）"""
    print("\n" + "=" * 50)
    print("测试 Step 3: 配音生成 (台词提取)")
    print("=" * 50)

    try:
        # 读取测试脚本
        script_file = Path("output/test_script.md")
        if not script_file.exists():
            print("  跳过：没有测试脚本文件")
            return None

        with open(script_file, "r", encoding="utf-8") as f:
            script = f.read()

        from run_workflow import AudioGenerator

        config = {
            "voice": "zh-CN-YunxiNeural",
            "bgm": {"enabled": False}
        }

        working_dir = Path("output")
        temp_dir = Path("tmp")

        generator = AudioGenerator(config, working_dir, temp_dir)
        dialogues = generator._parse_dialogue(script)

        print(f"提取到 {len(dialogues)} 句台词:")
        for i, d in enumerate(dialogues[:3], 1):
            print(f"  {i}. {d[:50]}...")

        if len(dialogues) > 3:
            print(f"  ... 还有 {len(dialogues) - 3} 句")

        # 保存台词
        dialogue_file = temp_dir / "test_dialogue.txt"
        with open(dialogue_file, "w", encoding="utf-8") as f:
            f.write("\n".join(dialogues))
        print(f"\n✓ 台词提取成功!")
        print(f"已保存到：{dialogue_file}")

        print("\n注意：TTS 音频生成需要有效的 Azure API Key")
        return True

    except Exception as e:
        print(f"\n✗ 配音生成失败：{e}")
        return False


def main():
    print("=" * 60)
    print("视频工作流测试")
    print("=" * 60)

    results = {
        "脚本生成": test_script_generation(),
        "画面生成": test_visual_generation(),
        "配音生成": test_audio_generation(),
    }

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, success in results.items():
        if success is True:
            print(f"  ✓ {name}: 成功")
        elif success is False:
            print(f"  ✗ {name}: 失败")
        else:
            print(f"  ○ {name}: 跳过")

    # 计算成功率
    valid_results = [v for v in results.values() if v is not None]
    if valid_results:
        success_rate = sum(valid_results) / len(valid_results) * 100
        print(f"\n成功率：{success_rate:.0f}%")

    all_passed = all(v for v in valid_results)
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
