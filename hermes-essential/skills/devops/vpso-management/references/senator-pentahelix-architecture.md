# Senator Pentahelix — Architecture & Operations

## Overview
Senator Pentahelix is a 5-agent research system that autonomously gathers intelligence from the web, stores findings in the VPSO Shared Knowledge Pool (SKP), and reports via Telegram.

## Agent Hierarchy (PIC Structure) — Updated 6 Mei 2026

```
👑 Upshalternal AI CEO (upshalternal, port 8645)
   └──▶ 🔍 Kurator Pentahelix (kurator-pentahelix)
            ├──▶ 🌐 Hermes Internet Research (hermes-internet)
            │      role: web_search, crawl, fact-check
            │      tools: web_search, browser, curl
            │
            ├──▶ 🏛️ Senator Akademisi  (port 9200)
            ├──▶ 💼 Senator Bisnis     (port 9201)
            ├──▶ 👥 Senator Komunitas  (port 9202)
            ├──▶ 🏛️ Senator Pemerintah (port 9203)
            └──▶ 📰 Senator Media      (port 9204)
```

### Registering Internet Research Agent
```python
o.register_agent(
    agent_id='hermes-internet',
    agent_name='Hermes Internet Research',
    capabilities=['web_search', 'web_crawl', 'internet_research', 'data_extraction', 'fact_checking'],
    metadata={'role': 'internet_research', 'type': 'hermes-agent', 'pic': 'kurator-pentahelix',
              'tools': ['web_search', 'browser', 'curl']}
)
```

### Updating Metadata (Post-Registration)
```python
import sqlite3, json
db = sqlite3.connect('/usr/local/lib/hermes-orchestrator/db/orchestrator.db')
cur = db.cursor()
meta = {'pic': 'kurator-pentahelix', 'kurator': 'Kurator Pentahelix', 'type': 'senator-pentahelix'}
cur.execute('UPDATE agents SET metadata = ? WHERE agent_id = ?', (json.dumps(meta), 'senator-akademisi'))
# Repeat for each senator
kurator_meta = {'role': 'kurator', 'manages': 'senator-pentahelix,hermes-internet', 'pic': 'upshalternal'}
cur.execute('UPDATE agents SET metadata = ? WHERE agent_id = ?', (json.dumps(kurator_meta), 'kurator-pentahelix'))
db.commit()
db.close()
```

## Registering Agents to VPSO

```python
from orchestrator import Orchestrator, AgentStatus
o = Orchestrator()

# Register kurator
o.register_agent(
    agent_id='kurator-pentahelix',
    agent_name='Kurator Pentahelix',
    capabilities=['curation', 'oversight', 'quality_control', 'reporting'],
    metadata={'role': 'kurator', 'manages': 'senator-pentahelix', 'pic': 'upshalternal'}
)

# Register senators
for sector in ['akademisi', 'bisnis', 'komunitas', 'pemerintah', 'media']:
    o.register_agent(
        agent_id=f'senator-{sector}',
        agent_name=f'Senator {sector.capitalize()}',
        capabilities=['research', sector, 'analysis'],
        metadata={'sector': sector, 'pic': 'kurator-pentahelix', 'type': 'senator-pentahelix'}
    )
```

## Generating API Keys

Hardcoded keys don't work. Must generate via AuthManager:

```python
from orchestrator.auth import AuthManager
am = AuthManager()
key = am.generate_key('senator-pentahelix')  # Returns hma_* format
# Store this — it's the only time it's visible
```

## Docker Deployment

### Key Configuration
```yaml
network_mode: host  # Reliable host access, no DNS/firewall issues
environment:
  - ORCHESTRATOR_URL=http://127.0.0.1:8000  # localhost from host
  - API_KEY=hma_<generated_key>
```

### Base Image Quirks
- `nousresearch/hermes-agent:latest` — Python 3.13.5 venv at `/opt/hermes/.venv`
- **No pip/ensurepip** — cannot install Python packages
- **requests pre-installed** (v2.33.1) — use stdlib + requests only
- **Entrypoint intercepts all commands** — override with `ENTRYPOINT ["/usr/bin/tini", "--"]`
- **Skill sync on every run** — ~10s startup overhead (normal)

### Web Search from Containers (Updated 6 Mei 2026)
- **Wikipedia**: Needs `User-Agent` header (403 without). PRIMARY source — most reliable.
  ```python
  headers = {"User-Agent": "SenatorPentahelix/3.0 (https://upshalter.com; research-bot)"}
  resp = requests.get("https://en.wikipedia.org/w/api.php",
      params={"action":"query","list":"search","srsearch":query,"srlimit":3,"format":"json"},
      headers=headers, timeout=10)
  ```
