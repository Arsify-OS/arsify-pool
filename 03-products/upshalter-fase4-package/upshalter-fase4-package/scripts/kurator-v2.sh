#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  KURATOR PENTAHELIX v2 — Konsolidasi & Quality Scoring
#  Versi: 2.0 — Mei 2026
#  Perubahan: 120s timeout, structured JSON output, confidence scoring,
#  langsung call Ollama (bypass Kanban/Gateway)
# ═══════════════════════════════════════════════════════════════════════

set -euo pipefail

SKP_DB="${SKP_DB_PATH:-/data/arsify.db}"
OLLAMA_API="http://localhost:11434"
REPORT_DIR="/root/upshalter-reports"
LOG_DIR="/root/upshalter-logs"
DATE=$(date +%Y%m%d)
HOUR=$(date +%H)
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
LOG="$LOG_DIR/kurator-$(date +%Y%m%d).log"
REPORT_FILE="$REPORT_DIR/pentahelix-brief-${DATE}-${HOUR}.md"

mkdir -p "$REPORT_DIR" "$LOG_DIR"

echo "" >> "$LOG"
echo "════════════════════════════════════════" >> "$LOG"
echo "KURATOR v2 START: $TIMESTAMP" >> "$LOG"
echo "════════════════════════════════════════" >> "$LOG"

# ── Step 1: Ambil data Senator dari SKP ───────────────────────────────
echo "[1/5] Reading recent SKP entries..." >> "$LOG"

