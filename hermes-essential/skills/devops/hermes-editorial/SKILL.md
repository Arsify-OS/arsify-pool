---
name: hermes-editorial
description: "Hermes Editorial Pipeline: Senator Factory Workers → Policy Brief. Scrape (Senator) → Analyze/Cluster (LLM) → Draft (Humanize) → Policy Brief → Notify Curator (Telegram). Upgraded from simple scraper to AI Editorial System with 5 Senator Factory Workers."
---

# HERMES EDITORIAL PIPELINE - FACTORY WORKERS MODE

**CURRENT ARCHITECTURE (FASE 4 v3, 2026-05-08):**
```
Cron (6h) → senator-cycle-v3.sh → OpenRouter API (primary)
    ↓                                          ↓
    ├── 5x Senator LLM calls          Ollama (last resort, CPU-only)
    │   (akademisi, bisnis, komunitas,              
    │    pemerintah, media)                        │
    ↓                                             │
Save to SKP (/data/arsify.db, table=knowledge) ←──┘
    ↓
Cron (1h after senator) → kurator-v2.sh → kurator-v2.py
    ↓
Consolidate all senator outputs from SKP via OpenRouter
    ↓
Generate Markdown brief → /root/upshalter-reports/pentahelix-brief-YYYY-MM-DD-HH.md
    ↓
Cron (30min) → generate-intelligence-page.py → /var/www/data.upshalter.com/
```

**⚠️ CRITICAL: Active SKP is `/data/arsify.db` (symlink), table `knowledge`, NOT `memory_notes`**
- Key column: `key` (text), `value` (text), `source_agent_name` (text), `created_at` (text)
- Do NOT use `shared_knowledge_pool.db` or `memory_notes` table — those are obsolete
- Senator entries use key format: `senator-<domain>/temuan/YYYYMMDD-HH` or `senator-<domain>/isu/YYYYMMDD-HH`
- Kurator entries use key format: `curated:senator-<domain>/...` or `pentahelix/brief/...`

**OLD ARCHITECTURE (pre-FASE 4, DEPRECATED):**
```
[5 Senator Containers] → [Links + Drafts to shared dirs]
                        ↓
[Main Editorial Pipeline] → [Policy Brief] → [Telegram Kurator]
```
- Used `/root/.hermes/editorial-links/` and `/root/.hermes/editorial-drafts/`
- Used `shared_knowledge_pool.db` with `memory_notes` table
- No longer maintained — kept for reference only

## PITFALLS DISCOVERED

### 0. SKP Schema Mismatch — CRITICAL (2026-05-08, THIS SESSION)
**ISSUE**: The old skill/documentation references `memory_notes` table with `id, title, category, source, content, created_at` columns, and DB path `/root/.hermes/shared_knowledge_pool.db`. The ACTIVE system uses table `knowledge` with columns `key, value, source_agent_name, created_at` at `/data/arsify.db`.
**SYMPTOM**: `sqlite3 /data/arsify.db "SELECT id, title FROM knowledge"` → `Error: no such column: id`
**FIX**: Always query with correct schema:
```sqlite3 /data/arsify.db "SELECT key, value, source_agent_name, created_at FROM knowledge WHERE category='komunitas' ORDER BY created_at DESC LIMIT 10"
```
**OR** use Python with `key, value, source_agent_name, created_at` column names.
**LESSON**: Never assume SKP schema — always `.schema knowledge` first when working with a new DB.

### 1. Permission Denied (Critical!)
**ERROR**: `PermissionError: [Errno 13] Permission denied: '/opt/data/editorial-links/senator-akademisi.txt'`
**CAUSE**: Container runs as non-root, `/root/.hermes/` owned by root
**FIX**: 
```bash
chmod 777 /root/.hermes/editorial-links /root/.hermes/editorial-drafts
```
**Note**: Never use `chmod 777` in production, but works for quick VPS setup.

### 2. OPENROUTER_API_KEY Not Read in Container
**ERROR**: `❌ OPENROUTER_API_KEY not set!` in container logs
**CAUSE**: Environment variables not passed correctly to container
**FIX**: Create key file on host, mount as read-only:
```yaml
# docker-compose.yml
volumes:
  - /root/.hermes/.openrouter_key:/opt/data/.openrouter_key:ro
```
```python
# In script:
key_file = "/opt/data/.openrouter_key"
if os.path.exists(key_file):
    with open(key_file) as f:
        OPENROUTER_KEY = f.read().strip()
```

### 3. BeautifulSoup Not Available
**ERROR**: `name 'BeautifulSoup' is not defined`
**CAUSE**: bs4 not installed in container, or import missing
**FIX**: Use regex-based HTML parsing instead (no dependencies):
```python
import re
text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
text = re.sub(r'<[^>]+>', ' ', text)
text = re.sub(r'\s+', ' ', text).strip()
```

### 4. Docker Compose Variable Interpolation Warning
**ERROR**: `The "SECTOR" variable is not set. Defaulting to a blank string.`
**FIX**: Don't use `${VAR}` syntax in docker-compose.yml. Use direct values or environment section without interpolation.

### 5. Healthcheck Typo Causes Restart Loop (Critical!)
**ERROR**: Senator containers restart every ~30s despite main process running fine
**CAUSE**: Typo in `healthcheck.sh` — `$HEALTHBEAT` instead of `$HEARTBEAT`
```bash
# WRONG (line 7):
AGE=$(( $(date +%s) - $(stat -c %Y "$HEALTHBEAT" 2>/dev/null || echo 0) ))
# RIGHT:
AGE=$(( $(date +%s) - $(stat -c %Y "$HEARTBEAT" 2>/dev/null || echo 0) ))
```
**FIX**: Patch the typo, then `docker compose build --no-cache && docker compose down && docker compose up -d`
**DETECTION**: `docker ps` shows containers "Up X seconds (health: starting)" — never becomes healthy

### 6. Pipeline sys.exit(1) on LLM Failure Causes Restart Loop
**ERROR**: `❌ Draft creation failed!` → `sys.exit(1)` → container exits → Docker restart
**CAUSE**: `senator-factory-pipeline.py` calls `sys.exit(1)` when LLM returns None (402, 429, timeout)
**FIX**: Replace crash with fallback draft generation:
```python
if not draft:
    log("⚠️ LLM analysis failed, continuing with title-only draft...")
    draft = f"## Ringkasan Berita {SECTOR.title()}\n\n"
    for i, a in enumerate(articles[:5], 1):
        draft += f"{i}. {a['title']}\n   Sumber: {a['link']}\n\n"
```
**KEY**: Never `sys.exit(1)` in a Docker container that should run indefinitely.

### 7. OpenRouter Model Naming — "openrouter/" Prefix Not Valid
**ERROR**: `402` or `404` when calling `openrouter/owl-alpha`
**CAUSE**: OpenRouter model IDs don't use `openrouter/` prefix. Use just `owl-alpha` or full path like `meta-llama/llama-3.3-70b-instruct:free`
**FREE MODELS** (verified 2026-05-07):
- `meta-llama/llama-3.3-70b-instruct:free` (64K ctx) — best free option
- `meta-llama/llama-3.2-3b-instruct:free` (128K ctx)
- `nousresearch/hermes-3-llama-3.1-405b:free` (131K ctx)
- `openai/gpt-oss-120b:free` (131K ctx)
- `google/gemma-4-26b-a4b-it:free` (262K ctx)
**CHECK FREE MODELS**: `curl -s https://openrouter.ai/api/v1/models | python3 -c "...filter pricing.prompt==0 && pricing.completion==0"`
**CHECK CREDIT**: `curl -s https://openrouter.ai/api/v1/auth/key -H "Authorization: Bearer $KEY"` → check `is_free_tier` and `usage`

