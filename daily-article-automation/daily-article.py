#!/usr/bin/env python3
"""
Daily Article Automation - 每日自动公众号文章生成与发布系统

主编排脚本，按顺序调用各技能完成文章生成和发布
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily-article.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from hot_topic_aggregator import HotTopicAggregator

# 延迟加载 Skill Invoker（可选依赖）
try:
    from claude_skill_invoker import ClaudeCodeSkillInvoker
    HAS_SKILL_INVOKER = True
except ImportError:
    HAS_SKILL_INVOKER = False
    logger.info("ClaudeCodeSkillInvoker not available, will use placeholder content")


class DailyArticleAutomation:
    """每日文章自动化编排器"""

    def __init__(self, config_path: str = "config.yaml", base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.config_path = self.base_dir / config_path
        self.config = self._load_config()
        self.article_dir: Optional[Path] = None
        self.materials_dir: Optional[Path] = None
        self.skill_invoker: Optional[ClaudeCodeSkillInvoker] = None if HAS_SKILL_INVOKER else None

    def _load_config(self) -> dict:
        """加载配置文件"""
        import yaml
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def _ensure_dirs(self, date_str: str):
        """创建必要的目录"""
        self.article_dir = self.base_dir / "article" / date_str
        self.materials_dir = self.article_dir / "research_materials"
        self.imgs_dir = self.article_dir / "imgs"

        self.article_dir.mkdir(parents=True, exist_ok=True)
        self.materials_dir.mkdir(parents=True, exist_ok=True)
        self.imgs_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created directories: {self.article_dir}")

    def step1_fetch_hot_topics(self) -> dict:
        """Step 1: 热点聚合"""
        logger.info("=" * 60)
        logger.info("Step 1: 热点聚合 (Hot Topic Aggregator)")
        logger.info("=" * 60)

        aggregator = HotTopicAggregator(str(self.config_path))
        topics = aggregator.fetch_all()

        # 保存热点数据
        topics_file = self.article_dir / "ranked_topics.json"
        aggregator.save_to_json(str(topics_file))

        logger.info(f"Fetched {len(topics)} hot topics")
        for i, topic in enumerate(topics[:5], 1):
            logger.info(f"  TOP{i}: [{topic.source}] {topic.topic} (score: {topic.score})")

        # 按分类获取 TOP3 话题
        categorized_topics = aggregator.get_top_topics_by_category(top_n=1)
        selected_topics = []
        for category, cats_topics in categorized_topics.items():
            if cats_topics:
                selected_topics.append(cats_topics[0])

        return {
            "topics": topics,
            "categorized_topics": categorized_topics,
            "selected_topics": selected_topics,
            "file": str(topics_file)
        }

    def step2_select_topics(self, topics_data: dict) -> dict:
        """Step 2: 选择 TOP3 话题（按分类：时事，科技，民生）"""
        logger.info("=" * 60)
        logger.info("Step 2: 选择 TOP3 话题（按分类）")
        logger.info("=" * 60)

        selected_topics = topics_data.get("selected_topics", [])
        if not selected_topics:
            raise ValueError("No topics available for selection")

        # 生成选题文件
        topic_file = self.article_dir / "selected_topics.md"
        with open(topic_file, 'w', encoding='utf-8') as f:
            f.write(f"""---
generated_at: {datetime.now().isoformat()}
categories: ['时事', '科技', '民生']
total_topics: {len(selected_topics)}
---

# 今日选题：TOP3 热点话题

## 选题概览

| 分类 | 话题 | 来源 | score | 热度 |
|------|------|------|-------|------|
""")
            for topic in selected_topics:
                f.write(f"| {topic.category} | {topic.topic} | {topic.source} | {topic.score} | {topic.heat_value} |\n")

            f.write(f"""

## 详细选题

""")
            for i, topic in enumerate(selected_topics, 1):
                f.write(f"""
### TOP{i}: [{topic.category}] {topic.topic}

- **来源**: {topic.source}
- **热度**: {topic.heat_value}
- **综合得分**: {topic.score}
- **关键词**: {', '.join(topic.keywords)}
- **链接**: {topic.url}

