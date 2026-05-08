#!/bin/bash
# Cek SSL cert dan alert jika < 14 hari

DOMAINS=(
    upshalter.com api.upshalter.com arsify.upshalter.com
    workspace.upshalter.com hermes.upshalter.com chat.upshalter.com
    n8n.upshalter.com flowise.upshalter.com workstation.upshalter.com
    terminal.upshalter.com data.upshalter.com game.upshalter.com
    play.upshalter.com flowtask.upshalter.com
)

ALERTS=""
for domain in "${DOMAINS[@]}"; do
    EXPIRY=$(echo | openssl s_client -connect "$domain:443" -servername "$domain" 2>/dev/null \
             | openssl x509 -noout -enddate 2>/dev/null \
             | cut -d= -f2)
    if [ -n "$EXPIRY" ]; then
        DAYS=$(( ( $(date -d "$EXPIRY" +%s) - $(date +%s) ) / 86400 ))
        if [ "$DAYS" -lt 14 ]; then
            ALERTS="$ALERTS\n⚠️ $domain — $DAYS hari lagi (PERLU RENEWAL)"
        fi
    fi
done

if [ -n "$ALERTS" ]; then
    echo -e "ALERT SSL CERT AKAN EXPIRED:$ALERTS"
    # Kirim alert via hermes (jika ada CLI)
    # hermes -z "Kirim alert Telegram: $ALERTS"
fi
