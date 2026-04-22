#!/usr/bin/env python3
"""
配图生成恢复脚本 - 直接调用 ARK API
用于为已生成的文章补全配图
"""

import os
import sys
import json
import logging
import hashlib
import requests
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ARKImageGenerator:
    """ARK 平台图片生成器"""

    def __init__(self, api_key: str, base_url: str, model: str = "doubao-seedream-4.0"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def generate(self, prompt: str, output_path: str, size: str = "1024x1024") -> bool:
        """生成单张图片"""
        try:
            response = self.session.post(
                f"{self.base_url}/images/generations",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "n": 1,
                    "size": size
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and len(data["data"]) > 0:
                    image_url = data["data"][0].get("url")
                    if image_url:
                        # 下载图片
                        img_response = requests.get(image_url, timeout=60)
                        if img_response.status_code == 200:
                            with open(output_path, 'wb') as f:
                                f.write(img_response.content)
                            logger.info(f"✓ 图片已保存：{output_path}")
                            return True
                        else:
                            logger.error(f"✗ 下载图片失败：{img_response.status_code}")
                            return False
                    else:
                        logger.error("✗ API 返回数据中没有图片 URL")
                        return False
                else:
                    logger.error(f"✗ API 返回数据异常：{data}")
                    return False
            else:
                logger.error(f"✗ API 请求失败：{response.status_code} - {response.text}")
                return False

        except requests.exceptions.Timeout:
            logger.error("✗ 请求超时")
            return False
        except Exception as e:
            logger.error(f"✗ 生成失败：{e}")
            return False


def load_env_file(env_path: str) -> dict:
    """加载 .env 文件"""
    env = {}
    if Path(env_path).exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
    return env


def main():
    """主函数"""
    # 查找 .env 文件
    script_dir = Path(__file__).parent
    env_file = None

    for path in [
        script_dir / ".baoyu-skills" / ".env",
        script_dir.parent / ".baoyu-skills" / ".env",
        Path.home() / ".baoyu-skills" / ".env"
    ]:
        if path.exists():
            env_file = path
            break

    if not env_file:
        logger.error("✗ 未找到 .baoyu-skills/.env 文件")
        sys.exit(1)

    logger.info(f"✓ 找到环境文件：{env_file}")
    env = load_env_file(str(env_file))

    # 验证环境变量
    ark_api_key = env.get("ARK_API_KEY")
    seedream_base_url = env.get("SEEDREAM_BASE_URL", "https://worklink.yealink.com/llmproxy/v1")
    seedream_model = env.get("SEEDREAM_IMAGE_MODEL", "doubao-seedream-4.0")

    if not ark_api_key:
        logger.error("✗ ARK_API_KEY 未配置")
        sys.exit(1)

    logger.info(f"✓ ARK_API_KEY: {ark_api_key[:10]}...")
    logger.info(f"✓ SEEDREAM_BASE_URL: {seedream_base_url}")
    logger.info(f"✓ Model: {seedream_model}")

    # 测试 API 连接
    generator = ARKImageGenerator(ark_api_key, seedream_base_url, seedream_model)
    logger.info("✓ 正在测试 API 连接...")

    try:
        test_response = generator.session.post(
            f"{seedream_base_url}/images/generations",
            json={"model": seedream_model, "prompt": "test", "n": 1, "size": "256x256"},
            timeout=30
        )
        if test_response.status_code == 200:
            logger.info("✓ API 连接正常")
        else:
            logger.warning(f"! API 返回状态：{test_response.status_code}")
    except Exception as e:
        logger.error(f"✗ API 连接测试失败：{e}")
        sys.exit(1)

    # 获取今日文章目录
    date_str = datetime.now().strftime("%Y-%m-%d")
    article_dir = script_dir / "article" / date_str
    imgs_dir = article_dir / "imgs"

    if not article_dir.exists():
        logger.error(f"✗ 文章目录不存在：{article_dir}")
        sys.exit(1)

    logger.info(f"✓ 文章目录：{article_dir}")

    # 创建图片目录
    imgs_dir.mkdir(parents=True, exist_ok=True)

    # 读取 batch.json（如果存在）
    batch_file = imgs_dir / "batch.json"
    if batch_file.exists():
        with open(batch_file, 'r', encoding='utf-8') as f:
            batch_data = json.load(f)

        logger.info(f"✓ 读取到 {len(batch_data.get('tasks', []))} 个生成任务")

        # 检查哪些图片已经生成
        existing_images = set(str(p.name) for p in imgs_dir.glob("*.png"))
        existing_images.update(str(p.name) for p in imgs_dir.glob("*.jpg"))

        # 生成缺失的图片
        for task in batch_data.get("tasks", []):
            task_id = task.get("id", "unknown")
            output_image = task.get("image", f"{task_id}.png")
            prompt_files = task.get("promptFiles", [])

            output_path = imgs_dir / output_image

            # 检查是否已存在
            if output_path.exists():
                logger.info(f"✓ 已存在：{output_image}")
                continue

            # 读取 prompt
            prompt = ""
            for pf in prompt_files:
                prompt_file = imgs_dir / pf
                if prompt_file.exists():
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 提取 prompt 内容
                        if "## 生成 Prompt" in content:
                            prompt = content.split("## 生成 Prompt")[1].strip()
                        else:
                            prompt = content[:500]  # 取前 500 字符
                    break

            if not prompt:
                prompt = f"科技风格插图：{task_id}"
                logger.warning(f"! 使用默认 prompt: {prompt}")

            logger.info(f"\n生成：{output_image}")
            logger.info(f"  Prompt: {prompt[:50]}...")

            success = generator.generate(prompt, str(output_path))
            if not success:
                logger.warning(f"! 生成失败：{output_image}")

    else:
        logger.warning("! batch.json 不存在，尝试从文章生成图片")

        # 查找 formatted 目录中的文章
        formatted_dir = article_dir / "formatted"
        if formatted_dir.exists():
            for article_file in formatted_dir.glob("*-formatted.md"):
                # 读取文章标题
                with open(article_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "title:" in content:
                        title = content.split("title:")[1].split("\n")[0].strip().strip('"\'')
                    else:
                        title = article_file.stem

                # 生成封面图
                output_path = imgs_dir / f"{article_file.stem}-cover.png"
                prompt = f"科技风格封面图：{title}，高质量，专业插画风格"

                logger.info(f"\n生成封面：{output_path.name}")
                logger.info(f"  标题：{title}")

                success = generator.generate(prompt, str(output_path), size="1024x1024")
                if not success:
                    logger.warning(f"! 生成失败：{output_path.name}")

    logger.info("\n" + "=" * 60)
    logger.info("配图生成完成！")
    logger.info(f"查看图片：ls -la {imgs_dir}")


if __name__ == "__main__":
    main()
