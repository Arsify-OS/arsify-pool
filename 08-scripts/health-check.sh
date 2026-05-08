#!/bin/bash
# Jalankan setiap 5 menit via cron
# Output ke /root/upshalter-logs/health-$(date +%Y%m%d).log

LOG="/root/upshalter-logs/health-$(date +%Y%m%d-%H%M).log"
TELEGRAM_ALERT=false

echo "=== HEALTH CHECK $(date) ===" > $LOG

# Check services
SERVICES=(
    "hermes-orchestrator:8000"
    "hermes-upshalternal:8645"
)

for svc in "${SERVICES[@]}"; do
    name="${svc%:*}"
    port="${svc#*:}"
    if curl -sf --max-time 3 "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $name ($port)" >> $LOG
    else
        echo "❌ $name ($port) — DOWN" >> $LOG
        TELEGRAM_ALERT=true
    fi
done

# Check Docker containers
echo "" >> $LOG
echo "--- Docker ---" >> $LOG
docker ps --format "{{.Names}}: {{.Status}}" | grep -E "(hermes|senator|kanban|workspace)" >> $LOG 2>&1 || echo "No matching containers" >> $LOG

# Check domain connectivity
echo "" >> $LOG
echo "--- Domains ---" >> $LOG
DOMAINS=(
    "upshalter.com"
    "workspace.upshalter.com"
    "hermes.upshalter.com"
    "chat.upshalter.com"
)

for domain in "${DOMAINS[@]}"; do
    status=$(curl -sI "https://$domain" --max-time 5 2>/dev/null | head -1 | awk '{print $2}')
    echo "$domain: HTTP ${status:-ERROR}" >> $LOG
done

# Alert jika ada yang down
if [ "$TELEGRAM_ALERT" = true ]; then
    ALERT_MSG="🚨 <b>HERMES ALERT</b> 🚨\nAda service yang DOWN.\nLog: $LOG\nWaktu: $(date '+%d %B %Y %H:%M:%S WIB')"
    /root/upshalter-scripts/telegram-alert.sh "$ALERT_MSG"
fi

echo "Health check selesai: $LOG"
