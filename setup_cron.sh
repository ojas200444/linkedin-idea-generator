#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# setup_cron.sh — Schedule the LinkedIn Idea Generator to run daily at 11:30 AM IST
# 11:30 AM IST = 06:00 AM UTC
# ─────────────────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python3"
MAIN_SCRIPT="$SCRIPT_DIR/main.py"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/daily_run.log"

# Create logs directory
mkdir -p "$LOG_DIR"

# Cron job: 11:30 AM IST = 06:00 UTC
# Format: minute hour day month weekday command
CRON_JOB="0 6 * * * cd $SCRIPT_DIR && $PYTHON_PATH $MAIN_SCRIPT >> $LOG_FILE 2>&1"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  LinkedIn Idea Generator — Cron Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$MAIN_SCRIPT"; then
    echo "  ⚠️  Cron job already exists. Skipping."
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "  ✅ Cron job added!"
fi

echo ""
echo "  📅  Schedule: Every day at 11:30 AM IST (6:00 AM UTC)"
echo "  🗂️   Script: $MAIN_SCRIPT"
echo "  📋  Logs: $LOG_FILE"
echo ""
echo "  Useful commands:"
echo "    View cron jobs:   crontab -l"
echo "    Edit cron jobs:   crontab -e"
echo "    View logs:        tail -f $LOG_FILE"
echo "    Run manually:     python3 $MAIN_SCRIPT"
echo "    Test run:         python3 $MAIN_SCRIPT --test --dry-run"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
