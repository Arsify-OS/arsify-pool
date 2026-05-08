# Senator → Cognitive Engine Integration (FASE C)

## Architecture

```
Senator Container (nousresearch/hermes-agent)
  │
  ├─ senator_cognitive_client.py  ← stdlib-only HTTP client (no requests/httpx)
  │     ├─ submit_to_cognitive()  → POST /v1/portsocket
  │     └─ poll_result()         → GET  /v1/result/{task_id}
  │
  └─ senator-cycle.sh v2         ← host-level cron, pakai cognitive engine
        │
        ▼
Hermes Cognitive Engine (port 8100)
  │
  ├─ API Server (FastAPI)        ← hermes-api container
  │     ├─ /v1/portsocket        ← submit task
  │     ├─ /v1/result/{id}      ← poll result
  │     └─ /v1/status            ← health check
  │
  └─ Celery Worker               ← hermes-worker container
        ├─ L1 Perception         ← classify intent, category, complexity
        ├─ L2 Cognition          ← plan steps + SKP knowledge injection
        ├─ L3 Execution          ← execute with model priority per agent
        └─ L4 Reflection         ← quality check + SKP write-back
```

## Key Pitfalls & Fixes

### 1. Celery Task Registration — include path mismatch
**ERROR**: `NotRegistered: ['hermes.run']` — worker doesn't know about the task
**CAUSE**: `celery_app.py` had `include=["src.tasks"]` but container working dir is `/app` with `PYTHONPATH=/app/src`. Celery's `include` uses Python import paths. When `PYTHONPATH=/app/src`, the module is `tasks` not `src.tasks`.
**FIX**: Change to `include=["tasks"]` in `celery_app.py`, rebuild image, restart worker.
**VERIFY**: `docker exec hermes-worker sh -c "cd /app && PYTHONPATH=/app/src python3 -c 'from src.celery_app import celery; print([t for t in celery.tasks if \"hermes\" in t])'"` → should show `['hermes.run']`

### 2. Read-Only Volume — Cannot docker cp into container
**ERROR**: `Error response from daemon: mounted volume is marked read-only`
**CAUSE**: `/opt/editorial-scripts` mounted from host with `:ro` flag
**FIX**: Update the source file on the host path (`/root/.hermes/skills/devops/hermes-editorial/scripts/`) — changes propagate automatically to containers.
**NOTE**: Cannot use `docker cp` to write into read-only mounted volumes.

### 3. Container Missing Python Packages (requests/httpx)
**ERROR**: `ModuleNotFoundError: No module named 'requests'`
**CAUSE**: `nousresearch/hermes-agent` image doesn't include requests or httpx
**FIX**: Rewrite client using stdlib `urllib.request` only. No external dependencies.

### 4. Worker Not Receiving Tasks After Rebuild
**ERROR**: Tasks submitted but worker never picks them up
**CAUSE**: Old worker process still running (from before rebuild). New image has new task registration but old worker is still consuming from queue.
**FIX**: `docker rm -f hermes-worker && docker run -d --name hermes-worker ...`

### 5. API Container Also Needs Rebuild
**ERROR**: Tasks show `route=queued` but never get picked up
**CAUSE**: API container was rebuilt but worker wasn't (or vice versa). Both must be on same image version.
**FIX**: Always rebuild BOTH api and worker, restart BOTH containers.

### 6. Free Model Rate Limits
**ERROR**: HTTP 429, 401, 402 from OpenRouter
**CAUSE**: Free models have 8 req/min limit. Credits exhausted = 402.
**FIX**:
- 429: backoff 15s (free model rate limit)
- 401: skip model (invalid key or model unavailable)
- 402: skip model (insufficient credits)
- Use `FREE_MODEL_MAP` with `:free` suffix models
- Set `USE_FREE_MODELS=true` in .env

### 7. L1/L2 JSON Parse Failures
**WARNING**: `L1: JSON parse failed — using fallback perception`
**CAUSE**: Free models sometimes return non-JSON output for structured prompts
**FIX**: Perception layer has fallback that extracts JSON from `{...}` brackets and normalizes categories. This is expected behavior with free models.

### 8. Task Duration with Free Models
**OBSERVATION**: Tasks take 30s-5min with free models (vs 5-15s with paid)
**CAUSE**: Free models are slower and rate-limited. L1+L2+L3 each need separate API calls.
**MITIGATION**: Set max_wait=600 for polling. Worker handles retries automatically.

### 9. OPENROUTER_API_KEY Not Passed to Container
**ERROR**: Worker container doesn't have OPENROUTER_API_KEY
**CAUSE**: `.env` file had placeholder `OPENROUTER_API_KEY=sk-or-v1-placeholder-replace-me`
**FIX**: `sed -i "s|OPENROUTER_API_KEY=sk-or-v1-placeholder-replace-me|OPENROUTER_API_KEY=${HOST_KEY}|" /opt/hermes-cognitive/.env`
**VERIFY**: `grep OPENROUTER_API_KEY /opt/hermes-cognitive/.env`

### 10. Celery App Name Mismatch
**ERROR**: API submits to `hermes.run` but worker registers as `src.tasks:hermes.run`
**CAUSE**: Different celery app names between API and worker containers
**FIX**: Ensure both use `celery -A celery_app` (not `src.celery_app`). The `include` path must match the import path from the working directory.