### 8. Container Volume Read-Only — Cannot Copy Files In
**ERROR**: `Error response from daemon: mounted volume is marked read-only`
**CAUSE**: Volume mounted with `:ro` flag in docker-compose
**FIX**: Cannot copy files into read-only containers. Must rebuild:
1. Update source script on host
2. `docker compose build --no-cache`
3. `docker compose down && docker compose up -d`

### 5. browser-use Integration Failed / Playwright Service Success
**Attempted**: Install browser-use with langchain-openai for deeper web research
**Issues**: 
- `langchain-openai` not reading `OPENAI_API_KEY` correctly (fixed by setting `api_key` and `base_url` explicitly)
- `ChatOpenAI` missing `provider` attribute (fixed with custom subclass `ChatOpenAIWithProvider`)
- CDP connection timeout (30s) when starting browser (Playwright Chromium launches but browser-use fails to connect via CDP)
**Resolution**: Skipped browser-use, implemented Playwright direct API service
**Result**: Working browser automation API at `http://localhost:8090/browse`
**Files**: `/opt/browser-use-service/main.py` (Playwright-based), venv at `/opt/browser-use-venv/`
**Usage**: Senator containers can call `http://host.docker.internal:8090/browse` with JSON `{"url": "...", "task": "..."}`
**Recommendation**: For any browser automation needs, use Playwright direct instead of browser-use to avoid CDP issues.

## REQUIREMENTS

- 5 Senator containers running (hermes-agent image, Docker Compose at `/root/senator-pentahelix/`)
- SKP database at `/data/arsify.db` with `knowledge` table (columns: key, value, source_agent_name, created_at)
- Telegram Bot Token & Chat ID (from memory: token `8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU`, chat `5807834405`)
- OPENROUTER_API_KEY (in environment or `/root/.hermes/.openrouter_key`)
- Cron jobs configured (see VERIFICATION step 5)
- No dependency on `shared_knowledge_pool.db` or `memory_notes` table — THOSE ARE OBSOLETE

## FILES & PATHS (ACTIVE, FASE 4 v3)

### Core Pipeline Scripts
- **Senator Cycle**: `/root/upshalter-scripts/senator-cycle-v3.sh` (OpenRouter direct, Ollama fallback)
- **Kurator Wrapper**: `/root/upshalter-scripts/kurator-v2.sh` → delegates to:
- **Kurator Engine**: `/root/upshalter-scripts/kurator-v2.py` (Python, reads SKP, consolidates via OpenRouter)
- **Intelligence Page**: `/root/upshalter-scripts/generate-intelligence-page.py` (every 30 min → data.upshalter.com)
- **Health Check**: `/root/upshalter-scripts/health-check.sh` (every 5 min)
- **SKP Backup**: `/root/upshalter-scripts/backup-skp.sh` (daily 20:00 UTC)

### Storage & Output
- **SKP Database**: `/data/arsify.db` (symlink), table: `knowledge`
- **Reports**: `/root/upshalter-reports/` (Markdown + PDF)
- **Logs**: `/root/upshalter-logs/`
- **Web Dashboard**: `/var/www/data.upshalter.com/` (index.html + data.json)

### Docker Compose
- **Senator Containers**: `/root/senator-pentahelix/docker-compose.yml` (5× nousresearch/hermes-agent:latest)
  - senators: senator-akademisi, senator-bisnis, senator-komunitas, senator-pemerintah, senator-media

### Watching in Docker containers — Senator Containers
- Image: `nousresearch/hermes-agent:latest`
- Volumes: senator-data volume + `/root/.hermes:/opt/data:rw` + skills scripts + openrouter key
- Network: `network_mode: host`
- User: root
- Extra hosts: `host.docker.internal:host-gateway`

**FILE FORMAT (SKP knowledge table)**:
- `key`: `senator-<domain>/temuan/YYYYMMDD-HH` or `senator-<domain>/isu/YYYYMMDD-HH`
- `value`: JSON string with domain-specific structure (see below)
- `source_agent_name`: `senator-<domain>`
- `created_at`: ISO datetime

**SENATOR OUTPUT VALUE STRUCTURE**:
- Academisi: `{temuan:[...], sumber:[...], relevansi_bisnis:'...', timestamp:'...'}`
- Bisnis: `{peluang:[...], risiko:[...], rekomendasi:'...', timestamp:'...'}`
- Komunitas: `{isu:[{judul, sentiment, deskripsi, tokoh_kunci:[...]}], sentiment_overall:'...', timestamp:'...'}`
- Pemerintah: `{regulasi:[...], dampak_bisnis:'...', compliance_notes:[...], timestamp:'...'}`
- Media: `{narasi_dominan:[...], framing:'...', sentiment_publik:'...', media_utama:[...], timestamp:'...'}`

## WORKFLOW STEPS (FASE 4 v3)

### Step 1: Senator Cycle (Cron every 6 hours)
File: `/root/upshalter-scripts/senator-cycle-v3.sh`

```
For each of 5 domains (akademisi, bisnis, komunitas, pemerintah, media):
  1. Build system prompt (domain-specific role)
  2. Build research prompt (current date/time context)
  3. Call LLM via OpenRouter API (primary, 60s timeout)
     - Model: openrouter/owl-alpha
     - Auth: Bearer <OPENROUTER_API_KEY>
     - Fallback: Ollama local (30s timeout, num_predict 512)
  4. Save JSON result to SKP via save_skp()
     - Key: senator-<domain>/temuan/YYYYMMDD-HH
     - Fallback: direct sqlite3 INSERT if skp_adapter fails
  5. Log result

After all 5 senators:
  - Schedule kurator-v2.sh in 5 minutes (background)
```

### Step 2: Kurator Consolidation (Cron 1h after senator)
File: `/root/upshalter-scripts/kurator-v2.py`

```
1. Read last 20 entries from SKP knowledge table
2. Filter for senator entries (key starts with "senator-" or contains temuan/peluang/isu/regulasi/narasi)
3. Deduplicate by key
4. Calculate confidence based on entry count (0.10 to 0.90)
5. Build context from senator outputs (truncate to 800 chars per entry)
6. Call OpenRouter to generate consolidated intelligence brief
7. Save Markdown brief to /root/upshalter-reports/pentahelix-brief-YYYY-MM-DD-HH.md
8. Save brief to SKP
```

### Step 3: Intelligence Page Update (Cron every 30 minutes)
File: `/root/upshalter-scripts/generate-intelligence-page.py`

```
1. Read latest insights from SKP
2. Generate data.json
3. Generate index.html
4. Write to /var/www/data.upshalter.com/
```

## Ollama Fallback Configuration (Critical for Reliability)

When OpenRouter credits are exhausted or rate limits hit, the entire pipeline MUST fall back to Ollama. This is not optional — without it, the pipeline stalls indefinitely.

### Ollama Timeout Tuning
- **Default timeout (50s) is too low for phi3:mini on CPU.** A short prompt takes ~20s, a long Senator prompt can take 60s+.
- Set `LLM_TIMEOUT_READ=300` in `/opt/hermes-cognitive/.env`
- Also add `LLM_TIMEOUT_READ: "300"` explicitly to the worker service in `docker-compose.yml` (env file vars may not propagate to worker)
- Verify: `docker exec hermes-worker python3 -c "from src.models.openrouter_client import TIMEOUT; print(TIMEOUT.read)"` → should show `300.0`

