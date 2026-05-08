#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  KURATOR PENTAHELIX v2.1 — Fixed: adaptive key format + 120s timeout
#  Mei 2026
# ═══════════════════════════════════════════════════════════════════════

set -uo pipefail

OLLAMA_API="http://localhost:11434"
REPORT_DIR="/root/upshalter-reports"
LOG_DIR="/root/upshalter-logs"
DATE=$(date +%Y%m%d); HOUR=$(date +%H)
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
LOG="$LOG_DIR/kurator-$(date +%Y%m%d).log"
REPORT_FILE="$REPORT_DIR/pentahelix-brief-${DATE}-${HOUR}.md"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$REPORT_DIR" "$LOG_DIR"
echo "" >> "$LOG"
echo "═══ KURATOR v2.1 START: $TIMESTAMP ═══" >> "$LOG"

# ── Step 1: Baca data Senator dari SKP (adaptive) ─────────────────────
SKP_DATA=$(python3 - << 'PYEOF'
import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__ if '__file__' in dir() else '.')), 'python'))

all_data = []
try:
    from skp_adapter import SKP
    skp = SKP()
    domains = ["akademisi", "bisnis", "komunitas", "pemerintah", "media"]
    for domain in domains:
        entries = skp.read_recent(domain, hours=12, limit=3)
        all_data.extend(entries)
    info = skp.get_info()
    if not all_data:
        # Fallback: ambil 15 entry terbaru dari domain manapun
        conn = skp.connect()
        rows = conn.execute(f"""
            SELECT key, value, source_agent_name, created_at
            FROM {skp.table}
            WHERE (
                key LIKE '%akademisi%' OR key LIKE '%bisnis%' OR
                key LIKE '%komunitas%' OR key LIKE '%pemerintah%' OR key LIKE '%media%' OR
                key LIKE '%senator%' OR key LIKE '%temuan%' OR key LIKE '%peluang%'
            )
            ORDER BY created_at DESC LIMIT 15
        """).fetchall()
        for r in rows:
            all_data.append({"key": r[0], "value": r[1][:600], "agent": r[2] or "unknown", "created_at": r[3] or ""})
except Exception as e:
    print(json.dumps({"error": str(e), "data": []}))
    sys.exit(0)

print(json.dumps(all_data[:15], ensure_ascii=False))
PYEOF
)

ENTRY_COUNT=$(echo "$SKP_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d) if isinstance(d, list) else 0)" 2>/dev/null || echo "0")
echo "Found $ENTRY_COUNT entries for consolidation" >> "$LOG"

