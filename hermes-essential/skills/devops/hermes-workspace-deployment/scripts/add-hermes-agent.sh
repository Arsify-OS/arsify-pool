#!/bin/bash
# add-hermes-agent.sh - Automated Hermes Agent Cloning Script
# Usage: ./add-hermes-agent.sh <agent-name> <port> "<description>"
# Example: ./add-hermes-agent.sh flowforce 9128 "Flowforce"

set -e

AGENT_NAME=$1
PORT=$2
DESCRIPTION=$3

if [ -z "$AGENT_NAME" ] || [ -z "$PORT" ] || [ -z "$DESCRIPTION" ]; then
    echo "Usage: $0 <agent-name> <port> \"<description>\""
    echo "Example: $0 flowforce 9128 \"Flowforce\""
    exit 1
fi

SERVICE_NAME="hermes-${AGENT_NAME}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=== Adding Hermes Agent: ${SERVICE_NAME} on port ${PORT} ==="

# Step 1: Create systemd service file
echo "1. Creating systemd service..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=VPSO Unit Upshalternal - ${DESCRIPTION} (${PORT})
After=network.target

[Service]
Environment="HERMES_ALLOWED_ORIGINS=*"
Type=simple
User=root
ExecStart=/usr/local/bin/hermes dashboard --host 0.0.0.0 --port ${PORT} --no-open --insecure
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Step 2: Reload and start service
echo "2. Enabling and starting service..."
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"
sleep 2

# Verify service
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Service ${SERVICE_NAME} is RUNNING"
else
    echo "❌ Service failed to start"
    exit 1
fi

# Step 3: Update Nginx config (use Python to avoid corruption)
echo "3. Updating Nginx config..."
python3 << PYEOF
from pathlib import Path

config_path = Path('/etc/nginx/sites-available/workstation-upshalter')
content = config_path.read_text()

# Find the closing } of SSL server block and insert before it
lines = content.split('\n')
ssl_end_idx = None
for i, line in enumerate(lines):
    if line.strip() == '}' and i > 0:
        # Check if this is the SSL server block closing
        # by looking backwards for "listen 443 ssl"
        for j in range(i, max(0, i-20), -1):
            if 'listen 443 ssl' in lines[j]:
                ssl_end_idx = i
                break
        if ssl_end_idx:
            break

if ssl_end_idx:
    new_location = f"""
    # {DESCRIPTION} Agent ({PORT})
    location /hermes/{AGENT_NAME} {{
        proxy_pass http://127.0.0.1:{PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
"""
    lines.insert(ssl_end_idx, new_location)
    new_content = '\n'.join(lines)
    config_path.write_text(new_content)
    print(f"✅ Added location /hermes/{AGENT_NAME} to Nginx config")
else:
    print("❌ Could not find SSL server block closing")
    exit(1)
PYEOF

# Test Nginx config
echo "4. Testing Nginx config..."
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx config syntax OK"
    systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "❌ Nginx config test failed"
    exit 1
fi

# Step 4: Update vpsoctl
echo "5. Updating vpsoctl..."
VPSOCTL="/usr/local/bin/vpsoctl"
if [ -f "$VPSOCTL" ]; then
    # Add to services array
    sed -i "s/services=(\"hermes-dashboard\" \\\"hermes-upshalternal\"/services=(\"hermes-dashboard\" \\\"hermes-upshalternal\" \\\"${SERVICE_NAME}\"/" "$VPSOCTL"
    echo "✅ vpsoctl updated"
else
    echo "⚠️ vpsoctl not found at $VPSOCTL"
fi

# Step 5: Update landing page (optional)
echo "6. Updating landing page..."
INDEX_HTML="/var/www/workstation/hermes/index.html"
if [ -f "$INDEX_HTML" ]; then
    # Add card before the closing </div> of the grid
    sed -i "/<\/a>.*<a href=\"\/hermes\/workstation\//i\            <a href=\"/hermes/${AGENT_NAME}/\" class=\"card\">\n                <div class=\"card-title\">🎯 ${DESCRIPTION}</div>\n                <div class=\"card-desc\">VPSO Unit ${DESCRIPTION} (${PORT})</div>\n            </a>" "$INDEX_HTML"
    echo "✅ Landing page updated"
else
    echo "⚠️ Landing page not found at $INDEX_HTML"
fi

# Final verification
echo ""
echo "=== VERIFICATION ==="
echo "Service status:"
systemctl status "$SERVICE_NAME" --no-pager | grep -E "Active:|Main PID:"
echo ""
echo "Nginx proxy test:"
curl -s -o /dev/null -w "%{http_code}" "https://workstation.upshalter.com/hermes/${AGENT_NAME}" --max-time 3
echo " :/hermes/${AGENT_NAME}"
echo ""
echo "✅ Hermes Agent ${SERVICE_NAME} successfully added!"
echo "   - Service: ${SERVICE_NAME}.service"
echo "   - Port: ${PORT}"
echo "   - Access: https://workstation.upshalter.com/hermes/${AGENT_NAME}/"
