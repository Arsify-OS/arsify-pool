# Fase 4: SKP Enhancement & Optimization

**Status**: Pre-implementation snapshot (8 Mei 2026)
**Full journal**: `/root/.hermes/journal/FASE-4-CONDITION-ANALYSIS.md`

## Pre-Implementation Snapshot

### SKP Quality Metrics (Before)

| Metric | Value | Gap |
|--------|-------|-----|
| Total entries | 414 | — |
| Category "general" | 334 (80.7%) | Target: <30% |
| Tagged entries | 5 (1.2%) | Target: >50% |
| Kurator fallback rate | 15/40 (37.5%) | Target: <10% |
| Kurator confidence (latest) | 0.3 | Target: >0.7 |
| Priority p8-p9 | 379 (91.5%) | Not differential |
| Duplicate keys | 0 | ✅ Clean |
| DB size | 636 KB | — |

### Category Distribution

| Category | Count | % |
|----------|-------|---|
| general | 334 | 80.7% |
| curated | 40 | 9.7% |
| backend | 37 | 8.9% |
| architecture | 1 | 0.2% |
| devops | 1 | 0.2% |
| infrastructure | 1 | 0.2% |

### Source Distribution

| Source | Count |
|--------|-------|
| senator-pemerintah | 101 |
| senator-bisnis | 73 |
| senator-media | 69 |
| senator-komunitas | 69 |
| senator-akademisi | 57 |
| kurator | 40 |
| system | 5 |

## Dry-Run Results (8 Mei 2026)

### What `backfill_general_entries(dry_run=True)` Actually Does

The function queries:
```sql
SELECT key, value, category, tags, source_agent_name
FROM   knowledge
WHERE  category = 'general'
  AND  key NOT LIKE 'system:%'
  AND  key NOT LIKE 'kurator:%'
  AND  key NOT LIKE 'curated:%'
```

**Critical finding**: Only **65 of 334** "general" entries pass this filter. The other **269** have `curated:*` keys — they were already processed by the Kurator but **still labeled "general"** because the Kurator sets `category = "general"` on curated output (a bug in kurator.py).

### Dry-Run Output

```
Total general entries matching query: 65
Would enrich: 65
Would skip: 0

Category changes from 65 entries:
  policy: 20       ← senator-pemerintah
  media: 19        ← senator-media
  business: 10     ← senator-bisnis
  community: 7     ← senator-komunitas
  research: 4      ← senator-akademisi
  education: 3     ← senator-akademisi
  finance: 1       ← senator-bisnis
  digital-gov: 1   ← senator-pemerintah
```

### Impact Calculation

```
BEFORE:  general 334/414 = 80.7%
AFTER:   general 269/414 = 65.0%  (only -15.7% improvement)

To reach <30% target, MUST also fix Kurator v2 to properly
categorize the 269 curated:* entries. See task j6.
```

### Recommended Execution Order

```
1. Run j3 now       → 65 entries enriched, general 80.7% → 65.0%
2. Fix j6 (Kurator v2) → curated entries get proper categories
3. Re-run backfill  → general 65.0% → <30%
4. Then j4 (tags) + j5 (dedup) on cleaner data
```

## Implementation Tasks

### j3: Category Enrichment (Backfill)
- **File**: `/root/.hermes/category_enrichment.py` (529 lines, exists but never run)
- **Run command**: `docker cp /root/.hermes/category_enrichment.py hermes-worker:/tmp/ && docker exec hermes-worker python3 -c "exec(open('/tmp/category_enrichment.py').read()); backfill_general_entries(dry_run=False)"`
- **Domain mapping**:
  - senator-akademisi → research, education, ai-ml
  - senator-bisnis → business, market, finance
  - senator-komunitas → community, sentiment, event
  - senator-pemerintah → regulation, policy, government
  - senator-media → media, framing, narrative

### j4: Auto-Tag Generation
- Part of `classify_content()` in category_enrichment.py — returns tags alongside category
- Keywords mapping per domain in `AGENT_DOMAIN_CATEGORIES`
- Still needs execution after j3

### j5: SKP Deduplication & Cleanup
- **Prerequisite**: `pip install scikit-learn` (NOT installed on host as of 8 Mei 2026)
- TF-IDF + cosine similarity for content-based dedup
- Filter boilerplate: "Task: Process request / Result: Successfully executed"
- Quality scoring per entry

### j6: Kurator v2
- **Critical bug**: Kurator sets `category = "general"` on curated entries → 269 entries mislabeled
- Fix: set category based on source_agent_name domain mapping
- Ollama fallback (local) if OpenRouter fails
- Better error handling + retry
- Improved confidence scoring

### j7: Testing & Validation
- Pre/post metrics comparison
- Category distribution improvement
- Kurator fallback rate reduction
- Tag coverage improvement

## Existing Code Assets

