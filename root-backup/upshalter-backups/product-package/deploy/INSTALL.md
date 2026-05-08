# PENTAHELIX — Installation Guide v1.0

> **Target:** Fresh Ubuntu 22.04+ VPS with root access  
> **Time:** ~2-3 hours  
> **Tech:** Docker, Systemd, Nginx, SQLite, Python 3.11+

---

## Prerequisites

- Ubuntu 22.04+ VPS (min 2 CPU, 4GB RAM, 20GB storage)
- Root access
- Domain name pointed to VPS IP
- OpenRouter API key (get from https://openrouter.ai)
- Telegram Bot token (get from @BotFather)

---

## Step 1: System Setup

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y \
  docker.io docker-compose \
  nginx certbot python3-certbot-nginx \
  sqlite3 redis-server \
  python3 python3-pip python3-venv \
  git curl jq \
  nodejs npm

# Enable services
systemctl enable docker nginx redis-server cron
systemctl start docker nginx redis-server cron

# Verify
docker --version
nginx -v
sqlite3 --version
python3 --version
```

---

## Step 2: Directory Structure

```bash
mkdir -p /root/upshalter-scripts
mkdir -p /root/upshalter-logs
mkdir -p /root/upshalter-reports
mkdir -p /root/upshalter-config
mkdir -p /root/upshalter-backups
mkdir -p /data
mkdir -p /root/product-package
mkdir -p /var/www/data.upshalter.com
```

---

## Step 3: SKP Database Setup

```bash
# Create database
sqlite3 /data/arsify.db << 'EOF'
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    source_agent_name TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    key, value, source_agent_name,
    content='knowledge',
    content_rowid='id'
);

CREATE TRIGGER knowledge_ai AFTER INSERT ON knowledge BEGIN
    INSERT INTO knowledge_fts(rowid, key, value, source_agent_name)
    VALUES (new.id, new.key, new.value, new.source_agent_name);
END;

CREATE TRIGGER knowledge_ad AFTER DELETE ON knowledge BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, key, value, source_agent_name)
    VALUES ('delete', old.id, old.key, old.value, old.source_agent_name);
END;
EOF

chmod 666 /data/arsify.db
echo "SKP database created: $(sqlite3 /data/arsify.db 'SELECT COUNT(*) FROM knowledge;') entries"
```

---

## Step 4: Python Dependencies

```bash
pip3 install --break-system-packages \
  httpx httpcore \
  fpdf2 \
  requests
```

---

## Step 5: Configuration

```bash
# Create .env file
cat > /root/upshalter-scripts/.env << 'EOF'
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
OPENROUTER_MODEL=openrouter/owl-alpha
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE
SKP_DB_PATH=/data/arsify.db
REPORT_DIR=/root/upshalter-reports
LOG_DIR=/root/upshalter-logs
EOF

