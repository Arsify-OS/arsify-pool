#!/bin/bash
# kurator-review.sh v2 — Pentahelix Intelligence Platform (PRD-002)
# Berjalan 1 jam setelah senator-cycle selesai
# Kurator membaca SKP entries → buat laporan terkonsolidasi → simpan ke SKP + file

set -euo pipefail

DATE=$(date +%Y%m%d)
HOUR=$(date +%H)
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
REPORT_DIR="/root/upshalter-reports"
LOG_FILE="/root/upshalter-logs/kurator-${DATE}.log"
mkdir -p "$REPORT_DIR" "/root/upshalter-logs"

REPORT_FILE="$REPORT_DIR/pentahelix-brief-${DATE}-${HOUR}.md"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "📋 Kurator Review v2 started — $TIMESTAMP"

# ── Config ─────────────────────────────────────────────────────────────────────
COGNITIVE_URL="http://host.docker.internal:8100"
HERMES_KEY="hermes-secret-change-me-in-production"
TELEGRAM_TOKEN="8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU"
TELEGRAM_CHAT="5807834405"

# ── Create Kurator Task via Cognitive Engine ─────────────────────────────────
log "🚀 Submitting Kurator task to Cognitive Engine..."

TASK_INPUT="Kamu adalah Kurator Pentahelix. Tugas hari ini:

1. Baca semua entries SKP yang dibuat Senator dalam 8 jam terakhir:
   - akademisi/temuan/*
   - bisnis/peluang/*
   - komunitas/isu/*
   - pemerintah/regulasi/*
   - media/narasi/*

2. Buat laporan konsolidasi dengan format BERIKUT (wajib diikuti):

# PENTAHELIX INTELLIGENCE BRIEF
Tanggal: $(date '+%A, %d %B %Y')

## RINGKASAN EKSEKUTIF
[Tulis 3 kalimat: apa yang paling penting terjadi hari ini dari 5 domain]

## TEMUAN PER DOMAIN
### Akademisi
[2-3 poin temuan penting]

### Bisnis
[2-3 poin temuan penting]

### Komunitas
[2-3 poin temuan penting]

### Pemerintah
[2-3 poin temuan penting]

### Media
[2-3 poin temuan penting]

## TEMA LINTAS DOMAIN
[2-3 tema yang muncul dari lebih dari 1 domain]

## IMPLIKASI UNTUK UPSHALTER
[1-2 poin yang relevan untuk strategi bisnis]

## ALERT
[Jika ada regulasi baru atau perubahan signifikan yang butuh perhatian segera, atau tulis 'Tidak ada alert khusus hari ini']

3. Simpan laporan ke SKP:
   Key: \"laporan/daily/$(date +%Y%m%d)\"
   Value: [seluruh laporan dalam markdown]

4. Simpan ke file: $REPORT_FILE

5. Berikan ringkasan maksimal 300 kata untuk Telegram.

Jawab dalam bahasa Indonesia yang profesional dan informatif."

TASK_RESPONSE=$(curl -s --max-time 10 \
    -X POST "${COGNITIVE_URL}/v1/portsocket" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${HERMES_KEY}" \
    -H "X-Agent-ID: kurator-pentahelix" \
    -d "{\"input\": $(echo "$TASK_INPUT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}" 2>&1)

TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('task_id',''))" 2>/dev/null)

if [ -z "$TASK_ID" ]; then
    log "❌ Failed to submit Kurator task — $TASK_RESPONSE"
    exit 1
fi

log "⏳ Kurator task $TASK_ID submitted, polling (max 15 min)..."

# Poll for result (max 15 min for report generation)
for i in $(seq 1 90); do
    sleep 10
    
    RESULT=$(curl -s --max-time 5 \
        "${COGNITIVE_URL}/v1/result/${TASK_ID}" \
        -H "X-API-Key: ${HERMES_KEY}" 2>&1)
    
    STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
    
    if [ "$STATUS" = "SUCCESS" ]; then
        log "✅ Kurator task completed successfully"
        
        # Extract report content
        REPORT_CONTENT=$(echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
r = d.get('result', {})
if isinstance(r, dict):
    results = r.get('results', [])
    if results:
        step = results[0]
        exec_data = step.get('execution', {})
        content = exec_data.get('content', '')
        print(content)
" 2>/dev/null)
        
        if [ -n "$REPORT_CONTENT" ]; then
            # Save to file
            echo "$REPORT_CONTENT" > "$REPORT_FILE"
            log "📄 Report saved to $REPORT_FILE"
            
            # Extract summary (first 300 words) for Telegram
            SUMMARY=$(echo "$REPORT_CONTENT" | python3 -c "
import sys
text = sys.stdin.read()
words = text.split()
summary = ' '.join(words[:300])
print(summary)
" 2>/dev/null)
            
            # Send to Telegram
            MSG="📊 *Pentahelix Intelligence Brief*

${SUMMARY}

📄 Full report: $REPORT_FILE
🕐 $(date '+%H:%M WIB')"

            curl -s --max-time 10 \
                -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
                -H "Content-Type: application/json" \
                -d "{\"chat_id\": \"${TELEGRAM_CHAT}\", \"text\": $(echo "$MSG" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'), \"parse_mode\": \"Markdown\"}" \
                > /dev/null 2>&1
            
            log "📨 Telegram notification sent"
        else
            log "⚠️ Report content is empty"
        fi
        
        log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log "✅ Kurator Review v2 complete"
        exit 0
        
    elif [ "$STATUS" = "FAILURE" ]; then
        log "❌ Kurator task failed — $RESULT"
        
        # Send failure notification
        curl -s --max-time 10 \
            -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\": \"${TELEGRAM_CHAT}\", \"text\": \"❌ *Kurator Review GAGAL*\n\n🕐 $(date '+%H:%M:%S')\n🔖 Task: $TASK_ID\n📄 Log: $LOG_FILE\", \"parse_mode\": \"Markdown\"}" \
            > /dev/null 2>&1
        exit 1
    fi
    
    if [ $((i % 6)) -eq 0 ]; then
        log "⏳ Still processing (${i}0s elapsed, status=$STATUS)"
    fi
done

log "⚠️ Kurator task timeout after 15 min"
exit 1
