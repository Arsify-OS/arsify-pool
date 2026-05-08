#!/bin/bash
# One-Click Upshalter Deployment Script
# Role: vpso-upshalter (VPSO Unit Upshalternal - TUI Mode)
# Usage: bash deploy-upshalter.sh [port] [install_dir]

set -e

PORT=${1:-9120}
INSTALL_DIR=${2:-/opt/hermes-upshalter}
SERVICE_NAME="hermes-upshalter"
USER="root"

echo "╔══════════════════════════════════════════════╗"
echo "║  Hermes Upshalter One-Click Deploy          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# 1. Create install directory
echo "📁 Creating install directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR/data"
cd "$INSTALL_DIR"

# 2. Create systemd service file
echo "📝 Creating systemd service: $SERVICE_NAME.service"
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=VPSO Unit Upshalternal - Upshalter (${PORT})
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${INSTALL_DIR}
Environment="HERMES_HOME=${INSTALL_DIR}/data"
ExecStart=/usr/local/bin/hermes dashboard --tui --host 0.0.0.0 --port ${PORT} --no-open --insecure
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 3. Reload systemd and enable service
echo "🔄 Reloading systemd and enabling service..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}

# 4. Start service
echo "🚀 Starting ${SERVICE_NAME} service..."
systemctl start ${SERVICE_NAME}

# 5. Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 3

# 6. Check status
echo "✅ Deployment complete! Service status:"
systemctl status ${SERVICE_NAME} --no-pager || true

echo ""
echo "📊 Quick Info:"
echo "  - Service: ${SERVICE_NAME}"
echo "  - Port: ${PORT}"
echo "  - Install Dir: ${INSTALL_DIR}"
echo "  - Data Dir: ${INSTALL_DIR}/data"
echo "  - TUI Access: hermes dashboard --host 0.0.0.0 --port ${PORT}"
echo ""
echo "🛠️ Management commands:"
echo "  - Status: systemctl status ${SERVICE_NAME}"
echo "  - Stop: systemctl stop ${SERVICE_NAME}"
echo "  - Start: systemctl start ${SERVICE_NAME}"
echo "  - Restart: systemctl restart ${SERVICE_NAME}"
echo "  - Logs: journalctl -u ${SERVICE_NAME} -f"
