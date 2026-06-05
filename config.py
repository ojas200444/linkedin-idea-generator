import os
from dotenv import load_dotenv

load_dotenv()

# ─── API Keys ───────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials/google-credentials.json")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "LinkedIn Post Ideas")

# ─── Reddit ──────────────────────────────────────────────────────────────────
# Using Reddit's public JSON API (no account needed)
REDDIT_SUBREDDITS = [
    "entrepreneur", "startups", "india", "technology",
    "finance", "marketing", "business", "worldnews",
    "personalfinance", "investing", "geopolitics",
    "IndiaInvestments", "developersIndia"
]

# ─── News RSS Feeds ───────────────────────────────────────────────────────────
# Balanced mix: India startups + global tech + business + economics + Reddit-adjacent
RSS_FEEDS = [
    # ── India Startup / Business ──────────────────────────────────────────────
    "https://inc42.com/feed/",
    "https://yourstory.com/feed",
    "https://the-ken.com/feed/",                                    # The Ken — premium India business
    "https://www.livemint.com/rss/news",                            # Mint — India business/economics
    "https://www.thehindubusinessline.com/feeder/default.rss",      # Hindu Business Line

    # ── India General News ────────────────────────────────────────────────────
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "https://www.moneycontrol.com/rss/business.xml",

    # ── Global Tech ───────────────────────────────────────────────────────────
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://hnrss.org/frontpage",                                   # Hacker News — tech/startup discussions
    "https://www.wired.com/feed/rss",                               # Wired — tech culture + science
    "https://www.technologyreview.com/feed/",                       # MIT Technology Review

    # ── Global Business / Economics ───────────────────────────────────────────
    "https://feeds.hbr.org/harvardbusiness",                        # Harvard Business Review
    "https://feeds.bbci.co.uk/news/business/rss.xml",              # BBC Business
    "https://feeds.bbci.co.uk/news/world/rss.xml",                 # BBC World

    # ── Science & Future ─────────────────────────────────────────────────────
    "https://www.scientificamerican.com/feed/rss/",                 # Scientific American
]

# ─── Nitter Instances (Twitter mirror — no API key needed) ────────────────────
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.net",
]

# Twitter/X search topics to check (these will be searched as hashtags / keywords)
TWITTER_SEARCH_TERMS = [
    "startup", "entrepreneur", "India", "technology", "marketing",
    "CEO", "business", "innovation", "economy"
]

# ─── Your Audience ───────────────────────────────────────────────────────────
AUDIENCE_DESCRIPTION = """
- Age: 16–40 years old
- Profile: Entrepreneurs, CEOs, startup founders, engineering students, young professionals
- Interests: Business, marketing strategies, current affairs, economics, psychology, tech
- Geography: Based in India (but interested in global comparisons and stories)
- Mindset: Open-minded, curious, ambitious, growth-oriented
"""

# ─── Your Previous Post Style (to guide the AI) ──────────────────────────────
POST_STYLE_EXAMPLES = [
    "IKEA Effect (psychology / consumer behavior)",
    "Domino's PR stunt (marketing strategy)",
    "Dettol vs Savlon Marketing Strategies (brand comparison)",
    "Dubai vs India Tax System for cold drinks (economics comparison)",
    "Bill Gates - Solar engineering (tech + billionaire insight)",
    "Bournvita's weird marketing (Indian brand controversy)",
    "India vs Japan Election (political comparison)",
    "China Social Media Ban (policy + tech impact)",
    "ISRO employee no salary for 17 months (emotional + current affairs)",
]
