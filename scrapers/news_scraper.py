"""
News RSS Scraper
Parses RSS feeds from major news sources relevant to the audience.
No API key needed.
"""

import feedparser
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import RSS_FEEDS


def get_news_trends() -> list[dict]:
    """Fetch latest articles from configured RSS feeds."""
    articles = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source_name = feed.feed.get("title", feed_url.split("//")[-1].split("/")[0])

            for entry in feed.entries[:8]:
                title = entry.get("title", "").strip()
                if not title:
                    continue

                summary = entry.get("summary", entry.get("description", ""))
                # Clean HTML tags from summary
                import re
                summary = re.sub(r"<[^>]+>", "", summary)[:250].strip()

                articles.append({
                    "source": f"News: {source_name}",
                    "title": title,
                    "url": entry.get("link", ""),
                    "summary": summary,
                    "score": 70,
                })

        except Exception as e:
            print(f"   [News] Error parsing {feed_url}: {e}")

    return articles
