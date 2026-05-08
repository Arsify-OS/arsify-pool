# FASE 4 v3 Architecture — Pentahelix Editorial Pipeline

**Date**: 2026-05-08
**Status**: ACTIVE — 5/5 senators succeeded on first run

## Overview

The editorial pipeline was redesigned in FASE 4 v3 to use OpenRouter API directly
(bypassing Hermes API and Ollama entirely for the primary path). The old container-based
senator architecture was replaced with a shell-script + Python approach.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CRON SCHEDULER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Every 6 hours:          Every 30 min:         Every 5 min:     │
│  senator-cycle-v3.sh     generate-intelligence  health-check.sh  │
│                          -page.py                                │
│         │                     │                    │            │
│         ▼                     ▼                    ▼            │
│  ┌─────────────┐    ┌─────────────────┐   ┌──────────┐        │
│  │  5x Senator │    │  Read SKP →     │   │  Check   │        │
│  │  LLM calls  │    │  Generate JSON  │   │  services│        │
│  │  (OpenRouter│    │  + HTML page    │   │  + Docker│        │
│  │   direct)   │    └────────┬────────┘   └──────────┘        │
│  └──────┬──────┘             │                                  │
│         │                    ▼                                  │
│         │            /var/www/data.upshalter.com/               │
│         │            (index.html + data.json)                   │
│         ▼                                                       │
│  ┌─────────────┐                                               │
│  │  Save to    │                                               │
│  │  SKP        │                                               │
│  │  /data/     │                                               │
│  │  arsify.db  │                                               │
│  └──────┬──────┘                                               │
│         │                                                       │
│         │ (1h later)                                           │
│         ▼                                                       │
│  ┌─────────────┐                                               │
│  │  Kurator    │                                               │
│  │  v2.py      │                                               │
│  │  (consolid- │                                               │
│  │   ate via   │                                               │
│  │  OpenRouter)│                                               │
│  └──────┬──────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  /root/upshalter-reports/                                       │
│  (pentahelix-brief-YYYY-MM-DD-HH.md)                           │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### senator-cycle-v3.sh
- **Path**: `/root/upshalter-scripts/senator-cycle-v3.sh`
- **Schedule**: Every 6 hours (cron: `0 */6 * * *`)
- **Primary LLM**: OpenRouter API (`https://openrouter.ai/api/v1/chat/completions`)
- **Model**: `openrouter/owl-alpha`
- **Fallback**: Ollama local (30s timeout, num_predict 512)
- **Auth**: `Authorization: Bearer <OPENROUTER_API_KEY>`
- **Output**: Saves to SKP via `save_skp()` function (Python inline)
- **Post-action**: Schedules kurator-v2.sh 5 minutes after completion

### kurator-v2.py
- **Path**: `/root/upshalter-scripts/kurator-v2.py`
- **Wrapper**: `/root/upshalter-scripts/kurator-v2.sh`
- **Schedule**: 1h after senator cycle (cron: `0 1,7,13,19 * * *`)
- **Process**:
  1. Reads last 20 entries from SKP `knowledge` table
  2. Filters for senator entries (key patterns: `senator-*/temuan/*`, `senator-*/isu/*`, etc.)
  3. Deduplicates by key
  4. Calculates confidence (0.10-0.90 based on entry count)
  5. Truncates values to 800 chars per entry
  6. Calls OpenRouter for consolidated brief
  7. Saves Markdown to `/root/upshalter-reports/pentahelix-brief-YYYY-MM-DD-HH.md`

### generate-intelligence-page.py
- **Path**: `/root/upshalter-scripts/generate-intelligence-page.py`
- **Schedule**: Every 30 minutes
- **Output**: `/var/www/data.upshalter.com/index.html` + `data.json`
- **Note**: Currently reads from `/root/.hermes/shared_knowledge_pool.db` (OLD DB) — may need update to `/data/arsify.db`

## SKP Schema (ACTIVE)

**Database**: `/data/arsify.db` (symlink)
**Table**: `knowledge`

```sql
CREATE TABLE knowledge (
    key TEXT PRIMARY KEY,
    value TEXT,
    source_agent_name TEXT,
    created_at TEXT
);
```

**Key patterns**:
- Raw senator: `senator-<domain>/temuan/YYYYMMDD-HH` or `senator-<domain>/isu/YYYYMMDD-HH`
- Curated: `curated:senator-<domain>/...`
- Kurator brief: `pentahelix/brief/...`