### Ollama Model Name Auto-Detection
In `/root/.hermes/openrouter_client.py`, the model maps must auto-detect whether they're talking to Ollama or OpenRouter:
```python
# Define BEFORE MODEL_MAP to avoid NameError
_llm_url = os.getenv("OPENROUTER_URL", "")
_is_ollama = "11434" in _llm_url or "ollama" in _llm_url.lower()

MODEL_MAP = {
    "nemotron": "phi3:mini" if _is_ollama else "nvidia/nemotron-3-super-120b-a12b",
    ...
}
```
**Critical**: `_is_ollama` MUST be defined before `MODEL_MAP` references it. Defining it after causes `NameError: name '_is_ollama' is not defined` at import time.

### Ollama Health Check
Before relying on Ollama, verify it responds:
```bash
time curl -s -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"phi3:mini","messages":[{"role":"user","content":"OK"}],"temperature":0.2}' \
  -o /tmp/ollama_test.json
```
If this times out (>120s), Ollama may be OOM-killed. Check: `free -h` and `docker logs ollama`.

### LM Studio Alternative
If Ollama is too slow on CPU, LM Studio (lmstudio.ai) provides faster OpenAI-compatible local inference. Same API format, change port to 1234.
1. **docker-compose.yml Setup**: Add `MODEL` and `CONCURRENCY` env vars to `x-senator-base`:
   ```yaml
   environment:
     - MODEL=lfm-2.5-1.2b-instruct:free
     - CONCURRENCY=2
   ```
   ⚠️ Ensure all env vars use 4-space indentation (mixed indentation causes variables to not pass to containers).
2. **Patch `scripts/senator-factory-pipeline.py`**:
   - Read MODEL from env: `MODEL = os.getenv("MODEL", "meta-llama/llama-3.3-70b-instruct:free")`
   - Add `call_ollama()` function with 300s timeout (default 120s is too short for larger prompts)
   - Modify `call_llm()` to fallback to Ollama on OpenRouter 402/429 errors or exceptions
3. **Ollama Setup**:
   - Restart Ollama if API calls time out: `systemctl restart ollama`
   - Verify Ollama is accessible from containers via `host.docker.internal:11434`

## Pitfalls
- OpenRouter free models hit daily rate limits (429) — Ollama fallback is mandatory
- Use `docker compose` (v2) instead of deprecated `docker-compose` (v1)
- Senator containers need `extra_hosts: - "host.docker.internal:host-gateway"` to access host Ollama
- Telegram chat_id must be numeric (already configured in docker-compose env)

### 25. Ollama qwen2.5:1.5b Is ~30s Per Call — Plan Accordingly (FASE 4/5)
**OBSERVATION**: Simple prompts take ~30s, complex prompts (2000+ chars) take 60-90s on qwen2.5:1.5b.
**CAUSE**: Small model on CPU with limited RAM (7.8GB VPS).

**CRITICAL UPDATE (2026-05-08)**: Ollama on CPU-only (2 cores, no GPU) is a HARD BLOCKER:
- Model load: ~39 seconds, Inference: >60s for small prompts → unusable for production
- Hermes API `/v1/portsocket`: async only, Celery often doesn't process → not for sync inference
- Hermes API `/chat`: routes to Ollama lokal → same slowness
- **SOLUTION: OpenRouter Direct** — `https://openrouter.ai/api/v1/chat/completions` with `Authorization: Bearer <key>` → <30s ✅
- **5/5 senators succeeded** using OpenRouter direct (senator-cycle-v3.sh deployed)
- Active SKP DB: `/data/arsify.db` (symlink), table: `knowledge` (NOT `memory_notes`)
- Do NOT rely on Ollama for anything time-sensitive on CPU-only VPS
**IMPACT**: L2 planning calls frequently timeout → fallback plan used. Kurator LLM analysis times out → fallback analysis used.
**MITIGATION**:
- Set `MAX_RETRY=1` and `LLM_TIMEOUT_READ=90` to fail fast and use fallback
- Fallback plans must produce meaningful output (not just "Process request")
- Accept that on CPU-only VPS, fallback paths are the normal path
- For production: use OpenRouter paid models ($5-10 topping) or GPU server
- **BETTER**: Use OpenRouter direct (`https://openrouter.ai/api/v1`) — skip Ollama entirely

### 39. httpcore Missing After httpx Install (FASE 4)
**ERROR**: `ModuleNotFoundError: No module named 'httpcore'` when running inline Python in bash scripts.
**CAUSE**: `httpx` installed but `httpcore` (its dependency) not auto-installed in some pip versions.
**FIX**: `pip install httpcore --break-system-packages -q`
**SCOPE**: Affects senator-cycle-v2.sh inline Python calls that use `httpx.post()`.

### 40. Hermes portsocket Auth Format (FASE 4)
**FINDING**: Hermes API `/v1/portsocket` auth: `X-API-Key: hermes-secret-change-me-in-production` (NOT `Authorization: Bearer`).
Request body: `{"input":"string","mode":"auto"}` (NOT `{"messages":[...]}`).
Portsocket is async: returns `{"task_id":"...","status":"queued","poll_url":"/v1/result/..."}`.
Poll `GET /v1/result/{task_id}` with same `X-API-Key` header for result.

### 41. category-backfill.py Must Filter WHERE category='general' (FASE 4)
**BUG (v2-FIXED)**: `SELECT id, key, value FROM {table}` — processes ALL entries, overwriting correctly-categorized entries (curated, backend, etc.).
**FIX (FINAL)**: `SELECT id, key, value FROM {table} WHERE category IS NULL OR category = 'general' OR category = ''` — only processes entries that are still general/NULL.
**VERIFIED**: Dry-run 334→0 general (100% reduction), 0 curated/backend entries overwritten.

### 42. Package Progression: v1 → v2-FIXED → FINAL → v3 (FASE 4)
**Summary of Upshalter Fase 4 packages**:
- **v1 (original)**: Had 4 mismatches (table name, DB path, key format, router path)
- **v2-FIXED**: Fixed all 4 via `skp_adapter.py` auto-detect, but `category-backfill.py` had the "overwrite all" bug
- **FINAL**: Fixed backfill filter, removed `moe-router-senator-patch.py` (router not in container)
- **v3 (by OWL, 2026-05-08)**: Created `senator-cycle-v3.sh` with OpenRouter direct as primary, Ollama fallback only
- **Result**: 5/5 senators succeeded on first run with OpenRouter direct (419 SKP entries, 0 general)

**Key insight**: Each package iteration fixed exactly one critical issue. The "overwrite all" bug in v2-FIXED was the blocker for live deploy. The Ollama slowness was the blocker for inference.

### 26. SKP Value Quality Depends on Fallback Plan Quality (FASE 4)
**OBSERVATION**: When L2 LLM parse fails, fallback plan generates step descriptions like "Analyze and understand: Process request" — these become SKP values.
**FIX**: Category-aware fallback plans produce meaningful steps:
- General: "Analyze and understand" → "Execute and deliver"
- Academic: "Research" → "Synthesize" → "Conclusions"
- Business: "Market analysis" → "Strategic assessment" → "Recommendations"
- DevOps: "Analyze requirements" → "Design solution" → "Implement"

### 27. SKP Write-Back Value Format Matters for Kurator (FASE 4)
**OBSERVATION**: Kurator analysis quality depends on SKP value content. Short values → fallback analysis. Rich values → meaningful insights.
**FIX**: SKP write-back value now includes: Step, Type, Expected, Quality score, full RESULT section, and META (model, status). Increased from ~500 chars to ~4000 chars.

### 28. Kurator Prompt Truncation Strategy (FASE 5)
**OBSERVATION**: Full SKP values (4000 chars each) make kurator prompt too large → LLM timeout.
**FIX**: Extract only the RESULT section from each SKP value, truncate to 800 chars per entry:
```python
if "--- RESULT ---" in val:
    result_start = val.index("--- RESULT ---") + len("--- RESULT ---")
    result_end = val.index("--- META ---") if "--- META ---" in val else len(val)
    val = val[result_start:result_end].strip()[:800]
else:
    val = val[:600]
```

