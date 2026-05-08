---
name: hermes-intelligence-pipeline
description: "Build automated intelligence/reporting pipelines using Hermes Cognitive Engine, SKP database, and multi-agent workflows (Senators, Kurators). Covers the full stack: task submission, result polling, report generation, subscriber delivery, and cron automation."
trigger:
  - "buatkan intelligence platform"
  - "setup senator automation"
  - "kurator review system"
  - "subscriber delivery system"
  - "automated reporting pipeline"
  - "PRD intelligence platform"
---

# Hermes Intelligence Pipeline

Build end-to-end intelligence automation: agents produce insights → curators consolidate → reports delivered to subscribers.

## Architecture

```
Senator (5 domains) → Cognitive Engine → SKP Database
                                    ↓
                            Kurator Agent
                                    ↓
                            Report Generation
                                    ↓
                            Subscriber Delivery (Telegram/Email)
```

## Arsify Documentation Context

The Arsify v0.1.1 final package at `/root/arsify-final-package_v0.1.1/` contains the **authoritative architecture documentation**. Before implementing any enhancement, check these docs:

- **3-Zone Architecture** (Plaza / Buffer / Core): `documentation/architecture-3zones.md` — partially implemented
- **Self-Learning / RAG**: `documentation/self-learning-architecture.md` + `documentation/rag-implementation.md` — targets LanceDB + Flowise. **NOT implemented** (LanceDB not installed). Target Q3 2026.
- **Skills Catalog**: `documentation/skills-catalog.md` — Sync_Vector_Memory, Inject_WS_Proxy, WA_Bridge_Resuscitate. **NOT implemented**.
- **Skill Monitoring**: `documentation/skill-monitoring.md` — JSONL logs + Telegram alerts. **NOT implemented**.

**Key principle**: The documented approach is vector-based (semantic search via LanceDB). When prerequisites are missing, use keyword-based as a stepping stone but plan migration. See `references/arsify-documentation-map.md` for full gap analysis.

## Core Patterns

### 1. Cognitive Engine Integration

Submit tasks and poll for results (reusable pattern):

```bash
# Submit task
TASK_RESPONSE=$(curl -s --max-time 10 \
    -X POST "${COGNITIVE_URL}/v1/portsocket" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${HERMES_KEY}" \
    -H "X-Agent-ID: ${agent_id}" \
    -d "{\"input\": $(echo "$INPUT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}" 2>&1)

TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('task_id',''))" 2>/dev/null)

# Poll for result (max 10 min)
for i in $(seq 1 60); do
    sleep 10
    RESULT=$(curl -s --max-time 5 \
        "${COGNITIVE_URL}/v1/result/${TASK_ID}" \
        -H "X-API-Key: ${HERMES_KEY}" 2>&1)
    
    STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
    
    if [ "$STATUS" = "SUCCESS" ]; then
        CONTENT=$(echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
r = d.get('result', {})
if isinstance(r, dict):
    results = r.get('results', [])
    if results:
        step = results[0]
        exec_data = step.get('execution', {})
        print(exec_data.get('content', ''))
" 2>/dev/null)
        break
    elif [ "$STATUS" = "FAILURE" ]; then
        echo "Task failed: $RESULT"
        exit 1
    fi
done
```

**Config:**
- `COGNITIVE_URL="http://host.docker.internal:8100"` (from container)
- `HERMES_KEY="hermes-secret-change-me-in-production"`

### 2. Senator Cycle Script

