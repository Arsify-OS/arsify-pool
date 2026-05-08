# Arsify Core — Changelog

## v1.0.0 — 2026-05-08

### Initial Release

**The Missing Layer** — Layer yang membuat AI senator menghasilkan real intelligence, bukan prompt junk.

#### Features

- **senator-execution.py** — Core execution engine
  - 5 domain senators: akademisi, bisnis, komunitas, pemerintah, media
  - Structured JSON output per domain
  - Response parsing (JSON blocks, markdown-wrapped, free text fallback)
  - Junk detection (prompt patterns, too-short responses)
  - Memory injection (previous cycle insights as context)
  - LLM fallback chain: OpenRouter → Ollama

- **skp_adapter.py** — Universal SKP database adapter
  - Auto-detect DB path, table name, key format
  - Schema-aware INSERT (handles different column sets)
  - Read recent entries with domain filtering
  - Supports both `knowledge` and `memory_notes` tables

- **skp-cleaner.py** — SKP cleanup tool
  - Pattern-based junk detection
  - Dry-run mode for safe preview
  - Removes prompt artifacts, execution results, config entries
  - Keeps real insights intact

- **senator-cycle-v5.sh** — Orchestration script
  - Runs all 5 senators sequentially
  - JSON result parsing per domain
  - Logging to `/root/upshalter-logs/`
  - Optional Telegram notification
  - Triggers kurator 5 minutes after completion

#### What Changed from v4/v3

| Before (v3/v4) | After (v5) |
|-----------------|------------|
| Bash inline Python call to OpenRouter | Dedicated Python module with proper parsing |
| Raw LLM output stored as "intelligence" | Structured JSON parsed into individual insights |
| No junk detection | Pattern-based junk filter + min length check |
| No memory context | Previous cycle insights injected as context |
| Single execution script | Modular: execution + adapter + cleaner |
| SKP had 421 junk entries | 75 junk removed, 353 real insights remain |

#### Verified Working

- ✅ OpenRouter API key verified (gpt-4o-mini model)
- ✅ All 5 domains produce structured JSON output
- ✅ SKP write with correct key format (`senator-{domain}/insight/{date}-{counter}`)
- ✅ Junk detection catches prompt artifacts
- ✅ Memory context injection from previous cycles
- ✅ Crontab scheduling every 6 hours

#### Known Limitations

- Hermes Cognitive Engine integration: `/v1/portsocket` returns pipeline metadata, not raw LLM text. Using direct OpenRouter until Hermes L3/L4 pipeline stabilizes.
- Ollama fast path not available (Ollama not running on this server)
- SKP database is SQLite — sufficient for current scale, migrate to PostgreSQL for high-volume production

#### Test Results (2026-05-08)

| Domain | Insights Written | Status |
|--------|-----------------|--------|
| Akademisi | 7 | ✅ success |
| Bisnis | 4 | ✅ success |
| Komunitas | 3 | ✅ success |
| Pemerintah | 3 | ✅ success |
| Media | 2 | ✅ success |
| **Total** | **19** | **5/5 success** |