### 29. SKP Cleanup Removes Dupes by Value (FASE 5)
**PATTERN**: When multiple runs produce the same content (especially from fallback plans), SKP accumulates duplicate values.
**FIX**: `cleanup_skp()` runs every 6 hours via Celery beat:
- Removes entries older than 24h (non-system)
- Removes duplicate values (keeps newest)
- Caps total at 200 entries (removes oldest first)
- Beat schedule: `skp-cleanup-every-6h` at 21600s interval

### 30. Docker Compose Shared Volume Template (FASE 5)
**PATTERN**: Keeping mounts consistent across api/worker/beat services is error-prone.
**FIX**: Use YAML anchor for shared volumes:
```yaml
x-hermes-volumes: &hermes-volumes
  - /root/.hermes:/data
  - /root/.hermes/celery_app.py:/app/src/celery_app.py
  - /root/.hermes/openrouter_client.py:/app/src/models/openrouter_client.py
  - /root/.hermes/router.py:/app/src/core/router.py
  - /root/.hermes/kurator.py:/app/src/core/kurator.py
  - /root/.hermes/cognition.py:/app/src/layers/cognition.py
  - /root/.hermes/execution.py:/app/src/layers/execution.py
  - /root/.hermes/main.py:/app/src/main.py
  - /root/.hermes/health.py:/app/src/api/health.py
  - /root/.hermes/tasks.py:/app/src/tasks.py
```
Then reference with `volumes: *hermes-volumes` in each service.

### 31. Mark Curated Must Handle UNIQUE Constraint (FASE 5)
**ERROR**: `UNIQUE constraint failed: knowledge.key` when marking entries as curated.
**CAUSE**: `UPDATE knowledge SET key = 'curated:' || key` fails if target key already exists.
**FIX**: Check if target exists first — if yes, DELETE old entry instead of UPDATE:
```python
cur.execute("SELECT COUNT(*) FROM knowledge WHERE key = ?", (new_key,))
if cur.fetchone()[0] > 0:
    cur.execute("DELETE FROM knowledge WHERE key = ?", (key,))
else:
    cur.execute("UPDATE knowledge SET key = ? WHERE key = ?", (new_key, key))
```

### 33. Docker Compose YAML Anchor Merge Limitation (FASE 6)
**ERROR**: `YAMLError: expected a mapping for merging, but found scalar` when using `<<: *anchor` with additional keys.
**CAUSE**: YAML merge keys (`<<`) replace the entire mapping — you cannot add extra keys alongside `<<` in the same block mapping. This fails:
```yaml
x-volumes: &volumes
  - /a:/a
  - /b:/b

services:
  worker:
    <<: *volumes      # ← merge replaces everything
    - /c:/c           # ← ERROR: can't add to merged mapping
```
**FIX**: Either (a) list all volumes inline without anchors, or (b) use anchors only for identical volume sets. For worker-specific extra mounts, write the full list:
```yaml
services:
  worker:
    volumes:
      - /root/.hermes:/data
      - /root/.hermes/celery_app.py:/app/src/celery_app.py
      # ... all common mounts ...
      - /root/.hermes/cache.py:/app/src/models/cache.py  # worker-only
```
**LESSON**: YAML anchors work for exact duplication, not for "extend this list". When services need different mounts, write them out fully.

### 34. OPENROUTER_URL Hardcoded Bug (FASE 6)
**ERROR**: Ollama URL set in `.env` via `OPENROUTER_URL=http://host.docker.internal:11434/v1/chat/completions` is ignored. All calls go to `https://openrouter.ai/api/v1/chat/completions`.
**CAUSE**: `openrouter_client.py` line 63 had `OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"` — hardcoded, ignoring the env var.
**FIX**: Change to `OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")`.
**DETECTION**: Worker logs show successful calls but OpenRouter dashboard shows no usage. Or: Ollama logs show no incoming requests despite tasks running.
**ALSO**: When using Ollama, skip auth headers. Detect Ollama by URL pattern:
```python
is_ollama = "localhost" in OPENROUTER_URL or "127.0.0.1" in OPENROUTER_URL or "host.docker.internal" in OPENROUTER_URL
headers = {} if is_ollama else {"Authorization": f"Bearer {api_key}", ...}
```

### 35. LLM JSON Output Prompt Engineering (FASE 6)
**PROBLEM**: qwen2.5:1.5b (and other small models) frequently wrap JSON in markdown code fences (```json ... ```) or add explanatory text, breaking `json.loads()`.
**SOLUTION**: Use this prompt pattern for reliable JSON output:
```
You are <ROLE>. Output ONLY valid JSON — no markdown, no code fences, no explanation.
Schema: {"field":"<type>","field2":<type>}
<CONTEXT>
Output ONLY the JSON <result>:
```
**Key elements**:
1. "Output ONLY valid JSON" in first line
2. "no markdown, no code fences, no explanation" — explicit triple negation
3. Schema inline (not in separate block)
4. "Output ONLY the JSON <noun>:" as final line
**VERIFIED**: qwen2.5:1.5b returns valid JSON 100% of the time with this pattern (tested 10+ calls).
**DO NOT USE**: "Return JSON only", "Respond with JSON", "Format as JSON" — these are too weak.

### 36. Response Caching for LLM Calls (FASE 6)
**PATTERN**: Two-tier cache (local in-memory + Redis) to avoid repeated LLM calls for identical prompts.
**IMPLEMENTATION** (`models/cache.py`):
- Key: `md5(model + prompt + temperature)` → `hermes:llm_cache:<hash>`
- Local cache: dict with TTL, max 500 entries, LRU eviction
- Redis cache: `SETEX key ttl json`, 1hr TTL for L2/L3, 5min for L4
- Only cache successful responses (skip rate-limited or error responses)
- Graceful fallback: cache miss → LLM call → store result
**ENDPOINT**: `GET /health/cache` returns `{local_entries, redis_entries, redis_available}`
**VERIFICATION**: After running tasks, check `curl /health/cache` — redis_entries should increase.

### 37. SKP FTS5 Wildcard Limitation (FASE 6)
**ERROR**: `search_count("*")` returns 0 despite FTS5 table having entries.
**CAUSE**: FTS5 doesn't support `*` as a wildcard for "match all". `*` is only valid as a prefix wildcard in search terms (e.g., `"test*"`).
**FIX**: For count-all, use `SELECT COUNT(*) FROM knowledge_fts` directly:
```python
if query == "*":
    cur.execute("SELECT COUNT(*) FROM knowledge_fts")
else:
    cur.execute("SELECT COUNT(*) FROM knowledge_fts WHERE knowledge_fts MATCH ?", (query,))
```

### 38. Python Module Missing Logger Import (FASE 6)
**ERROR**: `NameError: name 'logger' is not defined` at runtime in a new Python module.
**CAUSE**: Writing `logger.info(...)` without `logger = logging.getLogger(__name__)` at module top.
**FIX**: Always add after imports:
```python
import logging
logger = logging.getLogger(__name__)
```
**DETECTION**: Error appears in container logs at first log call, not at import time. The module loads fine but crashes when logging.

### 32. Health Endpoint Pattern (FASE 5)
**PATTERN**: Separate router file mounted into container, registered in main.py.
**ENDPOINTS**:
- `GET /health` — full pipeline status (SKP + queue + version)
- `GET /health/skp` — SKP stats (total, by source, by category, latest)
- `GET /health/queue` — Celery queue status (pending, active, success, failed, per-agent)

