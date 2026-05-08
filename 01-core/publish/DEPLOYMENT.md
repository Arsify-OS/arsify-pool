# Arsify Core — Deployment Guide

## Prerequisites

- Ubuntu 22.04+ (or any Linux with Python 3.10+)
- SQLite 3
- OpenRouter API key

## Quick Deploy

### 1. Clone and Setup

```bash
git clone https://github.com/Arsify-OS/arsify-core.git /opt/arsify-core
cd /opt/arsify-core
pip install httpx
```

### 2. Configure Environment

```bash
# Required
export OPENROUTER_API_KEY="INSERT_OPENROUTER_KEY_HERE-key-here"

# Optional (with defaults)
export OPENROUTER_MODEL="openai/gpt-4o-mini"
export SKP_DB_PATH="/data/arsify.db"
export SCRIPT_DIR="/opt/arsify-core"
```

For persistent config, add to `~/.bashrc` or create `/opt/arsify-core/.env`.

### 3. Initialize Database

The database and table will be created automatically on first run. To manually create:

```bash
sqlite3 /data/arsify.db << 'EOF'
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    tags TEXT DEFAULT '[]',
    priority INTEGER DEFAULT 5,
    source_agent_name TEXT DEFAULT 'system',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_knowledge_key ON knowledge(key);
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_created ON knowledge(created_at);
EOF
```

### 4. Test Run

```bash
# Test single domain (dry run)
python3 python/senator-execution.py --domain akademisi --dry-run

# Test single domain (live write)
python3 python/senator-execution.py --domain akademisi

# Test all domains
bash scripts/senator-cycle-v5.sh
```

### 5. Schedule with Cron

```bash
crontab -e
# Add:
0 */6 * * * SCRIPT_DIR=/opt/arsify-core OPENROUTER_API_KEY=sk-or-v1-... bash /opt/arsify-core/scripts/senator-cycle-v5.sh >> /var/log/arsify-senator.log 2>&1
```

### 6. Verify

```bash
# Check SKP entries
sqlite3 /data/arsify.db "SELECT COUNT(*) FROM knowledge;"
sqlite3 /data/arsify.db "SELECT key, substr(value,1,80) FROM knowledge ORDER BY id DESC LIMIT 10;"

# Check logs
tail -50 /var/log/arsify-senator.log
```

## Production Deployment (Arsify Workforce OS)

For the full Arsify Workforce OS deployment on `upshalter.com`:

### Systemd Service (Optional)

```ini
# /etc/systemd/system/arsify-senator.service
[Unit]
Description=Arsify Senator Cycle v5
After=network.target

[Service]
Type=oneshot
Environment=SCRIPT_DIR=/opt/arsify-core
Environment=OPENROUTER_API_KEY=sk-or-v1-...
Environment=OPENROUTER_MODEL=openai/gpt-4o-mini
ExecStart=/bin/bash /opt/arsify-core/scripts/senator-cycle-v5.sh
User=root
StandardOutput=append:/var/log/arsify-senator.log
StandardError=append:/var/log/arsify-senator-error.log

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/arsify-senator.timer
[Unit]
Description=Run Arsify Senator every 6 hours

[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl daemon-reload
systemctl enable --now arsify-senator.timer
systemctl list-timers | grep arsify
```

### Log Rotation

```
# /etc/logrotate.d/arsify
/var/log/arsify-*.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
}
```

### Monitoring

```bash
# Check if senator ran today
sqlite3 /data/arsify.db "SELECT COUNT(*) FROM knowledge WHERE date(created_at)=date('now');"

# Check last run from logs
grep "DONE" /var/log/arsify-senator.log | tail -5

# Check for errors
grep "✗\|ERROR\|failed" /var/log/arsify-senator.log | tail -10
```

## Cleanup

To clean accumulated junk entries:

```bash
# Preview
DRY_RUN=true python3 python/skp-cleaner.py

# Execute
python3 python/skp-cleaner.py
```

## Troubleshooting

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues.
