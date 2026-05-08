#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  SENATOR CYCLE v5 — Arsify Workforce OS
#  Menggunakan senator-execution.py — THE MISSING LAYER FIXED
#  Setiap senator DIJAMIN menulis insight nyata ke SKP, bukan prompt junk
# ═══════════════════════════════════════════════════════════════════════

set -uo pipefail

SCRIPT_DIR="${SCRIPT_DIR:-/root/upshalter-scripts}"
PDIR="$SCRIPT_DIR/python"
LOG_DIR="/root/upshalter-logs"
LOG="$LOG_DIR/senator-$(date +%Y%m%d).log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

mkdir -p "$LOG_DIR"
echo "" >> "$LOG"
echo "══════ SENATOR CYCLE v5 | $TIMESTAMP ══════" >> "$LOG"
echo "Using senator-execution.py — guaranteed real insights" >> "$LOG"

# ── Pastikan senator-execution.py ada ────────────────────────────────
if [ ! -f "$PDIR/senator-execution.py" ]; then
    echo "  ✗ senator-execution.py not found at $PDIR/" >> "$LOG"
    echo "  Install: copy senator-execution.py ke $PDIR/"
    exit 1
fi

# ── Jalankan semua 5 Senator ──────────────────────────────────────────
FAILED=0; SUCCESS=0

for domain in akademisi bisnis komunitas pemerintah media; do
    echo "" >> "$LOG"
    echo "[$(date +%H:%M:%S)] ▶ $domain" >> "$LOG"

    RESULT=$(SCRIPT_DIR="$SCRIPT_DIR" \
             OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}" \
             OPENROUTER_MODEL="${OPENROUTER_MODEL:-openai/gpt-4o-mini}" \
             python3 "$PDIR/senator-execution.py" --domain "$domain" \
             2>>"$LOG")

    EXIT_CODE=$?
    echo "$RESULT" >> "$LOG"

    if echo "$RESULT" | grep -q '"status": "success"'; then
        WRITTEN=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('written',0))" 2>/dev/null || echo "?")
        echo "  ✓ $domain: $WRITTEN insights written" >> "$LOG"
        ((SUCCESS++))
    else
        ERROR=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error','unknown'))" 2>/dev/null || echo "failed")
        echo "  ✗ $domain: $ERROR" >> "$LOG"
        ((FAILED++))
    fi
done

# ── Summary ───────────────────────────────────────────────────────────
TOTAL_SKP=$(python3 - << 'PYEOF' 2>/dev/null || echo "?"
import sqlite3, os, sys
for db in ["/data/arsify.db", "/data/shared_knowledge_pool.db"]:
    if os.path.exists(db):
        conn = sqlite3.connect(db)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        table = next((t for t in ['knowledge','memory_notes'] if t in tables), 'knowledge')
        total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        today = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE date(created_at)=date('now')").fetchone()[0]
        print(f"{total} ({today} hari ini)")
        conn.close()
        break
PYEOF
)

echo "" >> "$LOG"
echo "══ DONE: $SUCCESS/5 success | $FAILED failed | SKP: $TOTAL_SKP | $TIMESTAMP ══" >> "$LOG"

MSG="Arsify Workforce OS — Senator Cycle v5
$SUCCESS/5 analysts completed
SKP: $TOTAL_SKP entries
$([ $SUCCESS -eq 5 ] && echo '✓ All analysts produced real insights' || echo "⚠ $FAILED analysts failed — check $LOG")"

echo "$MSG" >> "$LOG"
command -v hermes &>/dev/null && \
    hermes -z "send_message Telegram: $MSG" 2>/dev/null || true

# Trigger kurator setelah 5 menit kalau ada yang berhasil
[ $SUCCESS -gt 0 ] && ( sleep 300 && SCRIPT_DIR="$SCRIPT_DIR" bash "$SCRIPT_DIR/kurator-v3.sh" ) & 2>/dev/null || true
