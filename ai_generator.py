"""
AI Generator
Uses Google Gemini API to analyze scraped content and generate
targeted LinkedIn post ideas tailored to the creator's style and audience.
Uses the new google.genai SDK.
"""

import json
import random
from collections import defaultdict
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, AUDIENCE_DESCRIPTION, POST_STYLE_EXAMPLES
from idea_history import get_recent_topics

# Maximum items contributed by any single source to the AI context.
# Prevents any one feed (e.g. inc42) from dominating the content list.
MAX_ITEMS_PER_SOURCE = 5

# Total items sent to the AI (after balancing)
MAX_TOTAL_ITEMS = 60


def _balance_sources(scraped_items: list[dict]) -> list[dict]:
    """
    Cap each source's contribution to MAX_ITEMS_PER_SOURCE items,
    then shuffle so the AI sees a varied mix rather than one big block
    from a single publication.
    """
    per_source: dict[str, list[dict]] = defaultdict(list)
    for item in scraped_items:
        source = item.get("source", "Unknown")
        per_source[source].append(item)

    balanced = []
    for source, items in per_source.items():
        # Sort by score desc within source so we keep the best ones
        items.sort(key=lambda x: x.get("score", 0), reverse=True)
        balanced.extend(items[:MAX_ITEMS_PER_SOURCE])

    random.shuffle(balanced)
    return balanced[:MAX_TOTAL_ITEMS]


def _build_prompt(scraped_items: list[dict]) -> str:
    """Build the Gemini prompt from scraped content."""

    # Balance sources before building the content block
    balanced_items = _balance_sources(scraped_items)

    content_lines = []
    # Build a lookup map: title → url (for AI to reference back)
    url_map = {}
    for item in balanced_items:
        source = item.get("source", "Unknown")
        title = item.get("title", "").strip()
        url = item.get("url", "")
        summary = item.get("summary", "")
        if title:
            line = f"  [{source}] {title}"
            if summary:
                line += f" — {summary[:120]}"
            if url:
                line += f" | URL: {url}"
            content_lines.append(line)
            if url:
                url_map[title] = url

    content_block = "\n".join(content_lines)
    examples_block = "\n".join(f"  • {ex}" for ex in POST_STYLE_EXAMPLES)

    # Load recently generated topics so the AI avoids repeating them
    recent_topics = get_recent_topics()
    if recent_topics:
        avoid_block = "\n".join(f"  - {t}" for t in recent_topics)
    else:
        avoid_block = "  (None yet — first run)"

    prompt = f"""You are a LinkedIn content strategist for an Indian creator who writes about business, marketing, economics, and current affairs.
Your goal is to optimize every generated idea for SHARES (not just likes or comments). Ask yourself: "Would someone forward this post to a friend or colleague?"

You MUST follow the guidelines from the "LinkedIn Post Rulebook" (YOSO Winning-Patterns Report):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TARGET AUDIENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{AUDIENCE_DESCRIPTION.strip()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CREATOR'S PAST POST STYLE (learn from these)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{examples_block}

Notice the pattern: each post takes a real event, brand story, policy, or concept and gives it a business/life-lesson/resilience angle. They are NOT generic — they are specific, often controversial or surprising, and tell a story.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⛔ RECENTLY COVERED TOPICS — DO NOT REPEAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The creator has ALREADY published or saved ideas on these topics.
Do NOT generate ideas that overlap with any of these — even with a different angle.
Be strict: if a topic is essentially the same subject, skip it.
{avoid_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TODAY'S TRENDING INTERNET CONTENT
(sourced from Reddit, Hacker News, Google Trends, News RSS, Quora, Twitter/X, and more)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
From the trending content above, generate exactly 8 high-quality LinkedIn post ideas for this creator.

Rules:
- Each idea must be SPECIFIC (not generic like "The future of AI").
- Take a unique angle that would spark discussion or surprise.
- Prefer India-relevant or India-comparison angles where possible.
- CRITICAL: Draw from a WIDE variety of sources above — Reddit discussions, global tech news,
  Quora questions, Google Trends, and international publications. Spread the inspiration across at least 4 different sources.
- Do NOT repeat any topic from the "RECENTLY COVERED TOPICS" list above.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LINKEDIN POST RULEBOOK SPECIFICATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. THE HOOK (Opening Line - Non-Negotiable):
   - Line 1 must stand alone. It must be powerful and readable without Line 2.
   - Never open with a question. Never open with a stat.
   - You must strictly use one of these 5 Hook Templates (vary them across the 8 ideas):
     - Template 1: The Confession -> "I [did/lost/failed at/got fired from] [X]."
     - Template 2: The 'Most People' Flip -> "Most people [common belief]. The truth is [contrarian Y]."
     - Template 3: The Reframe -> "[Common concept] isn't about [obvious/expected cause]."
     - Template 4: The One-Line Verdict -> "[Sharp, counterintuitive claim stated as flat truth]."
     - Template 5: The Numbered Promise -> "[Number] [things/lessons] that [specific payoff/outcome]."

2. TOPIC SELECTION (Identity beats Information):
   Choose topics that make the reader feel something about who THEY are (self-belief, career decisions, management, failure) rather than just delivering dry facts.

3. STRUCTURE & LENGTH (The Barbell Rule):
   Categorize each idea's writing style recommendation as one of these two:
   - "Truth Bomb": Extremely punchy statement (under 10 words total).
   - "Deep Story": Fully developed narrative in 150-200 or 300+ words using the "4-Beat Micro-Story" framework:
     - Beat 1: Open mid-scene with an anonymous, specific character (no setup).
     - Beat 2: Raise the stakes (tension or conflict).
     - Beat 3: Reveal the turn (non-obvious insight/reframe).
     - Beat 4: Hand it to the reader (transferable principle - never end with a question or link).

Categories to choose from:
  Mindset & Resilience | Career & Networks | Skills & Leadership | Economics & Policy | Marketing & Brands | Tech & Innovation | Current Affairs

Return ONLY valid JSON — no markdown, no explanation, just the JSON object:

{{
  "ideas": [
    {{
      "post_idea": "Concise topic title (e.g. 'How Zepto broke Blinkit's pricing strategy')",
      "angle": "The unique take or framing for this post",
      "hook": "The exact opening sentence matching one of the 5 templates (no questions, no stats)",
      "category": "One of the categories above",
      "recommended_format": "Either 'Truth Bomb' or 'Deep Story (4-Beat)'",
      "why_it_works": "1-2 sentences on why this resonates and how it drives shares (identity angle)",
      "source_inspiration": "Title of the scraped item that inspired this idea (copy it exactly from the list above)",
      "source_url": "The URL from the list for that item (copy it exactly, or empty string if none)"
    }}
  ]
}}"""

    return prompt


