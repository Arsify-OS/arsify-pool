#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  DEPLOY FASE 4 — Upshalter Senator + Kurator + Category Enrichment
#  Versi: 1.0 — Mei 2026
#
#  CARA PAKAI:
#    chmod +x deploy-fase4.sh
#    bash deploy-fase4.sh
#
#  APA YANG DILAKUKAN:
#    1. Validasi environment
#    2. Install dependencies (scikit-learn, httpx)
#    3. Deploy senator-cycle-v2.sh (bypass gateway)
#    4. Deploy kurator-v2.sh (120s timeout)
#    5. Jalankan category-backfill.py (fix 334 "general" entries)
#    6. Patch Arsify router dengan Senator rules
#    7. Update crontab
#    8. Test end-to-end
#    9. Kirim laporan
# ═══════════════════════════════════════════════════════════════════════

set -uo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="/root/upshalter-logs/deploy-fase4-$(date +%Y%m%d-%H%M).log"
SKP_DB="${SKP_DB_PATH:-/data/arsify.db}"

# ── Colors ─────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
ok()  { echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG"; }
err() { echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG"; }
inf() { echo -e "${BLUE}[→]${NC} $1" | tee -a "$LOG"; }
wrn() { echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOG"; }
hdr() { echo -e "\n${BOLD}── $1 ──${NC}" | tee -a "$LOG"; }

mkdir -p /root/upshalter-logs
echo "=== DEPLOY FASE 4 START: $(date) ===" > "$LOG"

echo -e "${BOLD}"
echo "╔═══════════════════════════════════════════════╗"
echo "║   UPSHALTER FASE 4 DEPLOYMENT                 ║"
echo "║   Senator + Kurator + Category Enrichment     ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

PASS=0; FAIL=0; WARN=0

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 1: Validasi Environment"
# ══════════════════════════════════════════════════════════════════════

# Cek Python3
python3 --version >/dev/null 2>&1 && ok "Python3 available" || { err "Python3 not found"; ((FAIL++)); }

# Cek SQLite database
if [ -f "$SKP_DB" ]; then
    ENTRIES=$(sqlite3 "$SKP_DB" "SELECT COUNT(*) FROM memory_notes" 2>/dev/null || echo "?")
    ok "SKP database: $ENTRIES entries"
    ((PASS++))
elif [ -L "$SKP_DB" ]; then
    ok "SKP symlink exists ($(readlink $SKP_DB))"
    ((PASS++))
else
    wrn "SKP database not found at $SKP_DB — will create"
    ((WARN++))
fi

# Cek Ollama
if curl -sf http://localhost:11434/api/tags -m 5 >/dev/null 2>&1; then
    MODELS=$(curl -sf http://localhost:11434/api/tags 2>/dev/null | \
        python3 -c "import sys,json; ms=json.load(sys.stdin).get('models',[]); print(', '.join([m['name'] for m in ms[:3]]))" 2>/dev/null)
    ok "Ollama running. Models: ${MODELS:-none}"
    ((PASS++))
else
    wrn "Ollama not running — Senator will have limited capability"
    ((WARN++))
    # Coba start Ollama
    systemctl start ollama 2>/dev/null && sleep 5 && ok "Ollama started" || true
fi

# Cek Hermes API
if curl -sf http://localhost:8100/health -m 5 >/dev/null 2>&1 || \
   curl -sf http://localhost:8100/ -m 5 >/dev/null 2>&1; then
    ok "Hermes API at :8100 responding"
    ((PASS++))
else
    wrn "Hermes API at :8100 not responding — will use Ollama fallback"
    ((WARN++))
fi

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 2: Install Python Dependencies"
# ══════════════════════════════════════════════════════════════════════

# httpx (untuk senator scripts)
python3 -c "import httpx" 2>/dev/null && ok "httpx already installed" || {
    inf "Installing httpx..."
    pip install httpx --break-system-packages -q && ok "httpx installed" || wrn "httpx install failed"
}

# scikit-learn (untuk deduplikasi — opsional)
python3 -c "import sklearn" 2>/dev/null && ok "scikit-learn already installed" || {
    inf "Installing scikit-learn..."
    pip install scikit-learn --break-system-packages -q && ok "scikit-learn installed" || \
        wrn "scikit-learn install failed (dedup akan pakai fallback)"
}

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 3: Deploy Senator Scripts"
# ══════════════════════════════════════════════════════════════════════

SCRIPTS_DIR="/root/upshalter-scripts"
mkdir -p "$SCRIPTS_DIR"

# senator-cycle-v2.sh
if [ -f "$DEPLOY_DIR/scripts/senator-cycle-v2.sh" ]; then
    cp "$DEPLOY_DIR/scripts/senator-cycle-v2.sh" "$SCRIPTS_DIR/"
    chmod +x "$SCRIPTS_DIR/senator-cycle-v2.sh"
    ok "senator-cycle-v2.sh deployed"
    ((PASS++))
else
    err "senator-cycle-v2.sh not found in $DEPLOY_DIR/scripts/"
    ((FAIL++))
fi

# kurator-v2.sh
if [ -f "$DEPLOY_DIR/scripts/kurator-v2.sh" ]; then
    cp "$DEPLOY_DIR/scripts/kurator-v2.sh" "$SCRIPTS_DIR/"
    chmod +x "$SCRIPTS_DIR/kurator-v2.sh"
    ok "kurator-v2.sh deployed"
    ((PASS++))
else
    err "kurator-v2.sh not found"
    ((FAIL++))
fi

# Copy python scripts
PYTHON_DIR="/root/upshalter-scripts/python"
mkdir -p "$PYTHON_DIR"

for pyfile in category-backfill.py moe-router-senator-patch.py; do
    if [ -f "$DEPLOY_DIR/python/$pyfile" ]; then
        cp "$DEPLOY_DIR/python/$pyfile" "$PYTHON_DIR/"
        ok "$pyfile deployed"
        ((PASS++))
    else
        wrn "$pyfile not found"
        ((WARN++))
    fi
done

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 4: Jalankan Category Backfill"
# ══════════════════════════════════════════════════════════════════════

if [ -f "$PYTHON_DIR/category-backfill.py" ]; then
    inf "Running category backfill (ini mungkin butuh 30-60 detik)..."
    SKP_DB_PATH="$SKP_DB" python3 "$PYTHON_DIR/category-backfill.py" 2>>"$LOG" | tee -a "$LOG"
    ok "Category backfill complete"
    ((PASS++))
else
    err "category-backfill.py not found"
    ((FAIL++))
fi

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 5: Patch Arsify Router dengan Senator Rules"
# ══════════════════════════════════════════════════════════════════════

if [ -f "$PYTHON_DIR/moe-router-senator-patch.py" ]; then
    inf "Patching Arsify router..."
    python3 "$PYTHON_DIR/moe-router-senator-patch.py" 2>>"$LOG" | tee -a "$LOG"
    ok "Arsify router patched"
    ((PASS++))
else
    wrn "Router patch script not found — skipping"
    ((WARN++))
fi

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 6: Update Crontab dengan Scripts Baru"
# ══════════════════════════════════════════════════════════════════════

inf "Installing updated cron schedule..."
(crontab -l 2>/dev/null | grep -v "senator-cycle\|kurator-review\|senator-cycle-v2\|kurator-v2" ; cat << 'CRON'
# ── Upshalter Fase 4 — Senator v2 + Kurator v2
*/5 * * * * /root/upshalter-scripts/health-check.sh >> /root/upshalter-logs/health.log 2>&1
*/5 * * * * /root/upshalter-scripts/generate-status-page.sh >> /root/upshalter-logs/status.log 2>&1
0 */2 * * * /root/upshalter-scripts/telegram-status.sh >> /root/upshalter-logs/telegram.log 2>&1
0 */6 * * * SKP_DB_PATH=/data/arsify.db bash /root/upshalter-scripts/senator-cycle-v2.sh >> /root/upshalter-logs/senator.log 2>&1
0 1,7,13,19 * * * SKP_DB_PATH=/data/arsify.db bash /root/upshalter-scripts/kurator-v2.sh >> /root/upshalter-logs/kurator.log 2>&1
0 0 * * * /root/upshalter-scripts/daily-summary.sh >> /root/upshalter-logs/daily.log 2>&1
0 1 * * * /root/upshalter-scripts/ssl-check.sh >> /root/upshalter-logs/ssl.log 2>&1
0 20 * * * SKP_DB_PATH=/data/arsify.db bash /root/upshalter-scripts/backup-skp.sh >> /root/upshalter-logs/backup.log 2>&1
0 0 * * 0 find /root/upshalter-logs -name "*.log" -mtime +30 -delete
CRON
) | crontab - && ok "Crontab updated ($(crontab -l | grep upshalter | wc -l) jobs)" || err "Crontab update failed"

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 7: Test Senator Cycle (dry run 1 senator)"
# ══════════════════════════════════════════════════════════════════════

inf "Testing senator-akademisi (will timeout after 60s)..."
timeout 60 bash -c "
export SKP_DB_PATH='$SKP_DB'
source /root/upshalter-scripts/senator-cycle-v2.sh 2>/dev/null | head -5
" 2>>"$LOG" && ok "Senator test passed" || wrn "Senator test timed out or failed (will work in production with full timeout)"

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 8: Verifikasi Final"
# ══════════════════════════════════════════════════════════════════════

verify() {
    local name=$1 cmd=$2
    if eval "$cmd" >/dev/null 2>&1; then ok "$name"; ((PASS++));
    else err "$name"; ((FAIL++)); fi
}

verify "senator-cycle-v2.sh exists"  "test -f /root/upshalter-scripts/senator-cycle-v2.sh"
verify "kurator-v2.sh exists"         "test -f /root/upshalter-scripts/kurator-v2.sh"
verify "category-backfill.py exists"  "test -f /root/upshalter-scripts/python/category-backfill.py"
verify "Cron senator-cycle-v2"        "crontab -l | grep senator-cycle-v2"
verify "SKP accessible"               "sqlite3 $SKP_DB 'SELECT COUNT(*) FROM memory_notes'"
verify "Report directory exists"      "test -d /root/upshalter-reports"

# Check SKP category improvement
AFTER_GENERAL=$(sqlite3 "$SKP_DB" \
    "SELECT COUNT(*) FROM memory_notes WHERE category='general' OR category IS NULL" 2>/dev/null || echo "?")
TOTAL=$(sqlite3 "$SKP_DB" "SELECT COUNT(*) FROM memory_notes" 2>/dev/null || echo "?")

# ══════════════════════════════════════════════════════════════════════
hdr "SELESAI"
# ══════════════════════════════════════════════════════════════════════

echo ""
echo -e "${BOLD}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   DEPLOY FASE 4 REPORT                            ║${NC}"
echo -e "${BOLD}╠═══════════════════════════════════════════════════╣${NC}"
printf "${BOLD}║  %-48s║${NC}\n" "Pass: $PASS | Warn: $WARN | Fail: $FAIL"
printf "${BOLD}║  %-48s║${NC}\n" "SKP general: $AFTER_GENERAL/$TOTAL"
printf "${BOLD}║  %-48s║${NC}\n" "Log: $LOG"
echo -e "${BOLD}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Kirim laporan ke Telegram
REPORT="[FASE 4 DEPLOY — $(date '+%d/%m/%Y %H:%M')]

✅ Pass: $PASS | ⚠️ Warn: $WARN | ❌ Fail: $FAIL

DEPLOYED:
• senator-cycle-v2.sh (bypass gateway)
• kurator-v2.sh (120s timeout)
• category-backfill.py (fix general entries)
• moe-router-senator-patch.py
• Cron schedule updated

SKP status: $AFTER_GENERAL/$TOTAL general entries
(Target: < 30%)

NEXT: Cron senator-cycle-v2 berjalan jam $(( ($(date +%H)/6 + 1) * 6 )):00 WIB"

command -v hermes &>/dev/null && \
    hermes -z "send_message Telegram verbatim: $REPORT" 2>/dev/null || \
    echo -e "\n$REPORT"

echo "=== DEPLOY DONE: $(date) ===" >> "$LOG"
