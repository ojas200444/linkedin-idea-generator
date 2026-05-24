"""
Google Trends Scraper
Fetches trending topics for India using pytrends.
Falls back to top searches if realtime endpoint returns 404.
"""

import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def get_google_trends() -> list[dict]:
    """Fetch trending search topics in India from Google Trends."""
    trends = []

    try:
        from pytrends.request import TrendReq

        # Some pytrends versions hit deprecated endpoints — use timeout/retries
        pytrends = TrendReq(hl="en-IN", tz=330, timeout=(10, 25))

        # Method 1: Daily trending searches in India (most reliable)
        try:
            df = pytrends.trending_searches(pn="india")
            for term in df[0].tolist()[:25]:
                term = str(term).strip()
                if term and term != "nan":
                    trends.append({
                        "source": "Google Trends India (Daily)",
                        "title": term,
                        "url": f"https://trends.google.com/trends/explore?q={term.replace(' ', '+')}&geo=IN",
                        "score": 100,
                    })
            time.sleep(1)
        except Exception as e:
            print(f"   [Trends] Daily trends unavailable: {e}")

        # Method 2: Interest over time for key entrepreneurship topics
        if not trends:
            try:
                keywords = ["startup", "entrepreneur", "India business", "technology India"]
                pytrends.build_payload(keywords[:4], timeframe="now 1-d", geo="IN")
                df2 = pytrends.interest_over_time()
                if df2 is not None and not df2.empty:
                    for kw in keywords[:4]:
                        if kw in df2.columns:
                            avg = df2[kw].mean()
                            if avg > 0:
                                trends.append({
                                    "source": "Google Trends Interest (India)",
                                    "title": f"{kw} trending in India",
                                    "url": "",
                                    "score": int(avg),
                                })
                time.sleep(1)
            except Exception as e:
                print(f"   [Trends] Interest over time error: {e}")

        # Method 3: Related queries for entrepreneur
        if not trends:
            try:
                pytrends.build_payload(["entrepreneur", "startup India"], geo="IN")
                related = pytrends.related_queries()
                for kw, data in related.items():
                    if data and data.get("top") is not None:
                        for _, row in data["top"].head(5).iterrows():
                            query = str(row.get("query", "")).strip()
                            if query:
                                trends.append({
                                    "source": "Google Trends Related Queries",
                                    "title": query,
                                    "url": "",
                                    "score": int(row.get("value", 50)),
                                })
            except Exception as e:
                print(f"   [Trends] Related queries error: {e}")

    except ImportError:
        print("   [Trends] pytrends not installed.")
    except Exception as e:
        print(f"   [Trends] Unexpected error: {e}")

    return trends
