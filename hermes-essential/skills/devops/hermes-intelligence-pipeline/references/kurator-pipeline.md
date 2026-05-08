# Kurator Pipeline — Implementation Reference

## Overview

The Kurator is a periodic Celery task that reads uncurated SKP entries produced by Senator pipelines, synthesizes them into structured analysis via LLM, and writes curated results back to the SKP database.

**Source**: `core/kurator.py` (255 lines)
**Task**: `hermes.kurator()` in `tasks.py`
**Schedule**: Every 5 minutes via Celery Beat

## SKP Key Convention

| Key Pattern | Meaning |
|---|---|
| `senator-{domain}/execution/{hash}` | Raw Senator output (uncurated) |
| `curated:senator-{domain}/execution/{hash}` | Marked as already curated |
| `kurator:{hash}` | Kurator analysis result |

## Flow

```
1. fetch_uncurated_entries(limit=10)
   → SELECT * FROM knowledge
     WHERE key NOT LIKE 'kurator:%'
       AND key NOT LIKE 'curated:%'
       AND created_at >= now() - 5min
     ORDER BY created_at DESC LIMIT 10

2. If count < MIN_ENTRIES_TO_CURATE (3) → skip

3. Group by source_agent_name
   → { "senator-akademisi": [...], "senator-bisnis": [...] }

4. Build prompt with entries text

5. Call LLM via call_with_fallback("nemotron", prompt)
   → Parse JSON response
   → Fallback to _fallback_analysis() if LLM fails

6. write_curated_result(title, analysis, sources)
   → INSERT INTO knowledge (key="kurator:{hash}", value=json, category="curated", priority=9, source_agent_name="kurator")

7. mark_as_curated([entry_keys])
   → UPDATE knowledge SET key = 'curated:' || key WHERE key = ?
```

## Celery Beat Configuration

```python
# celery_app.py
celery.conf.update(
    beat_schedule={
        "kurator-every-5-min": {
            "task": "hermes.kurator",
            "schedule": 300.0,
            "args": (),
        },
    },
)
```

## Docker Compose — Beat Service

```yaml
beat:
  build: { context: ., dockerfile: Dockerfile }
  container_name: hermes-beat
  restart: unless-stopped
  command: celery -A celery_app beat --loglevel=info
  environment:
    REDIS_URL: redis://host.docker.internal:6379/0
    PYTHONPATH: /app/src
  volumes:
    - /root/.hermes:/data
    - /root/.hermes/celery_app.py:/app/src/celery_app.py
    - /opt/hermes-cognitive/src/core/kurator.py:/app/src/core/kurator.py
  extra_hosts:
    - "host.docker.internal:host-gateway"
```

## Common Issues

### ModuleNotFoundError for newly-added modules
Adding a new `.py` file (e.g. `kurator.py`) and mounting it in docker-compose does NOT take effect with `docker compose restart worker`. Must use:
```bash
docker compose up -d --force-recreate worker
```

### Kurator uses fallback analysis (confidence 0.5)
This happens when:
1. LLM call fails (rate limit, timeout)
2. SKP entry values are too short/generic for LLM to synthesize meaningful insights
3. LLM returns markdown-wrapped JSON that the parser can't handle

Fix: Ensure Senator SKP write-back stores meaningful content (actual analysis results, not just "Task completed").

### Kurator JSON Parse — Ollama Markdown Fence Pattern
Ollama models (qwen2.5:1.5b, phi3:mini) frequently wrap JSON in markdown code fences:
```
```json
{"insights": [...], "trends": [...]}
```
```
The `_parse_analysis()` method must handle this with cascading extraction:
1. Strip ` ```json ` / ` ``` ` whitespace/fences from response
2. Try `json.loads()` on cleaned text
3. Regex fallback: `r'\{[^{]*"insights"\s*:\s*\[[^\]]*\]'`
4. Text/named-entity extraction as last resort

Similarly, `parse_kurator_result()` in tasks.py checks for nested keys (`analysis`, `result`, `data`) and returns the first match.

**Always add `import asyncio` at the top of kurator.py** when using `asyncio.wait_for()` — missing this causes silent `NameError` that triggers fallback. (See pitfall #21 in SKILL.md.)

### Beat not firing
- Verify beat container is running: `docker ps | grep beat`
- Check logs: `docker logs hermes-beat` — should show "Sending due task kurator-every-5-min" every 5 min
- If not firing, verify `celery_app.py` is mounted correctly and has `beat_schedule` in `celery.conf.update()`

## Recovery After Interruption

If kurator.py was being written when the session was interrupted:
1. Check current line count: `wc -l /opt/hermes-cognitive/src/core/kurator.py`
2. If incomplete (< 250 lines), the file likely needs the full `run_curation()`, `_parse_analysis()`, `fetch_uncurated_entries()`, `write_curated_result()`, and `mark_as_curated()` functions.
3. Verify imports at top: `import asyncio`, `import json`, `import hashlib`, `import re`, `import sqlite3`, `from datetime import datetime, timedelta`
4. After writing/updating: `docker compose up -d --force-recreate worker` (not just restart)
5. Verify syntax: `python3 -m py_compile /opt/hermes-cognitive/src/core/kurator.py`
6. Trigger manually to test: `docker exec hermes-worker python3 -c "import asyncio; from core.kurator import run_curation; print(asyncio.run(run_curation()))"`

```bash
# Check beat is running and firing
docker logs hermes-beat --tail 20

# Trigger kurator manually
docker exec hermes-worker python3 -c "
import asyncio
from core.kurator import run_curation
result = asyncio.run(run_curation())
print(result)
"

# Check kurator entries in SKP (from host)
sqlite3 /root/.hermes/shared_knowledge_pool.db "
  SELECT key, source_agent_name, priority, created_at
  FROM knowledge WHERE key LIKE 'kurator:%'
  ORDER BY created_at DESC LIMIT 5
"

# Check curated-marked entries
sqlite3 /root/.hermes/shared_knowledge_pool.db "
  SELECT COUNT(*) FROM knowledge WHERE key LIKE 'curated:%'
"
```
