# Hermes Gateway Conflict Resolution

## Problem: Multiple Gateway Instances Causing Telegram Polling Conflicts

**Symptoms:**
- Gateway logs show: `Conflict: terminated by other getUpdates request; make sure that only one bot instance is running`
- High restart counts in PM2 (e.g., restart #70, #269, #1155)
- Multiple Python processes running `hermes gateway` or `python -m hermes_cli.main gateway run`

**Root Cause:**
Multiple gateway instances polling the same Telegram bot token simultaneously. Common sources:
1. PM2-managed gateway processes
2. Standalone Python processes (via `hermes gateway run`)
3. Docker containerized gateways (e.g., Loyx container)
4. TUI gateway processes (`python -m tui_gateway.entry`)

## Resolution Steps

### 1. Identify All Running Instances
```bash
# Find all gateway processes
ps aux | grep -E "python.*gateway|hermes gateway" | grep -v grep

# Check PM2 processes
pm2 list

# Check Docker containers
docker ps --filter name=hermes
```

### 2. Stop Duplicate Instances

**Stop PM2 processes:**
```bash
pm2 stop hermes-gateway
pm2 stop hermes-dashboard
pm2 delete hermes-gateway
pm2 delete hermes-dashboard
```

**Kill standalone processes:**
```bash
# Kill by PID (from ps aux output)
kill -9 <PID>

# Or kill all gateway processes (careful!)
pkill -f "hermes gateway"
```

**Stop Docker gateway (if duplicate):**
```bash
docker exec <container_name> pkill -f "hermes gateway"
# Or restart container
docker restart <container_name>
```

### 3. Disable Telegram in Duplicate Gateways (Preferred for Multi-Gateway Setups)

If you need multiple gateways running (e.g., main + containerized Loyx), disable Telegram in all but one:

**Disable Telegram in Docker container:**
```bash
# Backup current config
docker exec <container_name> cat /opt/data/.env > /tmp/container_env_backup.txt

# Comment out Telegram token
docker exec <container_name> sed -i 's/^TELEGRAM_BOT_TOKEN=/#TELEGRAM_BOT_TOKEN=/' /opt/data/.env

# Restart container to apply
docker restart <container_name>

# Verify token is commented
docker exec <container_name> grep "^TELEGRAM_BOT_TOKEN" /opt/data/.env
# Should return nothing (exit code 1)
```

**Disable Telegram in native installation:**
```bash
# Edit ~/.hermes/.env and comment out TELEGRAM_BOT_TOKEN
sed -i 's/^TELEGRAM_BOT_TOKEN=/#TELEGRAM_BOT_TOKEN=/' ~/.hermes/.env

# Restart gateway
pkill -f "hermes gateway" && hermes gateway run --replace
```

### 4. Start Single Gateway Instance (If Running Only One)

**Option A: Background process (recommended for main gateway)**
```bash
# Use Hermes background process tracking
hermes gateway run --replace
```

**Option B: PM2 (if needed for auto-restart)**
```bash
pm2 start hermes-gateway --name hermes-gateway
pm2 save
```

### 5. Verify Resolution
```bash
# Should show only 1-2 gateway processes (main + optional container)
ps aux | grep -E "python.*gateway" | grep -v grep

# Check gateway health
curl -s http://localhost:8642/health
curl -s http://localhost:8643/health  # If running containerized gateway

# Monitor logs for conflicts (should be clean after 30-60 seconds)
docker logs -f <container_name> 2>&1 | grep -i conflict

# Wait for next Telegram notification cycle to confirm no conflicts
# Typical cron interval: 5 minutes
```

## Expected Final State

**Healthy multi-agent setup:**
- Main Gateway: localhost:8642 (native Hermes installation, handles Telegram)
- Loyx Container: localhost:8643 (Docker, Telegram disabled via commented TELEGRAM_BOT_TOKEN)
- No PM2 gateway processes (unless explicitly needed)
- No Telegram polling conflicts in logs
- Only 2 gateway processes total in `ps aux` output

**Single gateway setup:**
- One gateway process only
- Either native or containerized, not both
- Telegram enabled in the active gateway only

## Prevention

1. **Use `--replace` flag** when starting gateway to auto-kill existing instances
2. **Avoid mixing PM2 and native background processes** for the same service
3. **Use separate Telegram bot tokens** for each gateway instance if running multiple
4. **Check for existing processes** before starting new gateway: `ps aux | grep gateway`

## Related Issues

- PM2 restart loops often indicate underlying conflicts (fix root cause, don't just restart)
- Dashboard instability may be caused by gateway conflicts (shared resources)
- Memory usage drops after removing duplicate processes

## Session Reference
- Fixed 2026-05-04: Killed 3 duplicate gateway instances (PM2 #269, #1155 + standalone processes)
- Root cause: Both main gateway and Loyx container using same TELEGRAM_BOT_TOKEN
- Solution: Disabled Telegram in Loyx container by commenting out token in /opt/data/.env
- Result: Telegram conflict resolved, memory usage dropped from 28% to 27%, notifications working
- Verification: Waited 2+ minutes, no conflict logs, notification sent successfully at 05:53 UTC