""")

        logger.info(f"Selected {len(selected_topics)} topics:")
        for topic in selected_topics:
            logger.info(f"  [{topic.category}] {topic.topic} (score: {topic.score})")
        logger.info(f"Saved to: {topic_file}")

        return {
            "topics": selected_topics,
            "file": str(topic_file)
        }

    def step3_research(self, topics_data: dict) -> dict:
        """Step 3: 资料搜集（针对 TOP3 话题）"""
        logger.info("=" * 60)
        logger.info("Step 3: 资料搜集 (Parallel WebSearch)")
        logger.info("=" * 60)

        selected_topics = topics_data.get("topics", [])

        # 创建研究材料目录
        research_dir = self.materials_dir
        research_file = research_dir / "research_summary.md"

        research_content = "# 资料搜集：今日 TOP3 热点话题\n\n"
        research_content += f"搜集时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        search_queries = []

        for topic in selected_topics:
            topic_str = topic.topic if hasattr(topic, 'topic') else topic.get("topic", "")
            category = topic.category if hasattr(topic, 'category') else topic.get("category", "")

            research_content += f"## [{category}] {topic_str}\n\n"

            # 为每个话题生成搜索查询
            topic_queries = [
                f"{topic_str} 最新进展 2026",
                f"{topic_str} 教程 技巧",
                f"{topic_str} 使用方法",
            ]
            search_queries.extend(topic_queries)

            for query in topic_queries:
                research_content += f"### 搜索：{query}\n"
                research_content += "〔研究内容待填充〕\n\n"

            research_content += "\n"

        with open(research_file, 'w', encoding='utf-8') as f:
            f.write(research_content)

        logger.info(f"Research materials saved to: {research_file}")

        return {
            "research_dir": str(research_dir),
            "research_file": str(research_file),
            "queries": search_queries,
            "topics": selected_topics
        }

    def step4_write_article(self, research_data: dict, use_skills: bool = True) -> dict:
        """Step 4: 文章撰写 (针对 TOP3 话题，使用 wechat-article-writer skill)"""
        logger.info("=" * 60)
        logger.info("Step 4: 文章撰写 (WeChat Article Writer - TOP3 Topics)")
        logger.info("=" * 60)

        selected_topics = research_data.get("topics", [])
        article_files = []

        for topic in selected_topics:
            topic_str = topic.topic if hasattr(topic, 'topic') else topic.get("topic", "")
            category = topic.category if hasattr(topic, 'category') else topic.get("category", "")

            # 生成文章文件路径（带分类前缀）
            slug = self._generate_slug(f"{category}_{topic_str}")
            article_file = self.article_dir / f"{slug}.md"

            # 检查是否可以使用 Skills
            can_use_skills = HAS_SKILL_INVOKER and use_skills

            if can_use_skills:
                # 调用 Claude Code Skill
                if not self.skill_invoker:
                    self.skill_invoker = ClaudeCodeSkillInvoker(str(self.base_dir))

                success = self.skill_invoker.write_article(
                    topic=f"[{category}] {topic_str}",
                    research_file=research_data.get('research_file', ''),
                    output_file=str(article_file)
                )

                if success:
                    logger.info(f"文章生成成功：{article_file}")
                else:
                    logger.warning("文章生成失败，使用占位内容")
                    self._write_placeholder_article(article_file, f"[{category}] {topic_str}")
            else:
                if not HAS_SKILL_INVOKER:
                    logger.info("Skill Invoker 不可用，使用占位内容")
                self._write_placeholder_article(article_file, f"[{category}] {topic_str}")

            article_files.append({
                "file": str(article_file),
                "slug": slug,
                "category": category,
                "topic": topic_str
            })

        return {
            "article_files": article_files,
            "use_skills": can_use_skills if selected_topics else False
        }

    def _write_placeholder_article(self, article_file: Path, topic_str: str):
        """生成占位文章（当 Skill 调用失败时）"""
        placeholder_content = f"""---
title: 「{topic_str}」深度教程
summary: 本文详细介绍{topic_str}的实用技巧和方法
keywords: [{topic_str}]
date: {datetime.now().strftime('%Y-%m-%d')}
---

# {topic_str}

〔文章内容待 wechat-article-writer skill 生成〕

