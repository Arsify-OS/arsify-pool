# Arsify Core — Architecture Documentation

## System Overview

Arsify Core adalah **intelligence execution engine** yang menjalankan AI Senator secara periodik, menghasilkan structured insights, dan menyimpannya ke Shared Knowledge Pool (SKP).

## Core Components

### 1. senator-execution.py (555 lines)

**Tugas:** Menjalankan satu Senator (analyst) dari awal hingga selesai.

**Alur:**

```
Input: domain (akademisi/bisnis/komunitas/pemerintah/media)
  │
  ├─ 1. Load domain config (system prompt + user prompt + JSON schema)
  ├─ 2. Inject memory context (insight terbaru dari SKP untuk domain ini)
  ├─ 3. Call LLM:
  │     ├─ Primary: OpenRouter API (verified working)
  │     └─ Fallback: Ollama local
  ├─ 4. Parse response:
  │     ├─ Extract JSON blocks (code blocks, raw, bracket matching)
  │     ├─ Parse per-field (temuan, peluang, risiko, regulasi, isu, narasi)
  │     └─ Fallback: parse free text (paragraph/split)
  ├─ 5. Validate: is_junk_response() — reject jika mengandung prompt patterns
  └─ 6. Write structured insights to SKP via skp_adapter
```

**Junk Detection Patterns:**
- "step: analyze and understand"
- "anda adalah senator" / "kamu adalah senator"
- "## misi inti" / "soul.md"
- Response < 100 chars
- Analysis keys tanpa insight markers

**Domain Configuration:**

Setiap domain punya:
- `system`: System prompt yang mendefinisikan peran senator
- `prompt`: User prompt dengan instruksi + JSON schema yang diminta
- `insight_fields`: List field yang diekstrak dari JSON response
- `key_prefix`: Prefix untuk SKP key

### 2. skp_adapter.py (333 lines)

**Tugas:** Universal adapter untuk read/write ke SKP database.

**Features:**
- Auto-detect DB path (`/data/arsify.db`, `/data/shared_knowledge_pool.db`, dll)
- Auto-detect table name (`knowledge`, `memory_notes`)
- Auto-detect key format (legacy vs baru)
- Schema-aware INSERT (handle kolom yang berbeda-beda)
- Memory context read (recent entries per domain)

**DB Candidates (priority order):**
1. `$SKP_DB_PATH` env var
2. `/data/arsify.db` (symlink, production)
3. `/data/shared_knowledge_pool.db` (direct)
4. `/root/.upshalter/shared_knowledge_pool.db` (upshalter native)

### 3. skp-cleaner.py (214 lines)

**Tugas:** Bersihkan junk entries dari SKP.

**Junk Classification:**
- Contains prompt patterns ("Step: Analyze", "Anda adalah Senator", dll)
- Too short (< 150 chars untuk non-analysis keys)
- Analysis keys tanpa insight markers (universitas, startup, Kementerian, etc)

**Safe to Delete:**
- System config entries (cognitive pipeline, port allocation, fallback chain)
- Execution results ("Task: Process request\nResult: successfully executed")
- Prompt artifacts ("Step: Analyze and understand: ...")

**Keep:**
- Curated analysis entries (usually 200+ chars dengan real content)
- Kurator synthesis entries
- Konsolidasi reports
- Real senator insights (domain/temuan, domain/peluang, etc.)

### 4. senator-cycle-v5.sh (84 lines)

**Tugas:** Orkestrasi — jalankan semua 5 Senator dan track results.

**Flow:**
1. Check `senator-execution.py` exists
2. Loop: akademisi → bisnis → komunitas → pemerintah → media
3. Parse JSON result per domain
4. Log summary: X/5 success, Y failed, Z total SKP entries
5. Optional: send Telegram notification
6. Trigger kurator 5 minutes after completion (background)

## LLM Fallback Chain

```
OpenRouter (primary)
  ↓ (if failed)
Ollama local (fallback)
  ↓ (if failed)
Return error — senator marked as failed
```

**Note:** Upshalter Cognitive Engine dapat digunakan sebagai primary gateway, tapi saat ini direct OpenRouter lebih reliable karena:
- Upshalter `/v1/portsocket` return pipeline metadata, bukan raw LLM text
- Upshalter fast path `/chat` requires Ollama (Currently not running)
- OpenRouter key already verified working

## Memory Injection

Setiap senator baca insights sebelumnya dari domain yang sama (24 jam terakhir, max 2 entries) dan inject ke prompt sebagai context. Ini mencegah:
- Duplikasi insights
- Konten yang sama setiap cycle
- Senator "lupa" apa yang sudah ditemukan

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     VPS (upshalter.com)                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Crontab                                            │    │
│  │  0 */6 * * * → senator-cycle-v5.sh                  │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  senator-cycle-v5.sh                                │    │
│  │  Loop: run senator-execution.py untuk 5 domain      │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  senator-execution.py (per domain)                  │    │
│  │  1. Build prompt + memory context                   │    │
│  │  2. Call OpenRouter API                             │    │
│  │  3. Parse JSON response                             │    │
│  │  4. Validate + write to SKP                         │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  skp_adapter.py                                     │    │
│  │  Read/write to /data/arsify.db                      │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  SQLite: /data/arsify.db                            │    │
│  │  Table: knowledge                                   │    │
│  │  353+ real intelligence entries                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Upshalter Cognitive Engine :8100 (optional)           │    │
│  │  Dual mode: Fast path (Ollama) / Cognitive path     │    │
│  │  Auth: X-API-Key header                             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Cycle N:
  Senator Akademisi:
    1. Read memory: cycle N-1 insights for akademisi
    2. Build prompt: "Based on previous findings: [memory]. Now find NEW insights."
    3. Call LLM → JSON response
    4. Parse: 5 temuan + 2 peluang + 1 sinyal lemah
    5. Write: 8 individual SKP entries with keys:
       - senator-akademisi/insight/20260508-12-00
       - senator-akademisi/insight/20260508-12-01
       - senator-akademisi/insight/20260508-12-02
       ...

  [Repeat for all 5 domains]

Cycle N+1 (6 hours later):
  Senator Akademisi:
    1. Read memory: cycle N insights (8 entries from 6 hours ago)
    2. Build prompt: "Previous cycle found: [8 insights summarized]. Find DIFFERENT/New updates."
    3. ...
```

## Key Design Decisions

### 1. Why structured JSON instead of free text?
- Parsing free text reliably is hard
- JSON schema ensures consistent output structure
- Easy to validate, filter, and query
- Langsung bisa di-consume oleh dashboard/UI

### 2. Why 5 specific domains?
Setiap domain punya:
- Fokus intelligence yang berbeda
- JSON schema yang berbeda
- Senator persona yang berbeda
- Terinspirasi dari Pentahelix model (academia, business, government, community, media)

### 3. Why OpenRouter instead of direct OpenAI/Anthropic?
- Single API for multiple models
- Model switching tanpa code change
- Cost-effective untuk multi-model setup

### 4. Why SQLite instead of PostgreSQL?
- Zero configuration
- Single file, easy backup
- Sufficient untuk current scale (hundreds of entries/day)
- Can migrate to PostgreSQL later if needed

## Future Roadmap

- [ ] Integrate dengan Upshalter Cognitive Engine (ketika L3/L4 pipeline stabil)
- [ ] PostgreSQL migration untuk scale
- [ ] REST API untuk query SKP
- [ ] Web dashboard untuk visualisasi insights
- [ ] Kafka/RabbitMQ untuk async processing
- [ ] Multi-language support (EN/ZH)