def generate_post_ideas(scraped_data: list[dict]) -> list[dict]:
    """
    Send scraped content to Gemini and get back post ideas.
    Tries multiple models in order to handle quota limits.
    """

    if not scraped_data:
        print("   [AI] No scraped data to process.")
        return []

    # Try models in order — use lite/smaller models first (less quota pressure)
    MODELS_TO_TRY = [
        "gemini-2.5-flash-lite",   # Lowest quota usage
        "gemini-2.0-flash-lite",   # Fallback
        "gemini-2.5-flash",        # More capable, higher quota
        "gemini-2.0-flash",        # Last resort
    ]

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = _build_prompt(scraped_data)
    raw = ""

    for model_name in MODELS_TO_TRY:
        try:
            print(f"   [AI] Trying model: {model_name} ...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    max_output_tokens=4096,
                ),
            )

            raw = response.text.strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            raw = raw.strip()

            data = json.loads(raw)
            ideas = data.get("ideas", [])

            if not isinstance(ideas, list):
                print(f"   [AI] Unexpected response format from {model_name}.")
                continue

            print(f"   [AI] ✅ Success with {model_name}")
            return ideas

        except json.JSONDecodeError as e:
            print(f"   [AI] JSON parse error with {model_name}: {e}")
            print(f"   [AI] Raw response (first 500 chars): {raw[:500]}")
            continue
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"   [AI] Rate limit hit on {model_name} — trying next model...")
                continue
            elif "404" in err_str or "not found" in err_str.lower():
                print(f"   [AI] Model {model_name} not available — trying next...")
                continue
            else:
                print(f"   [AI] Error with {model_name}: {e}")
                continue

    print("   [AI] ❌ All models exhausted. Check your API key or try again later.")
    return []

