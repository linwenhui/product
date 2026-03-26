#!/usr/bin/env python3
"""
测试工作流配置
Test Workflow Configuration
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(".env")
load_dotenv(Path.home() / ".baoyu-skills" / ".env")

def check_env_var(name: str, required: bool = False) -> bool:
    """检查环境变量是否存在"""
    value = os.getenv(name, "")
    if not value and required:
        print(f"  ❌ {name}: 未设置")
        return False
    elif value:
        # 隐藏敏感信息
        masked = value[:8] + "..." + value[-4:] if len(value) > 12 else value[:4] + "..."
        print(f"  ✓ {name}: {masked}")
        return True
    else:
        print(f"  ○ {name}: 未设置 (可选)")
        return True

def main():
    print("=" * 50)
    print("工作流配置检查")
    print("=" * 50)

    all_ok = True

    # 检查脚本生成 API
    print("\n【脚本生成】")
    anthropic_base = os.getenv("ANTHROPIC_BASE_URL", "")
    if anthropic_base:
        masked = anthropic_base[:40] + "..." if len(anthropic_base) > 40 else anthropic_base
        print(f"  ✓ ANTHROPIC_BASE_URL: {masked}")

    if not check_env_var("CLAUDE_API_KEY"):
        if not anthropic_base:
            print("  提示：设置 ANTHROPIC_BASE_URL 使用代理模式")
        print("  提示：可使用 OpenAI 或 Kimi 替代")
    check_env_var("ANTHROPIC_API_KEY")
    check_env_var("CLAUDE_MODEL")
    check_env_var("OPENAI_API_KEY")
    check_env_var("KIMI_API_KEY")

    # 检查画面生成 API
    print("\n【画面生成】")
    if not check_env_var("ARK_API_KEY"):
        print("  提示：可使用 DashScope 或 FLUX 替代")
        all_ok = False
    check_env_var("SEEDREAM_BASE_URL")
    check_env_var("SEEDREAM_IMAGE_MODEL")
    check_env_var("DASHSCOPE_API_KEY")

    # 检查 TTS API
    print("\n【TTS 配音】")
    if not check_env_var("AZURE_API_KEY"):
        print("  提示：将使用本地 TTS 备用方案")
    check_env_var("AZURE_REGION")

    # 检查工具
    print("\n【系统工具】")
    import shutil
    if shutil.which("ffmpeg"):
        print("  ✓ FFmpeg: 已安装")
    else:
        print("  ❌ FFmpeg: 未安装")
        print("     安装：brew install ffmpeg 或 apt-get install ffmpeg")
        all_ok = False

    if shutil.which("ffprobe"):
        print("  ✓ FFprobe: 已安装")
    else:
        print("  ❌ FFprobe: 未安装")
        all_ok = False

    # 检查 Python 依赖
    print("\n【Python 依赖】")
    try:
        import yaml
        print("  ✓ pyyaml")
    except ImportError:
        print("  ❌ pyyaml")
        all_ok = False

    try:
        import click
        print("  ✓ click")
    except ImportError:
        print("  ❌ click")
        all_ok = False

    try:
        import requests
        print("  ✓ requests")
    except ImportError:
        print("  ❌ requests")
        all_ok = False

    try:
        import dotenv
        print("  ✓ python-dotenv")
    except ImportError:
        print("  ❌ python-dotenv")
        all_ok = False

    try:
        from openai import OpenAI
        print("  ✓ openai")
    except ImportError:
        print("  ❌ openai")
        all_ok = False

    try:
        from anthropic import Anthropic
        print("  ✓ anthropic")
    except ImportError:
        print("  ○ anthropic (使用 OpenAI/Kimi 时不需要)")

    print("\n" + "=" * 50)
    if all_ok:
        print("配置检查通过！可以运行工作流。")
        print("\n运行示例:")
        print('  python run_workflow.py --topic "时间管理技巧"')
    else:
        print("配置检查未通过，请先配置环境变量。")
        print("\n复制配置模板:")
        print("  cp .env.example .env")
        print("然后编辑 .env 文件填入 API Key")
    print("=" * 50)

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