| File | Path | Status |
|------|------|--------|
| kurator.py | `/root/.hermes/kurator.py` | 403 lines, v1 with fallback issues |
| category_enrichment.py | `/root/.hermes/category_enrichment.py` | 529 lines, never run |
| knowledge_injector.py | `/root/.hermes/knowledge_injector.py` | SKP → L2 injection |
| router.py | `/root/.hermes/router.py` | MoE routing |

## Key Pitfalls (from session)

1. **category_enrichment.py exists but has no cron job** — must be scheduled
2. **Only 65 of 334 general entries are raw senator** — 269 are curated:* with wrong category (kurator bug)
3. **Kurator v1 uses fallback for 37.7% of runs** — Ollama local fallback needed
4. **Content quality is low** — many entries are boilerplate templates
5. **Priority is not differential** — 91.5% are p8-p9, making priority meaningless
6. **scikit-learn not installed** — needed for j5 TF-IDF dedup, `pip install scikit-learn`
7. **Gateway port 8643 DOWN** — monitoring shows all agents offline, but hermes-api :8100 healthy
8. **File path gotcha** — `/root/.hermes/` files NOT accessible from hermes-worker container at same path; must `docker cp` to `/tmp/` first, or use `/data/` volume mount path

## Post-Deploy Results (8 Mei 2026 — FASE 4 FINAL)

### SKP Quality Metrics (After)

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total entries | 414 | 414 | — |
| Category "general" | 334 (80.7%) | 0 (0.0%) | **-334** ✅ |
| Tagged entries | 5 (1.2%) | 296 (71.5%) | **+291** ✅ |
| Kurator fallback rate | 15/40 (37.5%) | TBD (kurator-v2 not yet run live) | Pending |
| Priority p8-p9 | 379 (91.5%) | 174 (42.0%) | **-205** ✅ |
| Duplicate keys | 0 | 0 | ✅ Clean |

### Category Distribution (After)

| Category | Count | % |
|----------|-------|---|
| pemerintah | 101 | 24.4% |
| bisnis | 73 | 17.6% |
| komunitas | 69 | 16.7% |
| upshalter | 67 | 16.2% |
| curated | 40 | 9.7% |
| backend | 37 | 8.9% |
| akademisi | 22 | 5.3% |
| media | 2 | 0.5% |
| architecture | 1 | 0.2% |
| devops | 1 | 0.2% |
| infrastructure | 1 | 0.2% |

### Priority Distribution (After)

| Priority | Count | Meaning |
|----------|-------|---------|
| p10 | 67 | upshalter (highest) |
| p9 | 41 | — |
| p8 | 133 | pemerintah, bisnis |
| p7 | 6 | laporan |
| p6 | 74 | bisnis, ai-ml |
| p5 | 22 | akademisi |
| p4 | 2 | media |
| p3 | 69 | komunitas |

### Deployed Scripts

| File | Path | Status |
|------|------|--------|
| senator-cycle-v2.sh | `/root/upshalter-scripts/senator-cycle-v2.sh` | ✅ Deployed, cron active |
| kurator-v2.sh | `/root/upshalter-scripts/kurator-v2.sh` | ✅ Deployed, cron active |
| skp_adapter.py | `/root/upshalter-scripts/python/skp_adapter.py` | ✅ Deployed |
| category-backfill.py | `/root/upshalter-scripts/python/category-backfill.py` | ✅ Deployed + executed |

### Crontab (Active)

```
0 */6 * * * SCRIPT_DIR=/root/upshalter-scripts bash /root/upshalter-scripts/senator-cycle-v2.sh >> /root/upshalter-logs/senator.log 2>&1
0 1,7,13,19 * * * SCRIPT_DIR=/root/upshalter-scripts bash /root/upshalter-scripts/kurator-v2.sh >> /root/upshalter-logs/kurator.log 2>&1
```

### Connectivity (Verified 8 Mei 2026)

| Service | Port | Status |
|---------|------|--------|
| Hermes API | 8100 | REACHABLE (but /chat routes to Ollama = slow, portsocket = async only) |
| Ollama | 11434 | REACHABLE but CPU-only too slow for production |
| Gateway | 8643 | DOWN (bypassed by v3 scripts) |
| OpenRouter API | 443 | PRIMARY inference backend |

### Key Lessons

1. **category-backfill.py WHERE filter is critical** — Without `WHERE category='general'`, the script would overwrite all 414 entries including correctly-categorized curated/backend entries. The FINAL package's fix (v2.1) correctly filters.
2. **Manual deploy > script deploy when paths differ** — `deploy-fase4.sh` resolves `DEPLOY_DIR` to its own location. When running from `/tmp/`, container copy steps fail. Manual step-by-step is safer.
3. **skp_adapter.py auto-detection works** — Correctly detected `/data/arsify.db`, table `knowledge`, 414 entries, and `senator-X/` key format on first run.
4. **Tags populated automatically** — The backfill script's `classify()` function generates tags alongside categories. 296/414 entries now have meaningful tags.
5. **Priority now differentiated** — Previously 91.5% were p8-p9. Now spread from p3-p10 based on category importance.

