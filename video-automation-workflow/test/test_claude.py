#!/usr/bin/env python3
"""
测试 Claude API 连接
Test Claude API Connection
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(".env")

def test_claude_connection():
    """测试 Claude API 连接"""
    print("=" * 50)
    print("测试 Claude API 连接")
    print("=" * 50)

    # 获取配置
    base_url = os.getenv("ANTHROPIC_BASE_URL", "")
    api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or "dummy-key"
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    print(f"\n配置信息:")
    print(f"  Base URL: {base_url or '默认 (官方 API)'}")
    print(f"  Model: {model}")
    print(f"  API Key: {'已设置' if api_key and api_key != 'dummy-key' else '未设置 (代理模式)'}")

    try:
        from anthropic import Anthropic

        # 创建客户端
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url

        print(f"\n连接 Anthropic API...")
        client = Anthropic(**kwargs)

        # 发送测试消息
        print(f"发送测试消息...")
        response = client.messages.create(
            model=model,
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "你好，请用一句话介绍你自己。"
            }]
        )

        print(f"\n✓ 连接成功!")
        print(f"回复：{response.content[0].text}")
        print(f"Usage: input_tokens={response.usage.input_tokens}, output_tokens={response.usage.output_tokens}")

        return True

    except Exception as e:
        print(f"\n✗ 连接失败：{e}")
        return False


if __name__ == "__main__":
    success = test_claude_connection()
    exit(0 if success else 1)