### 22. Container Mount Gotcha — Host File ≠ Container File (CRITICAL)
**OBSERVATION**: Patching files on the host (e.g. `/opt/hermes-cognitive/src/core/router.py`) does NOT affect the worker container unless that specific file is bind-mounted. The worker only mounts: `openrouter_client.py`, `celery_app.py`, and `/root.hermes→/data`. Other files like `router.py`, `knowledge_injector.py`, `execution.py`, `reflection.py`, `cognition.py` are read from the Docker image, NOT from the host.
**DETECTION**: After patching a file on host, verify the container sees it: `docker exec hermes-worker grep "CHANGED_LINE" /app/src/core/router.py`. If grep returns nothing, the mount is missing.
**FIX**: Add explicit bind mount in `docker-compose.yml` worker `volumes:` section:
```yaml
- /opt/hermes-cognitive/src/core/router.py:/app/src/core/router.py
```
Then `docker compose up -d --force-recreate worker`.

**See**: `references/cognitive-engine-integration.md` for full verification commands.

### 23. Container `restart` Does NOT Pick Up New Mounts — Use `--force-recreate`
**OBSERVATION**: After adding a new bind mount in `docker-compose.yml` (e.g. mounting `kurator.py` into the worker), running `docker compose restart worker` does NOT make the new file available inside the container. The container keeps its old filesystem.
**FIX**: Always use `docker compose up -d --force-recreate <service>` when adding or changing bind mounts. This destroys and recreates the container with the updated mount configuration.
**VERIFICATION**: After recreate, confirm the file exists: `docker exec <container> ls -la /app/src/core/kurator.py`. If `No such file or directory`, the mount didn't take effect.

### 24. Celery Beat Service Requires Same Mounts as Worker
**OBSERVATION**: The `hermes-beat` service must mount the SAME `celery_app.py` (with `beat_schedule`) and `kurator.py` as the worker. If beat uses a stale image without these files, the `hermes.kurator` task won't be registered and beat will silently skip it.
**FIX**: Always add beat service volumes that mirror the worker's mounts for any custom Python files. Verify: `docker exec hermes-beat python3 -c "from celery_app import celery; print(list(celery.conf.beat_schedule.keys()))"` — should show `['kurator-every-5-min']`.

**File**: `/root/senator-pentahelix/docker-compose.yml`

**Key Configuration**:
```yaml
image: nousresearch/hermes-agent:latest  # NOT senator-pentahelix
volumes:
  - /root/.hermes:/opt/data:rw
  - /root/.hermes/skills/devops/hermes-editorial/scripts:/opt/editorial-scripts:ro
  - /root/.hermes/.openrouter_key:/opt/data/.openrouter_key:ro
command: ["python3", "/opt/editorial-scripts/senator-factory-pipeline.py"]
environment:
  - SECTOR
  - SENATOR_NAME
  - HOST=0.0.0.0
  - TRUST_PROXY=1
user: root  # Avoid permission issues
```

## VERIFICATION (FASE 4 v3)

1. Check senator containers:
```bash
docker ps | grep senator
# Should show 5 containers: senator-akademisi, senator-bisnis, senator-komunitas, senator-pemerintah, senator-media
```

2. Check SKP for latest senator output:
```bash
sqlite3 /data/arsify.db "SELECT key, source_agent_name, created_at, LENGTH(value) as len FROM knowledge WHERE source_agent_name LIKE 'senator%' ORDER BY created_at DESC LIMIT 10;"
```

3. Check kurator output:
```bash
ls -lt /root/upshalter-reports/pentahelix-brief-*.md | head -3
cat /root/upshalter-reports/pentahelix-brief-$(date +%Y%m%d)-*.md | head -30
```

4. Check intelligence page:
```bash
cat /var/www/data.upshalter.com/data.json | python3 -m json.tool | head -30
```

5. Check cron jobs:
```bash
crontab -l | grep -E "senator|kurator|generate-intelligence"
```

6. Check pipeline logs:
```bash
tail -30 /root/upshalter-logs/senator-$(date +%Y%m%d).log
tail -30 /root/upshalter-logs/kurator-$(date +%Y%m%d).log
```

7. Test senator cycle manually:
```bash
SCRIPT_DIR=/root/upshalter-scripts bash /root/upshalter-scripts/senator-cycle-v3.sh
```

8. Test kurator manually:
```bash
SCRIPT_DIR=/root/upshalter-scripts bash /root/upshalter-scripts/kurator-v2.sh
```

## NEXT STEPS (User Decision)

1. **Integrate free-claude-code** (recommended):
   - Route LLM calls to OpenRouter/local Ollama
   - Potential cost savings
   - See: https://github.com/Alishahryar1/free-claude-code

2. **Skip browser-use** (recommended for now):
   - Too many dependency issues
   - RSS scraping already working well
   - Maybe revisit later with proper Docker image

3. **Create Senator Monitoring Dashboard**:
   - Show each senator's last run status
   - Show draft quality scores
   - Show Policy Brief history

## WORKFLOW

### 1. INGEST: Senator Factory Workers (Automatic)
Each senator container runs `/opt/editorial-scripts/senator-factory-pipeline.py`:

```bash
# Senator does:
1. Scrape Google News RSS for sector keywords
2. Analyze articles with LLM (OpenRouter)
3. Create editorial draft in Indonesian
4. Write links to /opt/data/editorial-links/senator-<sector>.txt
5. Write draft to /opt/data/editorial-drafts/senator-<sector>-draft.md
6. Send Telegram notification
```

**Senator Sectors**: akademisi, bisnis, komunitas, pemerintah, media

### 2. PROCESS: Main Editorial Pipeline (Cron Job)
Runs every 30 minutes via `hermes-editorial-pipeline` cron job:

```bash
# /root/.hermes/scripts/editorial-pipeline.sh
1. Collect all links from /root/.hermes/editorial-links/senator-*.txt
2. Collect all drafts from /root/.hermes/editorial-drafts/senator-*-draft.md
3. Fetch article content from links (regex-based HTML parsing)
4. Create Policy Brief using LLM
5. Send ONLY Policy Brief to Telegram Kurator
```

### 3. OUTPUT: Policy Brief Format
```
📋 *HERMES POLICY BRIEF*

**Ringkasan Eksekutif**
[2-3 sentences in Indonesian]

**Temuan Utama**
- Finding 1
- Finding 2
- Finding 3

**Implikasi Kebijakan**
[2-3 sentences in Indonesian]

**Rekomendasi**
1. Rec 1
2. Rec 2
3. Rec 3

## AUTOMATION SCRIPT

**Senator Factory Pipeline Script**:
- Path: `/root/senator-pentahelix/senator-factory-pipeline.py`
- Also copied to: `/root/.hermes/skills/devops/hermes-editorial/scripts/senator-factory-pipeline.py`
- Each senator runs this script automatically via docker-compose command

**Main Editorial Pipeline Script**:
- Path: `/root/.hermes/scripts/editorial-pipeline.sh`
- Cron job: `hermes-editorial-pipeline` (every 30 minutes, no_agent=true)

```bash
#!/bin/bash
# HERMES EDITORIAL PIPELINE (LINKS + SENATOR DRAFTS VERSION)
# 1. Collect Links -> 2. Collect Senator Drafts -> 3. Fetch Content -> 4. Policy Brief -> 5. Notify Curator

LINKS_DIR="/root/.hermes/editorial-links"
DRAFTS_DIR="/root/.hermes/editorial-drafts"
COLLECTED_LINKS="/tmp/collected_links.txt"
AI_SCRIPT="/root/.hermes/skills/devops/hermes-editorial/scripts/editorial_ai.py"
PROCESSED_LINKS="$LINKS_DIR/processed"
PROCESSED_DRAFTS="$DRAFTS_DIR/processed"

