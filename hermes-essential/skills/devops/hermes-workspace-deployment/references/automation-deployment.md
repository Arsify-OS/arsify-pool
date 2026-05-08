# Full Automation Deployment for Multi-Agent Projects

## Overview

Pattern for deploying complete automation infrastructure around Hermes Workspace and multi-agent systems: real-time file watching, auto-deployment, scheduled monitoring, and notification delivery.

## Use Case

User wants autonomous development workflow where:
- Multiple AI agents collaborate (e.g., GameDev agent develops, Loyx orchestrates, Main Hermes coordinates)
- File changes trigger instant deployment to production
- Progress updates sent automatically via messaging platforms
- Zero manual intervention required

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Hermes Workspace (workstation.domain.com)                   │
│ - File editing, terminal, chat                              │
│ - Real-time collaboration                                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ File Watcher (systemd service)                              │
│ - inotify-tools monitoring project directory                │
│ - Detects .html/.js/.css changes instantly                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Auto-Deploy Pipeline                                         │
│ - Copies files to production directory                      │
│ - Sets permissions (www-data:www-data)                      │
│ - Logs deployment timestamp                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Production Website (app.domain.com)                         │
│ - Nginx serving static files or proxying app                │
│ - HTTPS via Certbot                                         │
└──────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Notification System (cron jobs)                             │
│ - Telegram bot: Every 5 minutes                             │
│ - Progress monitoring: Every 30 minutes                     │
│ - Build validation: Every 1 hour                            │
└──────────────────────────────────────────────────────────────┘
```

## Components

### 1. File Watcher (Real-time)

**Install inotify-tools:**
```bash
apt-get update && apt-get install -y inotify-tools
```

**Create watcher script** (`/path/to/project/file-watcher.sh`):
```bash
#!/bin/bash
# File watcher for auto-deployment

WATCH_DIR="/path/to/project"
LOG_FILE="$WATCH_DIR/watcher.log"

echo "[$(date)] File watcher started" | tee -a "$LOG_FILE"

inotifywait -m -r -e modify,create,move "$WATCH_DIR" \
  --exclude "(\.git|node_modules|\.log|config)" \
  --format "%w%f %e" | while read FILE EVENT
do
  echo "[$(date)] Change detected: $FILE ($EVENT)" | tee -a "$LOG_FILE"
  
  # Trigger deploy for relevant files
  if [[ "$FILE" =~ \.(html|js|css)$ ]]; then
    /path/to/project/deploy.sh >> "$LOG_FILE" 2>&1
  fi
done
```

**Create systemd service** (`/etc/systemd/system/project-watcher.service`):
```ini
[Unit]
Description=Project File Watcher
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/project
ExecStart=/path/to/project/file-watcher.sh
Restart=always
RestartSec=10
StandardOutput=append:/path/to/project/watcher.log
StandardError=append:/path/to/project/watcher.log

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
chmod +x /path/to/project/file-watcher.sh
systemctl daemon-reload
systemctl enable project-watcher
systemctl start project-watcher
systemctl status project-watcher
```

### 2. Auto-Deploy Script

**Create deploy script** (`/path/to/project/deploy.sh`):
```bash
#!/bin/bash
# Auto-deploy script

SOURCE="/path/to/project/app.html"
DEST="/var/www/production-site/index.html"
LOG_FILE="/path/to/project/deploy.log"

echo "[$(date)] Starting deployment..." | tee -a "$LOG_FILE"

# Copy files
cp "$SOURCE" "$DEST"

# Set permissions
chown www-data:www-data "$DEST"
chmod 644 "$DEST"

echo "[$(date)] Deployment complete" | tee -a "$LOG_FILE"

# Log to notifications
echo "[$(date)] 🚀 Deployed to production" >> /path/to/project/notifications.log
```

**Make executable:**
```bash
chmod +x /path/to/project/deploy.sh
```

### 3. Build Pipeline (Hourly Validation)

**Create build script** (`/path/to/project/build-pipeline.sh`):
```bash
#!/bin/bash
# Build pipeline for validation

PROJECT_DIR="/path/to/project"
LOG_FILE="$PROJECT_DIR/build.log"

echo "[$(date)] Build pipeline started" | tee -a "$LOG_FILE"

# Validate HTML
if command -v tidy &> /dev/null; then
  tidy -q -e "$PROJECT_DIR/app.html" 2>&1 | tee -a "$LOG_FILE"
fi

# Run tests (if applicable)
# npm test >> "$LOG_FILE" 2>&1

# Deploy if validation passed
if [ $? -eq 0 ]; then
  "$PROJECT_DIR/deploy.sh" >> "$LOG_FILE" 2>&1
  echo "[$(date)] ✅ Build passed, deployed" >> "$PROJECT_DIR/notifications.log"
else
  echo "[$(date)] ❌ Build failed" >> "$PROJECT_DIR/notifications.log"
fi
```

**Schedule with Hermes cron:**
```bash
hermes cron create \
  --name build-pipeline-hourly \
  --schedule "every 1h" \
  --prompt "Run /path/to/project/build-pipeline.sh to validate and build" \
  --toolsets terminal \
  --workdir /path/to/project
```

### 4. Telegram Notifications

**Create notifier script** (`/path/to/project/telegram-notifier.sh`):
```bash
#!/bin/bash
# Send notifications to Telegram

BOT_TOKEN="<your-bot-token>"
CHAT_ID=""  # Auto-detected from bot updates

