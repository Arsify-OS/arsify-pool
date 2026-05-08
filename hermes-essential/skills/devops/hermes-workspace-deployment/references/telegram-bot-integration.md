# Telegram Bot Integration for Hermes Agent

## Quick Setup

When integrating a Telegram bot with Hermes Agent for notifications and control:

### 1. Add Bot Token to Environment

```bash
# Add to ~/.hermes/.env
echo "TELEGRAM_BOT_TOKEN=<your-bot-token>" >> /root/.hermes/.env

# Enable reactions (optional)
hermes config set telegram.reactions true
```

### 2. Restart Gateway to Activate Bot

```bash
# If running via PM2
pm2 restart hermes-gateway

# If running in Docker
docker restart <container-name>

# Verify bot is active
curl -s "https://api.telegram.org/bot<TOKEN>/getMe" | python3 -m json.tool
```

### 3. Test Bot Connection

```bash
# Check bot info
curl -s "https://api.telegram.org/bot<TOKEN>/getMe"

# Get recent updates (to find your user ID)
curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates"
```

### 4. Configure User Allowlist (Optional)

```bash
# Allow specific users only
hermes config set telegram.allowed_users "123456789,987654321"

# Or allow all users (less secure)
echo "TELEGRAM_ALLOWED_USERS=" >> /root/.hermes/.env
```

## Bot Commands

Once bot is active, users can interact via Telegram:

- `/start` - Initialize bot and get welcome message
- `/status` - Check agent status
- `/help` - Show available commands
- Send any message - Agent will respond

## Automated Notifications

To send automated notifications from scripts or cron jobs:

```bash
# Via Telegram API directly
TOKEN="your-bot-token"
CHAT_ID="your-chat-id"
MESSAGE="GameDev agent completed task!"

curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d chat_id="${CHAT_ID}" \
  -d text="${MESSAGE}"
```

## Integration with Monitoring Scripts

Example cron job that sends Telegram notifications:

```bash
#!/bin/bash
# monitor_and_notify.sh

TELEGRAM_TOKEN="your-bot-token"
TELEGRAM_CHAT_ID="your-chat-id"

# Check for updates
if [ -f progress_log.md ]; then
    LATEST=$(tail -5 progress_log.md)
    
    # Send to Telegram
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
      -d chat_id="${TELEGRAM_CHAT_ID}" \
      -d text="📊 Progress Update:%0A%0A${LATEST}"
fi
```

## Troubleshooting

**Bot not responding:**
- Check gateway logs: `pm2 logs hermes-gateway`
- Verify token in .env: `grep TELEGRAM_BOT_TOKEN ~/.hermes/.env`
- Ensure gateway restarted after adding token

**"Unauthorized" errors:**
- Token is incorrect or revoked
- Regenerate token via @BotFather on Telegram

**Messages not reaching user:**
- User must start conversation with bot first (send /start)
- Check user ID is in allowlist if configured
- Verify CHAT_ID is correct (get from /getUpdates)

## Getting User Chat ID

To find your Telegram chat ID:

1. Send any message to your bot
2. Run: `curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates"`
3. Look for `"chat":{"id":123456789}` in response
4. Use that ID for automated notifications
