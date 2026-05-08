#!/bin/bash
# moe-router-start.sh — Start Arsify MoE Router
# Runs the FastAPI app that routes Senator/Kurator requests to appropriate models

set -e

MOE_DIR="/root/Arsify-OS/Arsify-core/moe"
PID_FILE="/tmp/moe-router.pid"
LOG_FILE="/var/log/moe-router.log"

echo "[$(date)] Starting Arsify MoE Router..."

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "MoE Router already running (PID: $OLD_PID)"
        exit 0
    else
        echo "Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

# Check Python dependencies
cd "$MOE_DIR"
for pkg in fastapi uvicorn httpx; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        echo "Installing $pkg..."
        pip3 install $pkg --quiet --break-system-packages 2>/dev/null || \
        pip3 install $pkg --quiet --user
    fi
done

# Start the server
echo "Starting MoE Router on port 8001..."
cd "$MOE_DIR"
nohup python3 -m uvicorn main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --workers 1 \
    > "$LOG_FILE" 2>&1 &
    
echo $! > "$PID_FILE"

sleep 2

# Verify it's running
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "✅ MoE Router started (PID: $(cat $PID_FILE))"
    echo "   Endpoint: http://localhost:8000/v1/chat/completions"
    echo "   Health: http://localhost:8000/health"
else
    echo "❌ Failed to start MoE Router. Check $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
