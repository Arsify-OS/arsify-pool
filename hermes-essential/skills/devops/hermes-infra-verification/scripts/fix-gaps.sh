#!/bin/bash
# ═════════════════════════════════════════════════════════════
#  fix-gaps.sh — Menutup 3 gap yang ditemukan Hermes verifikasi
#  Jalankan: bash fix-gaps.sh
#  Requires: root access, nginx running
# ═════════════════════════════════════════════════════════════

set -e
RED='\033[0;31m';GREEN='\033[0;32m';YELLOW='\033[1;33m';NC='\033[0m'
ok()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn(){ echo -e "${YELLOW}[!]${NC} $1"; }

echo "=== Fix 3 Gap dari Verifikasi Hermes ==="
echo ""

# ── GAP 1: status.upshalter.com → real-time ──────────────────
echo "--- Gap 1: status.upshalter.com real-time ---"

# Deploy HTML dengan JavaScript polling
cp /root/app.upshalter.com/status-realtime.html /var/www/status/index.html
ok "Status page real-time deployed"

# Pastikan nginx serve dengan no-cache agar selalu fresh
grep -q "Cache-Control" /etc/nginx/sites-available/status.upshalter.com 2>/dev/null || {
  warn "Tambahkan Cache-Control ke nginx config status.upshalter.com"
  cat >> /etc/nginx/sites-available/status.upshalter.com << 'NGINX'
# Tambahkan di dalam server block, location /:
# add_header Cache-Control "no-cache, no-store, must-revalidate";
NGINX
}
ok "status.upshalter.com: sekarang auto-check setiap 30 detik via JavaScript"
echo ""

# ── GAP 2: chat.upshalter.com → UI chat ──────────────────────
echo "--- Gap 2: chat.upshalter.com UI chat ---"

# Buat web root untuk chat
mkdir -p /var/www/chat.upshalter.com
cp /root/app.upshalter.com/chat-ui.html /var/www/chat.upshalter.com/index.html
ok "Chat UI deployed ke /var/www/chat.upshalter.com/"

# Update nginx untuk serve UI di root dan proxy /chat ke port 8000
cat > /etc/nginx/sites-available/chat.upshalter.com << 'NGINX'
server {
    listen 443 ssl;
    server_name chat.upshalter.com;

    ssl_certificate     /etc/letsencrypt/live/chat.upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chat.upshalter.com/privkey.pem;

    # Rate limiting untuk public access
    limit_req_zone $binary_remote_addr zone=chat_limit:10m rate=20r/m;

    # Root → serve chat UI (HTML)
    root /var/www/chat.upshalter.com;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }

    # /chat → proxy ke Arsify OS API (same-origin untuk JavaScript)
    location /chat {
        limit_req zone=chat_limit burst=10 nodelay;
        proxy_pass http://localhost:8000/chat;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    # /v1/ → OpenAI-compatible endpoint
    location /v1/ {
        proxy_pass http://localhost:8000/v1/;
        proxy_set_header Host $host;
        proxy_read_timeout 120s;
    }

    # /stats → untuk info bar di chat UI
    location /stats {
        proxy_pass http://localhost:8000/stats;
        proxy_set_header Host $host;
    }

    # /health, /models → status info
    location ~ ^/(health|models|ready)$ {
        proxy_pass http://localhost:8000/$1;
        proxy_set_header Host $host;
    }
}
server {
    listen 80;
    server_name chat.upshalter.com;
    return 301 https://$host$request_uri;
}
NGINX

ok "nginx config chat.upshalter.com: UI di root, API di /chat dan /v1/"
echo ""

# ── GAP 3: workspace.upshalter.com → fix missing features ────
echo "--- Gap 3: workspace.upshalter.com features ---"

warn "missing=[enhancedChat, mcp, mcpFallback] di Hermes Workspace"
warn "Ini adalah konfigurasi environment variable di Docker container"
echo ""

# Cek docker container
CONTAINER=$(docker ps --format "{{.Names}}" | grep workspace || echo "")
if [ -z "$CONTAINER" ]; then
  warn "Container hermes-workspace tidak ditemukan. Cek: docker ps | grep workspace"
else
  ok "Container ditemukan: $CONTAINER"

  # Cek env vars yang dibutuhkan
  echo "Checking required env vars..."
  docker exec $CONTAINER env | grep -E "(HERMES|ENHANCED|MCP)" 2>/dev/null || warn "Env vars MCP belum di-set"

  # Tambahkan env vars yang diperlukan
  cat >> /opt/hermes-workspace/.env 2>/dev/null << 'ENV' || warn ".env tidak ditemukan, buat manual"
# Enable enhanced chat dan MCP features
ENHANCED_CHAT_ENABLED=true
MCP_ENABLED=true
MCP_FALLBACK_ENABLED=true
HERMES_GATEWAY_URL=http://localhost:8642
HERMES_API_URL=http://localhost:8000
ENV

  warn "Setelah edit .env, jalankan: docker restart $CONTAINER"
  warn "Tunggu 30 detik, lalu cek: https://workspace.upshalter.com"
fi
echo ""

# ── Reload nginx ──────────────────────────────────────────────
echo "--- Reload Nginx ---"
nginx -t && systemctl reload nginx && ok "Nginx reloaded"
echo ""

# ── Verifikasi ────────────────────────────────────────────────
echo "--- Verifikasi ---"
sleep 2

check_url() {
  local name=$1 url=$2
  local code=$(curl -so /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
  if [ "$code" = "200" ] || [ "$code" = "301" ] || [ "$code" = "302" ]; then
    ok "$name → HTTP $code"
  else
    warn "$name → HTTP $code (perlu dicek)"
  fi
}

check_url "status.upshalter.com" "https://status.upshalter.com"
check_url "chat.upshalter.com" "https://chat.upshalter.com"
check_url "workspace.upshalter.com" "https://workspace.upshalter.com"
echo ""

echo "=== Fix Selesai ==="
echo ""
echo "Langkah manual yang masih perlu dikerjakan:"
echo "1. Buka https://status.upshalter.com — pastikan status dot berwarna hijau (bukan statis)"
echo "2. Buka https://chat.upshalter.com — ketik pesan, pastikan AI menjawab"
echo "3. Buka https://workspace.upshalter.com — pastikan chat aktif"
echo "4. Restart workspace container jika Gap 3 masih belum resolved"
echo ""
echo "Laporan ke Telegram setelah selesai:"
cat << 'MSG'
[GAP FIX COMPLETE]
✅ status.upshalter.com → real-time (JS polling 30s)
✅ chat.upshalter.com → UI chat deployed
⚠️  workspace.upshalter.com → perlu restart container setelah .env update
MSG