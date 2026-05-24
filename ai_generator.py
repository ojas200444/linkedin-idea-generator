"""
AI Generator
Uses Google Gemini API to analyze scraped content and generate
targeted LinkedIn post ideas tailored to the creator's style and audience.
Uses the new google.genai SDK.
"""

import json
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, AUDIENCE_DESCRIPTION, POST_STYLE_EXAMPLES


def _build_prompt(scraped_items: list[dict]) -> str:
    """Build the Gemini prompt from scraped content."""

    content_lines = []
    # Build a lookup map: title → url (for AI to reference back)
    url_map = {}
    for item in scraped_items[:50]:
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

    prompt = f"""You are a LinkedIn content strategist for an Indian creator who writes about business, marketing, economics, and current affairs.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TARGET AUDIENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{AUDIENCE_DESCRIPTION.strip()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CREATOR'S PAST POST STYLE (learn from these)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{examples_block}

Notice the pattern: each post takes a real event, brand story, policy, or concept and gives it a business/life-lesson angle. They are NOT generic — they are specific, often controversial or surprising, and tell a story.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TODAY'S TRENDING INTERNET CONTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
From the trending content above, generate exactly 8 high-quality LinkedIn post ideas for this creator.

Rules:
- Each idea must be SPECIFIC (not generic like "The future of AI")
- Take a unique angle that would spark discussion or surprise
- The hook must be a strong opening sentence, not a question
- Ideas should vary across categories
- Prefer India-relevant or India-comparison angles where possible

Categories to choose from:
  Marketing/Branding | Economics/Policy | Tech/Science | Psychology/Frameworks | India vs World | Entrepreneur Mindset | Current Affairs

Return ONLY valid JSON — no markdown, no explanation, just the JSON object:

{{
  "ideas": [
    {{
      "post_idea": "Concise topic title (e.g. 'How Zepto broke Blinkit's pricing strategy')",
      "angle": "The unique take or framing for this post",
      "hook": "The exact opening sentence that would stop the scroll",
      "category": "One of the 6 categories above",
      "why_it_works": "1-2 sentences on why this resonates with the target audience",
      "source_inspiration": "Title of the scraped item that inspired this idea (copy it exactly from the content list above)",
      "source_url": "The URL from the content list for that item (copy it exactly, or empty string if none)"
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

