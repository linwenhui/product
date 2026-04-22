#!/usr/bin/env python3
"""
Claude Code Skill Invoker - 调用 Claude Code Skills 完成文章生成
"""

import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeCodeSkillInvoker:
    """Claude Code Skill 调用器"""

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent

    def invoke(self, prompt: str, timeout: int = 300, allowed_tools: list = None) -> str:
        """
        调用 Claude Code 执行任务

        Args:
            prompt: 提示词
            timeout: 超时时间（秒）
            allowed_tools: 允许使用的工具列表

        Returns:
            执行结果
        """
        try:
            # 构建 claude 命令
            cmd = ["claude"]

            # 添加允许的工具列表
            if allowed_tools:
                tools_str = ",".join(allowed_tools)
                cmd.extend(["--allowed-tools", tools_str])

            # 添加 prompt（作为最后一个参数）
            cmd.append(prompt)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.base_dir)
            )

            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Claude Code 执行失败：{result.stderr}")
                return ""

        except subprocess.TimeoutExpired:
            logger.error(f"Claude Code 执行超时（{timeout}秒）")
            return ""
        except Exception as e:
            logger.error(f"Claude Code 调用异常：{e}")
            return ""

    def write_article(self, topic: str, research_file: str, output_file: str) -> bool:
        """
        调用 wechat-article-writer skill 撰写文章

        Args:
            topic: 文章主题
            research_file: 资料文件路径
            output_file: 输出文件路径

        Returns:
            是否成功
        """
        prompt = f"""请用 wechat-article-writer skill 撰写一篇关于"{topic}"的公众号文章

要求：
- 1000-1500 字
- 故事化开头，带情感色彩（兴奋/焦虑/好奇）
- 结构：效果展示 → 问题描述 → 步骤教学 → 升华总结
- 生成 5 个爆款标题备选
- 参考资料：{research_file}

输出文件：{output_file}

请按照 skill 定义的完整流程执行。"""

        logger.info(f"调用 wechat-article-writer skill 撰写文章...")
        result = self.invoke(prompt, timeout=600)

        if result:
            # 保存结果
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            logger.info(f"文章已保存到：{output_file}")
            return True
        else:
            logger.error("文章生成失败")
            return False

    def format_markdown(self, article_file: str, output_file: str) -> bool:
        """
        调用 baoyu-format-markdown skill 格式化文章

        Args:
            article_file: 文章文件路径
            output_file: 输出文件路径

        Returns:
            是否成功
        """
        prompt = f"""请用 baoyu-format-markdown skill 格式化这篇文章：{article_file}

要求：
- 添加 frontmatter (title, summary, cover)
- 优化排版：段落、加粗、列表、表格
- 输出文件：{output_file}

请按照 skill 定义的完整流程执行。"""

        logger.info(f"调用 baoyu-format-markdown skill 格式化文章...")
        result = self.invoke(prompt, timeout=300)

        if result:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            logger.info(f"格式化后的文章已保存到：{output_file}")
            return True
        else:
            logger.error("格式化失败")
            return False

    def generate_images(self, article_file: str, image_dir: str, density: str = "balanced") -> bool:
        """
        调用 baoyu-image-gen skill 生成配图

        Args:
            article_file: 文章文件路径
            image_dir: 图片输出目录
            density: 配图密度 (minimal/balanced/rich)

        Returns:
            是否成功
        """
        prompt = f"""请用 baoyu-image-gen skill 为这篇文章生成配图：{article_file}

要求：
- 配图密度：{density}
- 生成封面图 + 内文插图 (3-5 张)
- 输出目录：{image_dir}
- 使用 SEEDREAM 模型（配置已在.baoyu-skills/.env 中）

请按照 skill 定义的完整流程执行。"""

        logger.info(f"调用 baoyu-image-gen skill 生成配图...")
        # 图片生成时间较长，设置更长的超时
        result = self.invoke(prompt, timeout=900, allowed_tools=["WebSearch", "Bash", "Write", "Read", "Edit", "Glob", "Grep", "BatchWrite"])

        if result:
            logger.info(f"配图已生成到：{image_dir}")
            return True
        else:
            logger.error("配图生成失败")
            return False

    def generate_cover_image(self, title: str, image_dir: str, style: str = "tech") -> bool:
        """
        调用 baoyu-image-gen skill 生成封面图

        Args:
            title: 文章标题
            image_dir: 图片输出目录
            style: 图片风格 (tech/science/minimalist/artistic)

        Returns:
            是否成功
        """
        prompt = f"""请用 baoyu-image-gen skill 生成文章封面图

要求：
- 标题：{title}
- 风格：{style}
- 尺寸：16:9
- 输出目录：{image_dir}
- 使用 SEEDREAM 模型（配置已在.baoyu-skills/.env 中）

请按照 skill 定义的完整流程执行。"""

        logger.info(f"调用 baoyu-image-gen skill 生成封面图...")
        result = self.invoke(prompt, timeout=300, allowed_tools=["WebSearch", "Bash", "Write", "Read", "Edit", "Glob", "Grep", "BatchWrite"])

        if result:
            logger.info(f"封面图已生成到：{image_dir}")
            return True
        else:
            logger.error("封面图生成失败")
            return False

    def publish_wechat(self, article_file: str, draft_mode: bool = True) -> bool:
        """
        调用 baoyu-post-to-wechat skill 发布到微信

        Args:
            article_file: 文章文件路径
            draft_mode: 是否仅存为草稿

        Returns:
            是否成功
        """
        mode = "draft" if draft_mode else "publish"
        prompt = f"""请用 baoyu-post-to-wechat skill 发布这篇文章到微信公众号：{article_file}

模式：{mode}
使用 API 方式发布（非浏览器）

请按照 skill 定义的完整流程执行。"""

        logger.info(f"调用 baoyu-post-to-wechat skill 发布文章...")
        result = self.invoke(prompt, timeout=300)

        if result:
            logger.info("文章发布成功!")
            return True
        else:
            logger.error("文章发布失败")
            return False


def main():
    """测试"""
    invoker = ClaudeCodeSkillInvoker()

    # 测试调用
    print("测试 Claude Code Skill Invoker")
    print("=" * 50)

    # 简单测试
    result = invoker.invoke("你好，请用一句话介绍你自己")
    print(result)


if __name__ == "__main__":
    main()
