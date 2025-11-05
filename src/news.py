from __future__ import annotations

import time
from typing import Iterable

import feedparser
import requests
import trafilatura


# Map topics to a list of RSS feed URLs. You can extend these.
TOPIC_TO_FEEDS: dict[str, list[str]] = {
    "technology": [
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/index/",
        "https://www.engadget.com/rss.xml",
    ],
    "world": [
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.reuters.com/world/rss",
    ],
    "business": [
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "https://www.reuters.com/finance/markets/rss",
    ],
    "sports": [
        "http://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
        "https://www.espn.com/espn/rss/news",
    ],
    "science": [
        "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://www.sciencedaily.com/rss/top/science.xml",
    ],
    "health": [
        "http://feeds.bbci.co.uk/news/health/rss.xml",
        "https://www.medicalnewstoday.com/rss",
    ],
    "entertainment": [
        "http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        "https://www.rollingstone.com/music/music-news/feed/",
    ],
}


class Article:
    def __init__(self, title: str, url: str, published: float | None, summary: str | None = None, content: str | None = None) -> None:
        self.title = title
        self.url = url
        self.published = published
        self.summary = summary
        self.content = content


def parse_time_struct(entry) -> float | None:
    struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if struct is None:
        return None
    try:
        return time.mktime(struct)
    except Exception:
        return None


def fetch_rss_entries(feeds: Iterable[str], limit: int = 3) -> list[Article]:
    articles: list[Article] = []
    for feed_url in feeds:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries[:limit]:
            title = getattr(entry, "title", "Untitled")
            link = getattr(entry, "link", "")
            published_ts = parse_time_struct(entry)
            summary = getattr(entry, "summary", None)
            articles.append(Article(title=title, url=link, published=published_ts, summary=summary))
    # Order by published desc when available
    articles.sort(key=lambda a: a.published or 0, reverse=True)
    return articles[:limit]


def fetch_article_text(url: str, timeout: int = 12) -> str | None:
    try:
        # Try using trafilatura's convenience method first
        downloaded = trafilatura.fetch_url(url, no_ssl=True)
        if downloaded:
            text = trafilatura.extract(downloaded, favor_recall=True)
            if text:
                return text
        # Fallback: simple GET for some websites trafilatura may need raw input
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if resp.ok:
            text = trafilatura.extract(resp.text, favor_recall=True, include_comments=False)
            return text
    except Exception:
        return None
    return None


def get_latest_articles_for_topic(topic: str, limit: int = 3) -> list[Article]:
    feeds = TOPIC_TO_FEEDS.get(topic.lower(), [])
    if not feeds:
        return []
    articles = fetch_rss_entries(feeds, limit=limit)
    for art in articles:
        art.content = fetch_article_text(art.url) or art.summary or ""
    return articles


