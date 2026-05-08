#!/bin/bash
# Daily summary — dikirim ke Telegram setiap 07:00 WIB (00:00 UTC)

TANGGAL=$(date "+%A, %d %B %Y")
SERVICES_UP=$(systemctl list-units --type=service --state=active --no-pager --no-legend 2>/dev/null | grep -c "hermes-" || echo 0)
DOCKER_UP=$(docker ps --filter "status=running" | grep -E "(hermes|senator)" | wc -l)
SENATOR_BUSY=$(docker ps --filter "status=running" --format "{{.Names}}" | grep senator | wc -l)

# Hitung SKP entries hari ini
SKP_NEW=$(sqlite3 /root/.hermes/shared_knowledge_pool.db "SELECT COUNT(*) FROM memory_notes WHERE date(created_at) = date('now')" 2>/dev/null || echo "N/A")

SUMMARY="📊 DAILY SUMMARY — $TANGGAL

🏗️ INFRASTRUKTUR:
• Systemd services aktif: $SERVICES_UP/8
• Docker agents running: $DOCKER_UP
• Senator Pentahelix aktif: $SENATOR_BUSY/5

📚 KNOWLEDGE:
• Entry SKP baru hari ini: $SKP_NEW

🌐 DOMAIN:
• upshalter.com: $(curl -sI https://upshalter.com --max-time 5 2>/dev/null | head -1 | awk '{print $2}')
• workspace.upshalter.com: $(curl -sI https://workspace.upshalter.com --max-time 5 2>/dev/null | head -1 | awk '{print $2}')
• chat.upshalter.com: $(curl -sI https://chat.upshalter.com --max-time 5 2>/dev/null | head -1 | awk '{print $2}')

⏱️ Uptime VPS: $(uptime -p)
💾 Disk: $(df -h / | tail -1 | awk '{print $3"/"$2" ("$5")"}')
🧠 RAM: $(free -h | awk '/^Mem/{print $3"/"$2}')

Laporan otomatis FASE 4."

echo "$SUMMARY"

# Simpan ke log
# Kirim ke Telegram
/root/upshalter-scripts/telegram-alert.sh "$SUMMARY"

# Simpan ke log