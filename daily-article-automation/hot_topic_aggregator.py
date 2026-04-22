#!/usr/bin/env python3
"""
Hot Topic Aggregator - 热点聚合模块

从多平台获取热点并综合排名
重点关注:
  - 知乎热榜 (Zhihu Hot List)
  - 百度热搜 (Baidu Hot Search)
其他来源:
  - 微博热搜
  - 抖音热点
  - 今日头条
  - B 站热门
"""

import json
import logging
import random
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Playwright for JavaScript-heavy sites
try:
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Playwright not installed. Install with: pip install playwright playwright-stealth")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PoliteRequester:
    """礼貌的请求发送器"""

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15',
    ]

    def __init__(self, min_delay: float = 2.0, max_delay: float = 4.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_per_domain: dict[str, float] = {}
        self.session = requests.Session()

    def get_headers(self) -> dict:
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def get_api_headers(self) -> dict:
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

    def wait_for_domain(self, url: str):
        domain = urlparse(url).netloc
        last_request = self.last_request_per_domain.get(domain, 0)
        elapsed = time.time() - last_request
        delay = random.uniform(self.min_delay, self.max_delay)

        if elapsed < delay:
            time.sleep(delay - elapsed)

        self.last_request_per_domain[domain] = time.time()

    def fetch(self, url: str, retry_count: int = 3) -> Optional[requests.Response]:
        for attempt in range(retry_count):
            try:
                self.wait_for_domain(url)
                response = self.session.get(url, headers=self.get_headers(), timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt == retry_count - 1:
                    logger.error(f"Failed to fetch {url} after {retry_count} attempts: {e}")
                    return None
                time.sleep(2 ** attempt)
        return None


class PlaywrightScraper:
    """Playwright scraper for JavaScript-heavy sites"""

    def __init__(self):
        self.stealth_instance = Stealth() if PLAYWRIGHT_AVAILABLE else None

    def fetch_with_extraction(self, url: str, extract_fn, wait_selector: str = None) -> Optional[list]:
        if not PLAYWRIGHT_AVAILABLE:
            return None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                ])

                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=random.choice(PoliteRequester.USER_AGENTS),
                    locale='zh-CN',
                )

                page = context.new_page()
                self.stealth_instance.apply_stealth_sync(page)

                page.add_init_script('''
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                ''')

                page.goto(url, wait_until='networkidle', timeout=30000)

                if wait_selector:
                    try:
                        page.wait_for_selector(wait_selector, timeout=10000)
                    except Exception:
                        pass

                page.wait_for_timeout(5000)
                result = extract_fn(page)
                browser.close()
                return result

        except Exception as e:
            logger.debug(f"Playwright extraction failed for {url}: {e}")
            return None


@dataclass
class HotTopic:
    """热点话题数据结构"""
    topic: str
    score: float
    source: str
    rank: int
    heat_value: float = 0.0
    keywords: list = None
    url: str = ""
    timestamp: str = ""
    category: str = ""

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.category:
            self.category = self._classify_category()

    def _classify_category(self) -> str:
        topic_text = self.topic.lower() + ' ' + ' '.join(self.keywords).lower()

        tech_keywords = ['ai', '人工智能', '科技', '互联网', '数码', '技术', '软件', '硬件',
                        'app', '芯片', '算法', '模型', '自动驾驶', '机器人',
                        '区块链', 'web3', '元宇宙', 'vr', 'ar', '5g', '6g',
                        '手机', '电脑', '游戏', '电竞', '动画', '动漫', 'b 站', '哔哩哔哩',
                        '抖音', 'tiktok', '直播', '网红', '博主', 'up 主', '大模型',
                        '显卡', 'cpu', 'gpu', '编程', '代码', '程序员', '云计算', '大数据']

        livelihood_keywords = ['生活', '健康', '教育', '住房', '就业', '工资', '物价', '医疗',
                              '养老', '社保', '医保', '食品', '交通', '旅游', '购物', '消费',
                              '房价', '学区', '考研', '考公', '面试', '招聘', '失业', '创业',
                              '减肥', '美容', '护肤', '穿搭', '美妆', '美食', '餐厅', '酒店',
                              '恋爱', '婚姻', '相亲', '情感', '心理', '宠物', '健身', '运动',
                              '学校', '学生', '老师', '高考', '中考', '大学', '假期', '放假',
                              '旅游', '出行', '火车', '飞机', '地铁', '公交', '校园']

        current_events_keywords = ['政治', '国际', '社会', '政策', '新闻', '政府', '国务院',
                                  '外交', '军事', '战争', '选举', '投票', '法律', '法规',
                                  '会议', '峰会', '制裁', '贸易', '关税', '疫情', '灾害',
                                  '地震', '火灾', '事故', '案件', '判决', '逮捕', '调查',
                                  '总统', '主席', '总理', '部长', '使馆', '领事馆', '中国',
                                  '国家', '冲突', '国防', '外交部', '公安部']

        entertainment_keywords = ['明星', '演员', '歌手', '电影', '电视剧', '综艺', '演唱会',
                                 '恋情', '离婚', '结婚', '偶像', '粉丝', '八卦', '网红',
                                 '主播', 'mv', '专辑', '影评', '剧评', '选秀', '娱乐圈']

        tech_score = sum(1 for k in tech_keywords if k in topic_text)
        livelihood_score = sum(1 for k in livelihood_keywords if k in topic_text)
        current_events_score = sum(1 for k in current_events_keywords if k in topic_text)
        entertainment_score = sum(1 for k in entertainment_keywords if k in topic_text)

        max_score = max(tech_score, livelihood_score, current_events_score, entertainment_score)

        if max_score == 0:
            # 默认分类逻辑
            if self.source in ['bilibili']:
                return '科技'
            elif self.source in ['zhihu']:
                return '时事'
            elif self.source in ['weibo', 'douyin']:
                return '娱乐'
            else:
                return '民生'

        if tech_score == max_score:
            return '科技'
        elif livelihood_score == max_score:
            return '民生'
        elif current_events_score == max_score:
            return '时事'
        else:
            return '娱乐'


