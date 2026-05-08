# PENTAHELIX — Architecture Document v1.0

> **Versi:** 1.0  
> **Tanggal:** 2026-05-08  
> **Status:** Production (42% product-ready)

---

## 1. SYSTEM OVERVIEW

Pentahelix Intelligence Platform berjalan di **1 VPS** dengan arsitektur:

```
                    ┌─────────────────────────────────┐
                    │           NGINX :80/:443         │
                    │     (Reverse Proxy, 26 vhosts)  │
                    └───────────────┬─────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  data.upshalter │  │  API Endpoint   │  │  Other Services │
    │  .com (Dashboard)│  │  (Future)       │  │  (26 domains)   │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
              │
              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    APPLICATION LAYER                         │
    │                                                              │
    │  ┌──────────────────────────────────────────────────────┐   │
    │  │  CRON ORCHESTRATION                                   │   │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │   │
    │  │  │ Senator     │  │ Kurator     │  │ Intelligence │  │   │
    │  │  │ Cycle (6h)  │  │ (1h after)  │  │ Page (30min) │  │   │
    │  │  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  │   │
    │  └─────────┼───────────────┼────────────────┼──────────┘   │
    │            ▼               ▼                ▼               │
    │  ┌──────────────────────────────────────────────────────┐   │
    │  │  SKP KNOWLEDGE POOL                                   │   │
    │  │  /data/arsify.db (SQLite + FTS5)                     │   │
    │  │  Table: knowledge (key, value, source_agent_name,    │   │
    │  │         created_at)                                   │   │
    │  └──────────────────────────────────────────────────────┘   │
    │                                                              │
    │  ┌──────────────────────────────────────────────────────┐   │
    │  │  DELIVERY LAYER                                       │   │
    │  │  Telegram Bot → Email (stub) → Webhook (future)      │   │
    │  └──────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    INFRASTRUCTURE LAYER                      │
    │                                                              │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
    │  │ Docker       │  │ Systemd      │  │ Redis :6379      │  │
    │  │ Containers   │  │ Services     │  │ (Cache)          │  │
    │  │ (Senator +   │  │ (14 Hermes   │  │                  │  │
    │  │  Cognitive)  │  │  units)      │  │                  │  │
    │  └──────────────┘  └──────────────┘  └──────────────────┘  │
    │                                                              │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
    │  │ PM2          │  │ Fail2ban     │  │ UFW Firewall     │  │
    │  │ (9router)    │  │              │  │                  │  │
    │  └──────────────┘  └──────────────┘  └──────────────────┘  │
    └─────────────────────────────────────────────────────────────┘
```

---

## 2. DATA FLOW

### 2.1 Senator Cycle (setiap 6 jam)

```
Cron triggers senator-cycle-v3.sh
    │
    ├── For each of 5 senators:
    │   ├── Build system prompt (domain-specific)
    │   ├── Build user prompt (research question)
    │   ├── Call OpenRouter API (primary)
    │   │   └── On failure → Ollama fallback (30s timeout)
    │   ├── Parse JSON response
    │   └── Save to SKP via save_skp()
    │       └── INSERT INTO knowledge (key, value, source_agent_name)
    │
    └── Schedule kurator-v2.sh (5 minutes later, via background sleep)
```

### 2.2 Kurator Cycle (1 jam setelah senator)

```
Cron triggers kurator-v2.sh → kurator-v2.py
    │
    ├── Read last 12h senator entries from SKP
    ├── Deduplicate by key
    ├── Calculate confidence score (based on entry count)
    ├── Build consolidation prompt
    ├── Call OpenRouter API
    ├── Generate Markdown brief
    │   └── Save to /root/upshalter-reports/pentahelix-brief-YYYY-MM-DD-HH.md
    └── Update data.json for web dashboard
```

### 2.3 Intelligence Page Update (setiap 30 menit)

```
Cron triggers generate-intelligence-page.py
    │
    ├── Read latest SKP entries (last 10)
    ├── Read senator status (last update per domain)
    ├── Generate data.json
    └── Write to /var/www/data.upshalter.com/
```

### 2.4 Health Check (setiap 5 menit)

```
Cron triggers health-check.sh
    │
    ├── Check hermes-orchestrator:8000/health
    ├── Check hermes-upshalternal:8645/health
    ├── Check Docker containers (hermes|senator|kanban|workspace)
    ├── Log to /root/upshalter-logs/health-YYYY-MM-DD-HHMM.log
    └── On failure → send Telegram alert
```

