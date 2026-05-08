# Performance Optimization Patterns (FASE 6)

## Ollama Integration Fix

### Problem
`openrouter_client.py` had `OPENROUTER_URL` hardcoded to `https://openrouter.ai/api/v1/chat/completions`. Setting the env var had no effect.

### Fix
```python
# models/openrouter_client.py line 63
OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
```

### Ollama Auto-Detection
When URL contains `localhost`, `127.0.0.1`, or `host.docker.internal`:
- Skip `Authorization` header (Ollama doesn't need API key)
- Use `OLLAMA_MODEL` env var directly instead of `MODEL_MAP` lookups
- OpenRouter model IDs (e.g., `liquid/lfm-2.5-1.2b-instruct:free`) don't exist in Ollama

### Docker Compose Config
```yaml
environment:
  OPENROUTER_URL: http://host.docker.internal:11434/v1/chat/completions
  OLLAMA_MODEL: qwen2.5:1.5b
  LLM_TIMEOUT_READ: 90
  LLM_MAX_RETRY: 1
```

## LLM Response Caching (2-Tier)

### Architecture
- **Tier 1**: In-memory dict (~500 entries, sub-ms lookup, per-process)
- **Tier 2**: Redis (shared across workers, configurable TTL)
- **Key**: MD5 hash of `model + prompt + temperature`
- **Only caches successful responses** (no error, has content)

### TTL Strategy
- L2 (planning): 3600s (1 hour)
- L3 (execution): 3600s (1 hour)
- L4 (reflection): 300s (5 minutes)

### Integration
```python
# Drop-in replacement for call_with_fallback:
from models.cache import cached_call as call_with_fallback
```

### Health Endpoint
`GET /health/cache` → `{local_entries, local_max, redis_entries, redis_available}`

### Verified Results
- After benchmark: 14 Redis cache entries populated
- Repeated queries skip LLM call entirely
- Queue response: 74ms (vs 120s+ for full pipeline)

## SQLite FTS5 Full-Text Search

### Setup
```python
from core.skp_search import setup_fts, search, search_count
setup_fts()  # Idempotent — creates virtual table + triggers
```

### Auto-Sync Triggers
- `knowledge_ai`: AFTER INSERT → adds to FTS index
- `knowledge_ad`: AFTER DELETE → removes from FTS index
- `knowledge_au`: AFTER UPDATE → deletes old + inserts new

### API Endpoint
```
GET /search?q=query&limit=10&category=general&agent=senator-akademisi
```

### FTS5 Quirks
- Does NOT support `*` wildcard — use `search_count("query")` not `search_count("*")`
- Rebuild after manual DB changes: `rebuild_index()`

### Verified Results
- 45 entries indexed from SKP knowledge table
- Search "AI education" → 5 matches with relevance ranking

## Prompt Optimization for JSON Output

### Problem
Small LLMs (qwen2.5:1.5b, phi3:mini) frequently wrap JSON in markdown code fences or add explanatory text.

### Solution Pattern
```
You are L2 Planner. Output ONLY valid JSON — no markdown, no code fences, no explanation.
Schema: {"goal":"<goal>","steps":[{"id":N,"task":"<task>","type":"execution","tool":"<tool>","expected_output":"<output>"}],"estimated_complexity":N,"context_used":false}
PERCEPTION: {json.dumps(perception)}
Output ONLY the JSON plan:
```

### Key Techniques
1. Put schema INLINE in the prompt (not in system message)
2. Use "Output ONLY the JSON" as the FINAL line
3. Use `json.dumps(obj)` without `indent=2` (saves tokens)
4. Set `temperature=0.3` for planning, `0.1` for evaluation
5. Include "no markdown, no code fences, no explanation" explicitly

### Results
- qwen2.5:1.5b: valid JSON in ~19s on CPU (vs 30s+ with verbose prompts)
- phi3:mini: valid JSON in ~8s for short prompts

## tasks.py Logger Import Bug

### Problem
Mounting custom `tasks.py` without `logger` definition causes:
```
NameError: name 'logger' is not defined
```

### Fix
```python
import logging
logger = logging.getLogger(__name__)  # MUST be at module level, before any function uses it
```

## Ollama Performance on CPU VPS

### Baseline (qwen2.5:1.5b on 2-core VPS)
- Simple prompt ("ping"): 45s
- L2 planning prompt (schema + perception): 16-20s
- L3 execution prompt: 4-5s
- CPU steal time: 35%+ (neighbor contention)

### Mitigation
- Response caching (2-tier) reduces repeated calls
- Smaller prompts (no indent=2, inline schema) save ~30% tokens
- concurrency=2 in Celery worker prevents overload
- Set `LLM_TIMEOUT_READ=90` (not 300) for faster fallback

## PRD Audit Methodology

### Pattern: Cross-check STRATEGY-WAVES.md vs Implementation
```bash
# 1. Read the PRD/WAVE file
cat /root/upshalter-5-prd-package/STRATEGY-WAVES.md
cat /root/upshalter-5-prd-package/prds/PRD-*.md

# 2. Check each deliverable exists
ls -la /root/upshalter-scripts/    # scripts
ls -la /root/upshalter-reports/   # reports
ls -la /root/upshalter-config/    # config
ls -la /root/upshalter-materials/ # materials
ls -la /var/www/data.upshalter.com/ # landing page

# 3. Verify container state
docker ps --format "table {{.Names}}\t{{.Status}}" | grep hermes

# 4. Verify imports inside container
docker exec hermes-worker python3 -c "
import sys; sys.path.insert(0, '/app/src')
for m in ['models.cache','models.openrouter_client','core.skp_search',...]:
    try: __import__(m); print(f'✅ {m}')
    except Exception as e: print(f'❌ {m}: {e}')
"

# 5. Verify syntax on host
for f in /root/.hermes/*.py; do python3 -m py_compile "$f" && echo "✅" || echo "❌"; done
```

### Common Findings
- Scripts exist but not tested end-to-end
- Container mounts missing for new files
- SKP table name mismatch: PRD says `memory_notes`, code uses `knowledge`
- Docker compose duplicate mounts (check with `grep -n "mount" docker-compose.yml`)

## Docker Compose Mount Dedup Pattern

### Problem
After multiple edits, `docker-compose.yml` accumulates duplicate mount entries:
```yaml
- /root/.hermes/openrouter_client.py:/app/src/models/openrouter_client.py
- /root/.hermes/openrouter_client.py:/app/src/models/openrouter_client.py  # DUP
```

### Detection
```bash
grep "\- /root/.hermes" docker-compose.yml | sort | uniq -d
```

### Fix
Remove duplicate lines. Each file should appear exactly once in the anchor section.

### All Services Need All Mounts
When adding a new custom file (e.g., `cache.py`), add it to ALL services that need it:
- `api` — needs health.py, main.py, cache.py (for /health/cache endpoint)
- `worker` — needs all pipeline files
- `beat` — needs celery_app.py + all files beat tasks import

## SKP Table Name Discrepancy

### Issue
PRD-001 references `memory_notes` table. Implementation uses `knowledge` table.
- `memory_notes`: exists in DB but empty (0 entries)
- `knowledge`: has 77+ entries, actively used by pipeline

### Root Cause
Two different schemas coexist:
1. Arsify OS native: `memory_notes` (key, value, scope, source_agent_name, seci_phase)
2. SKP standalone: `knowledge` (key, value, category, tags, priority, source_agent_name)

### Resolution
The pipeline writes to `knowledge` table. PRD success criteria should reference `knowledge` table, not `memory_notes`. Both tables exist in the same DB file.