**Categories** (as of 2026-05-08):
| Category    | Count |
|-------------|-------|
| pemerintah  | 102   |
| bisnis      | 74    |
| komunitas   | 70    |
| upshalter   | 67    |
| curated     | 40    |
| backend     | 37    |
| akademisi   | 23    |
| other       | 8     |
| **Total**   | **421** |

## Senator Output Value Structures

### Akademisi
```json
{
  "temuan": ["...", "..."],
  "sumber": ["...", "..."],
  "relevansi_bisnis": "...",
  "timestamp": "2026-05-08T..."
}
```

### Bisnis
```json
{
  "peluang": ["...", "..."],
  "risiko": ["...", "..."],
  "rekomendasi": "...",
  "timestamp": "2026-05-08T..."
}
```

### Komunitas
```json
{
  "isu": [
    {
      "judul": "...",
      "sentiment": "negatif|positif|netral",
      "deskripsi": "...",
      "tokoh_kunci": ["...", "..."]
    }
  ],
  "sentiment_overall": "negatif|positif|netral",
  "tanggal": "2026-05-08",
  "timestamp": "2026-05-08T..."
}
```

### Pemerintah
```json
{
  "regulasi": ["...", "..."],
  "dampak_bisnis": "...",
  "compliance_notes": ["...", "..."],
  "timestamp": "2026-05-08T..."
}
```

### Media
```json
{
  "narasi_dominan": ["...", "..."],
  "framing": "...",
  "sentiment_publik": "...",
  "media_utama": ["...", "..."],
  "timestamp": "2026-05-08T..."
}
```

## Docker Senator Containers

**Compose**: `/root/senator-pentahelix/docker-compose.yml`
**Image**: `nousresearch/hermes-agent:latest`
**Containers**: senator-akademisi, senator-bisnis, senator-komunitas, senator-pemerintah, senator-media
**Network**: `network_mode: host`
**User**: root
**Restart**: unless-stopped
**Healthcheck**: disabled (containers run scripts, not HTTP servers)

## Key Pitfalls

1. **Wrong DB path**: Old docs say `/root/.hermes/shared_knowledge_pool.db` — ACTIVE is `/data/arsify.db`
2. **Wrong table name**: Old docs say `memory_notes` — ACTIVE is `knowledge`
3. **Wrong columns**: Old docs say `id, title, category, source, content` — ACTIVE is `key, value, source_agent_name, created_at`
4. **Ollama is too slow**: CPU-only VPS (2 cores) → 39s model load + >60s inference. Use OpenRouter direct.
5. **httpcore missing**: After `pip install httpx`, also need `pip install httpcore --break-system-packages`
6. **OpenRouter model prefix**: Use `openrouter/owl-alpha` (with prefix) for OpenRouter API calls
7. **generate-intelligence-page.py reads OLD DB**: Script at `/root/upshalter-scripts/generate-intelligence-page.py` line ~15 still references `/root/.hermes/shared_knowledge_pool.db` — needs update to `/data/arsify.db`

## LLM Configuration

### OpenRouter (Primary)
- **URL**: `https://openrouter.ai/api/v1/chat/completions`
- **Model**: `openrouter/owl-alpha`
- **Auth**: `Authorization: Bearer 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`
- **Timeout**: 60s
- **Max tokens**: 2048

### Ollama (Fallback only)
- **URL**: `http://localhost:11434/api/chat`
- **Model**: auto-detected (prefers qwen2.5:0.5b, phi3:mini, tinyllama)
- **Timeout**: 30s
- **num_predict**: 512

## Cron Schedule

| Job | Schedule | Script |
|-----|----------|--------|
| Senator cycle | Every 6h (0,6,12,18) | senator-cycle-v3.sh |
| Kurator review | 1h after senator (1,7,13,19) | kurator-v2.sh |
| Intelligence page | Every 30 min | generate-intelligence-page.py |
| Health check | Every 5 min | health-check.sh |
| Daily summary | 00:00 UTC | daily-summary.sh |
| SKP backup | 20:00 UTC | backup-skp.sh |
| SSL check | 01:00 UTC | ssl-check.sh |
| Log cleanup | Weekly (Sunday) | find ... -mtime +30 -delete |

## Reports Output

- **Briefs**: `/root/upshalter-reports/pentahelix-brief-YYYY-MM-DD-HH.md`
- **PDF**: `/root/upshalter-reports/sample-brief-DEMO.pdf` (generated on demand)
- **Logs**: `/root/upshalter-logs/`
  - `senator-YYYY-MM-DD.log`
  - `kurator-YYYY-MM-DD.log`
  - `health-YYYY-MM-DD-HHMM.log`
