#!/usr/bin/env python3
"""
LinkedIn Post Idea Generator — Main Runner
==========================================
Runs all scrapers, sends content to Gemini AI,
and writes the generated ideas to Google Sheets.

Usage:
    python main.py              → Full run (scrape + AI + Sheets)
    python main.py --dry-run    → Scrape + AI only (no Sheets write)
    python main.py --test       → Test with minimal scraping (faster)
"""

import sys
import os
import time
from datetime import datetime

# ─── Scrapers ────────────────────────────────────────────────────────────────
from scrapers.reddit_scraper import get_reddit_trends
from scrapers.trends_scraper import get_google_trends
from scrapers.news_scraper import get_news_trends
from scrapers.twitter_scraper import get_twitter_trends
from scrapers.quora_scraper import get_quora_trends

# ─── Core ────────────────────────────────────────────────────────────────────
from ai_generator import generate_post_ideas
from sheets_writer import write_ideas_to_sheet
from idea_history import filter_duplicates, save_to_history


def banner():
    print("\n" + "═" * 56)
    print("  🧠  LinkedIn Post Idea Generator")
    print(f"  ⏰  {datetime.now().strftime('%A, %d %B %Y — %I:%M %p IST')}")
    print("═" * 56 + "\n")


def scrape_all(test_mode: bool = False) -> list[dict]:
    """Run all scrapers and combine results."""
    all_content = []

    scrapers = [
        ("📡 Reddit",         get_reddit_trends),
        ("📈 Google Trends",  get_google_trends),
        ("📰 News RSS",       get_news_trends),
        ("🐦 Twitter/X",      get_twitter_trends),
        ("💬 Quora",          get_quora_trends),
    ]

    if test_mode:
        # In test mode only run fast scrapers
        scrapers = scrapers[:3]

    for label, scraper_fn in scrapers:
        print(f"{label} — scraping...")
        try:
            t0 = time.time()
            results = scraper_fn()
            elapsed = round(time.time() - t0, 1)
            print(f"   → {len(results)} items ({elapsed}s)\n")
            all_content.extend(results)
        except Exception as e:
            print(f"   → ❌ Failed: {e}\n")

    return all_content


def print_ideas(ideas: list[dict]):
    """Pretty-print ideas to the console."""
    print("\n" + "─" * 56)
    print("  💡  Generated Post Ideas")
    print("─" * 56)
    for i, idea in enumerate(ideas, 1):
        print(f"\n  [{i}] {idea.get('post_idea', 'Untitled')}")
        print(f"      📂  {idea.get('category', '')}")
        print(f"      🎯  {idea.get('hook', '')}")
        print(f"      🔍  Inspired by: {idea.get('source_inspiration', '')}")
    print("\n" + "─" * 56 + "\n")


def run(dry_run: bool = False, test_mode: bool = False):
    banner()

    # ── Step 1: Scrape ──────────────────────────────────────────────────────
    print("STEP 1 — SCRAPING\n")
    all_content = scrape_all(test_mode=test_mode)

    if not all_content:
        print("❌ No content was scraped. Check your internet connection and try again.")
        sys.exit(1)

    print(f"✅ Total items collected: {len(all_content)}\n")

    # ── Step 2: Generate Ideas ──────────────────────────────────────────────
    print("STEP 2 — GENERATING IDEAS WITH GEMINI AI\n")
    ideas = generate_post_ideas(all_content)

    if not ideas:
        print("❌ Idea generation failed. Check your Gemini API key in .env")
        sys.exit(1)

    print(f"✅ Generated {len(ideas)} post ideas\n")

    # ── Step 2b: Deduplicate Against History ────────────────────────────────
    print("STEP 2b — DEDUPLICATION CHECK\n")
    ideas, dropped = filter_duplicates(ideas)
    if dropped:
        print(f"   ⚠️  {len(dropped)} idea(s) dropped (too similar to past ideas)")
    else:
        print("   ✅ No duplicates found — all ideas are fresh!")

    if not ideas:
        print("\n❌ All generated ideas were duplicates. Run again tomorrow or check idea_history.json.")
        sys.exit(0)

    print(f"\n✅ {len(ideas)} fresh ideas ready\n")
    print_ideas(ideas)

    # ── Step 3: Write to Google Sheets ──────────────────────────────────────
    if dry_run:
        print("ℹ️  Dry-run mode — skipping Google Sheets write.\n")
        # Still save to history so future runs avoid these topics
        print("STEP 3 — SAVING TO HISTORY\n")
        save_to_history(ideas)
        return

    print("STEP 3 — WRITING TO GOOGLE SHEETS\n")
    try:
        count = write_ideas_to_sheet(ideas)
        print(f"\n✅ Done! {count} ideas added to your Google Sheet.")
        print("   Open Google Sheets and search for 'LinkedIn Post Ideas'\n")
        # Save to history after a successful write
        save_to_history(ideas)
    except FileNotFoundError as e:
        print(str(e))
        print("\n📖 See SETUP_GUIDE.md for Google Sheets setup instructions.\n")
    except Exception as e:
        print(f"❌ Google Sheets error: {e}\n")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    test_mode = "--test" in sys.argv
    run(dry_run=dry_run, test_mode=test_mode)
