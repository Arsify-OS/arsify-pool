# Hermes Internet Research Agent — Daemon Pattern

## Architecture

Hermes Internet is a **systemd daemon** (not Docker) that runs 24/7, collecting knowledge from the internet and storing it in the Shared Knowledge Pool (SKP).

### Why systemd and not Docker?
- Lighter weight (no 8GB+ image needed)
- Direct filesystem access for cache
- Easier to access host services (Redis, SQLite)
- Simpler logging via journalctl

### Service File
`/etc/systemd/system/hermes-internet.service`

```ini
[Unit]
Description=Hermes Internet Research Agent — Knowledge Bridge
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/hermes-internet
ExecStart=/usr/bin/python3 /root/hermes-internet/daemon.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hermes-internet

[Install]
WantedBy=multi-user.target
```

### Daemon Loop Structure

```
Main Loop (sleep 300s between checks)
├── RSS Feed Monitor (every 30 min)
├── News Search (every 2 hours, Wikipedia + DDG)
├── Social Monitor (every 1 hour, Reddit)
├── Deep Crawl (every 6 hours, full article extraction)
└── Cache Cleanup (every 6 days)
```

### Data Flow (Push Model)
```
Internet Sources → Hermes Internet Daemon → SKP (knowledge table) → Senators
```

### Data Flow (Pull Model)
```
Senator → API call → Hermes Internet → Deep crawl → SKP + response
```

### SKP Schema Extensions

```sql
-- Added to knowledge table
ALTER TABLE knowledge ADD COLUMN feedback TEXT DEFAULT '';
ALTER TABLE knowledge ADD COLUMN rating INTEGER DEFAULT 0;
ALTER TABLE knowledge ADD COLUMN source_quality TEXT DEFAULT 'unknown';
ALTER TABLE knowledge ADD COLUMN verified INTEGER DEFAULT 0;
ALTER TABLE knowledge ADD COLUMN verified_by TEXT DEFAULT '';
ALTER TABLE knowledge ADD COLUMN verified_at REAL DEFAULT 0;

-- New tables
CREATE TABLE fact_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_id INTEGER NOT NULL,
    claim TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK(verdict IN ('true','false','unverifiable','needs_review')),
    evidence_url TEXT,
    confidence REAL DEFAULT 0.0,
    checked_by TEXT DEFAULT 'hermes-internet',
    created_at REAL NOT NULL,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
);

CREATE TABLE feedback_loop (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_id INTEGER NOT NULL,
    agent_id TEXT NOT NULL,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at REAL NOT NULL,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
);

CREATE TABLE crawl_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    raw_content TEXT,
    extracted_content TEXT,
    source TEXT,
    crawled_at REAL NOT NULL,
    expires_at REAL NOT NULL
);
```

### Key Implementation Details

1. **Graceful shutdown**: SIGTERM/SIGINT handler sets `_shutdown = True`, loop exits cleanly
2. **Deduplication**: URL hash check before saving to SKP
3. **Categorization**: Keyword-based scoring per sector (akademisi, bisnis, komunitas, pemerintah, media)
4. **Priority**: 1-10 scale based on keyword matches and alert keywords
5. **Fact-checking**: Tier 1 (auto cross-reference), Tier 2 (source verification), Tier 3 (human-in-the-loop)
6. **Telegram alerts**: HIGH priority only (breaking news, critical keywords)
7. **Error handling**: Per-sector try/except, continues to next sector on failure

### Verification

```bash
# Check service status
systemctl status hermes-internet

# View logs
journalctl -u hermes-internet -f

# Check SKP entries
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
  "SELECT id, title, category, priority FROM knowledge WHERE source_agent_id='hermes-internet' ORDER BY id DESC LIMIT 10;"
```
