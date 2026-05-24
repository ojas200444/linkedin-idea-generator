"""
Quora Scraper
Searches Google for trending Quora questions relevant to the audience.
Uses requests + BeautifulSoup — no API key needed.
"""

import requests
from bs4 import BeautifulSoup
import time

SEARCH_QUERIES = [
    "site:quora.com entrepreneur India 2025",
    "site:quora.com startup marketing strategy 2025",
    "site:quora.com economics India business 2025",
    "site:quora.com technology CEO startup",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def get_quora_trends() -> list[dict]:
    """Search Google for trending Quora questions."""
    results = []

    for query in SEARCH_QUERIES:
        try:
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=5"
            r = requests.get(url, headers=HEADERS, timeout=10)

            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")

            # Extract search result titles
            for h3 in soup.find_all("h3")[:5]:
                title = h3.get_text(strip=True)
                if title and "Quora" not in title and len(title) > 20:
                    results.append({
                        "source": "Quora (via Google Search)",
                        "title": title,
                        "url": "",
                        "score": 50,
                    })

            time.sleep(2)  # Respect rate limits

        except Exception as e:
            print(f"   [Quora] Error for query '{query}': {e}")

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r["title"] not in seen:
            seen.add(r["title"])
            unique.append(r)

    return unique[:15]