"""
        with open(article_file, 'w', encoding='utf-8') as f:
            f.write(placeholder_content)

    def step5_format_markdown(self, article_data: dict) -> dict:
        """Step 5: 格式化优化 (针对 TOP3 文章，使用 baoyu-format-markdown skill)"""
        logger.info("=" * 60)
        logger.info("Step 5: 格式化优化 (Markdown Formatter - TOP3)")
        logger.info("=" * 60)

        article_files = article_data.get("article_files", [])
        formatted_files = []

        for article_info in article_files:
            article_file = article_info.get("file")

            # 调用 baoyu-format-markdown skill
            formatted_file = self.article_dir / f"{Path(article_file).stem}-formatted.md"

            logger.info(f"Formatting: {article_file} -> {formatted_file}")

            formatted_files.append({
                "file": str(formatted_file),
                "original_file": article_file,
                "category": article_info.get("category"),
                "topic": article_info.get("topic")
            })

        return {
            "formatted_files": formatted_files,
            "original_files": article_files
        }

    def step6_generate_images(self, article_data: dict) -> dict:
        """Step 6: 生成配图 (使用 baoyu-image-gen skill)"""
        logger.info("=" * 60)
        logger.info("Step 6: 生成配图 (Image Generation - baoyu-image-gen)")
        logger.info("=" * 60)

        formatted_files = article_data.get("formatted_files", [])
        image_density = self.config.get("article", {}).get("image_density", "balanced")

        logger.info(f"Generating images for {len(formatted_files)} articles")
        logger.info(f"Image density: {image_density}")

        # 为每篇文章生成配图
        for article_info in formatted_files:
            logger.info(f"  - {article_info.get('category')}: {article_info.get('topic')}")

        return {
            "image_dir": str(self.imgs_dir),
            "density": image_density,
            "articles": formatted_files
        }

    def step7_publish_wechat(self, article_data: dict) -> dict:
        """Step 7: 发布到微信 (针对 TOP3 文章，使用 baoyu-post-to-wechat skill)"""
        logger.info("=" * 60)
        logger.info("Step 7: 发布到微信 (WeChat Publisher - TOP3)")
        logger.info("=" * 60)

        formatted_files = article_data.get("formatted_files", [])
        auto_publish = self.config.get("article", {}).get("auto_publish", False)

        published_files = []

        for article_info in formatted_files:
            article_file = article_info.get("file")

            if auto_publish:
                logger.info(f"Publishing article: {article_file}")
                # 调用 baoyu-post-to-wechat API
                # bun run scripts/wechat-api.ts <file> --theme default
            else:
                logger.info(f"Draft mode - article ready for manual review: {article_file}")

            published_files.append(article_info)

        return {
            "article_files": [f.get("file") for f in published_files],
            "auto_publish": auto_publish,
            "mode": "publish" if auto_publish else "draft"
        }

    def step8_notify(self, result_data: dict):
        """Step 8: 通知与日志"""
        logger.info("=" * 60)
        logger.info("Step 8: 通知与日志")
        logger.info("=" * 60)

        # 记录最终日志
        logger.info(f"Article generation completed!")
        logger.info(f"Mode: {result_data.get('publish', {}).get('mode', 'draft')}")
        logger.info(f"Article: {result_data.get('publish', {}).get('article_file')}")

        # 发送通知
        notify_method = self.config.get("notification", {}).get("method", "wechat")
        recipient = self.config.get("notification", {}).get("recipient", "")

        if recipient:
            logger.info(f"Sending {notify_method} notification to: {recipient}")
            # 调用通知脚本

    def _generate_slug(self, text: str) -> str:
        """生成 URL slug"""
        # 简化版：中文转拼音，英文转小写连字符
        import re
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug[:50]  # 限制长度
        return slug or "daily-article"

    def run(self, dry_run: bool = False, draft_only: bool = False, step: str = None):
        """运行完整流程"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        self._ensure_dirs(date_str)

        if draft_only:
            self.config.setdefault("article", {})["auto_publish"] = False

        results = {}

        # 支持逗号分隔的多个步骤
        steps = []
        if step:
            steps = [s.strip() for s in step.split(",")]

        try:
            # Step 1: 热点聚合
            if not steps or "1" in steps:
                results["hot_topics"] = self.step1_fetch_hot_topics()

            # Step 2: 选择话题 (TOP3 by category)
            if not steps or "2" in steps:
                results["topics"] = self.step2_select_topics(results.get("hot_topics", {}))

            # Step 3: 资料搜集
            if not steps or "3" in steps:
                results["research"] = self.step3_research(results.get("topics", {}))

            # Step 4: 撰写文章 (TOP3)
            if not steps or "4" in steps:
                results["article"] = self.step4_write_article(
                    results.get("research", {})
                )

            # Step 5: 格式化
            if not steps or "5" in steps:
                results["format"] = self.step5_format_markdown(results.get("article", {}))

            # Step 6: 生成图片
            if not steps or "6" in steps:
                results["images"] = self.step6_generate_images(results.get("format", {}) or results.get("article", {}))

            # Step 7: 发布
            if not steps or "7" in steps:
                results["publish"] = self.step7_publish_wechat(results.get("format", {}) or results.get("article", {}))

            # Step 8: 通知
            if not steps or "8" in steps:
                self.step8_notify(results)

            logger.info("\n" + "=" * 60)
            logger.info("✅ 每日文章生成完成！(TOP3 热点话题)")
            logger.info("=" * 60)

            if dry_run:
                logger.info("📝 DRY RUN 模式 - 未执行实际操作")

            return results

        except Exception as e:
            logger.error(f"❌ 流程失败：{e}", exc_info=True)
            raise


def main():
    parser = argparse.ArgumentParser(
        description="每日自动公众号文章生成与发布系统 (TOP3 热点话题)"
    )
    parser.add_argument(
        "--config", default="config.yaml",
        help="配置文件路径"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Dry run 模式，不执行实际操作"
    )
    parser.add_argument(
        "--draft-only", action="store_true",
        help="仅生成草稿，不发布"
    )
    parser.add_argument(
        "--step", action="append", choices=["1", "2", "3", "4", "5", "6", "7", "8"],
        help="仅执行指定步骤 (可指定多个)"
    )
    parser.add_argument(
        "--base-dir", default=None,
        help="基础目录路径"
    )

    args = parser.parse_args()

    # 将 step 列表转换为逗号分隔的字符串
    step_str = None
    if args.step:
        step_str = ",".join(args.step)

    automation = DailyArticleAutomation(
        config_path=args.config,
        base_dir=args.base_dir
    )

    results = automation.run(
        dry_run=args.dry_run,
        draft_only=args.draft_only,
        step=step_str
    )

    print("\n最终结果:")
    for key, value in results.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
