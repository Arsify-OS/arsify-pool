# PENTAHELIX — Operations Runbook v1.0

> **Versi:** 1.0  
> **Tanggal:** 2026-05-08  
> **Audience:** System Administrator / New Team Member

---

## QUICK REFERENCE

| Item | Value |
|------|-------|
| Dashboard | https://data.upshalter.com |
| SKP DB | `/data/arsify.db` |
| Reports | `/root/upshalter-reports/` |
| Logs | `/root/upshalter-logs/` |
| Scripts | `/root/upshalter-scripts/` |
| Config | `/root/upshalter-config/` |
| Telegram Bot | `@upshalter_bot` |
| Log file prefix | `senator-`, `kurator-`, `health-`, `delivery-` |

---

## 1. DAILY OPERATIONS

### 1.1 Check System Health

```bash
# Quick health overview
bash /root/upshalter-scripts/health-check.sh

# Check Docker containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check systemd services
systemctl list-units --type=service --state=active | grep hermes

# Check disk space
df -h / /data

# Check memory
free -h

# Check CPU load
uptime
```

**Expected output:** All services `active`, all Docker `Up`, disk <80%, load <2.0

### 1.2 Check Latest Reports

```bash
# List latest reports
ls -lt /root/upshalter-reports/*.md | head -5

# View latest kurator brief
cat /root/upshalter-reports/pentahelix-brief-$(date +%Y%m%d)*.md | head -50

# Check SKP entry count
sqlite3 /data/arsify.db "SELECT COUNT(*) FROM knowledge;"

# Check latest entries
sqlite3 /data/arsify.db "SELECT key, source_agent_name, created_at FROM knowledge ORDER BY created_at DESC LIMIT 5;"
```

### 1.3 Check Logs

```bash
# Today's senator log
tail -50 /root/upshalter-logs/senator-$(date +%Y%m%d).log

# Today's kurator log
tail -50 /root/upshalter-logs/kurator-$(date +%Y%m%d).log

# Health check log
tail -20 /root/upshalter-logs/health-$(date +%Y%m%d)*.log

# Search for errors
grep -i "error\|failed\|✗" /root/upshalter-logs/senator-$(date +%Y%m%d).log
grep -i "error\|failed\|✗" /root/upshalter-logs/kurator-$(date +%Y%m%d).log
```

---

## 2. TROUBLESHOOTING

### 2.1 Senator Cycle Failed

**Symptom:** No new entries in SKP after 6-hour cycle

**Diagnosis:**
```bash
# Check the log
tail -100 /root/upshalter-logs/senator-$(date +%Y%m%d).log | grep -i "error\|failed\|✗\|timeout"

# Check OpenRouter API
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $(grep OPENROUTER_API_KEY /root/upshalter-scripts/.env | cut -d= -f2)" | head -5

# Check if script is executable
ls -la /root/upshalter-scripts/senator-cycle-v3.sh

# Check cron is running
systemctl status cron
crontab -l | grep senator
```

**Common fixes:**
```bash
# Fix 1: OpenRouter API key expired → update in .env file
nano /root/upshalter-scripts/.env

# Fix 2: Permission issue
chmod +x /root/upshalter-scripts/*.sh

# Fix 3: Manual run
bash /root/upshalter-scripts/senator-cycle-v3.sh

# Fix 4: Check SQLite is writable
sqlite3 /data/arsify.db "INSERT INTO knowledge (key, value, source_agent_name) VALUES ('test/check', 'ok', 'manual'); DELETE FROM knowledge WHERE key='test/check';"
```

### 2.2 Kurator Failed

**Symptom:** No brief generated after senator cycle

**Diagnosis:**
```bash
# Check log
tail -50 /root/upshalter-logs/kurator-$(date +%Y%m%d).log

# Check if Python dependencies installed
python3 -c "import httpx, json, sqlite3; print('OK')"

# Check if SKP has recent senator entries
sqlite3 /data/arsify.db "SELECT COUNT(*) FROM knowledge WHERE created_at > datetime('now', '-12 hours') AND key LIKE 'senator-%';"
```

**Common fixes:**
```bash
# Fix 1: Missing httpx
pip3 install httpx httpcore --break-system-packages

# Fix 2: Run manually
bash /root/upshalter-scripts/kurator-v2.sh

# Fix 3: Run Python directly
python3 /root/upshalter-scripts/kurator-v2.py
```

### 2.3 Dashboard Not Updating

**Symptom:** data.upshalter.com shows stale data

**Diagnosis:**
```bash
# Check when data.json was last updated
ls -la /var/www/data.upshalter.com/data.json

# Check if generate script is running
ps aux | grep generate-intelligence

# Check cron
crontab -l | grep intelligence
```

**Common fixes:**
```bash
# Fix 1: Run manually
python3 /root/upshalter-scripts/generate-intelligence-page.py

# Fix 2: Check if output dir exists
ls -la /var/www/data.upshalter.com/

# Fix 3: Fix permissions
chown -R www-data:www-data /var/www/data.upshalter.com/
```

### 2.4 Docker Container Down

**Symptom:** `docker ps` shows container as `Exited`

