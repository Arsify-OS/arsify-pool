# FASE 6 — Performance Optimization Reference

## Bottleneck Analysis (2026-05-07)

| Component | Latency | Notes |
|-----------|---------|-------|
| Ollama qwen2.5:1.5b (simple) | ~5s | After warm-up |
| Ollama qwen2.5:1.5b (L2 prompt) | ~16-20s | 1000+ char prompts |
| Ollama qwen2.5:1.5b (L3 prompt) | ~4-5s | Short execution prompts |
| End-to-end pipeline (L1→L4) | ~108s | 2 steps, quality 80 |
| API queue response | ~22ms | Immediate task ID |
| Cache hit (Redis) | ~74ms | Skip LLM entirely |

## CPU VPS Constraints
- Load average: ~2.0 (2 cores)
- Steal time: 35.7% (neighbor contention)
- Ollama runner: 156% CPU, 1.2GB RAM during inference
- Total RAM: 7.8GB, ~1.1GB free under load

## Response Caching Architecture

Two-tier cache (local in-memory + Redis) to avoid repeated LLM calls.

Files: `models/cache.py`, integrated into `cognition.py`, `execution.py`, `reflection.py`, `kurator.py`.

Key: `md5(model + prompt + temperature)` → `hermes:llm_cache:<hash>` in Redis with 3600s TTL.
Only successful responses cached (errors/rate-limits skipped).

## SKP FTS5 Search

```sql
CREATE VIRTUAL TABLE knowledge_fts USING fts5(
    key, value, category, source_agent_name,
    content='knowledge', content_rowid='id'
);
-- Triggers auto-sync on INSERT/UPDATE/DELETE
```

Endpoint: `GET /search?q=query&limit=10&category=X&agent=Y`
Health: `GET /health/search`

**FTS5 does NOT support `*` wildcard for "match all"**. Use `SELECT COUNT(*) FROM knowledge_fts` for total.

## Prompt Optimization Pattern (Verified 100% with qwen2.5:1.5b)

```
You are <ROLE>. Output ONLY valid JSON — no markdown, no code fences, no explanation.
Schema: {"field":"<type>"}
<CONTEXT>
Output ONLY the JSON <result>:
```

Avoid: "Return JSON only", "Respond with JSON" — too weak.

## Docker Compose Mounts (Final Verified State)

All three services (api, worker, beat) have identical 14 bind mounts each.
Do NOT use YAML `<<: *anchor` merge for volumes — write full lists per service.

## Verification Commands

```bash
# All containers healthy
docker ps --format "table {{.Names}}\t{{.Status}}" | grep hermes

# API health + cache + FTS
curl -s http://localhost:8100/health
curl -s http://localhost:8100/health/cache
curl -s http://localhost:8100/health/search

# SKP stats
docker exec hermes-worker python3 -c "
import sqlite3
conn = sqlite3.connect('/data/shared_knowledge_pool.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM knowledge')
print(f'SKP: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM knowledge_fts')
print(f'FTS: {cur.fetchone()[0]}')
conn.close()
"

# All imports work
docker exec hermes-worker python3 -c "
import sys; sys.path.insert(0, '/app/src')
for m in ['models.cache','models.openrouter_client','core.skp_search','core.knowledge_injector','layers.cognition','layers.execution','layers.reflection','tasks','core.router','core.kurator','main','api.health']:
    __import__(m)
    print(f'OK {m}')
"
```
