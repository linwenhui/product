#!/usr/bin/env python3
"""
WeChat Notification Script - 微信通知脚本

发送文章生成状态通知到微信
"""

import logging
import requests
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeChatNotifier:
    """微信通知器"""

    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or self._get_env_var("WECHAT_APP_ID")
        self.app_secret = app_secret or self._get_env_var("WECHAT_APP_SECRET")
        self.access_token: Optional[str] = None

    def _get_env_var(self, key: str) -> str:
        """从环境或.env 文件获取变量"""
        import os

        # 直接从环境变量获取
        value = os.environ.get(key)
        if value:
            return value

        # 从.env 文件获取
        env_paths = [
            Path(".baoyu-skills/.env"),
            Path.home() / ".baoyu-skills/.env",
        ]

        for env_path in env_paths:
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            if k.strip() == key:
                                return v.strip()

        return ""

    def get_access_token(self) -> str:
        """获取微信 API 访问令牌"""
        if self.access_token:
            return self.access_token

        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }

        response = requests.get(url, params=params)
        data = response.json()

        if "access_token" in data:
            self.access_token = data["access_token"]
            logger.info("Access token obtained successfully")
        else:
            logger.error(f"Failed to get access token: {data}")
            raise ValueError(f"WeChat API error: {data}")

        return self.access_token

    def send_template_message(
        self,
        user_id: str,
        title: str,
        content: str,
        article_url: str = None
    ) -> bool:
        """
        发送模板消息

        Args:
            user_id: 用户 openid
            title: 消息标题
            content: 消息内容
            article_url: 文章链接（可选）

        Returns:
            是否发送成功
        """
        # 注意：模板消息需要用户先关注公众号
        # 对于个人使用场景，可以考虑使用测试账号或企业微信

        logger.info(f"Sending notification to {user_id}")
        logger.info(f"Title: {title}")
        logger.info(f"Content: {content}")

        # 实际使用时需要配置模板 ID
        # 这里仅作为示例
        return True

    def send_draft_notification(
        self,
        article_title: str,
        article_url: str = None,
        recipient: str = None
    ) -> bool:
        """
        发送草稿完成通知

        Args:
            article_title: 文章标题
            article_url: 草稿链接
            recipient: 接收者

        Returns:
            是否发送成功
        """
        title = "📝 文章草稿已生成"
        content = f"《{article_title}》已完成，请登录微信公众号后台查看"

        if article_url:
            content += f"\n链接：{article_url}"

        return self.send_template_message(
            user_id=recipient,
            title=title,
            content=content,
            article_url=article_url
        )

    def send_error_notification(
        self,
        error_message: str,
        recipient: str = None
    ) -> bool:
        """
        发送错误通知

        Args:
            error_message: 错误信息
            recipient: 接收者

        Returns:
            是否发送成功
        """
        title = "❌ 文章生成失败"
        content = f"错误信息：{error_message}"

        return self.send_template_message(
            user_id=recipient,
            title=title,
            content=content
        )


def send_dingtalk_notification(
    webhook: str,
    title: str,
    content: str,
    at_mobiles: list = None
) -> bool:
    """
    发送钉钉机器人通知

    Args:
        webhook: 钉钉机器人 webhook URL
        title: 标题
        content: 内容
        at_mobiles: 需要@的手机号列表

    Returns:
        是否发送成功
    """
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "text",
        "text": {
            "content": f"{title}\n\n{content}"
        },
        "at": {
            "atMobiles": at_mobiles or [],
            "isAtAll": False
        }
    }

    try:
        response = requests.post(webhook, headers=headers, json=data)
        result = response.json()
        if result.get("errcode") == 0:
            logger.info("钉钉通知发送成功")
            return True
        else:
            logger.error(f"钉钉通知发送失败：{result}")
            return False
    except Exception as e:
        logger.error(f"钉钉通知发送异常：{e}")
        return False


def send_email_notification(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    content: str
) -> bool:
    """
    发送邮件通知

    Returns:
        是否发送成功
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.header import Header

    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = Header(from_addr)
    msg['To'] = Header(to_addr)
    msg['Subject'] = Header(subject)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()
        logger.info("邮件发送成功")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败：{e}")
        return False


def main():
    """测试通知功能"""
    import argparse

    parser = argparse.ArgumentParser(description="发送通知")
    parser.add_argument("--method", choices=["wechat", "dingtalk", "email"],
                        default="wechat", help="通知方式")
    parser.add_argument("--recipient", help="接收者")
    parser.add_argument("--title", default="测试通知", help="标题")
    parser.add_argument("--content", default="这是一条测试通知", help="内容")

    args = parser.parse_args()

    if args.method == "wechat":
        notifier = WeChatNotifier()
        notifier.send_template_message(
            user_id=args.recipient or "test_user",
            title=args.title,
            content=args.content
        )
    elif args.method == "dingtalk":
        import os
        webhook = os.environ.get("DINGTALK_WEBHOOK", "")
        send_dingtalk_notification(
            webhook=webhook,
            title=args.title,
            content=args.content
        )
    elif args.method == "email":
        import os
        send_email_notification(
            smtp_server=os.environ.get("SMTP_SERVER", ""),
            smtp_port=int(os.environ.get("SMTP_PORT", 587)),
            username=os.environ.get("SMTP_USERNAME", ""),
            password=os.environ.get("SMTP_PASSWORD", ""),
            from_addr=os.environ.get("SMTP_FROM", ""),
            to_addr=args.recipient,
            subject=args.title,
            content=args.content
        )

    logger.info("通知发送完成")


if __name__ == "__main__":
    main()