class HotTopicAggregator:
    """热点聚合器"""

    SOURCE_WEIGHTS = {
        "baidu": 0.35,
        "zhihu": 0.35,
        "bilibili": 0.30,
        "weibo": 0.15,
        "douyin": 0.12,
        "toutiao": 0.08,
    }

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path) if config_path else {}
        self.topics: list[HotTopic] = []
        self.requester = PoliteRequester()
        self.playwright_scraper = PlaywrightScraper() if PLAYWRIGHT_AVAILABLE else None

    def _load_config(self, config_path: str) -> dict:
        if Path(config_path).exists():
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def fetch_bilibili(self) -> list[dict]:
        """获取 B 站热门视频"""
        logger.info("Fetching topics from Bilibili...")

        if self.playwright_scraper:
            topics = self._fetch_bilibili_playwright()
            if topics:
                logger.info(f"Fetched {len(topics)} topics from Bilibili (Playwright)")
                return topics

        return self._fetch_bilibili_api()

    def fetch_weibo(self) -> list[dict]:
        """获取微博热搜"""
        logger.info("Fetching topics from Weibo...")
        return self._fetch_weibo_mobile_api()

    def _fetch_weibo_mobile_api(self) -> list[dict]:
        """通过微博移动版 API 获取热搜"""
        urls = [
            'https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_4181',
            'https://weibo.com/ajax/side/hotSearch',
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json',
        }

        for url in urls:
            try:
                self.requester.wait_for_domain(url)
                response = self.requester.session.get(url, headers=headers, timeout=30)
                if response.status_code != 200:
                    continue

                data = response.json()
                topics = []

                # Try different response structures
                realtime = data.get('data', {}).get('realtime', [])
                if not realtime:
                    cards = data.get('data', {}).get('cards', [])
                    if cards:
                        for card in cards:
                            word = card.get('word', '') or card.get('note', {}).get('word', '')
                            hot = card.get('hot', 0) or card.get('note', {}).get('hot', 0)
                            if word:
                                topics.append({
                                    "topic": word,
                                    "heat": hot if isinstance(hot, (int, float)) else 0,
                                    "keywords": self._extract_keywords(word),
                                    "url": f"https://s.weibo.com/weibo/{word}"
                                })
                else:
                    for item in realtime:
                        note = item.get('note', {})
                        word = note.get('word') or item.get('word', '')
                        hot = note.get('hot') or item.get('hot', 0)
                        if word:
                            topics.append({
                                "topic": word,
                                "heat": hot if isinstance(hot, (int, float)) else 0,
                                "keywords": self._extract_keywords(word),
                                "url": f"https://s.weibo.com/weibo/{word}"
                            })

                if topics:
                    logger.info(f"Fetched {len(topics)} topics from Weibo")
                    return topics[:20]

            except Exception as e:
                logger.debug(f"Weibo API failed: {e}")
                continue

        return []

    def fetch_zhihu(self) -> list[dict]:
        """获取知乎热榜"""
        logger.info("Fetching topics from Zhihu...")
        return self._fetch_zhihu_hotlist()

    def _parse_zhihu_heat_value(self, detail_text: str) -> int:
        """从知乎 detail_text 中解析热度值，如 '3058 万热度' -> 30580000"""
        if not detail_text:
            return 0

        # 匹配 "X 万热度" 格式
        match = re.search(r'([\d.]+)\s*万', detail_text)
        if match:
            return int(float(match.group(1)) * 10000)

        # 匹配纯数字格式
        match = re.search(r'([\d,]+)', detail_text)
        if match:
            return int(match.group(1).replace(',', ''))

        return 0

    def _fetch_zhihu_hotlist(self) -> list[dict]:
        """获取知乎热榜列表"""
        url = 'https://api.zhihu.com/topstory/hot-lists/total?limit=50'
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)',
            'Accept': 'application/json',
        }

        try:
            self.requester.wait_for_domain(url)
            response = self.requester.session.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                topics = []

                for item in data.get('data', []):
                    target = item.get('target', {})
                    title = target.get('title', '')
                    # 从 detail_text 字段获取热度值，如 "3058 万热度"
                    detail_text = item.get('detail_text', '')
                    hot = self._parse_zhihu_heat_value(detail_text)

                    if title:
                        topics.append({
                            "topic": title,
                            "heat": hot,
                            "keywords": self._extract_keywords(title),
                            "url": f"https://www.zhihu.com/question/{target.get('id', '')}"
                        })

                if topics:
                    logger.info(f"Fetched {len(topics)} topics from Zhihu")
                    return topics[:20]

        except Exception as e:
            logger.debug(f"Zhihu API failed: {e}")

        return []

    def fetch_douyin(self) -> list[dict]:
        """获取抖音热点"""
        logger.info("Fetching topics from Douyin...")
        return self._fetch_douyin_hotsearch()

    def _fetch_douyin_hotsearch(self) -> list[dict]:
        """获取抖音热点搜索列表"""
        url = 'https://www.douyin.com/aweme/v1/web/hot/search/list/'
        params = {
            'device_platform': 'webapp',
            'aid': '6383',
            'channel': 'channel_pc_web',
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }

        try:
            self.requester.wait_for_domain(url)
            response = self.requester.session.get(url, params=params, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                topics = []

                word_list = data.get('data', {}).get('word_list', [])
                for item in word_list[:20]:
                    word = item.get('word', '')
                    hot_value = item.get('hot_value', 0)

                    if word:
                        topics.append({
                            "topic": word,
                            "heat": hot_value if isinstance(hot_value, (int, float)) else 0,
                            "keywords": self._extract_keywords(word),
                            "url": f"https://www.douyin.com/hot/{item.get('sentence_id', '')}"
                        })

                if topics:
                    logger.info(f"Fetched {len(topics)} topics from Douyin")
                    return topics

        except Exception as e:
            logger.debug(f"Douyin API failed: {e}")

        return []

    def fetch_toutiao(self) -> list[dict]:
        """获取今日头条热点"""
        logger.info("Fetching topics from Toutiao...")
        return self._fetch_toutiao_hotboard()

    def fetch_baidu(self) -> list[dict]:
        """获取百度热搜"""
        logger.info("Fetching topics from Baidu...")
        return self._fetch_baidu_hotboard()

    def _fetch_baidu_hotboard(self) -> list[dict]:
        """获取百度热搜榜单"""
        url = 'https://top.baidu.com/board?tab=realtime'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

        try:
            self.requester.wait_for_domain(url)
            response = self.requester.session.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                html = response.text

                # 提取热点数据："word":"xxx","hotScore":"123456"
                pattern = r'"word":"([^"]+)".*?"hotScore":"(\d+)"'
                matches = re.findall(pattern, html)

                topics = []
                for idx, (word, hot_score) in enumerate(matches[:20]):
                    # 构建搜索链接
                    search_url = f"https://www.baidu.com/s?wd={requests.utils.quote(word)}&sa=fyb_news"

                    topics.append({
                        "topic": word,
                        "heat": int(hot_score),
                        "keywords": self._extract_keywords(word),
                        "url": search_url,
                        "rank": idx + 1
                    })

                if topics:
                    logger.info(f"Fetched {len(topics)} topics from Baidu")
                    return topics

        except Exception as e:
            logger.debug(f"Baidu hotboard failed: {e}")

        return []

    def _fetch_toutiao_hotboard(self) -> list[dict]:
        """获取今日头条热点榜单"""
        url = 'https://www.toutiao.com/hot-event/hot-board/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }

        try:
            self.requester.wait_for_domain(url)
            response = self.requester.session.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                topics = []

                items = data if isinstance(data, list) else []
                for item in items[:20]:
                    title = item.get('Title', '') or item.get('title', '')
                    hot = item.get('HotValue', 0) or item.get('hot_value', 0)

                    if title:
                        topics.append({
                            "topic": title,
                            "heat": hot if isinstance(hot, (int, float)) else 0,
                            "keywords": self._extract_keywords(title),
                            "url": f"https://www.toutiao.com/a{item.get('ClusterId', '') or item.get('cluster_id', '')}/"
                        })

                if topics:
                    logger.info(f"Fetched {len(topics)} topics from Toutiao")
                    return topics

        except Exception as e:
            logger.debug(f"Toutiao API failed: {e}")

        return []

    def _fetch_bilibili_playwright(self) -> list[dict]:
        url = "https://www.bilibili.com/v/popular/rank/all"

        def extract(page):
            topics = []
            items = page.query_selector_all('.rank-item')

            for item in items[:20]:
                title_elem = item.query_selector('.title') or item.query_selector('a[title]')
                if not title_elem:
                    continue
                topic_name = title_elem.get_attribute('title') or title_elem.inner_text().strip()

                hot_elem = item.query_selector('.data-box')
                heat_str = hot_elem.inner_text().strip() if hot_elem else "0"
                heat_value = self._parse_heat_value(heat_str)

                link_elem = item.query_selector('a[href*="/video/"]')
                url = link_elem.get_attribute('href') if link_elem else ""
                if url and url.startswith('/'):
                    url = f"https://www.bilibili.com{url}"

                topics.append({
                    "topic": topic_name,
                    "heat": heat_value if heat_value else 10000 - len(topics) * 500,
                    "keywords": self._extract_keywords(topic_name),
                    "url": url
                })
            return topics

        return self.playwright_scraper.fetch_with_extraction(url, extract, '.rank-item')

    def _fetch_bilibili_api(self) -> list[dict]:
        url = "https://api.bilibili.com/x/web-interface/ranking/v2"
        params = {"rid": "0", "type": "all"}
        headers = self.requester.get_api_headers()
        headers['Referer'] = 'https://www.bilibili.com/'

        try:
            self.requester.wait_for_domain(url)
            response = self.requester.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            video_list = data.get('data', {}).get('list', [])
            topics = []

            for item in video_list[:20]:
                topic_name = item.get('title', '')
                play_count = item.get('stat', {}).get('view', 0)

                bvid = item.get('bvid', '')
                url = f"https://www.bilibili.com/video/{bvid}" if bvid else "https://www.bilibili.com"

                topics.append({
                    "topic": topic_name,
                    "heat": play_count,
                    "keywords": self._extract_keywords(topic_name),
                    "url": url
                })

            return topics
        except Exception as e:
            logger.debug(f"Bilibili API fetch failed: {e}")
            return []

    def _parse_heat_value(self, heat_str: str) -> int:
        heat_str = heat_str.lower()

        if '万' in heat_str:
            match = re.search(r'([\d.]+)\s*万', heat_str)
            if match:
                return int(float(match.group(1)) * 10000)
        elif '亿' in heat_str:
            match = re.search(r'([\d.]+)\s*亿', heat_str)
            if match:
                return int(float(match.group(1)) * 100000000)

        match = re.search(r'([\d,]+)', heat_str)
        if match:
            return int(match.group(1).replace(',', ''))

        return 0

    def _extract_keywords(self, text: str) -> list[str]:
        keywords = re.split(r'[,\s,，,\s,,\t]+', text)
        return [k.strip() for k in keywords if k.strip() and len(k.strip()) > 1]

    def _calculate_score(self, heat: float, source: str, keywords: list = None, category: str = "") -> float:
        """
        计算话题得分
        优先级：热度值 > 来源权重 > 科技题材增益
        """
        # 热度值归一化 (基础分，上限 1.0)
        # 知乎热榜最高约 5000 万热度，以此为基准归一化
        normalized_heat = min(heat / 50_000_000, 1.0)

        # 来源权重 (知乎 0.35 > B 站 0.30 > 微博 0.15 > 抖音 0.12 > 头条 0.08)
        source_weight = self.SOURCE_WEIGHTS.get(source, 0.1)

        # 科技题材增益：科技类话题 +50% 加分
        tech_boost = 1.5 if category == "科技" else 1.0

        # 计算公式：归一化热度 × (1 + 来源权重) × 题材增益
        score = normalized_heat * (1 + source_weight) * tech_boost

        return round(min(score, 1.5), 3)  # 允许超过 1.0 以体现高热度 + 科技题材的优势

    def fetch_all(self) -> list[HotTopic]:
        """获取所有来源的热点"""
        all_raw = []

        fetchers = {
            "zhihu": self.fetch_zhihu,
            "baidu": self.fetch_baidu,
            #"bilibili": self.fetch_bilibili,
            #"weibo": self.fetch_weibo,
            #"douyin": self.fetch_douyin,
            #"toutiao": self.fetch_toutiao,
        }

        for source, fetcher in fetchers.items():
            try:
                items = fetcher()
                for item in items:
                    # 先计算分类，再计算得分（科技题材有增益）
                    temp_topic = HotTopic(
                        topic=item.get("topic", ""),
                        score=0,
                        source=source,
                        rank=0,
                        heat_value=item.get("heat", 0),
                        keywords=item.get("keywords", []),
                        url=item.get("url", ""),
                    )
                    score = self._calculate_score(
                        item.get("heat", 0),
                        source,
                        item.get("keywords", []),
                        temp_topic.category
                    )
                    topic = HotTopic(
                        topic=item.get("topic", ""),
                        score=score,
                        source=source,
                        rank=0,
                        heat_value=item.get("heat", 0),
                        keywords=item.get("keywords", []),
                        url=item.get("url", ""),
                    )
                    all_raw.append(topic)
            except Exception as e:
                logger.error(f"Failed to fetch from {source}: {e}")

        if not all_raw:
            logger.warning("No topics fetched from any source")
            return []

        all_raw.sort(key=lambda x: x.score, reverse=True)

        for i, topic in enumerate(all_raw):
            topic.rank = i + 1

        self.topics = all_raw
        logger.info(f"Fetched total {len(self.topics)} topics")
        return self.topics

    def fetch_all_categorized(self) -> dict[str, list[HotTopic]]:
        self.fetch_all()
        return self.get_top_topics_by_category(top_n=1)

    def save_to_json(self, output_path: str = None) -> str:
        if output_path is None:
            timestamp = datetime.now().strftime("%Y-%m-%d")
            output_path = f"ranked_topics_{timestamp}.json"

        data = {
            "generated_at": datetime.now().isoformat(),
            "total_count": len(self.topics),
            "topics": [asdict(t) for t in self.topics]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(self.topics)} topics to {output_path}")
        return output_path

    def get_top_topics_by_category(self, top_n: int = 1) -> dict[str, list[HotTopic]]:
        result = {'时事': [], '科技': [], '民生': [], '娱乐': []}

        for topic in self.topics:
            category = topic.category
            if category in result:
                result[category].append(topic)

        for category in result:
            result[category] = result[category][:top_n]

        return result

    def get_top_topic(self) -> HotTopic | None:
        if not self.topics:
            return None
        return self.topics[0]


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Hot Topic Aggregator")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--output-dir", default=".", help="输出目录")
    parser.add_argument("--dry-run", action="store_true", help="仅测试，不保存")
    parser.add_argument("--categorized", action="store_true", help="按分类输出 TOP3 话题")
    parser.add_argument("--markdown", action="store_true", help="生成 Markdown 报告")
    parser.add_argument("--top-n", type=int, default=5, help="输出 TOP N 话题")

    args = parser.parse_args()

    aggregator = HotTopicAggregator(config_path=args.config)

    print("=" * 60)
    print("🔥 热点聚合器 - 全网热点话题采集")
    print("=" * 60)
    print("\n正在从多平台获取热点话题...\n")

    topics = aggregator.fetch_all()

    print(f"\n{'='*60}")
    print(f"✅ 获取到 {len(topics)} 个热点话题")
    print(f"{'='*60}\n")

    # 按平台统计
    platform_stats = {}
    for topic in topics:
        platform_stats[topic.source] = platform_stats.get(topic.source, 0) + 1

    print("📊 各平台获取情况:")
    for platform, count in sorted(platform_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"   {platform}: {count} 个")

    print(f"\n📋 TOP {args.top_n} 话题榜单:\n")
    print(f"{'排名':<4} {'来源':<10} {'分类':<6} {'话题':<40} {'得分':>6} {'热度':>12}")
    print("-" * 85)

    for i, topic in enumerate(topics[:args.top_n], 1):
        topic_display = topic.topic[:38] + ".." if len(topic.topic) > 40 else topic.topic
        print(f"{i:<4} {topic.source:<10} {topic.category:<6} {topic_display:<40} {topic.score:>6.3f} {topic.heat_value:>12,.0f}")

    if args.categorized:
        categorized_topics = aggregator.get_top_topics_by_category(top_n=3)
        print(f"\n{'='*60}")
        print("📂 分类 TOP 话题")
        print(f"{'='*60}")
        for category, cats_topics in categorized_topics.items():
            if cats_topics:
                print(f"\n【{category}】")
                for topic in cats_topics:
                    print(f"   • {topic.topic}")
                    print(f"     来源：{topic.source} | 得分：{topic.score:.3f}")

    if args.markdown or True:  # 默认生成 Markdown
        _generate_markdown_report(aggregator, args.output_dir, args.top_n)

    if not args.dry_run:
        output_file = aggregator.save_to_json(Path(args.output_dir) / f"ranked_topics_{datetime.now().strftime('%Y-%m-%d')}.json")
        print(f"\n✅ 已保存到：{output_file}")

        top_topic = aggregator.get_top_topic()
        if top_topic:
            print(f"\n🏆 推荐选题 (TOP 1):")
            print(f"   标题：{top_topic.topic}")
            print(f"   得分：{top_topic.score:.3f}")
            print(f"   来源：{top_topic.source}")
            print(f"   分类：{top_topic.category}")