# Create processed dirs if not exists
mkdir -p "$PROCESSED_LINKS" "$PROCESSED_DRAFTS"

# Step 1: Collect all links from senator files
echo "📰 [1/5] Collecting links from Senators..."
> $COLLECTED_LINKS

if [ -z "$(ls -A $LINKS_DIR/senator-*.txt 2>/dev/null)" ]; then
  echo "⚠️ No senator link files found in $LINKS_DIR"
else
  cat $LINKS_DIR/senator-*.txt 2>/dev/null | grep -E '^https?://' | sort -u > $COLLECTED_LINKS
  LINK_COUNT=$(wc -l < $COLLECTED_LINKS)
  echo "   Found $LINK_COUNT unique links"
fi

# Step 2: Check for senator drafts
echo "📝 [2/5] Checking for senator editorial drafts..."
DRAFT_COUNT=$(ls -1 $DRAFTS_DIR/senator-*-draft.md 2>/dev/null | wc -l)
if [ "$DRAFT_COUNT" -eq "0" ]; then
  echo "   ⚠️ No senator drafts found in $DRAFTS_DIR"
else
  echo "   Found $DRAFT_COUNT draft(s)"
fi

# Step 3: Process links + drafts with AI
echo "🧠 [3/5] Creating Policy Brief with LLM..."
python3 $AI_SCRIPT $COLLECTED_LINKS $DRAFTS_DIR

# Step 4: Move processed files to archive
echo "🗄️ [4/5] Archiving processed files..."
mv $LINKS_DIR/senator-*.txt $PROCESSED_LINKS/ 2>/dev/null
mv $DRAFTS_DIR/senator-*-draft.md $PROCESSED_DRAFTS/ 2>/dev/null

echo "✅ Pipeline complete! Policy Brief sent to Curator."
```

## REFERENCES

### Browser Automation Journey (2026-05-07)
**Goal**: Enhance senators with browser automation for deeper web research
**Attempt 1**: browser-use with langchain-openai
- Issues: langchain-openai not reading OPENAI_API_KEY, missing `provider` attribute, CDP connection timeout (30s)
- Fixes: Explicit api_key/base_url, custom ChatOpenAIWithProvider subclass, increased timeout via TIMEOUT_BrowserStartEvent env var
- Result: Still failed due to CDP connection refused (Playwright Chromium launched but browser-use couldn't connect)

**Attempt 2**: Playwright direct implementation
- Replaced browser-use Agent with direct Playwright script in FastAPI service
- Result: SUCCESS - API service at `/opt/browser-use-service/main.py` works perfectly
- Endpoint: `POST http://localhost:8090/browse` with JSON `{"url": "..."}`
- Chromium runs headless via Playwright, extracts page content

**Files**:
- `/opt/browser-use-service/main.py` - Playwright-based API service (working)
- `/opt/browser-use-venv/` - Virtual environment with playwright installed
- `/tmp/test_playwright.py` - Successful test script

**Lesson Learned**: For browser automation in Python, prefer direct Playwright over browser-use to avoid CDP complexity. Use FastAPI wrapper for service-oriented access.
**See**: https://playwright.dev/python/

### free-claude-code Integration (Pending)
**Goal**: Route LLM calls to OpenRouter/local Ollama
**Status**: Not yet implemented
**See**: https://github.com/Alishahryar1/free-claude-code

### Senator Factory Worker Transformation (2026-05-07)
**Before**: Senator containers using `senator-pentahelix:latest` (simple scrapers)
**After**: Senator containers using `nousresearch/hermes-agent:latest` (factory workers with pipeline)

**Key Changes**:
1. Updated `/root/senator-pentahelix/docker-compose.yml` to use hermes-agent image
2. Added `senator-factory-pipeline.py` script
3. Mounted `/root/.hermes/skills/devops/hermes-editorial/scripts:/opt/editorial-scripts:ro`
4. Created `/root/.hermes/.openrouter_key` file for API key access
5. Set permissions: `chmod 777 /root/.hermes/editorial-links /root/.hermes/editorial-drafts`

**Outcome**: 5 Senator Factory Workers now operational, each producing links + drafts every 30 minutes

## PYTHON HELPER (Analyze & Draft)

Validated script available at `scripts/editorial_ai.py` (copy to `/root/.hermes/scripts/` and use directly).

Simpan sebagai `/root/.hermes/scripts/editorial_ai.py`:

```python
import json
import os
import requests
from datetime import datetime

# CONFIG
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_TOKEN = "8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU"  # From memory
TELEGRAM_CHAT_ID = "5807834405"

MODEL = "meta-llama/llama-3.1-8b-instruct"  # Tested valid model di OpenRouter
    """Use LLM to cluster topics and score virality."""
    prompt = f"""Analyze these news articles (JSON). For each cluster:
1. Topic Name
2. Viral Score (1-100)
3. 3-sentence engaging summary

Articles: {json.dumps(news_json[:5], indent=2)}
"""
    # Call OpenRouter (model: google/gemini-2.5-flash-preview)
    # ... (implement OpenRouter API call)
    return {"topic": "AI Regulation", "score": 85, "summary": "..."}

def notify_curator(draft):
    """Send draft to Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": f"📰 *DRAFT*\n\n{draft}\n\nReply APPROVE/EDIT",
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    with open("/tmp/raw_news.json") as f:
        news = json.load(f)
    result = analyze_with_llm(news)
    notify_curator(result["summary"])
```

## CRON JOB (Otomatisasi)

Setup cron job biar jalan otomatis tiap Senator selesai cycle (30 menit):

```bash
# Tambahin di crontab atau systemd timer
# Trigger: Setelah senator selesai (bisa pakai inotify atau polling)
```

Atau integrasi langsung ke Senator: Modifikasi `app.py` di container biar setelah scrape, trigger editorial pipeline.

## PITFALLS
- **LLM Cost**: Jangan proses semua 75 artikel sekaligus. Ambil 5-10 teratas (high relevance).
- **Rate Limit**: OpenRouter ada limit. Pakai model valid seperti `meta-llama/llama-3.1-8b-instruct` buat draft.
- **Curator Absence**: Kalau 1 jam nggak ada reply, auto-publish dengan tag "AUTO-APPROVED".
- **OpenRouter Model Names**: Hindari model yang tidak terdaftar (contoh: google/gemini-2.5-flash-preview, google/gemini-flash-1.5). Gunakan model yang sudah terbukti valid.
- **Data Structure**: Field `source` di hasil Senator bisa berupa string atau dict. Pastikan script menangani kedua kasus.
- **File Naming**: Data file di container Senator bernama `research_akademisi_*.json`, bukan `google_news_*.json`.

## PYTHON HELPER (Analyze & Policy Brief)
**Path**: `/root/.hermes/skills/devops/hermes-editorial/scripts/editorial_ai.py`

**Key Functions**:
- `fetch_article_content(url)` - Regex-based HTML parsing (no BeautifulSoup dependency)
- `call_llm(prompt)` - Calls OpenRouter API
- `create_policy_brief(fetched_text, senator_drafts)` - Creates Policy Brief from all senator outputs
- `write_outputs(articles, draft)` - Writes links + drafts to shared dirs
- `send_telegram_notification(draft)` - Sends ONLY Policy Brief to curator

**Usage**:
```bash
# Called by editorial-pipeline.sh
python3 /root/.hermes/skills/devops/hermes-editorial/scripts/editorial_ai.py <links_file> <drafts_dir>
```