- **DuckDuckGo**: Slow from containers. Use 5s timeout. SECONDARY/fallback source.
  ```python
  resp = requests.get("https://api.duckduckgo.com/",
      params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
      timeout=5)
  ```
- **Pattern**: Try Wikipedia first → fallback to DDG → placeholder if both empty
- **Result**: Wikipedia returns ~12 results per sector query reliably

### POST /api/knowledge Endpoint (Added 6 Mei 2026)
```bash
curl -s -X POST http://localhost:8000/api/knowledge \
  -H "Content-Type: application/json" \
  -H "X-API-Key: hma_<key>" \
  -d '{
    "title": "[SECTOR] Topic",
    "content": "JSON content",
    "category": "research",
    "source_agent_id": "senator-akademisi",
    "source_agent_name": "Senator Akademisi",
    "tags": ["research", "academia"],
    "priority": 7
  }'
```
Returns: `{"knowledge_id": 19, "status": "created", "message": "..."}`

Required changes to make this work:
1. Add `create_knowledge()` method to `knowledge_sync.py`
2. Add `KnowledgeEntryRequest` and `KnowledgeEntryResponse` Pydantic models to `api.py`
3. Add POST `/knowledge` and POST `/api/knowledge` routes
4. Add `import json` to `knowledge_sync.py`

### Poll-Loop Pattern (NanoClaw-inspired)
```python
import signal, time

_shutdown_requested = False
def _handle_signal(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)

while not _shutdown_requested:
    research_cycle()
    remaining = CYCLE_INTERVAL_SECONDS
    while remaining > 0 and not _shutdown_requested:
        time.sleep(min(30, remaining))
        remaining -= 30
        touch_heartbeat()
```

## SKP Knowledge Storage

### POST /api/knowledge Endpoint
```bash
curl -s -X POST http://localhost:8000/api/knowledge \
  -H "Content-Type: application/json" \
  -H "X-API-Key: hma_<key>" \
  -d '{
    "title": "[SECTOR] Topic",
    "content": "JSON content",
    "category": "research",
    "source_agent_id": "senator-akademisi",
    "source_agent_name": "Senator Akademisi",
    "tags": ["research", "academia"],
    "priority": 7
  }'
```

### KnowledgeSync.create_knowledge() Method
Added to `/usr/local/lib/hermes-orchestrator/orchestrator/knowledge_sync.py`:
- Creates DB and table if not exists
- Stores: title, content, category, source_agent_id, source_agent_name, tags, priority, created_at, updated_at, metadata
- Returns knowledge_id or None on error

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 405 on POST /api/knowledge | No POST route exists | Add POST endpoint to api.py + KnowledgeSync.create_knowledge() |
| 401 on API calls | Invalid/missing API key | Generate key via AuthManager |
| Web search empty | DDG rate limit / Wikipedia 403 | Use Wikipedia with User-Agent header first, DDG 5s timeout fallback |
| 405 on POST /api/knowledge | No POST route exists | Add POST endpoint to api.py + KnowledgeSync.create_knowledge() |
| include_router not working | Inside if __name__ block | Move `app.include_router(api_router)` to module level |
| Systemd service fails | Wrong python path | Use venv python: `/usr/local/lib/hermes-orchestrator/venv/bin/python3` |
| pip not found in container | Base image has no pip | Use stdlib + pre-installed requests only; no pip install possible |
| Connection timeout host→container | UFW blocking Docker | `ufw allow from 172.17.0.0/16 to any port 8000` OR use `network_mode: host` |
| Container restart loop | Script exits normally | Use poll-loop pattern with signal handling |
| 401 on API calls | Invalid/missing API key | Generate key via AuthManager — hardcoded strings won't work |

## File Locations

| File | Path |
|------|------|
| Senator scripts | `/root/senator-pentahelix/scripts/` |
| Senator compose | `/root/senator-pentahelix/docker-compose.yml` |
| Senator data | Docker volume `senator-data` |
| Orchestrator API | `/usr/local/lib/hermes-orchestrator/api.py` |
| KnowledgeSync | `/usr/local/lib/hermes-orchestrator/orchestrator/knowledge_sync.py` |
| Middleware | `/usr/local/lib/hermes-orchestrator/orchestrator/middleware.py` |
| Auth DB | `/usr/local/lib/hermes-orchestrator/data/auth.db` |
| Orchestrator DB | `/usr/local/lib/hermes-orchestrator/db/orchestrator.db` |
| Shared Memory DB | `/usr/local/lib/hermes-shared-memory/db/memory.db` |
