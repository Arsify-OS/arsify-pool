#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
#  SENATOR CYCLE v6 — Arsify Workforce OS (MoE Version)
#  Menggunakan senator-execution-moe.py + Arsify MoE Router
#  Setiap senator ada DIJAMIN menulis insight nyata ke SKP
# ══════════════════════════════════════════════════════════════════════

set -uo pipefail

SCRIPT_DIR="${SCRIPT_DIR:-/root/upshalter-scripts}"
PDIR="$SCRIPT_DIR/python"
LOG_DIR="/root/upshalter-logs"
LOG="$LOG_DIR/senator-$(date +%Y%m%d).log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
MOE_SCRIPT="$SCRIPT_DIR/moe-router-start.sh"
MOE_PID_FILE="/tmp/moe-router.pid"

mkdir -p "$LOG_DIR"
echo "" >> "$LOG"
echo "══════ SENATOR CYCLE v6 (MoE) | $TIMESTAMP ═════" >> "$LOG"
echo "Using senator-execution-moe.py + Arsify MoE Router" >> "$LOG"

# ── Start MoE Router if not running ────────────────────────────────
start_moe_router() {
    if [ -f "$MOE_PID_FILE" ]; then
        OLD_PID=$(cat "$MOE_PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo "  ✓ MoE Router already running (PID: $OLD_PID)" >> "$LOG"
            return 0
        fi
    fi
    
    echo "  Starting MoE Router..." >> "$LOG"
    if [ -x "$MOE_SCRIPT" ]; then
        bash "$MOE_SCRIPT" >> "$LOG" 2>&1
        sleep 3
        if [ -f "$MOE_PID_FILE" ] && ps -p $(cat "$MOE_PID_FILE") > /dev/null 2>&1; then
            echo "  ✓ MoE Router started" >> "$LOG"
            return 0
        fi
    fi
    
    echo "  ✗ Failed to start MoE Router, will use OpenRouter fallback" >> "$LOG"
    return 1
}

start_moe_router

# ── Pastikan senator-execution-moe.py ada ─────────────────────────
if [ ! -f "$PDIR/senator-execution-moe.py" ]; then
    echo "  ✗ senator-execution-moe.py not found at $PDIR/" >> "$LOG"
    exit 1
fi

# ── Jalankan semua 5 Senator ──────────────────────────────────────
FAILED=0; SUCCESS=0; TOTAL_WRITTEN=0

for domain in akademisi bisnis pemerintah komunitas media; do
    echo "" >> "$LOG"
    echo "[$(date +%H:%M:%S)] ▶ $domain" >> "$LOG"

    # Check if MoE Router is running, if not use OpenRouter fallback
    USE_MOE="--use-moe"
    if [ -f "$MOE_PID_FILE" ] && ps -p $(cat "$MOE_PID_FILE") > /dev/null 2>&1; then
        USE_MOE=""
    else
        USE_MOE="--use-openrouter"
    fi
    
RESULT=$(OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-INSERT_OPENROUTER_KEY_HERE}" \
             SCRIPT_DIR="$SCRIPT_DIR" \
             python3 "$PDIR/senator-execution-moe.py" \
                --domain "$domain" \
                $USE_MOE \
                2>>"$LOG")

    EXIT_CODE=$?
    echo "$RESULT" >> "$LOG"

    if echo "$RESULT" | grep -q "Insights written to SKP:"; then
        WRITTEN=$(echo "$RESULT" | grep -oP '(?<=Insights written to SKP: )\d+' || echo "0")
        echo "  ✓ $domain: $WRITTEN insights written" >> "$LOG"
        ((SUCCESS++)) || true
        TOTAL_WRITTEN=$((TOTAL_WRITTEN + WRITTEN))
    else
        echo "  ✗ $domain: failed" >> "$LOG"
        ((FAILED++)) || true
    fi
done

# ── Summary ─────────────────────────────────────────────────────
echo "" >> "$LOG"
echo "══════ CYCLE COMPLETE | $TIMESTAMP ══════" >> "$LOG"
echo "  Success: $SUCCESS/5" >> "$LOG"
echo "  Failed:  $FAILED/5" >> "$LOG"
echo "  Total insights written: $TOTAL_WRITTEN" >> "$LOG"
echo "" >> "$LOG"

# ── Cron friendly output ─────────────────────────────────────────
if [ "$FAILED" -eq 0 ]; then
    echo "✅ All 5 Senators completed: $TOTAL_WRITTEN insights written"
else
    echo "⚠️  $SUCCESS/5 succeeded, $FAILED failed — $TOTAL_WRITTEN insights written"
fi

exit $FAILED
