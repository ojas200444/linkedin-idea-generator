"""
Idea History
============
Persists past generated ideas to a local JSON file so that:
  1. The AI prompt can be told which topics were already covered (avoid repeats).
  2. Newly generated ideas can be filtered if they are too similar to past ones.

Uses only Python built-ins — no extra libraries required.
"""

import json
import os
from datetime import datetime
from difflib import SequenceMatcher

# Path of the history file (sits next to this script)
_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "idea_history.json")

# Similarity threshold — ideas with a ratio above this are considered duplicates
DUPLICATE_THRESHOLD = 0.70

# How many past topics to inject into the AI prompt to guide it away from repeats
RECENT_TOPICS_FOR_PROMPT = 40


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase + strip punctuation for robust comparison."""
    import re
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def _similarity(a: str, b: str) -> float:
    """Return similarity ratio between two strings (0.0 – 1.0)."""
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


# ─── Public API ──────────────────────────────────────────────────────────────

def load_history() -> list[dict]:
    """
    Load all past ideas from the history file.
    Returns an empty list if the file doesn't exist yet.
    """
    if not os.path.exists(_HISTORY_FILE):
        return []
    try:
        with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        print(f"   [History] Warning — could not read history file: {e}")
        return []


def save_to_history(ideas: list[dict]) -> None:
    """
    Append newly generated ideas (with a timestamp) to the history file.
    Creates the file if it doesn't exist.
    """
    if not ideas:
        return

    existing = load_history()
    today = datetime.now().strftime("%Y-%m-%d")

    for idea in ideas:
        existing.append({
            "date": today,
            "post_idea": idea.get("post_idea", "").strip(),
            "category": idea.get("category", ""),
            "angle": idea.get("angle", ""),
        })

    try:
        with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"   [History] ✅ Saved {len(ideas)} ideas to history "
              f"(total: {len(existing)} recorded ideas)")
    except OSError as e:
        print(f"   [History] Warning — could not save history: {e}")


def get_recent_topics(n: int = RECENT_TOPICS_FOR_PROMPT) -> list[str]:
    """
    Return the titles of the `n` most recent past ideas.
    Used to inject into the AI prompt so Gemini knows what NOT to repeat.
    """
    history = load_history()
    # Most recent first
    recent = [entry["post_idea"] for entry in reversed(history) if entry.get("post_idea")]
    return recent[:n]


def filter_duplicates(new_ideas: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Compare new ideas against history and remove near-duplicates.

    Returns:
        (unique_ideas, dropped_ideas)
        - unique_ideas : ideas that are sufficiently different from all past ones
        - dropped_ideas: ideas that matched something in history
    """
    history = load_history()
    past_titles = [entry.get("post_idea", "") for entry in history]

    unique = []
    dropped = []

    for idea in new_ideas:
        title = idea.get("post_idea", "")
        is_duplicate = False

        for past in past_titles:
            if _similarity(title, past) >= DUPLICATE_THRESHOLD:
                print(f"   [History] 🔁 Dropped duplicate: \"{title}\"")
                print(f"              ↳ Too similar to past idea: \"{past}\"")
                is_duplicate = True
                break

        if is_duplicate:
            dropped.append(idea)
        else:
            unique.append(idea)
            # Also check against other new ideas in this batch to avoid
            # intra-batch duplicates (AI sometimes generates very similar ideas)
            past_titles.append(title)

    return unique, dropped