### Remaining Work

- **Kurator v2 live test** — Script deployed but not yet run live. First run will show if confidence scoring improves from 0.3. **Note**: Kurator primarily uses Ollama directly (not Hermes API). May need route change to Hermes API for reliable inference.
- **Senator v2 first cycle** — Will run at next 6h cron slot. Expected: 5 senators produce real insights via Hermes API :8100. **Ollama fallback will likely timeout — must fix primary route**.
- **SKP Deduplication (j5)** — scikit-learn still not installed on host. Install before starting.
- **Tag Generation (j4)** — Partially done via backfill. Remaining: ensure new senator/kurator entries auto-tag.
- **Ollama route fix (NEW)** — Change senator-cycle-v2.sh and kurator-v2.sh to use Hermes API :8100 as primary LLM endpoint. Ollama only as true last resort with 120s timeout.

### Ollama CPU-Only Performance Reality Check (8 Mei 2026 — CRITICAL)

**Root cause discovered**: Ollama on CPU-only VPS (2 cores, no GPU, 7.8GB RAM) is **too slow for production inference**.

| Operation | Time | Impact |
|-----------|------|--------|
| Model load (qwen2.5:1.5b) | ~39 seconds | Runner startup per request |
| Inference (any prompt) | >60 seconds | Exceeds all client timeouts |
| Ollama runner CPU | 100-172% | Single-thread bound |

**Evidence from journalctl**:
```
llama runner started in 39.25 seconds
[GIN] 500 | 20.09s | POST /api/chat    ← client timeout
[GIN] 500 | 1m30s  | POST /v1/chat/completions  ← Hermes API timeout
```

**What this means**:
1. Senator v2 call_llm() WILL timeout on Ollama (>60s inference + 39s load)
2. Kurator v2 WILL timeout on Ollama
3. **Ollama is only viable as LAST RESORT fallback** — Hermes API :8100 (OpenRouter backend) must be primary
4. Models affected: qwen2.5:1.5b (1GB), phi3:mini (2GB) — both too heavy for 2-core CPU

**Recommended fix**: In senator-cycle-v2.sh and kurator-v2.sh, always try Hermes API :8100 first (it routes to OpenRouter with GPU backend). Ollama fallback should have 120s+ timeout AND graceful degradation.

**Test results** (8 Mei 2026):
```
Quick Ollama test (60s timeout): TIMEOUT — 0 bytes received
After killing stuck runner + 10s warmup: STILL TIMEOUT
Ollama runner CPU during test: 102-172%
```

**httpcore dependency fix**: `httpx` was installed but `httpcore` was missing. Fixed with `pip install httpcore --break-system-packages`. Always install both: `pip install httpx httpcore --break-system-packages`.

```bash
# Check category distribution
docker exec hermes-worker python3 -c "
import sqlite3
conn = sqlite3.connect('/data/shared_knowledge_pool.db')
cur = conn.cursor()
cur.execute('SELECT category, COUNT(*) FROM knowledge GROUP BY category ORDER BY COUNT(*) DESC')
for r in cur.fetchall(): print(f'  {r[0]}: {r[1]}')
conn.close()
"

# Check kurator fallback rate
docker exec hermes-worker python3 -c "
import sqlite3, json
conn = sqlite3.connect('/data/shared_knowledge_pool.db')
cur = conn.cursor()
cur.execute(\"SELECT COUNT(*) FROM knowledge WHERE key LIKE 'kurator:%'\")
total = cur.fetchone()[0]
cur.execute(\"SELECT COUNT(*) FROM knowledge WHERE key LIKE 'kurator:%' AND value LIKE '%\\\"_fallback\\\": true%'\")
fallback = cur.fetchone()[0]
print(f'Kurator: {total} total, {fallback} fallback ({fallback*100/total:.1f}%)')
conn.close()
"

# Check tagged entries
docker exec hermes-worker python3 -c "
import sqlite3
conn = sqlite3.connect('/data/shared_knowledge_pool.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM knowledge WHERE tags IS NOT NULL AND tags != \"\" AND tags != \"[]\"')
print(f'Tagged: {cur.fetchone()[0]}')
conn.close()
"

# Check general breakdown (raw vs curated)
docker exec hermes-worker python3 -c "
import sqlite3
conn = sqlite3.connect('/data/shared_knowledge_pool.db')
cur = conn.cursor()
cur.execute(\"\"\"
    SELECT 
        CASE 
            WHEN key LIKE 'curated:%' THEN 'curated'
            WHEN key LIKE 'kurator:%' THEN 'kurator'
            WHEN key LIKE 'system:%' THEN 'system'
            ELSE 'raw_senator'
        END as key_type,
        COUNT(*) as cnt
    FROM knowledge 
    WHERE category = 'general'
    GROUP BY key_type
    ORDER BY cnt DESC
    \"\"\")
for r in cur.fetchall(): print(f'  {r[0]}: {r[1]}')
conn.close()
"
```
