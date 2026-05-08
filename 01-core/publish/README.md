# Arsify Core — AI Workforce Intelligence Engine

> **The missing layer that makes AI agents produce real intelligence, not prompt junk.**

Arsify Core adalah execution engine untuk [Arsify Workforce OS](https://github.com/Arsify-OS) — sistem yang menjalankan 5 AI Senator (analyst) secara otomatis, menghasilkan structured intelligence, dan menyimpannya ke Shared Knowledge Pool (SKP).

## Masalah yang Diselesaikan

Sebelumnya, AI senator menyimpan **prompt-nya sendiri** ke database sebagai "intelligence":

```
Key: senator-media/analysis/48874
Value: "Step: Analyze and understand: Anda adalah Senator Media..."
```

Ini bukan insight. Ini **prompt junk**.

Arsify Core fix ini dengan:
1. **Structured JSON output** — LLM diminta output JSON dengan schema spesifik per domain
2. **Response parsing** — Extract insights dari JSON, bukan simpan raw text
3. **Junk detection** — Filter otomatis: kalau output mengandung "Step: Analyze" → dibuang
4. **SKP cleanup** — Hapus 75 junk entries yang sudah terakumulasi

## Arsitektur

```
┌─────────────────────────────────────────────────────────┐
│                  SENATOR CYCLE v5                        │
│                  (setiap 6 jam via cron)                 │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │Akademisi │  │ Bisnis   │  │Komunitas │  ... 5 total │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │              │              │                    │
│       ▼              ▼              ▼                    │
│  ┌─────────────────────────────────────────┐            │
│  │       senator-execution.py              │            │
│  │  1. Build prompt + memory context       │            │
│  │  2. Call LLM (OpenRouter)               │            │
│  │  3. Parse JSON response                 │            │
│  │  4. Validate (junk detection)           │            │
│  │  5. Write structured insights to SKP    │            │
│  └────────────────┬────────────────────────┘            │
│                   │                                     │
│                   ▼                                     │
│  ┌─────────────────────────────────────────┐            │
│  │       skp_adapter.py                    │            │
│  │  Auto-detect DB path, table, schema     │            │
│  │  INSERT with correct column mapping     │            │
│  └────────────────┬────────────────────────┘            │
│                   │                                     │
│                   ▼                                     │
│  ┌─────────────────────────────────────────┐            │
│  │  SKP (/data/arsify.db)                  │            │
│  │  Table: knowledge                       │            │
│  │  353+ real intelligence entries         │            │
│  └─────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

## 5 Domain Senator

| Domain | Focus | Key Prefix |
|--------|-------|------------|
| **Akademisi** | Riset AI, universitas, hibah, edtech | `senator-akademisi/insight/` |
| **Bisnis** | Funding, startup, market, regulasi | `senator-bisnis/insight/` |
| **Komunitas** | Sentiment, developer, tools trending | `senator-komunitas/insight/` |
| **Pemerintah** | Regulasi, kebijakan, compliance | `senator-pemerintah/insight/` |
| **Media** | Narasi, framing, sentiment publik | `senator-media/insight/` |

## Quick Start

### Prerequisites
- Python 3.10+
- SQLite 3
- OpenRouter API key ([get one](https://openrouter.ai/keys))

### Install

```bash
# Clone
git clone https://github.com/Arsify-OS/arsify-core.git
cd arsify-core

# Install dependencies (only httpx needed)
pip install httpx

# Set environment variables
export OPENROUTER_API_KEY="sk-or-v1-..."
export OPENROUTER_MODEL="openai/gpt-4o-mini"  # or any OpenRouter model
export SKP_DB_PATH="/data/arsify.db"          # optional, auto-detects
```

### Run Single Senator

```bash
# Dry run (parse only, don't write)
python3 python/senator-execution.py --domain akademisi --dry-run

# Live run (write to SKP)
python3 python/senator-execution.py --domain akademisi

# Test mode (mock LLM response)
python3 python/senator-execution.py --domain akademisi --test-mode
```

### Run Full Cycle (All 5 Senators)

```bash
# Via shell script
bash scripts/senator-cycle-v5.sh

# Or via Python
python3 python/senator-execution.py --domain akademisi --dry-run
python3 python/senator-execution.py --domain bisnis --dry-run
python3 python/senator-execution.py --domain komunitas --dry-run
python3 python/senator-execution.py --domain pemerintah --dry-run
python3 python/senator-execution.py --domain media --dry-run
```

### Clean Junk from SKP

```bash
# Preview what will be deleted
DRY_RUN=true python3 python/skp-cleaner.py

# Actually delete
python3 python/skp-cleaner.py
```

### Schedule with Cron

```bash
# Every 6 hours
0 */6 * * * SCRIPT_DIR=/path/to/arsify-core OPENROUTER_API_KEY=sk-or-v1-... bash /path/to/arsify-core/scripts/senator-cycle-v5.sh >> /var/log/senator.log 2>&1
```

## File Structure

```
arsify-core/
├── README.md                   # This file
├── LICENSE                     # MIT License
├── .gitignore                  # Git ignore rules
├── ARCHITECTURE.md             # Detailed architecture docs
├── DEPLOYMENT.md               # Production deployment guide
├── CHANGELOG.md                # Version history
├── scripts/
│   └── senator-cycle-v5.sh     # Orchestration: run all 5 senators
├── python/
│   ├── senator-execution.py    # Core: run one senator, parse, write SKP
│   ├── skp_adapter.py          # DB adapter: auto-detect schema, read/write
│   └── skp-cleaner.py          # Cleanup: remove junk entries from SKP
└── docs/
    ├── SENATOR_DOMAINS.md      # Domain configuration reference
    ├── SKP_SCHEMA.md           # Database schema documentation
    └── TROUBLESHOOTING.md      # Common issues and fixes
```

## SKP Database Schema

```sql
CREATE TABLE knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,           -- e.g. "senator-akademisi/insight/20260508-11-00"
    value TEXT NOT NULL,                -- JSON insight data
    category TEXT DEFAULT 'general',    -- domain: akademisi/bisnis/komunitas/pemerintah/media
    tags TEXT DEFAULT '[]',             -- JSON array of tags
    priority INTEGER DEFAULT 5,         -- 1-10 priority
    source_agent_name TEXT DEFAULT 'system',  -- e.g. "senator-akademisi"
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Insight JSON Schema (per Domain)

### Akademisi
```json
{
  "temuan": [{"judul": "...", "detail": "...", "sumber": "...", "dampak_bisnis": "...", "urgensi": "tinggi|sedang|rendah"}],
  "peluang_baru": ["..."],
  "sinyal_lemah": ["..."],
  "confidence": 0.0,
  "timestamp": "2026-05-08 11:00 UTC"
}
```

### Bisnis
```json
{
  "peluang": [{"nama": "...", "detail": "...", "estimasi_nilai": "...", "urgensi": "tinggi|sedang|rendah"}],
  "risiko": [{"nama": "...", "dampak": "...", "probabilitas": "tinggi|sedang|rendah"}],
  "funding_tracker": [{"startup": "...", "amount": "...", "stage": "...", "investor": "..."}],
  "rekomendasi": "...",
  "confidence": 0.0,
  "timestamp": "2026-05-08 11:00 UTC"
}
```

### Komunitas
```json
{
  "isu": [{"topik": "...", "sentiment": "positif|negatif|netral", "intensitas": "tinggi|sedang|rendah", "detail": "...", "platform": "..."}],
  "tokoh_kunci": [{"nama": "...", "handle": "...", "konteks": "..."}],
  "tools_trending": ["..."],
  "sentiment_overall": "positif|negatif|netral|campuran",
  "confidence": 0.0,
  "timestamp": "2026-05-08 11:00 UTC"
}
```

### Pemerintah
```json
{
  "regulasi": [{"nama": "...", "nomor": "...", "lembaga": "...", "tanggal_efektif": "...", "deadline_compliance": "...", "dampak_bisnis": "...", "urgensi": "kritis|tinggi|sedang|rendah"}],
  "program_pemerintah": [{"nama": "...", "anggaran": "...", "cara_akses": "...", "deadline": "..."}],
  "alert_compliance": ["..."],
  "confidence": 0.0,
  "timestamp": "2026-05-08 11:00 UTC"
}
```

### Media
```json
{
  "narasi_dominan": [{"topik": "...", "framing": "...", "sentiment": "positif|negatif|netral", "media_utama": ["..."]}],
  "frekuensi_ai": {"per_minggu": 0, "trend": "naik|turun|stabil"},
  "sentiment_publik": "positif|negatif|netral|campuran",
  "tokoh_tersebut": [{"nama": "...", "konteks": "..."}],
  "confidence": 0.0,
  "timestamp": "2026-05-08 11:00 UTC"
}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | — | OpenRouter API key |
| `OPENROUTER_MODEL` | No | `openai/gpt-4o-mini` | Model to use |
| `SKP_DB_PATH` | No | auto-detect | Path to SQLite database |
| `SCRIPT_DIR` | No | `/root/upshalter-scripts` | Base directory for scripts |
| `UPSHALTER_API` | No | `http://localhost:8100` | Upshalter Cognitive Engine URL |
| `UPSHALTER_API_KEY` | No | — | Upshalter API key (if using Upshalter) |

## Integration with Upshalter Cognitive Engine

Arsify Core can optionally use [Upshalter Cognitive Engine](https://github.com/nousresearch/upshalter-cognitive) as an LLM gateway. However, direct OpenRouter calls are recommended for simplicity.

To use Upshalter:
```bash
export UPSHALTER_API="http://localhost:8100"
export UPSHALTER_API_KEY="your-upshalter-key"
```

The execution engine will try Upshalter first, then fall back to OpenRouter, then Ollama.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Part of Arsify Workforce OS

This is the **intelligence layer** of [Arsify Workforce OS](https://github.com/Arsify-OS):

- **arsify-core** (this repo) — Senator execution engine + SKP
- **arsify-infra** — Infrastructure: Docker, Nginx, PM2, systemd
- **arsify-dashboard** — Web dashboard for intelligence visualization
- **arsify-kurator** — Kurator synthesis engine (coming soon)

---

Built by [Arsify](https://upshalter.com) — AI Workforce Operating System.