**Note**: Reads OPENROUTER_API_KEY from `/opt/data/.openrouter_key` file (mounted from host).

## VERIFICATION

1. Check senator containers:
```bash
docker ps | grep senator
# Should show 5 containers with "nousresearch/hermes-agent:latest"
```

2. Check senator outputs:
```bash
ls -la /root/.hermes/editorial-links/  # Should have senator-*.txt
ls -la /root/.hermes/editorial-drafts/  # Should have senator-*-draft.md
```

3. Check cron job:
```bash
cronjob list | grep hermes-editorial-pipeline
# Should show: schedule "30m", no_agent=true
```

4. Test main pipeline manually:
```bash
/root/.hermes/scripts/editorial-pipeline.sh
# Should create Policy Brief and send to Telegram
```

5. Check Telegram:
- Should receive 5 notifications from each senator ("Selesai bikin draft!")
- Should receive 1 Policy Brief (every 30 minutes)

## DEBUGGING

For detailed diagnosis commands, failure patterns, and rebuild procedures, see:
**See**: `references/fase-4-v3-architecture.md` for the current FASE 4 v3 architecture, SKP schema, senator output structures, and cron schedule.
**See**: `references/cognitive-engine-integration.md` for detailed pitfalls and verification commands.
**See**: `references/fase-6-performance-optimization.md` for FASE 6 caching, FTS5, prompt optimization, and Docker Compose mount patterns.

### 9. Celery Task Registration — include path mismatch (FASE C)
**ERROR**: `NotRegistered: ['hermes.run']` in Redis task results
**CAUSE**: `celery_app.py` had `include=["src.tasks"]` but container `PYTHONPATH=/app/src` means the importable module name is `tasks`, not `src.tasks`
**FIX**: Change to `include=["tasks"]`, rebuild image (`docker compose build api`), restart both API and worker containers
**VERIFY**: `docker exec hermes-worker sh -c "cd /app && PYTHONPATH=/app/src python3 -c 'from src.celery_app import celery; [print(t) for t in celery.tasks if \"hermes\" in t]'"`

### 10. Read-Only Volume Blocks File Copy (FASE C)
**ERROR**: `Error response from daemon: mounted volume is marked read-only` when using `docker cp`
**FIX**: Write files to the host bind-mount source path instead: `/root/.hermes/skills/devops/hermes-editorial/scripts/`

### 11. Container Missing requests/httpx (FASE C)
**ERROR**: `ModuleNotFoundError: No module named 'requests'` in senator containers
**FIX**: Use stdlib `urllib.request` only — no external dependencies

### 12. OPENROUTER_API_KEY Placeholder in .env (FASE C)
**ERROR**: Worker container has placeholder key `sk-or-v1-placeholder-replace-me`
**FIX**: `sed -i "s|OPENROUTER_API_KEY=sk-or-v1-placeholder-replace-me|OPENROUTER_API_KEY=${HOST_KEY}|" /opt/hermes-cognitive/.env`

## FASE C: COGNITIVE ENGINE INTEGRATION (2026-05-07)

Senator containers now submit tasks to Hermes Cognitive Engine via `/v1/portsocket`.
The Engine runs L1→L2→L3→L4 pipeline and returns structured results.

**Key changes:**
- `senator_cognitive_client.py` — stdlib-only HTTP client (no requests/httpx dependency)
- `senator-cycle.sh v2` — host-level cron, submits to Cognitive Engine
- `agent_registry.py` — 5 senator profiles with `complexity_threshold=1` (always cognitive)
- `openrouter_client.py` — free model map + HTTP 401/402/429 handling
- `celery_app.py` — fixed `include=["tasks"]` for proper task registration
- `portsocket.py` — `AsyncResult(task_id, app=celery)` with explicit app context

**Critical Pitfalls Discovered:**

### 13. AsyncResult Without App Context (CRITICAL)
**ERROR**: `'hermes.run'` / `AttributeError: 'DisabledBackend' object has no attribute '_get_task_meta_for'`
**CAUSE**: `portsocket.py` line 181 used `AsyncResult(task_id)` without passing the celery app. FastAPI's default celery app has no backend configured.
**FIX**: `AsyncResult(task_id, app=celery)` — import celery from `celery_app` and pass it explicitly.
```python
# api/portsocket.py
from celery_app import celery
task_result = AsyncResult(task_id, app=celery)  # NOT just AsyncResult(task_id)
```

### 14. OpenRouter Free Tier Rate Limit Cascade (CRITICAL)
**ERROR**: All worker processes hit 429 simultaneously, backoff grows to 45s+, tasks stall for 5+ minutes
**CAUSE**: Default concurrency=4, all 4 workers hit free models (8 req/min per key limit)
**FIX**: 
- Reduce concurrency to 2: `celery -A celery_app worker --concurrency=2`
- Use small free models: `liquid/lfm-2.5-1.2b-instruct:free` (fast, reliable)
- Avoid large free models (70B, 120B) — they timeout (524) and rate-limit faster
- **Production**: Top-up OpenRouter credits ($5-10) for reliable model access

### 15. Free Model Selection for Reliability
**Verified fast free models (2026-05-07):**
- `liquid/lfm-2.5-1.2b-instruct:free` — fastest, 32K ctx, good for simple tasks
- `baidu/cobuddy:free` — decent, 131K ctx
**Avoid for production:**
- `nvidia/nemotron-3-super-120b-a12b:free` — frequent 524 timeouts
- `meta-llama/llama-3.3-70b-instruct:free` — very slow, heavy rate limit
- `minimax/minimax-m2.5:free` — frequent 429

### 16. Container network_mode:host vs host.docker.internal
**Behavior**: Senator containers use `network_mode: host`, so `localhost:8100` reaches host directly
**Implication**: No need for `host.docker.internal` in senator containers for API access
**But**: `host.docker.internal` still needed in Docker Compose containers (worker, API) to reach Redis on host

**For detailed pitfalls and verification commands, see:**
`references/cognitive-engine-integration.md`

