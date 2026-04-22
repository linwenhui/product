#!/usr/bin/env python3
"""
微信公众号文章推送脚本
直接调用微信 API 推送文章到草稿箱
"""

import os
import sys
import json
import logging
import requests
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeChatPublisher:
    """微信公众号发布器"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://api.weixin.qq.com"
        self.access_token: Optional[str] = None
        self.session = requests.Session()

    def get_access_token(self) -> str:
        """获取 access_token"""
        url = f"{self.base_url}/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }

        response = self.session.get(url, params=params, timeout=30)
        data = response.json()

        if "access_token" in data:
            self.access_token = data["access_token"]
            logger.info(f"✓ 获取 access_token 成功，有效期 {data.get('expires_in', 7200)}秒")
            return self.access_token
        else:
            error_msg = data.get("errmsg", "未知错误")
            logger.error(f"✗ 获取 access_token 失败：{error_msg}")
            raise ValueError(f"获取 access_token 失败：{error_msg}")

    def upload_permanent_material(self, image_path: str) -> str:
        """
        上传永久素材（图片），返回 media_id
        用于图文消息封面 thumb_media_id
        """
        if not self.access_token:
            self.get_access_token()

        # 使用上传永久素材 API
        url = f"{self.base_url}/cgi-bin/material/add_material"
        params = {
            "access_token": self.access_token,
            "type": "image"
        }

        with open(image_path, 'rb') as f:
            files = {"media": f}
            response = self.session.post(url, files=files, params=params, timeout=60)

        data = response.json()

        if "media_id" in data:
            logger.info(f"✓ 永久素材上传成功，media_id: {data['media_id']}")
            return data["media_id"]
        else:
            error_msg = data.get("errmsg", "未知错误")
            logger.error(f"✗ 永久素材上传失败：{error_msg} (code: {data.get('errcode')})")
            return ""

    def upload_image(self, image_path: str) -> str:
        """上传图片，返回图片 URL（用于文章内容）"""
        if not self.access_token:
            self.get_access_token()

        url = f"{self.base_url}/cgi-bin/media/uploadimg"
        params = {"access_token": self.access_token}

        with open(image_path, 'rb') as f:
            files = {"media": f}
            response = self.session.post(url, files=files, params=params, timeout=60)

        data = response.json()

        if "url" in data:
            logger.info(f"✓ 图片上传成功：{image_path}, url: {data['url']}")
            return data["url"]
        else:
            error_msg = data.get("errmsg", "未知错误")
            logger.error(f"✗ 图片上传失败：{error_msg}")
            return ""

    def add_draft(self, title: str, content: str, thumb_media_id: str = "") -> Optional[str]:
        """
        添加草稿
        返回 media_id

        微信 API 限制:
        - title: 最多 32 个字符（不是字节）
        - content: HTML 格式
        - thumb_media_id: 必填，封面图片的 media_id
        """
        if not self.access_token:
            self.get_access_token()

        # 标题截断（微信限制 32 个字符）
        if len(title) > 32:
            title = title[:30] + '...'
            logger.info(f"标题截断：{title}")

        url = f"{self.base_url}/cgi-bin/draft/add"
        params = {"access_token": self.access_token}

        # 构建图文消息
        article_data = {
            "title": title,
            "content": content,
            "thumb_media_id": thumb_media_id,  # 必填
            "need_open_comment": 1,  # 打开评论
            "only_fans_can_comment": 0,  # 不限粉丝评论
        }

        payload = {
            "articles": [article_data]
        }

        response = self.session.post(url, json=payload, params=params, timeout=60)
        data = response.json()

        # 调试信息：打印请求大小
        import json as json_module
        request_size = len(json_module.dumps(payload).encode('utf-8'))
        logger.info(f"请求大小：{request_size} 字节，标题：{len(title.encode('utf-8'))} 字节")

        if "media_id" in data:
            logger.info(f"✓ 草稿添加成功，media_id: {data['media_id']}")
            return data["media_id"]
        else:
            error_msg = data.get("errmsg", "未知错误")
            logger.error(f"✗ 草稿添加失败：{error_msg} (code: {data.get('errcode')})")
            return None

    def publish_article(self, article_path: str, imgs_dir: str) -> Tuple[bool, str]:
        """
        发布单篇文章
        返回 (成功标志，media_id 或错误信息)
        """
        # 读取文章文件
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析 frontmatter
        title = ""
        summary = ""

        if "---" in content:
            parts = content.split("---")
            if len(parts) >= 3:
                frontmatter = parts[1]
                article_body = parts[2].strip()

                # 从 frontmatter 提取 title
                for line in frontmatter.split("\n"):
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip().strip('"\'')
                        break
                    elif line.startswith("summary:"):
                        summary = line.split(":", 1)[1].strip().strip('"\'')
            else:
                article_body = content
        else:
            article_body = content
            # 备用标题提取
            if "title:" in content:
                title = content.split("title:")[1].split("\n")[0].strip().strip('"\'')

        # 移除标题中的分类前缀 [分类]
        if title.startswith("["):
            if "]" in title:
                title = title.split("]", 1)[1].strip()

        # 确保标题不超过 32 字节（微信限制，中文约 10-12 字）
        title_bytes = title.encode('utf-8')
        if len(title_bytes) > 30:  # 微信限制约 30 字节（10 个中文字）
            # 按字节截断，避免中文乱码
            while len(title.encode('utf-8')) > 27:  # 27 字节 + '...' = 30 字节
                title = title[:-1]
            title = title + '...'
            logger.info(f"标题截断：{title} ({len(title.encode('utf-8'))} 字节)")
        logger.info(f"最终标题：{title} ({len(title)} 字符，{len(title.encode('utf-8'))} 字节)")

        # 将 markdown 转换为 HTML（简化版）
        html_content = self._markdown_to_html(article_body)

        # 查找封面图
        cover_url = ""
        cover_file = Path(imgs_dir) / f"{Path(article_path).stem.replace('-formatted', '')}.png"
        if not cover_file.exists():
            # 尝试查找 cover.png
            cover_file = Path(imgs_dir) / "cover.png"

        if cover_file.exists():
            logger.info(f"找到封面图：{cover_file}")
            # 上传永久图片素材获取 media_id
            cover_media_id = self.upload_permanent_material(str(cover_file))
            if cover_media_id:
                cover_url = cover_media_id
            else:
                logger.warning("封面图上传失败，使用默认封面")

        # 添加草稿 - 不再添加 [每日精选] 前缀，避免标题超长
        media_id = self.add_draft(title, html_content, cover_url)

        if media_id:
            return True, media_id
        else:
            return False, "添加草稿失败"

    def _markdown_to_html(self, markdown: str) -> str:
        """
        简单的 markdown 转 HTML 转换器
        """
        html = markdown

        # 标题
        html = html.replace("\n### ", "\n<h3>")
        html = html.replace("\n## ", "\n<h2>")
        html = html.replace("\n# ", "\n<h1>")

        # 加粗
        import re
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

        # 换行
        html = html.replace("\n\n", "</p><p>")
        html = html.replace("\n", "<br>")

        return f"<div class='article'>{html}</div>"


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

    # 获取微信配置
    wechat_app_id = env.get("WECHAT_APP_ID")
    wechat_app_secret = env.get("WECHAT_APP_SECRET")

    if not wechat_app_id or not wechat_app_secret:
        logger.error("✗ 微信公众号配置缺失")
        sys.exit(1)

    logger.info(f"✓ 微信公众号配置：{wechat_app_id[:8]}...")

    # 获取今日文章目录
    date_str = datetime.now().strftime("%Y-%m-%d")
    article_dir = script_dir / "article" / date_str
    formatted_dir = article_dir / "formatted"
    imgs_dir = article_dir / "imgs"

    if not formatted_dir.exists():
        logger.error(f"✗ formatted 目录不存在：{formatted_dir}")
        sys.exit(1)

    # 创建发布器
    publisher = WeChatPublisher(wechat_app_id, wechat_app_secret)

    # 遍历文章（支持两种命名方式）
    articles = sorted(list(formatted_dir.glob("*-formatted.md")) + list(formatted_dir.glob("*.md")))

    # 去重（如果一个文件同时匹配两种模式）
    seen = set()
    unique_articles = []
    for article in articles:
        if article.name not in seen:
            seen.add(article.name)
            unique_articles.append(article)

    articles = unique_articles

    if not articles:
        logger.error("✗ 未找到文章文件")
        sys.exit(1)

    logger.info(f"✓ 找到 {len(articles)} 篇文章待推送")
    logger.info("")

    # 推送结果
    results = []

    for article_file in articles:
        logger.info("=" * 60)
        logger.info(f"推送文章：{article_file.name}")
        logger.info("=" * 60)

        try:
            success, result = publisher.publish_article(str(article_file), str(imgs_dir))

            if success:
                logger.info(f"✓ 推送成功，media_id: {result}")
                results.append({
                    "file": article_file.name,
                    "status": "success",
                    "media_id": result
                })
            else:
                logger.error(f"✗ 推送失败：{result}")
                results.append({
                    "file": article_file.name,
                    "status": "failed",
                    "error": result
                })

        except Exception as e:
            logger.error(f"✗ 推送异常：{e}")
            results.append({
                "file": article_file.name,
                "status": "error",
                "error": str(e)
            })

        logger.info("")

    # 汇总结果
    logger.info("=" * 60)
    logger.info("推送结果汇总")
    logger.info("=" * 60)

    success_count = sum(1 for r in results if r["status"] == "success")
    logger.info(f"成功：{success_count}/{len(results)}")

    for r in results:
        status = "✓" if r["status"] == "success" else "✗"
        logger.info(f"  {status} {r['file']}")

    if success_count == len(results):
        logger.info("")
        logger.info("🎉 全部推送成功！")
        logger.info("查看草稿：https://mp.weixin.qq.com")
        logger.info("路径：内容管理 → 草稿箱")

    # 保存结果
    result_file = article_dir / "push_results.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"结果已保存：{result_file}")


if __name__ == "__main__":
    main()