SKP_DATA=$(python3 - << 'PYEOF'
import sqlite3, json, sys, os
from datetime import datetime, timedelta

db_path = os.getenv("SKP_DB_PATH", "/data/arsify.db")
hours_back = 12  # Ambil 12 jam terakhir untuk pastikan dapat data

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cutoff = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat()

    rows = conn.execute("""
        SELECT key, value, source_agent_name, category, created_at
        FROM memory_notes
        WHERE (
            key LIKE 'akademisi/%'
            OR key LIKE 'bisnis/%'
            OR key LIKE 'komunitas/%'
            OR key LIKE 'pemerintah/%'
            OR key LIKE 'media/%'
        )
        AND created_at >= ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (cutoff,)).fetchall()

    if not rows:
        # Fallback: ambil 10 terbaru dari semua domain
        rows = conn.execute("""
            SELECT key, value, source_agent_name, category, created_at
            FROM memory_notes
            WHERE key LIKE 'akademisi/%'
               OR key LIKE 'bisnis/%'
               OR key LIKE 'komunitas/%'
               OR key LIKE 'pemerintah/%'
               OR key LIKE 'media/%'
            ORDER BY created_at DESC
            LIMIT 10
        """).fetchall()

    result = []
    for r in rows:
        result.append({
            "key": r["key"],
            "value": r["value"][:800],  # Truncate untuk prompt
            "agent": r["source_agent_name"] or "unknown",
            "created_at": r["created_at"]
        })

    conn.close()
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps([]), file=sys.stdout)
    print(f"SKP read error: {e}", file=sys.stderr)
PYEOF
)

ENTRY_COUNT=$(echo "$SKP_DATA" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
echo "  Found $ENTRY_COUNT recent entries" >> "$LOG"

# ── Step 2: Deteksi model Ollama ──────────────────────────────────────
echo "[2/5] Detecting Ollama model..." >> "$LOG"

OLLAMA_MODEL=$(curl -sf "$OLLAMA_API/api/tags" 2>/dev/null | \
    python3 -c "
import sys,json
try:
    ms = [m['name'] for m in json.load(sys.stdin).get('models',[])]
    # Prefer lebih besar untuk kurator (konsolidasi kompleks)
    for prefer in ['qwen2.5:7b','llama3.1:8b','llama3.2:3b','qwen2.5:1.5b','phi3:mini']:
        if any(prefer in m for m in ms): print(prefer); exit()
    print(ms[0] if ms else '')
except: print('')
" 2>/dev/null || echo "")

if [ -z "$OLLAMA_MODEL" ]; then
    echo "  ✗ No Ollama model available, exiting" >> "$LOG"
    exit 1
fi
echo "  Using model: $OLLAMA_MODEL" >> "$LOG"

# ── Step 3: Generate laporan via Ollama ───────────────────────────────
echo "[3/5] Generating consolidated report..." >> "$LOG"

KURATOR_PROMPT="Kamu adalah Kurator Pentahelix Upshalter. Tugasmu: konsolidasi temuan 5 Senator menjadi intelligence brief yang actionable untuk eksekutif bisnis Indonesia.

DATA DARI SENATOR (JSON):
$SKP_DATA

Tanggal brief: $TIMESTAMP

Buat laporan dengan FORMAT PERSIS berikut (gunakan markdown):

# PENTAHELIX INTELLIGENCE BRIEF
**Tanggal:** $TIMESTAMP
**Kurator:** kurator-pentahelix-v2
**Confidence:** [0.0-1.0 berdasarkan kelengkapan data]

## RINGKASAN EKSEKUTIF
[2-3 kalimat: apa yang paling penting hari ini dari seluruh domain]

## TEMUAN PER DOMAIN

### AKADEMISI
[2-3 poin temuan spesifik dengan angka/fakta]

### BISNIS
[2-3 poin temuan spesifik dengan angka/fakta]

### KOMUNITAS
[2-3 poin temuan spesifik dengan angka/fakta]

### PEMERINTAH
[2-3 poin temuan spesifik dengan angka/fakta]

### MEDIA
[2-3 poin temuan spesifik dengan angka/fakta]

## TEMA LINTAS DOMAIN
[2-3 tema yang muncul di lebih dari 1 domain — ini yang paling valuable]

## IMPLIKASI UNTUK UPSHALTER
[1-2 poin: apa yang harus dilakukan Upshalter berdasarkan brief ini]

## ALERT
[Kosongkan jika tidak ada yang kritis. Isi HANYA jika ada: regulasi baru yang mengancam, peluang yang time-sensitive, atau risiko yang perlu respons segera]

Penting: Jika data Senator tidak ada atau kosong, tetap buat brief dengan note 'Data Senator belum tersedia — menggunakan konteks historis' dan confidence 0.1."

REPORT_CONTENT=$(python3 - << PYEOF
import httpx, json, sys

model = "$OLLAMA_MODEL"
prompt = """$KURATOR_PROMPT"""

try:
    with httpx.Client(timeout=120.0) as c:
        r = c.post("$OLLAMA_API/api/chat", json={
            "model": model,
            "messages": [
                {"role": "system", "content": "Kamu adalah Kurator Pentahelix Upshalter. Tulis laporan intelligence yang tajam, faktual, dan actionable dalam Bahasa Indonesia."},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 3000,
                "top_p": 0.9
            }
        })
        r.raise_for_status()
        print(r.json()["message"]["content"])
except Exception as e:
    print(f"# PENTAHELIX INTELLIGENCE BRIEF\n**Error:** {e}\n**Confidence:** 0.0\n\n## ALERT\nKurator gagal generate. Periksa koneksi Ollama.", file=sys.stdout)
    print(f"Error: {e}", file=sys.stderr)
PYEOF
)

# ── Step 4: Hitung confidence score ───────────────────────────────────
echo "[4/5] Calculating confidence score..." >> "$LOG"

CONFIDENCE=$(python3 - << PYEOF
import json

data = $ENTRY_COUNT
max_entries = 10  # 2 entry per senator = ideal

# Base score dari jumlah entry
base = min(data / max_entries, 1.0)

# Penalty kalau 0 data
if data == 0:
    print("0.1")
elif data < 3:
    print(f"{base * 0.5:.2f}")
else:
    print(f"{base * 0.9:.2f}")
PYEOF
)

echo "  Confidence: $CONFIDENCE (entries: $ENTRY_COUNT)" >> "$LOG"

# ── Step 5: Simpan laporan ────────────────────────────────────────────
echo "[5/5] Saving report..." >> "$LOG"

# Tambahkan metadata ke laporan
FINAL_REPORT="<!-- Generated: $TIMESTAMP | Model: $OLLAMA_MODEL | Entries: $ENTRY_COUNT | Confidence: $CONFIDENCE -->
$REPORT_CONTENT
---
*Generated by Hermes Kurator Pentahelix v2 | $TIMESTAMP | $ENTRY_COUNT senator entries | confidence $CONFIDENCE*"

echo "$FINAL_REPORT" > "$REPORT_FILE"
echo "  Report saved: $REPORT_FILE" >> "$LOG"

# Simpan ke SKP
python3 - << PYEOF
import sqlite3, os
from datetime import datetime

db = os.getenv("SKP_DB_PATH", "/data/arsify.db")
key = f"laporan/konsolidasi/${DATE}-${HOUR}"
value = """$FINAL_REPORT"""[:4000]
now = datetime.utcnow().isoformat()

conn = sqlite3.connect(db)
conn.execute("""
    INSERT OR REPLACE INTO memory_notes (key, value, scope, source_agent_name, category, updated_at)
    VALUES (?, ?, 'global', 'kurator-v2', 'laporan', ?)
""", (key, value, now))
conn.commit()
conn.close()
print(f"SKP key: {key}")
PYEOF

# Buat ringkasan untuk Telegram (max 300 kata)
TELEGRAM_MSG=$(echo "$REPORT_CONTENT" | python3 - << 'PYEOF'
import sys, re

content = sys.stdin.read()

# Ambil ringkasan eksekutif
match = re.search(r'## RINGKASAN EKSEKUTIF\n(.*?)(?=##|\Z)', content, re.DOTALL)
summary = match.group(1).strip() if match else "Brief tersedia di server"

# Ambil tema lintas domain
match2 = re.search(r'## TEMA LINTAS DOMAIN\n(.*?)(?=##|\Z)', content, re.DOTALL)
themes = match2.group(1).strip() if match2 else ""

# Ambil alert
match3 = re.search(r'## ALERT\n(.*?)(?=##|\Z)', content, re.DOTALL)
alert = match3.group(1).strip() if match3 else ""

msg = f"""🔍 PENTAHELIX BRIEF — $(date '+%d %b %Y %H:%M WIB')

📋 RINGKASAN:
{summary[:400]}

🔗 TEMA LINTAS DOMAIN:
{themes[:200] if themes else "Belum teridentifikasi"}"""

if alert and len(alert) > 5:
    msg += f"\n\n⚠️ ALERT:\n{alert[:200]}"

msg += f"\n\n📊 Confidence: $CONFIDENCE | Entries: $ENTRY_COUNT\n🔗 Full: /root/upshalter-reports/pentahelix-brief-$DATE-$HOUR.md"

print(msg[:1500])
PYEOF
)

# Kirim ke Telegram (jika tersedia)
if command -v hermes &>/dev/null; then
    hermes -z "send_message Telegram verbatim: $TELEGRAM_MSG" 2>>"$LOG" || true
else
    echo "Telegram skip (hermes not available)" >> "$LOG"
    echo "--- TELEGRAM MSG ---" >> "$LOG"
    echo "$TELEGRAM_MSG" >> "$LOG"
fi

echo "" >> "$LOG"
echo "═══ KURATOR v2 DONE: $(date) | Confidence: $CONFIDENCE | Report: $REPORT_FILE ═══" >> "$LOG"
echo "Report generated successfully: $REPORT_FILE"