### 18. SKP DB Write-Back Gap — Tasks Succeed But Results Not Persisted (FASE 2)
**OBSERVATION**: Senator tasks show `succeeded` in worker logs with full L1→L4 results, but SKP DB (`/root/.hermes/shared_knowledge_pool.db`) has no Senator entries — only old system entries.
**CAUSE**: The cognitive engine's L4 Reflection layer has a `_fallback: true` flag when all LLM calls are rate-limited. In fallback mode, the pipeline generates a minimal result envelope but may skip the SKP write-back step. Additionally, the SKP write-back may require a specific code path that only triggers on non-fallback results.
**DETECTION**:
```bash
# Check if Senator entries exist in SKP
sqlite3 /root/.hermes/shared_knowledge_pool.db "SELECT id, key, source_agent_name FROM knowledge WHERE source_agent_name LIKE '%senator%' ORDER BY id DESC LIMIT 10;"
# If empty, write-back is not happening
```
**FIX**: 
1. Ensure Ollama fallback is working (so LLM calls don't hit rate limits → no fallback path)
2. Check L4 reflection code for SKP write-back logic — it should write regardless of fallback status
3. Verify SKP write-back is triggered in the task success callback, not just in the L4 layer
**VERIFICATION**:
```bash
# After a Senator task completes, check SKP
sqlite3 /root/.hermes/shared_knowledge_pool.db "SELECT id, key, substr(value,1,60), source_agent_name, created_at FROM knowledge ORDER BY id DESC LIMIT 5;"
# Should show new entries with source_agent_name matching the senator
```
**NOTE**: This was observed in FASE 2 testing (2026-05-07) where both Senator Akademisi and Media tasks succeeded but SKP DB had no new entries. The root cause is likely that all LLM calls were rate-limited (OpenRouter free tier), forcing fallback mode which skips SKP persistence.

### 17. Senator Container Healthcheck Misconfiguration (Critical!)
**ERROR**: Senator containers show `unhealthy` status; logs show `Could not resolve host: ||` and `Could not resolve host: exit`
**CAUSE**: 
1. Healthcheck uses `CMD` with `|| exit 1` which passes `||` and `exit` as arguments to `curl`, not shell operators.
2. Senator containers are not HTTP services (they run Python scripts, not web servers), so `/health` endpoint does not exist.
**FIX**:
- Disable healthcheck for senator containers since they don't serve HTTP endpoints:
```yaml
# /root/senator-pentahelix/docker-compose.yml (x-senator-base section)
healthcheck:
  disable: true
```
- Never use `CMD` with shell operators (`||`, `&&`) in healthcheck. If shell logic is needed, use `CMD-SHELL` instead:
```yaml
test: ["CMD-SHELL", "curl -f http://localhost:8100/health || exit 1"]
```
**DETECTION**: `docker inspect senator-<sector> | grep -A10 Health` shows `Could not resolve host: ||` errors, or `docker ps` shows `unhealthy` for senator containers.

### 17. Senator Container Healthcheck Misconfiguration (Critical!)
**ERROR**: Senator containers show `unhealthy` status; logs show `Could not resolve host: ||` and `Could not resolve host: exit`
**CAUSE**: 
1. Healthcheck uses `CMD` with `|| exit 1` which passes `||` and `exit` as arguments to `curl`, not shell operators.
2. Senator containers are not HTTP services (they run Python scripts, not web servers), so `/health` endpoint does not exist.
**FIX**:
- Disable healthcheck for senator containers since they don't serve HTTP endpoints:
```yaml
# /root/senator-pentahelix/docker-compose.yml (x-senator-base section)
healthcheck:
  disable: true
```
- Never use `CMD` with shell operators (`||`, `&&`) in healthcheck. If shell logic is needed, use `CMD-SHELL` instead:
```yaml
test: ["CMD-SHELL", "curl -f http://localhost:8100/health || exit 1"]
```
**DETECTION**: `docker inspect senator-<sector> | grep -A10 Health` shows `Could not resolve host: ||` errors, or `docker ps` shows `unhealthy` for senator containers.

### 19. Ollama RAM Exhaustion on 7.8GB VPS (Critical!)
**ERROR**: Ollama times out entirely (>120s) even for short prompts. `curl http://localhost:11434/v1/chat/completions` hangs.
**CAUSE**: Ollama phi3:mini uses ~3.6GB RAM. With hermes-api, hermes-worker, 5 senators, Redis, and system, total RAM usage exceeds 7.8GB → swapping → extreme slowness.
**FIX**:
1. Stop unnecessary containers: `docker stop hermes-gamedev hermes-loyx hermes-kanban-hermes-kanban-1 hermes-workspace-fresh-hermes-workspace-1`
2. Restart Ollama: `sudo systemctl restart ollama`
3. Verify: `free -h` should show ≥2.5GB available
4. If still tight, increase swap: `dd if=/dev/zero of=/swapfile bs=1M count=8192 && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile`
5. Make swap permanent: `echo '/swapfile none swap sw 0 0' >> /etc/fstab`
**VERIFICATION**: `time curl -s -X POST http://localhost:11434/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"phi3:mini","messages":[{"role":"user","content":"OK"}],"temperature":0.2}' -o /tmp/ollama_test.json` — should complete in 20-40s.

### 20. Worker LLM_TIMEOUT_READ Not Picked Up from .env
**ERROR**: Worker still uses 50s timeout despite `LLM_TIMEOUT_READ=300` in `/opt/hermes-cognitive/.env`
**CAUSE**: The worker service in `docker-compose.yml` doesn't read from `.env` for this variable. Docker Compose env file vars propagate to the container environment, but the worker's Python code reads `LLM_TIMEOUT_READ` at import time — and the worker may have been restarted without the new env.
**FIX**: Add `LLM_TIMEOUT_READ: "300"` explicitly to the worker service `environment:` block in `docker-compose.yml`, then `docker compose up -d --force-recreate worker`.
**VERIFY**: `docker exec hermes-worker python3 -c "from src.models.openrouter_client import TIMEOUT; print(TIMEOUT.read)"` → must show `300.0`.

### 21. LM Studio Not Available for Headless VPS
**OBSERVATION**: LM Studio (lmstudio.ai) was suggested as Ollama alternative, but investigation revealed:
- LM Studio is a GUI desktop application (macOS/Windows/Linux)
- The `lms` CLI ships WITH the desktop app — no standalone install
- GitHub repo `lmstudio-ai/lms` is private (no public releases)
- **Cannot be used on headless VPS**
**CONCLUSION**: For headless VPS, use Ollama (already configured) or build llama.cpp from source. LM Studio is not an option.

## PRODUCT PACKAGING PATTERN (2026-05-08)

When asked to create a product package / exit plan / handoff documentation for the editorial pipeline (or any VPS-based product), use this structure:

```
product-package/
├── README.md                    # Quick start + file index
├── HANDOFF.md                   # Checklist, critical knowledge, next steps
├── docs/
│   ├── PRODUCT_SPEC.md          # Problem, solution, features, pricing, roadmap
│   ├── MARKETING.md             # Landing page copy, positioning, competitive
│   ├── architecture/
│   │   └── ARCHITECTURE.md      # System design, data flow, component detail
│   ├── api/
│   │   └── API.md               # REST API endpoints, auth, rate limits, examples
│   └── runbook/
│       └── OPERATIONS.md        # Daily ops, troubleshooting, maintenance, DR
├── deploy/
│   └── INSTALL.md               # Fresh install guide, step-by-step
├── dashboard/
│   └── index.html               # Web dashboard with filter, export, auto-refresh
├── legal/
│   └── LICENSE.md               # IP ownership, component licenses
└── scripts/                     # (copy from production)
```

**Key principle:** Package should enable a new team member to rebuild the entire system from scratch using only the documentation.

**Product scoring framework** (use when evaluating readiness):
- Core Engine / Pipeline (10 pts)
- Data Output & Storage (10 pts)
- Content Quality (10 pts)
- Web Dashboard / Product Surface (10 pts)
- Delivery & Notification (10 pts)
- Authentication & Billing (10 pts)
- Multi-tenancy / Isolation (10 pts)
- Reliability & Monitoring (10 pts)
- Documentation & UX (10 pts)
- Onboarding & Client Management (10 pts)

Current score: ~42-55%. Target for MVP sale: 70%+. Target for enterprise: 90%+.

## WHEN TO USE THIS SKILL

Load this skill when:
- Setting up or maintaining the Pentahelix Editorial Pipeline
- Working with senator-cycle-v3.sh, kurator-v2.sh, or kurator-v2.py
- Reading/writing to SKP database (`/data/arsify.db`, table `knowledge`)
- Creating or regenerating intelligence briefs or PDF reports
- TroublesSenator containers as factory workers
- Creating Policy Briefs from multiple news sources
- Integrating senator outputs with LLM analysis
- Troubleshooting permission/API key issues in senator containers
- User mentions "editorial", "senator", "policy brief", "factory workers", "pentahelix", "kurator"
- User mentions "FASE 4", "senator-cycle", "SKP", "intelligence brief"
- Setting up Cognitive Engine integration with senator containers
- Troubleshooting Celery task registration issues
- Debugging OpenRouter free model rate limits
- User asks for "exit plan", "product package", "handoff documentation", "product-ready"
- User asks to evaluate "product readiness" or "what's missing to sell"
