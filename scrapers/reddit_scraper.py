"""
Reddit Scraper
Uses Reddit's public JSON API — no account or API key needed.
Scrapes hot/rising posts from targeted subreddits.
"""

import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import REDDIT_SUBREDDITS

HEADERS = {"User-Agent": "LinkedInIdeaBot/1.0 (by /u/anonymous)"}


def get_reddit_trends() -> list[dict]:
    """Fetch hot posts from configured subreddits."""
    posts = []

    for subreddit in REDDIT_SUBREDDITS:
        for sort in ["hot", "rising"]:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit=10"
                r = requests.get(url, headers=HEADERS, timeout=10)

                if r.status_code != 200:
                    continue

                data = r.json()
                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    score = post.get("score", 0)

                    if score < 50:
                        continue  # skip low-engagement posts

                    posts.append({
                        "source": f"Reddit r/{subreddit}",
                        "title": post.get("title", "").strip(),
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "score": score,
                        "comments": post.get("num_comments", 0),
                        "flair": post.get("link_flair_text", ""),
                    })

            except requests.RequestException as e:
                print(f"   [Reddit] Error scraping r/{subreddit}/{sort}: {e}")
            except Exception as e:
                print(f"   [Reddit] Unexpected error for r/{subreddit}: {e}")

    # Deduplicate by title and sort by engagement
    seen = set()
    unique_posts = []
    for p in posts:
        if p["title"] not in seen:
            seen.add(p["title"])
            unique_posts.append(p)

    unique_posts.sort(key=lambda x: x["score"] + x["comments"], reverse=True)
    return unique_posts[:30]