Key elements for `senator-cycle.sh`:
- Run 5 senators independently (failure doesn't block others)
- Per-senator logging: `/opt/data/editorial-logs/senator-${sector}-$(date +%Y%m%d).log`
- Kanban integration (optional): `hermes kanban create "task" --assignee senator-X --board research`
- Telegram failure alerts (send notification if senator fails)
- Submit to Cognitive Engine with sector-specific prompts

**Prompt template for senators:**
```
Riset [domain] Indonesia terbaru:
1. Cari berita dan perkembangan terbaru (gunakan web_search)
2. Identifikasi 3-5 temuan penting
3. Simpan ke SKP dengan key '[domain]/temuan/$(date +%Y%m%d-%H)'
4. Berikan rekomendasi untuk [business context]
Jawab dalam bahasa Indonesia dengan format terstruktur.
```

### 3. Kurator Pipeline

The Kurator is a periodic Celery task that reads uncurated SKP entries, synthesizes them via LLM, and writes curated results back.

**Flow:**
1. `fetch_uncurated_entries(limit=10)` — entries where `key NOT LIKE 'kurator:%'` AND `key NOT LIKE 'curated:%'` AND created > 5 min ago
2. Group by `source_agent_name`
3. Build prompt with entries text (extract `--- RESULT ---` section, truncate 800 chars/entry)
4. Call LLM via `call_with_fallback("nemotron", prompt)`
5. Parse JSON response with cascading extraction (strip fences → json.loads → regex → text fallback)
6. Write result: `key = "kurator:{hash}"`, `category = "curated"`, `priority = 9`
7. Mark source entries as curated: `UPDATE knowledge SET key = 'curated:' || key WHERE key = ?`
8. Fallback: if LLM fails, generate simple analysis (confidence 0.5)

**SKP Key Convention:**
| Key Pattern | Meaning |
|---|---|
| `senator-{domain}/execution/{hash}` | Raw Senator output (uncurated) |
| `curated:senator-{domain}/execution/{hash}` | Marked as already curated |
| `kurator:{hash}` | Kurator analysis result |

See `references/kurator-pipeline.md` for full implementation details.

### 4. Subscriber Delivery System

**subscribers.json template:**
```json
{
  "subscribers": [
    {
      "id": "sub001",
      "name": "Client Name",
      "telegram_id": "NUMERIC_ID",
      "tier": "pro",
      "topics": ["akademisi", "bisnis", "komunitas", "pemerintah", "media"],
      "active": true
    }
  ],
  "tiers": {
    "starter": {"price_idr": 2000000, "domains": 2, "delivery": "weekly"},
    "pro": {"price_idr": 5000000, "domains": 5, "delivery": "daily"},
    "enterprise": {"price_idr": 15000000, "domains": "custom", "delivery": "api"}
  }
}
```

**Delivery script must:**
- Check for latest report: `ls -t /root/upshalter-reports/pentahelix-brief-*.md`
- Skip if already delivered: check for `${REPORT}.delivered` flag
- Filter by subscriber tier (starter gets shorter summary)
- Send via Telegram using urllib (avoid subprocess with curl)

### 5. Landing Page Generation

**generate-intelligence-page.py:**
- Read 10 latest insights from SKP
- Check senator status (last update per domain)
- Generate HTML with insight cards, senator status grid, subscription CTA, auto-refresh every 30s
- Output to `/var/www/data.upshalter.com/index.html`
- Also save JSON data to `data.json` for JavaScript

## Cron Job Schedule

```bash
# In crontab -e
0 */6 * * * /root/upshalter-scripts/senator-cycle.sh >> /root/upshalter-logs/senator.log 2>&1
0 1,7,13,19 * * * /root/upshalter-scripts/kurator-review.sh >> /root/upshalter-logs/kurator.log 2>&1
*/30 * * * * /usr/bin/python3 /root/upshalter-scripts/generate-intelligence-page.py >> /root/upshalter-logs/generate-page.log 2>&1
```

## Technical Frameworks

### CRISP-DM Mapping
Map the 5-phase CRISP-DM to Senator→SKP→Kurator flow:
1. Business Understanding: Senator receives domain brief
2. Data Understanding: Senator crawls sources
3. Data Preparation: Clean and structure insights into SKP entries
4. Modeling: Kurator analyzes cross-domain patterns
5. Evaluation: Kurator delivers report, subscribers provide feedback

### SECI Spiral (Nonaka Knowledge Management)
- Socialization: Senators gather raw data → tacit knowledge
- Externalization: Senators write to SKP → explicit knowledge
- Combination: Kurator compiles reports → new explicit knowledge
- Internalization: Subscribers read reports → new tacit knowledge

### Prompt Engineering Techniques
| Technique | Application | Impact |
|-----------|--------------|--------|
| Few-Shot Prompting | Provide 3 example SKP entries → Senator generates similar | Improve SKP structure |
| Chain-of-Thought | "Analyze step-by-step: 1) Read source 2) Extract insight" | Better Kurator reports |
| Role Prompting | "You are Senator Akademisi expert in Indonesian AI" | Better domain focus |
| Constrained Output | "Output JSON with fields: source, insight, confidence" | Structured SKP entries |
| Context Stuffing | Inject Brand Brain into system prompt | Brand-consistent content |

See `references/upshalter-technical-frameworks.md` for full details.

## Product Readiness

**Current Score: 42/100** (audited 8 Mei 2026)

| Dimension | Score | Gap |
|-----------|-------|-----|
| Core Engine / Pipeline | 8/10 | End-to-end works, Orchestrator bypassed |
| Data Output & Storage | 7/10 | 421 entries but 80% un-enriched category |
| Content Quality | 4/10 | Generic output, no real data feed |
| Web Dashboard | 5/10 | Static HTML, no filter/auth/export |
| Delivery & Notification | 4/10 | Only 1 test subscriber, single channel |
| Authentication & Billing | 2/10 | No payment gateway, no per-client API key |
| Multi-tenancy | 2/10 | All shared, no tenant isolation |
| Reliability & Monitoring | 5/10 | Basic checks, no SLA/uptime tracking |
| Documentation & UX | 3/10 | Internal docs only, no client-facing guides |
| Onboarding & Client Mgmt | 2/10 | No self-signup, no client portal |

**MVP-Ready (70%): ~5-7 hari** — prioritize content quality (A), dashboard (B), delivery (D).
**100% Enterprise-Ready: ~12-17 hari** — all phases A→F.

See `references/product-readiness-assessment.md` for full scoring framework, phased roadmap, actual infrastructure snapshot, and pricing tiers.

## Pitfalls

1. **Telegram numeric chat_id** — must be numeric, not @username. Get via `curl https://api.telegram.org/bot${TOKEN}/getUpdates`

2. **Python environment variables in bash** — pass via `export` before heredoc, not inline

3. **Cognitive Engine inside Docker** — use `host.docker.internal:8100`, ensure `extra_hosts: host.docker.internal:host-gateway` in docker-compose.yml

4. **SKP database path** — use symlink: `/data/arsify.db → /root/.hermes/shared_knowledge_pool.db`

5. **Delivery idempotency** — always check/touch `.delivered` flag to avoid duplicate sends

6. **Free model rate limits** — use `concurrency=2` and small models to avoid 429 cascade

7. **Ollama timeout on CPU** — phi3:mini on CPU needs 20s+ for short prompts, 60s+ for long prompts. Set `LLM_TIMEOUT_READ=300` in `.env` AND docker-compose. If Ollama times out entirely, check RAM: `free -h` — Ollama may be OOM-killed.

7a. **Ollama model too slow for complex prompts** — phi3:mini (3.8B) times out on L2 planning prompts. Solutions: (a) pull `qwen2.5:1.5b`, (b) set `OLLAMA_MODEL=qwen2.5:1.5b`, (c) simplify L2 system prompt. Verify with `ollama list`.

7b. **Ollama model name verification** — Free model names from OpenRouter (e.g. `liquid/lfm-2.5-1.2b-instruct:free`) do NOT exist in Ollama. When `OPENROUTER_URL` points to Ollama (port 11434), `MODEL_MAP` and `FREE_MODEL_MAP` MUST use Ollama model names only.

8. **Ollama model name mismatch** — Define `_is_ollama` BEFORE `MODEL_MAP` (not after) to avoid `NameError`.

9. **Container mount vs. file patch gotcha** — Patching a file on the host does NOT affect containers that don't mount that file. Verify: `docker exec <container> python3 -c "import core.router; print(core.router.__file__)"`. If path is `/app/src/core/router.py` (inside image), the host file is NOT being used.

10. **SKP write-back quality threshold mismatch** — Threshold is defined in TWO places: `router.py` (`WRITE_BACK_QUALITY_THRESHOLD`) and `knowledge_injector.py` (`WRITE_BACK_MIN_Q`). Both must be ≤ expected quality score. Set both to 60 for reliable write-back with small models.

11. **SKP_DB_PATH must match worker volume** — Worker mounts `/root/.hermes→/data`, so `SKP_DB_PATH=/data/shared_knowledge_pool.db`.

12. **LM Studio NOT Suitable for Headless VPS** — Use Ollama or llama.cpp instead.

13. **Container `restart` vs `--force-recreate` for Mount Changes** — New bind mounts require `docker compose up -d --force-recreate <service>`. `restart` only restarts with existing mounts.

14. **Celery Beat Setup for Periodic Tasks** — Add `beat_schedule` to `celery_app.py`, add `beat` service in docker-compose with SAME mounts as worker. Beat must mount the SAME `celery_app.py`.

15. **Kurator Pipeline — SKP Curation Pattern** — See pitfall #15 above and `references/kurator-pipeline.md`.

16. **SKP Value Quality Affects Kurator Output** — Ensure L4 execution stores meaningful content, not just "Task completed".

17. **SKP Write-Back Value Format** — Use structured multi-section format with `--- RESULT ---` section (up to 4000 chars).

18. **L2 Fallback Plan — Category-Based Step Generation** — Generate meaningful steps based on category, not a single generic step.

19. **L3 Execution Prompt — Enforce Detailed Output** — "Produce a detailed, substantive output — NOT a summary or placeholder", "Minimum 200 characters".

20. **Kurator LLM Timeout on Long Prompts** — Extract only `--- RESULT ---` section, truncate 800 chars/entry. Reduces prompt from ~15KB to ~4KB.

21. **Kurator asyncio Import Bug** — Ensure `import asyncio` is at the top of kurator.py when using `asyncio.wait_for()`.

22. **Kurator mark_as_curated UNIQUE Constraint Fix** — Check if target key exists first — if yes, DELETE old entry instead of UPDATE.

23. **Kurator/Ollama JSON Parse — Markdown Fence Wrapping** — Ollama models wrap JSON in ` ```json ... ``` ` fences. Use cascading extraction: (a) strip fences, (b) `json.loads()`, (c) regex extraction, (d) text fallback. Same pattern for `parse_kurator_result()` in tasks.py — check nested keys (`analysis`, `result`, `data`).

24. **L2 JSON Parse — 4-Strategy Extraction** — Free LLMs frequently return markdown-wrapped JSON. Use: (1) strip fences + json.loads, (2) regex `r'\{[^{]*"steps"\s*:\s*\[[^\]]*\]'}`, (3) nested `execution_plan.steps` → normalize, (4) parse numbered lists, (5) category-aware fallback.

25. **Docker Compose Shared Volume Anchor** — Use YAML anchor `&hermes-volumes` to keep mounts consistent across api/worker/beat. When adding a new file, add it to BOTH the anchor AND all services.

26. **Health Endpoint Pattern** — Separate `api/health.py` router with `/health`, `/health/skp`, `/health/queue`, `/health/cache` endpoints.

27. **Ollama OPENROUTER_URL Env Var** — Set `OPENROUTER_URL=http://host.docker.internal:11434/v1/chat/completions` and `OLLAMA_MODEL=qwen2.5:1.5b`. Client auto-detects Ollama by checking URL for `localhost`/`127.0.0.1`/`host.docker.internal`.

28. **LLM Response Caching — 2-Tier** — In-memory dict (~500 entries) + Redis (shared, configurable TTL). Key: MD5 of `model + prompt + temperature`. Only caches successful responses.

29. **SQLite FTS5 Full-Text Search** — `knowledge_fts` virtual table with auto-sync triggers. Endpoint: `GET /search?q=query`. FTS5 doesn't support `*` wildcard.

30. **Prompt Optimization for Reliable JSON** — Put schema INLINE, use "Output ONLY the JSON" as final line, no `indent=2`, `temperature=0.3` for planning.

31. **tasks.py Logger Import Bug** — `logger = logging.getLogger(__name__)` MUST be at module level before any function uses it.

32. **SKP Cleanup Periodic Task** — Add `skp-cleanup-every-6h` to beat schedule. Removes entries older than 24h, deduplicates, caps at 200 total.

33. **Enrichment: Check Arsify Docs First** — Before implementing category/tag enrichment, check `/root/arsify-final-package_v0.1.1/`. The documented approach is vector-based (LanceDB + Flowise RAG). If LanceDB not available, keyword-based is acceptable as stepping stone. Document the gap. See `references/arsify-documentation-map.md`.

33a. **Fase 4 Enrichment — category_enrichment.py Exists But Never Run** — The file `/root/.hermes/category_enrichment.py` (529 lines) has full keyword-based classification + tag generation but has **never been executed**. Before writing new enrichment code, run the existing script. Schedule it via cron or Celery beat. See `references/fase-4-enrichment.md` for the full pre-implementation snapshot, domain mapping, and verification commands.

33b. **Fase 4 Dry-Run: Only 65 of 334 General Entries Are Enrichable** — Running `backfill_general_entries(dry_run=True)` returns only **65** targets (raw senator entries with `key NOT LIKE 'curated:%'`). The other **269** "general" entries have `curated:*` keys — excluded by design because Kurator already processed them, but Kurator v1 incorrectly sets `category = "general"` on curated output. Impact: running j3 alone only improves general from 80.7% → 65.0% (-15.7pp). To reach <30% target, **must fix Kurator v2 (j6) to properly categorize curated entries**, then re-run enrichment. See `references/fase-4-enrichment.md` §Dry-Run Results for the full breakdown (policy:20, media:19, business:10, community:7, research:4, education:3, finance:1, digital-gov:1).

33c. **Fase 4 Dedup (j5) Requires scikit-learn** — `pip install scikit-learn` is NOT installed on host (verified 8 Mei 2026). TF-IDF + cosine similarity for content-based dedup is impossible without it. Install before starting j5. Naive string matching is possible but far less accurate.

33d. **Container File Access Gotcha for category_enrichment.py** — The file lives at `/root/.hermes/category_enrichment.py` on the host but is NOT accessible at that path inside hermes-worker container. Must either: (a) `docker cp /root/.hermes/category_enrichment.py hermes-worker:/tmp/` then exec from `/tmp/`, or (b) access via the volume mount at `/data/` (symlink `/data/arsify.db` exists but not the `.py` files).

33f. **Ollama CPU-Only Is Too Slow for Production (8 Mei 2026)** — Ollama on 2-core CPU-only VPS takes 39s to load model + >60s for inference. ALL client timeouts (20s, 60s, 90s) are exceeded. Ollama is NOT viable as primary LLM endpoint. **FIX**: Use OpenRouter API direct (`https://openrouter.ai/api/v1/chat/completions` with `Authorization: Bearer <key>`) as primary. Verified 5/5 senators succeed via OpenRouter direct (senator-cycle-v3.sh). Hermes API :8100 `/chat` routes to Ollama (same slowness). Hermes API `/v1/portsocket` is async-only (not for sync inference). Ollama only as last-resort fallback with 30s timeout and num_predict=512. See `references/fase-4-enrichment.md` §Ollama CPU-Only Performance Reality Check.

33g. **httpx Requires httpcore on This System** — `pip install httpx` does NOT automatically install `httpcore` on this VPS (Python 3.12, pip 24+). Always install both: `pip install httpx httpcore --break-system-packages`. The `ModuleNotFoundError: No module named 'httpcore'` error caused 0/5 senator failures even after httpx was "installed".

33h. **Hermes API :8100 Portsocket Auth & Behavior (8 Mei 2026)** — Hermes API auth: `X-API-Key: hermes-secret-change-me-in-production` (NOT `Authorization: Bearer`). Portsocket endpoint: `POST /v1/portsocket` with body `{"input": "string", "method": "auto"}`. Response: `{"task_id": "...", "status": "queued", ...}` — it's ASYNC. Poll `GET /v1/result/{task_id}` for result. However, Celery worker may not process external tasks (stuck at PENDING). Do NOT use portsocket for sync inference. The `/chat` endpoint routes to Ollama lokal (same CPU slowness problem). **For sync inference, call OpenRouter API directly.**

33i. **SKP DB Path and Table Name (FASE 4+)** — Active SKP database: `/data/arsify.db` (symlink to `/root/.hermes/shared_knowledge_pool.db`). Table name: `knowledge` (NOT `memory_notes`, NOT `romi_theses`). The file `/data/shared_knowledge_pool.db` is a stale/empty file (0 bytes), NOT the active DB. Always try paths in order: `/data/arsify.db` → `/root/.hermes/shared_knowledge_pool.db` → `/data/shared_knowledge_pool.db`. Use `skp_adapter.py` for auto-detection.

33m. **SKP `knowledge` Table Has No `scope` Column (8 Mei 2026)** — The production `knowledge` table schema is: `id, key, value, category, tags, priority, source_agent_name, created_at, updated_at`. There is **NO `scope` column**. Any adapter `write()` method must check column existence before INSERT: `cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]` then branch on `"scope" in cols`. The `_ensure_table()` method creates `memory_notes` with `scope`, but production uses `knowledge` which lacks it. Error message: `table knowledge has no column named scope`.

33n. **OpenRouter Key Discrepancy — Two Keys, Different Status (8 Mei 2026)** — The system has TWO separate OpenRouter keys: (1) `/root/.hermes/.env` — active, senators succeed. (2) `/opt/hermes-cognitive/.env` — expired (402 Payment Required). The cognitive engine key can expire independently of the host key. When debugging 402 errors, check BOTH files. Fix: `sed -i 's|OLD_KEY|NEW_KEY|' /opt/hermes-cognitive/.env` then `docker restart hermes-cognitive`.

33o. **Senator Execution v5 Pattern — THE MISSING LAYER (8 Mei 2026)** — The fundamental fix for "SKP stores prompts not insights": `senator-execution.py` implements the full pipeline: (1) Build structured JSON prompt per domain, (2) Call LLM (OpenRouter direct), (3) Parse JSON response per domain schema, (4) Junk detection (`is_junk_response()`), (5) Write structured insights to SKP. Replaces the old pattern where bash scripts called LLM and stored raw output (which was the prompt itself). Deployed and verified: 5 domains → 16 insights/cycle. See `references/senator-execution-v5.md` for full architecture.

33p. **GitHub Deploy from VPS (8 Mei 2026)** — When `gh` CLI is not available: (1) `ssh-keygen -t ed25519 -C "project@domain.com" -f ~/.ssh/id_ed25519_project -N ""`, (2) User manually adds `.pub` key to https://github.com/settings/keys, (3) User creates repo on GitHub (do NOT check "Add README" if local files exist), (4) `git init && git branch -M main && git remote add origin git@github.com:ORG/REPO.git`, (5) Push: `GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_project -o StrictHostKeyChecking=no" git push -u origin main`. **Common failures:** `Permission denied (publickey)` = key not added yet; `Repository not found` = repo not created yet. Once pushed, configure `~/.ssh/config` with `IdentityFile` for the key to avoid repeating `GIT_SSH_COMMAND`.

33k. **SKP-to-PDF Generation with fpdf2 (8 Mei 2026)** — To generate formatted PDF reports from SKP data: (1) Query SKP for best entry (largest `LENGTH(value)`, `created_at DESC`), (2) Install fpdf2: `pip3 install fpdf2 --break-system-packages`, (3) Use DejaVu fonts from `/usr/share/fonts/truetype/dejavu/` — NOTE: `DejaVuSans-Oblique.ttf` does NOT exist, map italic→regular and bold-oblique→bold as fallback, (4) Run generator via `terminal` NOT `execute_code` (sandbox Python is different from system Python), (5) Verify with `file` command — expect "PDF document, version 1.3, 1 page(s)". See `references/skp-to-pdf-report.md` for full template and color scheme.

33l. **execute_code Sandbox vs System Python** — The `execute_code` tool runs a separate Python environment that does NOT share packages with the system `python3`. Packages installed via `pip3 install --break-system-packages` (fpdf2, pymupdf, etc.) are only available via `terminal` → `python3`. Always use `terminal` for running Python scripts that need system-installed packages. Use `execute_code` only for pure-stdlib Python or quick shell commands.

33j. **Kurator Rewrite: Bash Inline-Python to Separate .py File (8 Mei 2026)** — kurator-v2.sh used inline `python3 - << 'PYEOF'` with `sys.path.insert(0, ...)` that resolved incorrectly (the `__file__` variable doesn't exist in inline Python invoked from bash heredoc). Fix: rewrite logic as standalone `kurator-v2.py` and make the .sh a thin wrapper. Same issue affected senator-cycle.sh's `SKP_DATA` inline Python blocks — use `SCRIPT_DIR` (bash variable) not `__file__` (Python variable) for path resolution.

34. **Senator Cycle Gateway Dependency** — `senator-cycle.sh` uses `hermes kanban create` which requires `hermes gateway` to be running. Without gateway, tasks are created in kanban.db but never dispatched → 0/5 senator success. **Always verify gateway**: `hermes gateway status` or check port 8000. If gateway not running, either start it (`hermes gateway start`) or bypass kanban by calling Cognitive Engine API directly. See `references/senator-cycle-debugging.md`.

35. **workspace.upshalter.com 502 Pattern** — If workspace returns 502: (1) check `docker ps | grep workspace` — container may be unhealthy, (2) check nginx proxy_pass port matches container port, (3) check workspace app logs for crash. The workspace container sets `ENHANCED_CHAT`, `HERMES_MCP`, and `HERMES_MCP_FALLBACK` env vars — verify these are set. See `references/workspace-debugging.md`.

36. **Arsify MoE Integration Pattern** — Do NOT replace Hermes API with Arsify MoE router. Instead, inject MoE capabilities INTO Hermes API: (a) Use `classify()` from arsify router.py for domain routing per senator, (b) Use `build_memory_context()` for conversation history injection, (c) Extend ROUTING_RULES with senator-specific domains (akademisi→research/education, bisnis→business/marketing, etc.), (d) Timeout: use 120s (from arsify config) instead of 60s for kuratur tasks. See `references/moe-integration-pattern.md`.

37. **PRD Audit Must Include STRATEGY-WAVES Timeline** — When auditing PRD compliance, also check against `STRATEGY-WAVES.md` in `/root/upshalter-5-prd-package/`. The wave-based timeline defines dependencies between PRDs (e.g., Wave 3 blocked by Wave 1). Track overall completion percentage per wave, not just per-PRD deliverables. See `references/prd-audit-checklist.md`.

## Verification Steps

```bash
# Check scripts exist and executable
ls -la /root/upshalter-scripts/*.sh

# Test senator-cycle (dry run)
bash -n /root/upshalter-scripts/senator-cycle.sh

# Check cron jobs registered
crontab -l | grep -E "senator|kurator|generate"

# Test Cognitive Engine connectivity
curl -sf http://host.docker.internal:8100/health

# Check SKP database
sqlite3 /data/arsify.db "SELECT COUNT(*) FROM knowledge"

# Test Telegram
curl -s "https://api.telegram.org/bot${TOKEN}/getMe"

# Check Kurator entries
sqlite3 /root/.hermes/shared_knowledge_pool.db "SELECT COUNT(*) FROM knowledge WHERE key LIKE 'kurator:%'"

# Check beat is firing
docker logs hermes-beat --tail 20
```

## File Structure

```
/root/upshalter-scripts/
├── senator-cycle.sh          # v3: Kanban + logging + alerts
├── kurator-review.sh         # v2: Auto-generate laporan
├── deliver-intelligence.sh    # v2: Subscriber delivery
└── generate-intelligence-page.py  # Landing page generator

/root/upshalter-config/
└── subscribers.json          # Subscriber database

/root/upshalter-reports/
└── pentahelix-brief-*.md    # Generated reports

/var/www/data.upshalter.com/
├── index.html                # Landing page (auto-generated)
└── data.json                 # Insights data (auto-generated)
```

## References

- Kurator Pipeline: `references/kurator-pipeline.md` — full implementation, SKP key convention, beat config, verification, recovery
- Performance Optimization: `references/performance-optimization.md` — Ollama integration, 2-tier caching, FTS5, prompt optimization
- Upshalter Technical Frameworks: `references/upshalter-technical-frameworks.md` — CRISP-DM, SECI, ISO 30401
- NotebookLM Reporting: `references/notebooklm-reporting.md`
- PRD Audit Checklist: `references/prd-audit-checklist.md`
- Quality Improvement: `references/quality-improvement.md` — L2/L3/L4 prompt optimization, fallback plans, Kurator timeout mitigation
- Arsify Documentation Map: `references/arsify-documentation-map.md` — v0.1.1 docs location, architecture gaps, documented vs implemented, vector-based RAG path, keyword vs vector enrichment decision
- Fase 4 Enrichment: `references/fase-4-enrichment.md` — pre-implementation snapshot, dry-run results, domain mapping, execution order, verification commands, post-deploy results
- Senator Cycle v3: `references/senator-cycle-v3.md` — OpenRouter direct pattern, Hermes API auth details, prompt fixes, kurator rewrite lessons
- SKP-to-PDF Report Generation: `references/skp-to-pdf-report.md` — Query best SKP entry, generate formatted PDF with fpdf2 + DejaVu fonts, color-coded sentiments, single-page A4 layout
- Product Readiness Assessment: `references/product-readiness-assessment.md` — 10-dimension scoring framework (42/100 current), phased roadmap to 100%, actual infrastructure snapshot (19 systemd services, 12 Docker containers, 26 nginx vhosts), pricing tiers, key pitfalls
