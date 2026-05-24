"""
Twitter/X Scraper
Uses public Nitter RSS feeds (Twitter mirror) — no API key needed.
Falls back gracefully if all Nitter instances are unavailable.
"""

import requests
import feedparser
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import NITTER_INSTANCES, TWITTER_SEARCH_TERMS


def _get_working_nitter_instance() -> str | None:
    """Try each Nitter instance and return the first responsive one."""
    for instance in NITTER_INSTANCES:
        try:
            r = requests.get(instance, timeout=6)
            if r.status_code == 200:
                return instance
        except Exception:
            continue
    return None


def get_twitter_trends() -> list[dict]:
    """Fetch trending posts from Twitter via Nitter RSS."""
    tweets = []

    instance = _get_working_nitter_instance()
    if not instance:
        print("   [Twitter] No Nitter instance reachable — skipping Twitter data.")
        return []

    for term in TWITTER_SEARCH_TERMS[:6]:  # Limit requests
        try:
            rss_url = f"{instance}/search/rss?q={term}+lang%3Aen&f=tweets"
            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                if not title or len(title) < 20:
                    continue

                tweets.append({
                    "source": f"Twitter/X #{term}",
                    "title": title,
                    "url": entry.get("link", ""),
                    "score": 60,
                })

        except Exception as e:
            print(f"   [Twitter] Error for term '{term}': {e}")

    # Deduplicate
    seen = set()
    unique = []
    for t in tweets:
        if t["title"] not in seen:
            seen.add(t["title"])
            unique.append(t)

    return unique[:20]
