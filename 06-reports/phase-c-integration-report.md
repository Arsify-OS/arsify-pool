# FASE C: Integrasi Senator — Hermes Cognitive Engine

## Status: ✅ SELESAI

## Ringkasan

Senator Pentahelix (5 sektor) terintegrasi dengan Hermes Cognitive Engine
melalui API `/v1/portsocket`. Setiap senator submit task ke Cognitive Engine yang
menjalankan pipeline L1→L2→L3→L4.

## Arsitektur

```
Senator Container (nousresearch/hermes-agent)
  │
  ├─ senator_cognitive_client.py  ← stdlib-only HTTP client
  │     ├─ submit_to_cognitive()  → POST /v1/portsocket
  │     └─ poll_result()         → GET  /v1/result/{task_id}
  │
  └─ senator-cycle.sh v2         ← sequential cognitive submission
        │
        ▼
Hermes Cognitive Engine (port 8100)
  ├─ API Server (FastAPI)        ← hermes-api container
  └─ Celery Worker (conc=2)      ← hermes-worker container
        ├─ L1 Perception
        ├─ L2 Cognition + SKP inject
        ├─ L3 Execution
        └─ L4 Reflection + SKP write-back
```

## Perubahan

1. **senator_cognitive_client.py** — stdlib-only, retry logic, fallback
2. **docker-compose.yml** — COGNITIVE_ENGINE_URL + HERMES_API_KEY
3. **senator-cycle.sh v2** — sequential API calls + telegram notification
4. **agent_registry.py** — 5 senator profiles (complexity_threshold=1)
5. **openrouter_client.py** — free model map + rate limit handling
6. **celery_app.py** — task registration fix
7. **perception.py** — JSON extraction + category normalization
8. **portsocket.py** — AsyncResult with celery app context

## Known Issues

1. **Free model rate limit**: 8 req/min per key — worker backoff 15-45s
2. **Task duration**: 15-30s per task (free models lambat)
3. **Worker concurrency**: 2 — task antri jika >2 bersamaan
4. **OpenRouter credits**: Key is free tier — perlu top-up untuk production

## Verifikasi

```bash
# Test dari dalam container
docker exec senator-akademisi python3 /opt/editorial-scripts/senator_cognitive_client.py \
  --sector akademisi --input "Test query" --max-wait 180

# Check worker
docker logs --tail=20 hermes-worker

# Health check
curl http://localhost:8100/v1/status
```

## Files

- `/opt/editorial-scripts/senator_cognitive_client.py`
- `/root/.hermes/skills/devops/hermes-editorial/scripts/senator_cognitive_client.py`
- `/root/senator-pentahelix/docker-compose.yml`
- `/root/upshalter-scripts/senator-cycle.sh`
- `/opt/hermes-cognitive/src/core/agent_registry.py`
- `/opt/hermes-cognitive/src/models/openrouter_client.py`
- `/opt/hermes-cognitive/src/layers/perception.py`
- `/opt/hermes-cognitive/src/celery_app.py`
- `/opt/hermes-cognitive/src/api/portsocket.py`
- `/opt/hermes-cognitive/.env`
