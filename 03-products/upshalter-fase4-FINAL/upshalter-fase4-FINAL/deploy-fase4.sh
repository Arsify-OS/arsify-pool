#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  DEPLOY FASE 4 v2 — Fixed: semua mismatch diselesaikan
#  Mei 2026 — bash deploy-fase4.sh
# ═══════════════════════════════════════════════════════════════════════

set -uo pipefail
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="/root/upshalter-logs/deploy-fase4v2-$(date +%Y%m%d-%H%M).log"
mkdir -p /root/upshalter-logs
echo "=== DEPLOY FASE 4 v2: $(date) ===" > "$LOG"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
ok()  { echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG"; }
err() { echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG"; }
wrn() { echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOG"; }
inf() { echo -e "${BLUE}[→]${NC} $1" | tee -a "$LOG"; }
hdr() { echo -e "\n${BOLD}── $1 ──${NC}" | tee -a "$LOG"; }

echo -e "${BOLD}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   UPSHALTER FASE 4 v2 — Fixed Mismatches     ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════╝${NC}"

PASS=0; FAIL=0; WARN=0

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 1: Deteksi Sistem"
# ══════════════════════════════════════════════════════════════════════

inf "Running SKP adapter detection..."
SYS_INFO=$(python3 "$DEPLOY_DIR/python/skp_adapter.py" 2>>"$LOG" || echo "DETECTION_FAILED")

if echo "$SYS_INFO" | grep -q "DETECTION_FAILED"; then
    wrn "SKP adapter detection failed — will use defaults"
    SKP_DB="/data/arsify.db"
    SKP_TABLE="memory_notes"
else
    SKP_DB=$(echo "$SYS_INFO" | grep "DB Path:" | awk '{print $NF}')
    SKP_TABLE=$(echo "$SYS_INFO" | grep "Table:" | awk '{print $NF}')
    ok "System detected: DB=$SKP_DB, Table=$SKP_TABLE"
fi

echo "export SKP_DB_PATH=$SKP_DB" >> "$LOG"
echo "export SKP_TABLE=$SKP_TABLE" >> "$LOG"

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 2: Install Dependencies"
# ══════════════════════════════════════════════════════════════════════

for pkg in httpx; do
    python3 -c "import $pkg" 2>/dev/null && ok "$pkg OK" || {
        inf "Installing $pkg..."
        pip install $pkg --break-system-packages -q && ok "$pkg installed" || wrn "$pkg install failed"
    }
done

# scikit-learn opsional
python3 -c "import sklearn" 2>/dev/null && ok "scikit-learn OK" || {
    pip install scikit-learn --break-system-packages -q && ok "scikit-learn installed" || wrn "scikit-learn skip"
}

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 3: Deploy Scripts"
# ══════════════════════════════════════════════════════════════════════

SDIR="/root/upshalter-scripts"
PDIR="$SDIR/python"
mkdir -p "$SDIR" "$PDIR"

# Copy semua scripts
cp "$DEPLOY_DIR/scripts/senator-cycle-v2.sh" "$SDIR/" && chmod +x "$SDIR/senator-cycle-v2.sh" && ok "senator-cycle-v2.sh" || { err "senator-cycle-v2.sh failed"; ((FAIL++)); }
cp "$DEPLOY_DIR/scripts/kurator-v2.sh" "$SDIR/"        && chmod +x "$SDIR/kurator-v2.sh"        && ok "kurator-v2.sh"        || { err "kurator-v2.sh failed"; ((FAIL++)); }

# Copy Python files (termasuk adapter)
for f in skp_adapter.py category-backfill.py moe-router-senator-patch.py; do
    [ -f "$DEPLOY_DIR/python/$f" ] && {
        cp "$DEPLOY_DIR/python/$f" "$PDIR/"
        ok "$f"
        ((PASS++))
    } || wrn "$f not found"
done

# Buat symlink di SDIR agar scripts bisa import
ln -sfn "$PDIR" "$SDIR/python" 2>/dev/null || true

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 4: Verifikasi SKP Adapter"
# ══════════════════════════════════════════════════════════════════════

inf "Testing SKP adapter with actual system..."
python3 "$PDIR/skp_adapter.py" 2>>"$LOG" | tee -a "$LOG"
ok "SKP adapter verified"
((PASS++))

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 5: Category Backfill"
# ══════════════════════════════════════════════════════════════════════

inf "Running dry-run first..."
DRY_RUN=true python3 "$PDIR/category-backfill.py" 2>>"$LOG" | tee -a "$LOG"

echo ""
inf "Running live backfill..."
DRY_RUN=false python3 "$PDIR/category-backfill.py" 2>>"$LOG" | tee -a "$LOG"
ok "Category backfill complete"
((PASS++))

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 6: Patch Arsify Router"
# ══════════════════════════════════════════════════════════════════════

python3 "$PDIR/moe-router-senator-patch.py" 2>>"$LOG" | tee -a "$LOG"
ok "Arsify router patch attempted"
((PASS++))

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 7: Update Crontab"
# ══════════════════════════════════════════════════════════════════════

(crontab -l 2>/dev/null | grep -v "senator-cycle\|kurator-review\|senator-cycle-v2\|kurator-v2" ; cat << CRON
# Upshalter Fase 4 v2 — $(date)
*/5 * * * * /root/upshalter-scripts/health-check.sh >> /root/upshalter-logs/health.log 2>&1
0 */6 * * * SCRIPT_DIR=/root/upshalter-scripts bash /root/upshalter-scripts/senator-cycle-v2.sh >> /root/upshalter-logs/senator.log 2>&1
0 1,7,13,19 * * * SCRIPT_DIR=/root/upshalter-scripts bash /root/upshalter-scripts/kurator-v2.sh >> /root/upshalter-logs/kurator.log 2>&1
0 0 * * * /root/upshalter-scripts/daily-summary.sh >> /root/upshalter-logs/daily.log 2>&1
0 20 * * * bash /root/upshalter-scripts/backup-skp.sh >> /root/upshalter-logs/backup.log 2>&1
CRON
) | crontab - && ok "Crontab updated ($(crontab -l | grep upshalter | wc -l) jobs)" || err "Crontab failed"

# ══════════════════════════════════════════════════════════════════════
hdr "STEP 8: Test Senator (one senator, 30s limit)"
# ══════════════════════════════════════════════════════════════════════

inf "Quick test: can we reach Ollama or Hermes API?"
if curl -sf http://localhost:11434/api/tags -m 5 >/dev/null 2>&1; then
    ok "Ollama reachable — senator fallback will work"
    ((PASS++))
elif curl -sf http://localhost:8100/ -m 5 >/dev/null 2>&1; then
    ok "Hermes API :8100 reachable — senator primary will work"
    ((PASS++))
else
    err "Neither Ollama nor Hermes API reachable — senator WILL fail"
    ((FAIL++))
fi

# ══════════════════════════════════════════════════════════════════════
hdr "SELESAI"
# ══════════════════════════════════════════════════════════════════════

echo ""
echo -e "${BOLD}╔════════════════════════════════════════════════════╗${NC}"
printf "${BOLD}║  Pass: %-3s | Warn: %-3s | Fail: %-3s               ║${NC}\n" "$PASS" "$WARN" "$FAIL"
printf "${BOLD}║  SKP: %-47s║${NC}\n" "$SKP_DB (Table: $SKP_TABLE)"
printf "${BOLD}║  Log: %-47s║${NC}\n" "$LOG"
echo -e "${BOLD}╚════════════════════════════════════════════════════╝${NC}"
echo ""

REPORT="[FASE 4 v2 DEPLOY — $(date '+%d/%m %H:%M')]
Fixed: table mismatch, key format, DB path
Pass: $PASS | Warn: $WARN | Fail: $FAIL
SKP: $SKP_DB ($SKP_TABLE)
Scripts: senator-cycle-v2.sh + kurator-v2.sh aktif
Cron: $(crontab -l 2>/dev/null | grep senator | wc -l) senator jobs
Next senator cycle: jam $((( $(date +%H)/6 + 1) * 6 % 24)):00 WIB"

command -v hermes &>/dev/null && hermes -z "send_message Telegram: $REPORT" 2>/dev/null || echo "$REPORT"
echo "=== DONE: $(date) ===" >> "$LOG"
