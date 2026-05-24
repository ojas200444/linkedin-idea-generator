"""
Google Sheets Writer
Connects to Google Sheets via a Service Account and appends generated ideas.
Each run adds new rows with today's date — never overwrites existing data.
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
from config import GOOGLE_CREDENTIALS_FILE, SPREADSHEET_NAME

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Direct sheet ID (more reliable than searching by name)
SPREADSHEET_ID = "11cIVzAU2rsY_y1KNHH4FWYQtjCjJrik8Ib1tmDHnC6k"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"

HEADERS = [
    "Date",
    "Category",
    "Post Idea",
    "Angle",
    "Hook Line",
    "Why It Works",
    "Source / Inspiration",
    "Source URL",
    "Status",
]

# Status column values you can use to track ideas:
# Pending → Used → Skipped → Saved for later


def _get_client():
    """
    Authenticate and return a gspread client.
    Supports two modes:
      - Local dev: reads credentials from the JSON file path in config
      - Cloud/CI:  reads credentials from GOOGLE_CREDENTIALS_JSON env variable
    """
    import json

    creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if creds_json_str:
        # Cloud mode — parse JSON directly from environment variable
        try:
            creds_info = json.loads(creds_json_str)
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"\n❌ GOOGLE_CREDENTIALS_JSON env var contains invalid JSON: {e}"
            )
    else:
        # Local mode — read from credentials file
        creds_path = os.path.join(os.path.dirname(__file__), GOOGLE_CREDENTIALS_FILE)
        if not os.path.exists(creds_path):
            raise FileNotFoundError(
                f"\n❌ Credentials file not found: {creds_path}\n"
                f"   Either set the GOOGLE_CREDENTIALS_JSON environment variable,\n"
                f"   or place your credentials JSON at: {creds_path}\n"
                f"   See SETUP_GUIDE.md for instructions."
            )
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)

    return gspread.authorize(creds)



def _get_or_create_sheet(client):
    """Open the spreadsheet by ID (pre-created and shared with service account)."""
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.sheet1
        return sheet
    except Exception as e:
        raise RuntimeError(
            f"\n❌ Could not open Google Sheet by ID.\n"
            f"   Sheet ID: {SPREADSHEET_ID}\n"
            f"   Make sure the sheet is shared with: linkedin-bot@linkedin-idea-bot.iam.gserviceaccount.com\n"
            f"   Error: {e}"
        )


def _ensure_headers(sheet):
    """Add headers if the sheet is empty."""
    existing = sheet.get_all_values()
    if not existing or existing[0] != HEADERS:
        sheet.insert_row(HEADERS, index=1)
        # Style the header row
        sheet.format("A1:H1", {
            "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.8},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        })
        sheet.freeze(rows=1)


def write_ideas_to_sheet(ideas: list[dict]) -> int:
    """
    Append generated ideas to the Google Sheet.
    Returns the number of rows added.
    """
    if not ideas:
        print("   [Sheets] No ideas to write.")
        return 0

    client = _get_client()
    sheet = _get_or_create_sheet(client)
    _ensure_headers(sheet)

    today = datetime.now().strftime("%Y-%m-%d")
    rows = []

    for idea in ideas:
        rows.append([
            today,
            idea.get("category", ""),
            idea.get("post_idea", ""),
            idea.get("angle", ""),
            idea.get("hook", ""),
            idea.get("why_it_works", ""),
            idea.get("source_inspiration", ""),
            idea.get("source_url", ""),
            "Pending",  # Default status
        ])

    sheet.append_rows(rows, value_input_option="USER_ENTERED")

    print(f"   [Sheets] ✅ Added {len(rows)} ideas for {today}")
    print(f"   [Sheets] 🔗 Open: {SHEET_URL}")

    return len(rows)