send_telegram() {
    local message="$1"
    
    # Get chat_id from last update if not set
    if [ -z "$CHAT_ID" ]; then
        CHAT_ID=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates" | \
                  grep -o '"chat":{"id":[0-9]*' | head -1 | grep -o '[0-9]*')
    fi
    
    if [ -n "$CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
             -d chat_id="$CHAT_ID" \
             -d text="$message" \
             -d parse_mode="Markdown" > /dev/null
        echo "[$(date)] Telegram notification sent to $CHAT_ID"
    else
        echo "[$(date)] No chat_id found. User needs to /start the bot first."
    fi
}

# Read notifications log and send new entries
NOTIF_LOG="/path/to/project/notifications.log"
LAST_SENT="/path/to/project/.last_telegram_sent"

if [ -f "$NOTIF_LOG" ]; then
    if [ -f "$LAST_SENT" ]; then
        NEW_LINES=$(comm -13 <(sort "$LAST_SENT") <(sort "$NOTIF_LOG"))
    else
        NEW_LINES=$(tail -5 "$NOTIF_LOG")
    fi
    
    if [ -n "$NEW_LINES" ]; then
        MESSAGE="🤖 *Project Update*\n\n$NEW_LINES"
        send_telegram "$MESSAGE"
        cp "$NOTIF_LOG" "$LAST_SENT"
    fi
fi
```

**Schedule with Hermes cron:**
```bash
hermes cron create \
  --name telegram-notifications \
  --schedule "every 5m" \
  --prompt "Run /path/to/project/telegram-notifier.sh to send notifications" \
  --toolsets terminal \
  --workdir /path/to/project
```

### 5. Progress Monitoring

**Schedule with Hermes cron:**
```bash
hermes cron create \
  --name monitor-progress \
  --schedule "every 30m" \
  --prompt "Check /path/to/project/progress_log.md for updates and log to notifications.log" \
  --toolsets file,terminal \
  --workdir /path/to/project
```

## Multi-Agent Container Setup

When deploying specialized agent containers (e.g., GameDev agent for autonomous development):

**Create docker-compose.yml:**
```yaml
services:
  gamedev-agent:
    image: nousresearch/hermes-agent:latest
    command: ["hermes", "gateway", "run"]
    restart: unless-stopped
    ports:
      - "8644:8642"  # Unique port per agent
    env_file:
      - .env
    volumes:
      - ./gamedev-config:/opt/data
      - /path/to/project:/workspace  # Mount project directory
```

**Configure .env:**
```bash
OPENROUTER_API_KEY=sk-or-v1-...
# Use cost-effective model for autonomous agents
# Set via: docker exec <container> hermes config set model.default "openai/gpt-4o-mini"
```

**Start agent:**
```bash
docker compose up -d
docker logs <container-name> --tail 20
```

## Complete Workflow

1. **Developer or AI agent edits file** in Hermes Workspace
2. **File watcher detects change** (instant, via inotify)
3. **Auto-deploy script runs** (copies to production, sets permissions)
4. **Production site updated** (live within seconds)
5. **Notification logged** to notifications.log
6. **Telegram bot sends update** (within 5 minutes via cron)
7. **User receives notification** on phone

**Zero manual intervention required.**

## Verification Commands

```bash
# Check file watcher status
systemctl status project-watcher

# View real-time logs
tail -f /path/to/project/watcher.log
tail -f /path/to/project/deploy.log
tail -f /path/to/project/notifications.log

# List cron jobs
hermes cron list

# Check agent containers
docker ps | grep hermes

# Test Telegram bot
curl -s "https://api.telegram.org/bot<token>/getMe"
```

## Pitfalls

- **File watcher exits on error**: Use `Restart=always` in systemd service to auto-recover
- **inotify watch limit exceeded**: Increase with `echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p`
- **Telegram bot not receiving messages**: User must `/start` the bot first to establish chat_id
- **Deploy script fails silently**: Always redirect stderr to log: `deploy.sh >> log 2>&1`
- **Cron jobs not running**: Check `hermes cron list` for next_run_at timestamp, verify workdir exists
- **File watcher triggers on own log files**: Use `--exclude` pattern to ignore `.log` files
- **Multiple deploys for single edit**: Add debounce delay in watcher script (e.g., `sleep 2` before deploy)
- **Permissions denied on production directory**: Ensure deploy script runs as root or user with write access to `/var/www/`
- **Notifications sent multiple times**: Use `.last_telegram_sent` tracking file to avoid duplicates

## Integration with Hermes Workspace

When workspace is deployed via Docker Compose:

1. **Mount project directory** into workspace container:
   ```yaml
   volumes:
     - /path/to/project:/workspace/project
   ```

2. **Agent can edit files** via workspace UI or terminal

3. **File watcher on host** detects changes (inotify works across bind mounts)

4. **Auto-deploy runs on host** (has access to production directories)

5. **Notifications flow** through cron jobs to Telegram

This creates a seamless autonomous development loop where AI agents can develop, test, and deploy without human intervention.

## Example: Regrow Up World Setup

Real-world deployment from session:

- **Project**: /root/regrow-up-world-dev/
- **Workspace**: https://workstation.upshalter.com (Docker Compose)
- **Production**: https://regrow.upshalter.com (Nginx static site)
- **Agents**: GameDev (8644), Loyx (8643), Main Hermes (native)
- **Automation**: File watcher (systemd), 3 cron jobs (5m/30m/1h)
- **Notifications**: Telegram bot @upshalter_hermes_bot

Total setup time: ~60 minutes
Components deployed: 11 systems
Result: Fully autonomous 24/7 development workflow
