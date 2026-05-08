# Hermes Cognitive Engine — Deployment Reference

## Architecture
- **FastAPI** (port 8100) — L1-L4 cognitive pipeline API
- **Celery** — async task workers (concurrency=4)
- **Redis** (host, port 6379) — broker + cache + rate limit + agent registry
- **SQLite** (`/data/arsify.db` → `/root/.hermes/shared_knowledge_pool.db`) — SKP knowledge store

## Key Files
```
/opt/hermes-cognitive/
├── Dockerfile
├── docker-compose.yml
├── .env
├── requirements.txt
└── src/
    ├── main.py              # FastAPI entry
    ├── celery_app.py        # Celery config
    ├── tasks.py             # Celery tasks
    ├── api/
    │   └── portsocket.py    # /v1/portsocket endpoint
    ├── core/
    │   ├── agent_registry.py
    │   ├── auth.py
    │   ├── knowledge_injector.py
    │   └── router.py
    ├── layers/
    │   ├── cognition.py     # L2
    │   ├── execution.py     # L3
    │   ├── perception.py    # L1
    │   └── reflection.py    # L4
    ├── models/
    │   └── openrouter_client.py
    └── observability/
        └── efeknomis.py
```

## SKP Database Schema
```sql
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    category TEXT DEFAULT 'general',
    tags TEXT DEFAULT '[]',
    source_agent_name TEXT DEFAULT 'system',
    priority INTEGER DEFAULT 5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## .env Key Variables
```bash
OPENROUTER_API_KEY=sk-or-v1-...          # Required but can be placeholder initially
HERMES_API_KEY=hermes-secret-change-me   # API auth key
SKP_DB_PATH=/data/arsify.db              # Symlink to /root/.hermes/shared_knowledge_pool.db
REDIS_URL=redis://host.docker.internal:6379/0  # Host Redis
ARSIFY_URL=http://localhost:8000         # Not yet active
```

## Docker Compose Pattern (Host Redis)
When Redis runs on the host (not in Docker), use this pattern:
- Add `extra_hosts: ["host.docker.internal:host-gateway"]` to each service
- Set `REDIS_URL=redis://host.docker.internal:6379/0`
- Remove the Redis service from docker-compose.yml
- Remove all `depends_on: redis` blocks
- Mount host volumes directly: `/root/.hermes:/data`

## Deploy Commands
```bash
cd /opt/hermes-cognitive
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=30
```

## Verification
```bash
# API health
curl http://localhost:8100/

# With auth
curl -H "Authorization: Bearer <HERMES_API_KEY>" http://localhost:8100/v1/portsocket

# Redis connectivity from container
docker exec hermes-api python3 -c "import redis; r=redis.Redis(host='host.docker.internal',port=6379); print(r.ping())"

# SKP DB access from container
docker exec hermes-api python3 -c "import sqlite3; conn=sqlite3.connect('/data/arsify.db'); print(conn.execute('SELECT COUNT(*) FROM knowledge').fetchone())"
```

## Known Issues (May 2026)
- OpenRouter API key exhausted (HTTP 402) — need top-up or switch to free model
- ARSIFY_URL not yet active (no Arsify OS endpoint)
- LLM-dependent features (cognition, reflection) will fail without valid OpenRouter key
- SKP knowledge table was created fresh — no historical data migrated yet