---

## 3. COMPONENT DETAIL

### 3.1 Senator Cycle v3 (`/root/upshalter-scripts/senator-cycle-v3.sh`)

**Entry point:** Cron `0 */6 * * *`

**Key functions:**
- `call_llm(system, prompt, timeout)` — OpenRouter primary, Ollama fallback
- `save_skp(domain, content, agent)` — Write to SQLite via Python adapter
- `run_senator(name, domain, system_prompt, research_prompt)` — Full pipeline per senator

**Environment variables:**
```
OPENROUTER_API=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openrouter/owl-alpha
OLLAMA_API=http://localhost:11434
SKP_DB=/data/arsify.db
```

**Key format in SKP:**
- Raw: `senator-{domain}/temuan|peluang|isu|regulasi|narasi/YYYYMMDD-HH`
- Analysis: `senator-{domain}/analysis/{random_id}`
- Execution: `senator-{domain}/execution/{random_id}`
- Curated: `curated:senator-{domain}/...`

### 3.2 Kurator v2 (`/root/upshalter-scripts/kurator-v2.py`)

**Entry point:** Cron `0 1,7,13,19 * * *` (1h after senator at 0,6,12,18)

**Key steps:**
1. Read senator entries from SKP (last 12h, exclude kurator entries)
2. Deduplicate by key
3. Calculate confidence: `min(entry_count / 10, 1.0) * 0.9`
4. Build consolidation context (truncated to fit token limit)
5. Call OpenRouter with system prompt: "Kamu Kurator Pentahelix..."
6. Parse response → Markdown brief
7. Save to `/root/upshalter-reports/pentahelix-brief-{DATE}-{HOUR}.md`
8. Update `data.json` for web dashboard

**Confidence scoring:**
| Entry Count | Confidence |
|-------------|------------|
| 0 | 0.10 |
| 1-2 | 0.10-0.25 |
| 3-7 | 0.24-0.56 |
| 8+ | 0.72-0.90 |

### 3.3 SKP Database Schema

```sql
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

-- Triggers to keep FTS index in sync
CREATE TRIGGER knowledge_ai AFTER INSERT ON knowledge BEGIN
    INSERT INTO knowledge_fts(rowid, key, value, source_agent_name)
    VALUES (new.id, new.key, new.value, new.source_agent_name);
END;

CREATE TRIGGER knowledge_ad AFTER DELETE ON knowledge BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, key, value, source_agent_name)
    VALUES ('delete', old.id, old.key, old.value, old.source_agent_name);
END;
```

**Current stats (2026-05-08):**
- Total entries: 421
- Size: ~650 KB
- FTS indexed: 421 (100%)
- Categories: pemerintah(102), bisnis(74), komunitas(70), upshalter(67), curated(40), backend(37), akademisi(23), other(8)

### 3.4 Docker Containers

**Senator Pentahelix Stack** (`/root/senator-pentahelix/docker-compose.yml`):
```yaml
services:
  senator-{akademisi,bisnis,komunitas,pemerintah,media}:
    image: nousresearch/hermes-agent:latest
    volumes:
      - senator-data:/app/data
      - /root/.hermes:/opt/data:rw
    network_mode: host
    environment:
      - SECTOR={domain}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - MODEL=ollama/phi3:mini
    restart: unless-stopped
    user: root
```

**Hermes Cognitive Stack** (`/opt/hermes-cognitive/docker-compose.yml`):
```yaml
services:
  hermes-api:     # port 8100, cognitive engine API
  hermes-worker:  # background task processor
  hermes-beat:    # scheduler
```

### 3.5 Nginx Configuration

**26 active vhosts** in `/etc/nginx/sites-enabled/`:
- data.upshalter.com → dashboard (static)
- api.upshalter.com → API gateway
- arsify.upshalter.com → SKP/Arsify
- hermes.upshalter.com → Hermes frontend
- workspace.upshalter.com → workspace :3000
- + 21 other services

**SSL:** Certbot-managed, auto-renewal configured.

---

## 4. INFRASTRUCTURE

### 4.1 VPS Specs

