# Hermes Cognitive Engine — Deployment Reference

## Overview
FastAPI + Celery + Redis cognitive pipeline (L1-L4) deployed as Docker container on Upshalter VPS.

## Architecture
```
Client → POST /v1/portsocket → FastAPI (:8100) → Celery → Redis (:6379)
                                    ↓
                              SKP SQLite (:/data/shared_knowledge_pool.db)
```

## Deployment Steps

### 1. Deploy to /opt/hermes-cognitive
```bash
mkdir -p /opt/hermes-cognitive
cp -r "/root/Upshalter Gateway MoE/Final Material/hermes-cognitive/"* /opt/hermes-cognitive/
```

### 2. Create .env
Key variables:
- `OPENROUTER_API_KEY` — from env var or hermes history
- `HERMES_API_KEY` — random secret for client auth
- `SKP_DB_PATH=/data/shared_knowledge_pool.db` — mount /root/.hermes as /data
- `REDIS_URL=redis://:<password>@host.docker.internal:6379/0`
- `PYTHONPATH=/app/src`

### 3. Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app/src
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY .env .
EXPOSE 8100
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8100"]
```

### 4. docker-compose.yml Key Settings
- No Redis container — use host Redis via `host.docker.internal`
- `extra_hosts: host.docker.internal:host-gateway` on api and worker
- `volumes: /root/.hermes:/data` for SKP DB access
- `PYTHONPATH: /app/src` for correct imports

### 5. Host Prerequisites
```bash
# Redis: bind to all interfaces
redis-cli CONFIG SET bind "0.0.0.0 -::"
redis-cli CONFIG SET protected-mode no
redis-cli CONFIG SET requirepass "<password>"

# iptables: allow container→host traffic
iptables -I INPUT -i docker0 -p tcp --dport 6379 -j ACCEPT

# Persist Redis config
echo "requirepass <password>" >> /etc/redis/redis.conf
sed -i 's/^bind 127.0.0.1 -::1/bind 0.0.0.0 -::/' /etc/redis/redis.conf
sed -i 's/^protected-mode yes/protected-mode no/' /etc/redis/redis.conf
```

### 6. Run
```bash
docker rm -f hermes-api 2>/dev/null
docker run -d \
  --name hermes-api \
  --env-file /opt/hermes-cognitive/.env \
  -e PYTHONPATH=/app/src \
  -v /root/.hermes:/data \
  -p 8100:8100 \
  --add-host=host.docker.internal:host-gateway \
  hermes-cognitive-api:latest
```

### 7. Verify
```bash
# Root + SKP stats
curl -s http://localhost:8100/ | python3 -m json.tool

# Auth check (should be 401)
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8100/v1/portsocket \
  -H "Content-Type: application/json" -d '{"input":"test"}'

# With auth (should return task_id)
curl -s -X POST http://localhost:8100/v1/portsocket \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <key>" \
  -H "X-Agent-ID: test-agent" \
  -d '{"input": "test"}'

# Agent registration
curl -s -X POST http://localhost:8100/agent/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <key>" \
  -d '{"agent_id": "test-agent", "capabilities": ["cognitive"]}'
```

## SKP Schema
The engine auto-detects two SQLite schemas:
1. **skp** — table `knowledge` with columns: key, value, category, tags, priority, source_agent_name, created_at, updated_at
2. **arsify** — table `memory_notes` with columns: key, value, scope, created_at

Create the knowledge table if needed:
```bash
sqlite3 /root/.hermes/shared_knowledge_pool.db "
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    category TEXT DEFAULT 'general',
    tags TEXT DEFAULT '[]',
    priority INTEGER DEFAULT 5,
    source_agent_name TEXT DEFAULT 'system',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);"
```

## Common Pitfalls
1. **Import errors**: `PYTHONPATH=/app/src` must be set, and imports use `from api.xxx` not `from src.api.xxx`
2. **Redis timeout**: `host.docker.internal` resolves but TCP blocked by iptables — need `iptables -I INPUT -i docker0`
3. **Redis protected mode**: Returns `-DENIED` error — disable or set password
4. **SKP schema not_found**: DB path wrong — check `/data/` mount maps to `/root/.hermes`
5. **422 on portsocket**: Field name mismatch — schema expects `input` not `message`
6. **Celery worker not running**: Tasks stay PENDING — deploy worker container for actual execution
7. **Celery task registration**: `include=["tasks"]` not `include=["src.tasks"]` when `PYTHONPATH=/app/src`. Celery's `include` uses Python import paths, not filesystem paths. Rebuild image after changing `celery_app.py`.
8. **AsyncResult without app context**: `AsyncResult(task_id)` uses DisabledBackend. Must pass `app=celery`: `AsyncResult(task_id, app=celery)`. Import celery from `celery_app` module.
9. **OPENROUTER_API_KEY placeholder in .env**: If `.env` has `OPENROUTER_API_KEY=sk-or-v1-placeholder-replace-me`, worker will use placeholder. Fix: `sed -i "s|OPENROUTER_API_KEY=sk-or-v1-placeholder-replace-me|OPENROUTER_API_KEY=${HOST_KEY}|" /opt/hermes-cognitive/.env`
10. **Free model rate limit cascade**: Default concurrency=4 all hitting free models (8 req/min limit). Fix: `--concurrency=2` and use small fast free models like `liquid/lfm-2.5-1.2b-instruct:free`. Avoid large free models (70B, 120B) — they timeout (524) and rate-limit faster.
11. **Both API and worker must be rebuilt together**: After changing `celery_app.py` or `tasks.py`, rebuild image and recreate BOTH containers. Mismatched versions cause tasks to be submitted but never picked up.
12. **Container network_mode:host**: Senator containers with `network_mode: host` reach host via `localhost:8100` directly. Docker Compose containers (worker, API) need `extra_hosts: "host.docker.internal:host-gateway"` for Redis access.

## Files
- Source: `/opt/hermes-cognitive/`
- Original design: `/root/Upshalter Gateway MoE/`
- SKP DB: `/root/.hermes/shared_knowledge_pool.db`
- Config: `/opt/hermes-cognitive/.env`