**Diagnosis:**
```bash
# Check container logs
docker logs senator-komunitas --tail 50
docker logs hermes-api --tail 50

# Check restart policy
docker inspect senator-komunitas --format '{{.HostConfig.RestartPolicy}}'
```

**Common fixes:**
```bash
# Fix 1: Restart container
docker restart senator-komunitas

# Fix 2: Restart all senators
cd /root/senator-pentahelix && docker compose restart

# Fix 3: Full rebuild
cd /root/senator-pentahelix && docker compose down && docker compose up -d

# Fix 4: Check disk space (container may fail if disk full)
df -h
```

### 2.5 Nginx Issues

**Symptom:** Website not accessible

**Diagnosis:**
```bash
# Test config
nginx -t

# Check status
systemctl status nginx

# Check error log
tail -50 /var/log/nginx/error.log

# Check if ports are listening
ss -tlnp | grep -E '80|443'
```

**Common fixes:**
```bash
# Fix 1: Config error
nginx -t  # read the error, fix config, then:
systemctl reload nginx

# Fix 2: Service down
systemctl restart nginx

# Fix 3: Certbot renewal
certbot renew --dry-run
```

---

## 3. MAINTENANCE

### 3.1 SKP Database Maintenance

```bash
# Check database integrity
sqlite3 /data/arsify.db "PRAGMA integrity_check;"

# Check database size
ls -lh /data/arsify.db

# Optimize (VACUUM reclaims space)
sqlite3 /data/arsify.db "VACUUM;"

# Export backup
sqlite3 /data/arsify.db ".dump" > /root/upshalter-backups/skp-$(date +%Y%m%d).sql

# Full-text search check
sqlite3 /data/arsify.db "SELECT COUNT(*) FROM knowledge_fts;"
```

### 3.2 Log Rotation

Logs are auto-cleaned weekly (cron: delete >30 days). Manual cleanup:

```bash
# Check log sizes
du -sh /root/upshalter-logs/

# Manual cleanup (>7 days)
find /root/upshalter-logs -name "*.log" -mtime +7 -delete

# Manual cleanup (>30 days, same as cron)
find /root/upshalter-logs -name "*.log" -mtime +30 -delete
```

### 3.3 SSL Certificate Renewal

```bash
# Check cert expiry
certbot certificates

# Test renewal
certbot renew --dry-run

# Force renewal
certbot renew --force-renewal

# Check auto-renewal timer
systemctl status certbot.timer
```

### 3.4 System Updates

```bash
# Check for updates
apt-get update && apt-get list --upgradable

# Apply security updates only
apt-get upgrade -y

# Full dist-upgrade (careful — may break things)
apt-get dist-upgrade -y

# Docker image updates
docker pull nousresearch/hermes-agent:latest
cd /root/senator-pentahelix && docker compose up -d
```

---

## 4. DISASTER RECOVERY

### 4.1 SKP Database Corruption

```bash
# Step 1: Stop all writes
systemctl stop cron

# Step 2: Check corruption level
sqlite3 /data/arsify.db "PRAGMA integrity_check;"

# Step 3: If recoverable, dump and restore
sqlite3 /data/arsify.db ".dump" > /tmp/recovery.sql
mv /data/arsify.db /data/arsify.db.corrupt
sqlite3 /data/arsify.db < /tmp/recovery.sql

# Step 4: If not recoverable, restore from backup
ls -lt /root/upshalter-backups/
sqlite3 /data/arsify.db < /root/upshalter-backups/skp-YYYY-MM-DD.sql

# Step 5: Verify
sqlite3 /data/arsify.db "SELECT COUNT(*) FROM knowledge;"
systemctl start cron
```

### 4.2 Full VPS Rebuild

Lihat `/root/product-package/deploy/INSTALL.md` untuk panduan rebuild dari nol.

**Critical files to backup:**
```
/data/arsify.db                    ← SKP database (MOST IMPORTANT)
/root/upshalter-scripts/           ← All automation scripts
/root/upshalter-config/            ← Config files
/root/upshalter-reports/           ← Generated reports
/root/senator-pentahelix/          ← Senator Docker compose
/etc/nginx/sites-available/       ← Nginx configs
/etc/systemd/system/hermes-*.service  ← Service definitions
/root/.hermes/                     ← Shared agent data
```

**Backup command:**
```bash
tar czf /root/upshalter-backups/full-backup-$(date +%Y%m%d).tar.gz \
  /data/arsify.db \
  /root/upshalter-scripts/ \
  /root/upshalter-config/ \
  /root/senator-pentahelix/ \
  /etc/nginx/sites-available/ \
  /etc/systemd/system/hermes-*.service \
  /root/.hermes/
```

---

## 5. CONTACT & ESCALATION

| Issue Type | First Action | Escalate To |
|------------|--------------|-------------|
| Pipeline failure | Check logs, restart | Telegram group |
| API failure | Check OpenRouter status | OpenRouter support |
| VPS down | Check VPS provider console | VPS provider support |
| Security incident | Isolate, check logs | Security team |
| Client complaint | Check delivery logs | Product owner |

---

## 6. CHANGE LOG

| Date | Change | Author |
|------|--------|--------|
| 2026-05-08 | Initial runbook created | OWL |
