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
    Load all past ideas.
    First tries to fetch from Google Sheets (remote source of truth).
    Falls back to the local idea_history.json file.
    """
    # 1. Try to load from Google Sheets
    try:
        from sheets_writer import _get_client, _get_or_create_sheet
        client = _get_client()
        sheet = _get_or_create_sheet(client)
        rows = sheet.get_all_values()
        if rows and len(rows) > 1:
            headers = rows[0]
            try:
                idea_idx = headers.index("Post Idea")
                cat_idx = headers.index("Category")
                angle_idx = headers.index("Angle")
            except ValueError:
                # Fallback indices if header names differ
                idea_idx = 2
                cat_idx = 1
                angle_idx = 3

            history = []
            for row in rows[1:]:
                if len(row) > idea_idx and row[idea_idx].strip():
                    history.append({
                        "post_idea": row[idea_idx].strip(),
                        "category": row[cat_idx].strip() if len(row) > cat_idx else "",
                        "angle": row[angle_idx].strip() if len(row) > angle_idx else "",
                    })
            if history:
                print(f"   [History] ✅ Loaded {len(history)} past ideas from Google Sheets (source of truth).")
                return history
    except Exception as e:
        print(f"   [History] Google Sheets history loading unavailable: {e}")
        print("             ↳ Falling back to local history file check...")

    # 2. Fallback to local file check
    if not os.path.exists(_HISTORY_FILE):
        return []
    try:
        with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            print(f"   [History] Loaded {len(data)} past ideas from local file.")
            return data
    except (json.JSONDecodeError, OSError) as e:
        print(f"   [History] Warning — could not read local history file: {e}")
    return []


def save_to_history(ideas: list[dict]) -> None:
    """
    Append newly generated ideas to the local history file as a backup.
    Note: Remote Google Sheet writes are handled by write_ideas_to_sheet() separately.
    """
    if not ideas:
        return

    existing = load_history()
    today = datetime.now().strftime("%Y-%m-%d")

    new_entries = []
    # Deduplicate within new ideas to avoid double-adding if they match existing
    existing_titles = {entry.get("post_idea", "").strip().lower() for entry in existing}

    for idea in ideas:
        title = idea.get("post_idea", "").strip()
        if title.lower() not in existing_titles:
            new_entries.append({
                "date": today,
                "post_idea": title,
                "category": idea.get("category", ""),
                "angle": idea.get("angle", ""),
            })

    if not new_entries:
        return

    # Merge and save local copy
    existing.extend(new_entries)
    try:
        with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"   [History] ✅ Saved local backup of {len(new_entries)} new ideas (total: {len(existing)})")
    except OSError as e:
        print(f"   [History] Warning — could not save local backup: {e}")


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