chmod 600 /root/upshalter-scripts/.env
echo "Edit /root/upshalter-scripts/.env with your actual keys!"
```

---

## Step 6: Deploy Scripts

Copy all scripts from `/root/product-package/scripts/` (or from existing installation):

**Required scripts:**
```
/root/upshalter-scripts/senator-cycle-v3.sh
/root/upshalter-scripts/kurator-v2.sh
/root/upshalter-scripts/kurator-v2.py
/root/upshalter-scripts/generate-intelligence-page.py
/root/upshalter-scripts/health-check.sh
/root/upshalter-scripts/telegram-alert.sh
/root/upshalter-scripts/deliver-intelligence.sh
/root/upshalter-scripts/backup-skp.sh
/root/upshalter-scripts/daily-summary.sh
```

```bash
# Make executable
chmod +x /root/upshalter-scripts/*.sh
```

---

## Step 7: SKP Adapter

```bash
mkdir -p /root/upshalter-scripts/python

cat > /root/upshalter/scripts/python/skp_adapter.py << 'EOF'
import sqlite3
import json
import os
from datetime import datetime, timezone

class SKP:
    def __init__(self, db_path="/data/arsify.db"):
        self.db_path = db_path
    
    def get_info(self):
        conn = sqlite3.connect(self.db_path)
        total = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        conn.close()
        return {
            "db_path": self.db_path,
            "table": "knowledge",
            "total_entries": total,
            "router_path": None
        }
    
    def write_senator(self, domain, content, agent_name):
        conn = sqlite3.connect(self.db_path)
        date_key = datetime.now().strftime("%Y%m%d-%H")
        key = f"senator-{domain}/temuan/{date_key}"
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO knowledge (key, value, source_agent_name, created_at) VALUES (?,?,?,?)",
            (key, content[:3000], agent_name, now)
        )
        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        conn.close()
        return key
EOF
```

---

## Step 8: Nginx Configuration

```bash
cat > /etc/nginx/sites-available/data.upshalter.com << 'EOF'
server {
    listen 80;
    server_name data.upshalter.com;

    root /var/www/data.upshalter.com;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

ln -sf /etc/nginx/sites-available/data.upshalter.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# SSL
certbot --nginx -d data.upshalter.com --non-interactive --agree-tos -m your@email.com
```

---

## Step 9: Deploy Senator Containers

```bash
mkdir -p /root/senator-pentahelix

# Copy docker-compose.yml from product-package
cp /root/product-package/deploy/senator-compose.yml /root/senator-pentahelix/docker-compose.yml

# Create .env for senator
cat > /root/senator-pentahelix/.env << 'EOF'
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
EOF

# Deploy
cd /root/senator-pentahelix
docker compose up -d

# Verify
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## Step 10: Setup Cron

```bash
crontab -l > /tmp/current_cron 2>/dev/null

cat >> /tmp/current_cron << 'EOF'
# Pentahelix Intelligence Platform
*/5 * * * * /root/upshalter-scripts/health-check.sh >> /root/upshalter-logs/cron.log 2>&1
*/30 * * * * /usr/bin/python3 /root/upshalter-scripts/generate-intelligence-page.py >> /root/upshalter-logs/generate-page.log 2>&1
0 */6 * * * SCRIPT_DIR=/root/upshalter-scripts bash /root/upshalter-scripts/senator-cycle-v3.sh >> /root/upshalter-logs/senator.log 2>&1
0 1,7,13,19 * * * SCRIPT_DIR=/root/upshalter-scripts bash /root/upshalter-scripts/kurator-v2.sh >> /root/upshalter-logs/kurator.log 2>&1
0 0 * * * /root/upshalter-scripts/daily-summary.sh >> /root/upshalter-logs/cron.log 2>&1
0 20 * * * /root/upshalter-scripts/backup-skp.sh >> /root/upshalter-logs/cron.log 2>&1
0 0 * * 0 find /root/upshalter-logs -name "*.log" -mtime +30 -delete
EOF

crontab /tmp/current_cron
rm /tmp/current_cron

echo "Cron jobs installed:"
crontab -l
```

---

## Step 11: Verify Installation

```bash
# 1. Check all services
systemctl is-active docker nginx redis-server cron

# 2. Check Docker containers
docker ps

# 3. Check Nginx
curl -s -o /dev/null -w "%{http_code}" http://localhost/

# 4. Check SKP
sqlite3 /data/arsify.db "SELECT COUNT(*) FROM knowledge;"

# 5. Check Python deps
python3 -c "import httpx, sqlite3; print('Dependencies OK')"

# 6. Test Telegram
bash /root/upshalter-scripts/telegram-alert.sh "Pentahelix installed successfully!"

# 7. Test manual run (wait ~2 min for senators)
bash /root/upshalter-scripts/senator-cycle-v3.sh
```

---

## Step 12: Post-Install

1. **Update .env** with real API keys
2. **Configure DNS** — point data.upshalter.com to VPS IP
3. **Setup SSL** — certbot should handle this
4. **Test end-to-end** — run senator cycle, check brief generation
5. **Monitor** — check Telegram for health alerts

---

## Next Steps

- Read `/root/product-package/docs/PRODUCT_SPEC.md` for product details
- Read `/root/product-product/docs/architecture/ARCHITECTURE.md` for system design
- Read `/root/product-package/docs/runbook/OPERATIONS.md` for daily operations
- Configure client subscriptions in `/root/upshalter-config/subscribers.json`

---

*Installation guide v1.0 — Last updated: 2026-05-08*