# ── Step 2: Detect Ollama model ───────────────────────────────────────
OLLAMA_MODEL=$(curl -sf "$OLLAMA_API/api/tags" 2>/dev/null | python3 -c "
import sys,json
try:
    ms=[m['name'] for m in json.load(sys.stdin).get('models',[])]
    prefer=['qwen2.5:7b','llama3.1:8b','llama3.2:3b','qwen2.5:1.5b','phi3:mini']
    for p in prefer:
        if any(p in m for m in ms): print(p); exit()
    print(ms[0] if ms else '')
except: print('')
" 2>/dev/null || echo "")

[ -z "$OLLAMA_MODEL" ] && { echo "✗ No Ollama model" >> "$LOG"; exit 1; }
echo "Model: $OLLAMA_MODEL" >> "$LOG"

# ── Step 3: Calculate confidence ──────────────────────────────────────
CONFIDENCE=$(echo "$ENTRY_COUNT" | python3 -c "
import sys
n = int(sys.stdin.read().strip() or 0)
if n == 0: print('0.10')
elif n < 3: print(f'{n/10*0.5:.2f}')
elif n < 8: print(f'{n/10*0.8:.2f}')
else: print(f'{min(n/10,1.0)*0.9:.2f}')
" 2>/dev/null || echo "0.10")

# ── Step 4: Build context dari SKP data ───────────────────────────────
SKP_CONTEXT=$(echo "$SKP_DATA" | python3 - << 'PYEOF'
import sys, json
try:
    data = json.load(sys.stdin)
    if not isinstance(data, list):
        print("Data Senator belum tersedia.")
        sys.exit(0)
    lines = []
    for entry in data[:12]:
        domain = entry.get('key','').split('/')[0]
        value = entry.get('value','')[:400]
        lines.append(f"[{domain.upper()}] {value}")
    print("\n---\n".join(lines) if lines else "Belum ada data Senator.")
except Exception as e:
    print(f"Error reading SKP: {e}")
PYEOF
)

# ── Step 5: Generate laporan via Ollama ───────────────────────────────
echo "[$(date +%H:%M:%S)] Generating report with 120s timeout..." >> "$LOG"

REPORT_CONTENT=$(python3 - << PYEOF
import httpx, sys

SYSTEM = """Kamu adalah Kurator Pentahelix Upshalter. Buat intelligence brief yang tajam, faktual, dan actionable dalam Bahasa Indonesia untuk eksekutif bisnis."""

PROMPT = """Buat Pentahelix Intelligence Brief berdasarkan data Senator berikut:

=== DATA SENATOR ===
$SKP_CONTEXT
=== END DATA ===

Tanggal: $TIMESTAMP
Confidence tersedia: $CONFIDENCE (berdasarkan $ENTRY_COUNT entries)

Format laporan (gunakan PERSIS):

# PENTAHELIX INTELLIGENCE BRIEF
**Tanggal:** $TIMESTAMP
**Confidence:** $CONFIDENCE

## RINGKASAN EKSEKUTIF
[2-3 kalimat paling penting dari seluruh data]

## TEMUAN PER DOMAIN
### AKADEMISI
[2-3 poin spesifik dengan fakta/angka]
### BISNIS
[2-3 poin spesifik]
### KOMUNITAS
[2-3 poin spesifik]
### PEMERINTAH
[2-3 poin spesifik, terutama regulasi]
### MEDIA
[2-3 poin spesifik]

## TEMA LINTAS DOMAIN
[2-3 tema yang muncul di 2+ domain]

## IMPLIKASI UNTUK UPSHALTER
[1-2 poin actionable]

## ALERT
[Kosong jika tidak ada yang kritis]

Jika data minimal/kosong: tulis dengan note confidence rendah tapi tetap buat brief menggunakan pengetahuan kontekstual Indonesia terkini."""

try:
    with httpx.Client(timeout=120.0) as c:
        r = c.post("$OLLAMA_API/api/chat", json={
            "model": "$OLLAMA_MODEL",
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": PROMPT}
            ],
            "stream": False,
            "options": {"temperature": 0.25, "num_predict": 3000}
        })
        r.raise_for_status()
        print(r.json()["message"]["content"])
except Exception as e:
    print(f"""# PENTAHELIX INTELLIGENCE BRIEF
**Tanggal:** $TIMESTAMP
**Confidence:** 0.05

## ALERT
Kurator gagal generate: {e}

## CATATAN TEKNIS
Model: $OLLAMA_MODEL | Entries: $ENTRY_COUNT | Error: {type(e).__name__}
""")
    sys.exit(0)
PYEOF
)

# ── Step 6: Simpan laporan ─────────────────────────────────────────────
FINAL="<!-- Generated: $TIMESTAMP | Model: $OLLAMA_MODEL | Entries: $ENTRY_COUNT | Confidence: $CONFIDENCE -->
$REPORT_CONTENT
---
*Hermes Kurator Pentahelix v2.1 | $TIMESTAMP | confidence $CONFIDENCE*"

echo "$FINAL" > "$REPORT_FILE"
echo "Report saved: $REPORT_FILE" >> "$LOG"

# Simpan ke SKP
python3 - << PYEOF
import sys, os
sys.path.insert(0, os.path.join('$SCRIPT_DIR', 'python'))
try:
    from skp_adapter import SKP
    skp = SKP()
    key = f"laporan/konsolidasi/$DATE-$HOUR"
    skp.write(key, """$REPORT_CONTENT"""[:4000], "kurator-v2", "laporan")
    print(f"SKP written: {key}")
except Exception as e:
    print(f"SKP write skipped: {e}")
PYEOF

# Telegram summary
SUMMARY=$(echo "$REPORT_CONTENT" | python3 - << 'PYEOF'
import sys, re
content = sys.stdin.read()
m = re.search(r'## RINGKASAN EKSEKUTIF\n(.*?)(?=##|\Z)', content, re.DOTALL)
summary = m.group(1).strip()[:500] if m else "Brief tersedia."
m2 = re.search(r'## TEMA LINTAS DOMAIN\n(.*?)(?=##|\Z)', content, re.DOTALL)
themes = m2.group(1).strip()[:200] if m2 else ""
m3 = re.search(r'## ALERT\n(.*?)(?=##|\Z)', content, re.DOTALL)
alert = m3.group(1).strip() if m3 else ""
msg = f"PENTAHELIX BRIEF {__import__('datetime').date.today()}\n\n{summary}"
if themes: msg += f"\n\nTEMA: {themes}"
if alert and len(alert.strip()) > 10: msg += f"\n\nALERT: {alert[:200]}"
print(msg[:1200])
PYEOF
)

command -v hermes &>/dev/null && \
    hermes -z "send_message Telegram: $SUMMARY | Confidence: $CONFIDENCE | $ENTRY_COUNT entries" 2>/dev/null || \
    echo "$SUMMARY" >> "$LOG"

echo "═══ KURATOR v2.1 DONE: $(date) | Conf: $CONFIDENCE ═══" >> "$LOG"
echo "Report: $REPORT_FILE"