| Resource | Value |
|----------|-------|
| CPU | 2 core |
| RAM | (check with `free -h`) |
| Storage | (check with `df -h`) |
| OS | Ubuntu 22.04+ |
| Network | 1 Gbps |

### 4.2 Port Map

| Port | Service | Type |
|------|---------|------|
| 80 | Nginx HTTP | Public |
| 443 | Nginx HTTPS | Public |
| 3000 | Hermes Workspace | Internal |
| 6379 | Redis | Internal |
| 8000 | Hermes Orchestrator | Internal |
| 8080 | Terminal | Internal |
| 8100 | Hermes Cognitive API | Public (Docker) |
| 8645 | Upshalternal (Main Manager) | Public |
| 9120-9137 | VPSO Units (Systemd) | Public |
| 9124 | Archivist | Public |
| 9125 | Frontend | Public |
| 9126 | Backend | Public |
| 9127 | Workstation | Public |
| 9128 | Flowforce | Public |
| 9135 | API | Public |
| 9136 | Loyx | Public |
| 9137 | Dev | Public |

### 4.3 Cron Schedule

| Schedule | Script | Purpose |
|----------|--------|---------|
| Every 5 min | health-check.sh | Service monitoring |
| Every 30 min | generate-intelligence-page.py | Dashboard update |
| Every 6 hours | senator-cycle-v3.sh | Senator analysis |
| 1h after senator | kurator-v2.sh | Brief consolidation |
| Daily 00:00 UTC | daily-summary.sh | Daily report |
| Daily 01:00 UTC | ssl-check.sh | SSL cert check |
| Daily 20:00 UTC | backup-skp.sh | SKP backup |
| Weekly Sunday | log cleanup | Delete logs >30 days |

---

## 5. DEPLOYMENT

### 5.1 Fresh Install

Lihat `/root/product-package/deploy/INSTALL.md` untuk panduan instalasi dari nol.

### 5.2 Backup & Recovery

Lihat `/root/product-package/docs/runbook/BACKUP_RECOVERY.md`.

### 5.3 Environment Variables

File: `/root/upshalter-scripts/.env` (create from `.env.example`)

```bash
OPENROUTER_API_KEY=sk-or-v1-...
TELEGRAM_BOT_TOKEN=8673939697:...
TELEGRAM_CHAT_ID=5807834405
SKP_DB_PATH=/data/arsify.db
REPORT_DIR=/root/upshalter-reports
LOG_DIR=/root/upshalter-logs
```

---

## 6. MONITORING & ALERTING

### 6.1 Health Check Endpoints

| Endpoint | Expected | Check |
|----------|----------|-------|
| http://localhost:8000/health | 200 OK | Orchestrator |
| http://localhost:8645/health | 200 OK | Upshalternal |
| `docker ps` | All Up | Containers |
| `systemctl is-active` | active | Services |

### 6.2 Log Locations

| Log | Path |
|-----|------|
| Senator cycle | `/root/upshalter-logs/senator-YYYY-MM-DD.log` |
| Kurator | `/root/upshalter-logs/kurator-YYYY-MM-DD.log` |
| Health check | `/root/upshalter-logs/health-YYYY-MM-DD-HHMM.log` |
| Delivery | `/root/upshalter-logs/delivery.log` |
| Nginx | `/var/log/nginx/` |
| System | `/var/log/syslog` |

### 6.3 Alert Rules

| Condition | Action |
|-----------|--------|
| Service down > 3 min | Telegram alert |
| Docker container exited | Telegram alert |
| SKP backup failed | Telegram alert |
| SSL cert < 7 days | Telegram alert |
| Disk usage > 85% | Telegram alert |

---

## 7. SCALING CONSIDERATIONS

### Current Limitations
- Single VPS (2 CPU) — Ollama CPU-only too slow for production
- SQLite — fine for <100K entries, then migrate to PostgreSQL
- Single Redis instance — no replication
- No load balancer

### Scaling Path
1. **Vertical:** Upgrade VPS to 4+ CPU, add RAM
2. **Horizontal:** Separate DB server, separate app server
3. **LLM:** Use dedicated GPU server for Ollama, or stay with OpenRouter
4. **Storage:** Migrate SQLite → PostgreSQL when >100K entries
5. **Queue:** Add Celery + Redis for async task processing

---

*Dokumen ini adalah living document. Update setiap ada perubahan arsitektur.*
