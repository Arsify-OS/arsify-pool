# HERMES INFRASTRUCTURE RECOVERY GUIDE
## FASE 7: Backup & Recovery Documentation

### BACKUP LOCATION
- Local: `/var/backups/hermes/`
- Format: Timestamped directories (YYYYMMDD_HHMMSS)
- Retention: 7 days

### BACKUP CONTENTS
1. **hermes-config.tar.gz** - Config, auth, skills, channel data
2. **systemd-services.tar.gz** - All hermes-*.service files
3. **nginx-configs.tar.gz** - Nginx sites-available & sites-enabled
4. **ssl-certs.tar.gz** - Let's Encrypt certificates
5. **docker-metadata.tar.gz** - Container metadata & volume info
6. **hermes-workspace.tar.gz** - Workspace code (if exists)
7. **MANIFEST.txt** - Backup details & restore instructions

### RECOVERY PROCEDURES

#### 1. FULL RECOVERY (Fresh VPS)
```bash
# Extract latest backup
LATEST=$(ls -t /var/backups/hermes/ | head -1)
cd /var/backups/hermes/$LATEST

# Restore Hermes config
tar -xzf hermes-config.tar.gz -C /root/.hermes/

# Restore systemd services
tar -xzf systemd-services.tar.gz -C /etc/systemd/system/
systemctl daemon-reload

# Restore Nginx configs
tar -xzf nginx-configs.tar.gz -C /etc/nginx/
nginx -t && systemctl reload nginx

# Restore SSL certs (if exists)
[ -f ssl-certs.tar.gz ] && tar -xzf ssl-certs.tar.gz -C /

# Start services
systemctl start hermes-*
```

#### 2. PARTIAL RECOVERY (Single Component)
```bash
# Example: Restore only Nginx config
cd /var/backups/hermes/20260506_162848
tar -xzf nginx-configs.tar.gz -C /etc/nginx/
nginx -t && systemctl reload nginx
```

#### 3. CONFIG RECOVERY (Corrupted config.yaml)
```bash
# Restore from backup
cd /var/backups/hermes/20260506_162848
tar -xzf hermes-config.tar.gz -C /tmp/
cp /tmp/root/.hermes/config.yaml /root/.hermes/config.yaml
systemctl restart hermes-upshalternal
```

#### 4. DOCKER RECOVERY
```bash
# Check metadata for container info
cat /var/backups/hermes/20260506_162848/docker-metadata.tar.gz | tar -xzO docker/containers-metadata.txt

# Recreate containers from docker-compose if available
cd /root/hermes-workspace-personal
docker-compose up -d
```

### VERIFICATION CHECKLIST
After recovery, verify:
- [ ] `systemctl status hermes-*` - All services running
- [ ] `nginx -t` - Config valid
- [ ] `docker ps` - Containers running
- [ ] `curl -I https://hermes.upshalter.com` - Site accessible
- [ ] `curl -I https://api.upshalter.com` - API accessible
- [ ] Telegram bot responds (@upshalter_hermes_bot)

### AUTOMATED BACKUP
- **Service**: `hermes-backup.service`
- **Timer**: `hermes-backup.timer` (runs daily)
- **Enable**: `systemctl enable --now hermes-backup.timer`
- **Check**: `systemctl list-timers | grep hermes`

### MONITORING
- **Log**: `/var/backups/hermes/backup.log`
- **Check last backup**: `ls -lt /var/backups/hermes/ | head -5`
- **Backup size**: `du -sh /var/backups/hermes/`

### EMERGENCY CONTACTS
- Telegram: @upshalter_hermes_bot
- Status Page: http://status.upshalter.com (after SSL: https://status.upshalter.com)