def _generate_markdown_report(aggregator: HotTopicAggregator, output_dir: str, top_n: int = 5):
    """生成 Markdown 格式的报告"""
    from pathlib import Path

    date_str = datetime.now().strftime('%Y-%m-%d')
    output_path = Path(output_dir) / f"hot-topics-{date_str}.md"

    # 按分类整理
    categorized = aggregator.get_top_topics_by_category(top_n=3)

    content = f"""---
title: "全网热点 Top{top_n} - {date_str} - 公众号选题参考"
date: {date_str}
category: 热点分析
tags: [热点，社会，科技，民生，公众号选题]
---

# 🔥 全网热点话题 Top {top_n}

> **数据来源**: 知乎热榜 | B 站热门 | 微博热搜 | 抖音热点 | 今日头条
>
> **重点关注**: 知乎热榜 (深度讨论) | B 站热门 (年轻视角)
>
> **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 📊 综合热度榜单

| 排名 | 来源 | 分类 | 话题 | 得分 | 热度值 |
|:---:|:---:|:---:|------|:---:|---:|
"""

    for i, topic in enumerate(aggregator.topics[:top_n], 1):
        topic_display = topic.topic[:25] + ".." if len(topic.topic) > 28 else topic.topic
        content += f"| {i} | {topic.source} | {topic.category} | {topic_display} | {topic.score:.3f} | {topic.heat_value:,} |\n"

    content += f"""

---

## 📂 分类精选

"""

    for category, topics in categorized.items():
        if topics:
            content += f"### {category}\n\n"
            for t in topics[:2]:
                content += f"- **{t.topic}** (来源：{t.source}, 得分：{t.score:.3f})\n"
            content += "\n"

    content += f"""
---

## 💡 选题建议

### 🏆 首选推荐：{aggregator.topics[0].topic if aggregator.topics else 'N/A'}

**推荐理由**:
- 跨平台热度最高
- 适合深度解读 + 观点输出
- 24 小时黄金窗口期

**标题参考**:
- "{aggregator.topics[0].topic[:30] if aggregator.topics else 'N/A'}背后的真相..."
- "全网刷屏的{aggregator.topics[0].topic[:20] if aggregator.topics else 'N/A'}，这才是正确的打开方式"

---

## ⚡ 快速行动清单

1. **立即**: 确定选题方向
2. **2 小时内**: 完成素材收集 + 大纲拟定
3. **4 小时内**: 完成初稿 + 配图
4. **6 小时内**: 排版优化 + 发布

> 💡 **提示**: 热点文章最重要的是**快**和**准**

---

*生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    output_path.write_text(content, encoding='utf-8')
    print(f"\n📝 Markdown 报告：{output_path}")


if __name__ == "__main__":
    main()
