#!/bin/bash
# deliver-intelligence.sh v2 — Pentahelix Intelligence Platform (PRD-002)
# Mengirim laporan ke semua subscriber aktif

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
SUBSCRIBERS_FILE="/root/upshalter-config/subscribers.json"
REPORT_DIR="/root/upshalter-reports"
LOG_FILE="/root/upshalter-logs/delivery.log"
TELEGRAM_TOKEN="8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU"

mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# ── Find Latest Report ────────────────────────────────────────────────
LATEST_REPORT=$(ls -t "$REPORT_DIR"/pentahelix-brief-*.md 2>/dev/null | head -1)

if [ -z "$LATEST_REPORT" ]; then
    log "ERROR: No report found to deliver"
    echo "No report found in $REPORT_DIR"
    exit 1
fi

log "Starting delivery for report: $LATEST_REPORT"

# ── Check if Already Delivered ───────────────────────────────────────
DELIVERY_FLAG="${LATEST_REPORT}.delivered"
if [ -f "$DELIVERY_FLAG" ]; then
    log "Report already delivered (flag exists: $DELIVERY_FLAG)"
    echo "Report already delivered"
    exit 0
fi

# ── Run Python Delivery Script ───────────────────────────────────────
export LATEST_REPORT
export SUBSCRIBERS_FILE
export TELEGRAM_TOKEN
export LOG_FILE

python3 << 'PYTHON_SCRIPT'
import json
import os
import sys
import urllib.request
import urllib.parse

report_file = os.environ.get('LATEST_REPORT', '')
subscribers_file = os.environ.get('SUBSCRIBERS_FILE', '/root/upshalter-config/subscribers.json')
telegram_token = os.environ.get('TELEGRAM_TOKEN', '')
log_file = os.environ.get('LOG_FILE', '/root/upshalter-logs/delivery.log')

def log(msg):
    with open(log_file, 'a') as f:
        f.write(f"[{__import__('datetime').datetime.now()}] {msg}\n")

# Get report content
try:
    with open(report_file, 'r', encoding='utf-8') as f:
        report_content = f.read()
except Exception as e:
    log(f"Error reading report: {e}")
    sys.exit(1)

# Get summary (first 500 chars)
summary = report_content[:500]

# Load subscribers
try:
    with open(subscribers_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    log(f"Error loading subscribers: {e}")
    sys.exit(1)

subscribers = data.get("subscribers", [])

delivered = 0
failed = 0

for sub in subscribers:
    if not sub.get("active", False):
        continue
    
    name = sub.get("name", "Unknown")
    telegram_id = sub.get("telegram_id")
    tier = sub.get("tier", "starter")
    
    if not telegram_id:
        log(f"Skipping {name}: no telegram_id")
        continue
    
    # Prepare message
    msg = f"""📊 *Pentahelix Intelligence Brief* ({tier.upper()})

Halo {name},

{summary}

---
📄 Full report: {report_file}
🆔 Subscriber: {sub.get('id', 'N/A')}
💎 Tier: {tier}
"""
    
    # Send via Telegram
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': str(telegram_id),
            'text': msg,
            'parse_mode': 'Markdown'
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('ok'):
                print(f"✅ Delivered to {name} ({telegram_id})")
                log(f"✅ Delivered to {name} ({telegram_id})")
                delivered += 1
            else:
                print(f"❌ Failed to deliver to {name}: {result}")
                log(f"❌ Failed to deliver to {name}: {result}")
                failed += 1
    except Exception as e:
        print(f"❌ Error delivering to {name}: {e}")
        log(f"❌ Error delivering to {name}: {e}")
        failed += 1

print(f"\nDelivery complete: {delivered} success, {failed} failed")
log(f"Delivery complete: {delivered} success, {failed} failed")
PYTHON_SCRIPT

DELIVERY_STATUS=$?

if [ $DELIVERY_STATUS -eq 0 ]; then
    touch "$DELIVERY_FLAG"
    log "Delivery successful, flag set: $DELIVERY_FLAG"
else
    log "Delivery failed with status: $DELIVERY_STATUS"
fi

exit $DELIVERY_STATUS