### 11. AsyncResult Without App Context (CRITICAL)
**ERROR**: `AttributeError: 'DisabledBackend' object has no attribute '_get_task_meta_for'` or task results never resolve in FastAPI
**CAUSE**: `portsocket.py` used `AsyncResult(task_id)` without passing the celery app instance. FastAPI's default celery app has no backend configured.
**FIX**: Import celery from `celery_app` and pass it explicitly:
```python
# api/portsocket.py
from celery_app import celery
task_result = AsyncResult(task_id, app=celery)  # NOT just AsyncResult(task_id)
```
**VERIFY**: After fix, `task_result.status` should return `PENDING`/`STARTED`/`SUCCESS` instead of raising AttributeError.

### 12. OpenRouter Free Tier Rate Limit Cascade
**ERROR**: All worker processes hit 429 simultaneously, backoff grows to 45s+, tasks stall for 5+ minutes
**CAUSE**: Default concurrency=4, all 4 workers hit free models (8 req/min per key limit)
**FIX**:
- Reduce concurrency to 2: `celery -A celery_app worker --concurrency=2`
- Use small free models: `liquid/lfm-2.5-1.2b-instruct:free` (fast, reliable, 32K ctx)
- Avoid large free models (70B, 120B) — they timeout (524) and rate-limit faster
- **Production**: Top-up OpenRouter credits ($5-10) for reliable model access

### 13. Free Model Selection for Reliability (2026-05-07)
**Verified fast free models:**
- `liquid/lfm-2.5-1.2b-instruct:free` — fastest, 32K ctx, good for simple tasks
- `baidu/cobuddy:free` — decent, 131K ctx
**Avoid for production:**
- `nvidia/nemotron-3-super-120b-a12b:free` — frequent 524 timeouts
- `meta-llama/llama-3.3-70b-instruct:free` — very slow, heavy rate limit
- `minimax/minimax-m2.5:free` — frequent 429

### 14. Container network_mode:host vs host.docker.internal
**Behavior**: Senator containers use `network_mode: host`, so `localhost:8100` reaches host directly
**Implication**: No need for `host.docker.internal` in senator containers for API access
**But**: `host.docker.internal` still needed in Docker Compose containers (worker, API) to reach Redis on host

## Environment Variables

### Senator Containers (docker-compose.yml)
```yaml
environment:
  - COGNITIVE_ENGINE_URL=http://host.docker.internal:8100
  - HERMES_API_KEY=hermes-secret-change-me-in-production
  - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
  - TELEGRAM_BOT_TOKEN=8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU
  - TELEGRAM_CHAT_ID=5807834405
```

### Cognitive Engine (.env)
```bash
USE_FREE_MODELS=true
REDIS_URL=redis://:hermes-redis-secret-2026@host.docker.internal:6379/0
OPENROUTER_API_KEY=sk-or-v1-...
HERMES_API_KEY=hermes-secret-change-me-in-production
SKP_DB_PATH=/data/shared_knowledge_pool.db
```

## Verification Commands

```bash
# Test from host
curl -X POST http://localhost:8100/v1/portsocket \
  -H "Content-Type: application/json" \
  -H "X-API-Key: hermes-secret-change-me-in-production" \
  -H "X-Agent-ID: senator-akademisi" \
  -d '{"input": "Test query"}'

# Test from senator container
docker exec senator-akademisi python3 /opt/editorial-scripts/senator_cognitive_client.py \
  --sector akademisi --input "Test query" --max-wait 300

# Check worker task registration
docker exec hermes-worker sh -c "cd /app && PYTHONPATH=/app/src python3 -c \
  'from src.celery_app import celery; print([t for t in sorted(celery.tasks.keys()) if \"hermes\" in t])'"

# Check worker logs
docker logs --tail=20 hermes-worker

# Check Redis for task results
python3 -c "
import json, redis
r = redis.Redis.from_url('redis://:hermes-redis-secret-2026@localhost:6379/0', decode_responses=True)
keys = [k for k in r.keys('celery-task-meta-*')]
for k in keys[-3:]:
    d = json.loads(r.get(k))
    print(f'{k}: status={d.get(\"status\")}')
"
```

## Files

| File | Path | Description |
|------|------|-------------|
| senator_cognitive_client.py | `/opt/editorial-scripts/` (container), `/root/.hermes/skills/devops/hermes-editorial/scripts/` (host) | stdlib-only HTTP client |
| senator-cycle.sh v2 | `/root/upshalter-scripts/senator-cycle.sh` | Host-level cron script |
| docker-compose.yml | `/root/senator-pentahelix/docker-compose.yml` | Senator container config |
| agent_registry.py | `/opt/hermes-cognitive/src/core/agent_registry.py` | Senator profiles |
| openrouter_client.py | `/opt/hermes-cognitive/src/models/openrouter_client.py` | Free model support |
| celery_app.py | `/opt/hermes-cognitive/src/celery_app.py` | Task registration fix |
| perception.py | `/opt/hermes-cognitive/src/layers/perception.py` | JSON extraction + fallback |
