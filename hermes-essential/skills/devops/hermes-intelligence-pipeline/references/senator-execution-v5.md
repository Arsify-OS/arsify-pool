# Senator Execution Engine — v5 Architecture (8 Mei 2026)

Tested and deployed `senator-execution.py` — the "missing layer" that transforms LLM output into structured SKP insights.

## Architecture

```
senator-cycle-v5.sh
  └─ senator-execution.py (--domain X)
       ├─ 1. Memory injection: read_recent(domain) from SKP
       ├─ 2. Call LLM: OpenRouter → Ollama fallback
       ├─ 3. Parse response: JSON extraction → field-level insights
       ├─ 4. Junk detection: is_junk_response() filters prompt artifacts
       └─ 5. Write SKP: write_insights_to_skp() with correct schema
```

## Key Files

| File | Location | Purpose |
|------|----------|---------|
| `senator-execution.py` | `/root/upshalter-scripts/python/` | Main execution engine |
| `skp_adapter.py` | `/root/upshalter-scripts/python/` | Universal DB connector (auto-detect path, table, key format) |
| `skp-cleaner.py` | `/root/upshalter-scripts/python/` | Junk cleanup (pattern-based) |
| `senator-cycle-v5.sh` | `/root/upshalter-scripts/` | Orchestration wrapper |

## Domain Configuration

5 domains, each with structured JSON output schema:
- **akademisi** → `temuan`, `peluang_baru`, `sinyal_lemah`
- **bisnis** → `peluang`, `risiko`, `funding_tracker`
- **komunitas** → `isu`, `tokoh_kunci`, `tools_trending`
- **pemerintah** → `regulasi`, `program_pemerintah`, `alert_compliance`
- **media** → `narasi_dominan`, `tokoh_tersebut`

Each domain prompt specifies `"Format output HANYA JSON"` with explicit field schema.

## SKP Write Pattern

Key format: `senator-{domain}/insight/{YYYYMMDD-HH}-{counter:02d}`
Value: raw structured JSON string, NOT free text.

Verified: 5 domains produce ~16 insights per cycle.

## Junk Detection

Patterns that indicate prompt junk (not insight):
- `"step: analyze and understand"` — Hermes agent prompt leaked into SKP
- `"anda adalah senator"` / `"kamu adalah senator"` — agent self-description
- `"## misi inti"` / `"soul.md"` — agent metadata
- `"step 1:"` / `"step 2:"` / `"step 3:"` — workflow step markers
- `"task_id:"` / `"agent_id:"` / `"workflow_step"` — orchestrator artifacts
- Anything < 100 chars

## SKP Schema Pitfall — No `scope` Column

Production `knowledge` table at `/data/arsify.db`:
```
id, key, value, category, tags, priority, source_agent_name, created_at, updated_at
```

**NO `scope` column.** The adapter must check column existence before INSERT:
```python
cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
if "scope" in cols:
    INSERT with scope
else:
    INSERT without scope  # production knowledge table
```

Failing to check produces: `Adapter error: table knowledge has no column named scope`

## OpenRouter Key Management

Two different keys exist in the system:
- `/root/.hermes/.env` → ACTIVE (verified working, senators succeed)
- `/opt/hermes-cognitive/.env` → can expire independently (402 Payment Required)

The cognitive engine key can expire while the host key still works. Always check BOTH `.env` files when debugging 402 errors.

## Hermes Cognitive Engine — Sync Inference Reality

- `/v1/portsocket` → async task submission. Returns pipeline metadata (`route, perception, plan, results`), NOT raw LLM text. When Ollama is down: `results: []`. **Not suitable for sync chat-like inference.**
- `/chat` → fast path to Ollama. Also fails on CPU-only VPS (model load 39s+, inference 60s+, all timeouts exceeded).
- **For sync inference: call OpenRouter directly.** Verified 5/5 senators succeed with `curl -X POST https://openrouter.ai/api/v1/chat/completions`.

## Deployment Order

1. Backup: `cp -r /root/upshalter-scripts/ /root/upshalter-scripts-backup-TIMESTAMP/`
2. Copy files → verify syntax with `py_compile`
3. SKP cleanup: dry-run → review → live delete
4. Test single domain dry-run → then live write
5. Test all 5 domains
6. Update crontab (replace old cycle with v5)

## First Deploy Results (8 Mei 2026)

- SKP: 421 entries → cleanup 75 junk → 346 remain → live write 7 → 353 total
- Full dry-run 5 domains: 16 insights parsed across all domains
- Sample real insights (not prompt junk):
  - "Riset AI untuk Smart City di Universitas Indonesia"
  - "Kurikulum Berbasis AI di Universitas Gadjah Mada"
  - "Program AI untuk Pendidikan oleh Kemdikbud"
  - "Inisiatif BRIN untuk Riset AI"
  - "Startup EdTech: AI Learning Indonesia"
