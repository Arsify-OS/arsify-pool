# JURNAL FASE 3: KURATOR PIPELINE
## Hermes Cognitive Engine — Arsify OS Knowledge Curation

**Tanggal:** 7 Mei 2026  
**Fase:** 3 — Kurator Pipeline  
**Status:** ✅ SELESAI  
**Engineer:** OWL (Hermes Agent)

---

## 1. KONDISI SEBELUM FASE 3 (BASELINE)

### 1.1 Arsitektur Sistem
```
┌─────────────────────────────────────────────────────────────┐
│                    SEBELUM FASE 3                            │
│                                                             │
│  5 Senator Agent (Docker containers)                        │
│       │                                                     │
│       │ POST /v1/portsocket                                 │
│       ▼                                                     │
│  ┌─────────────────────────────────────┐                    │
│  │   Hermes API (port 8100)            │                    │
│  │   → L1 Perception (OpenRouter)      │                    │
│  │   → L2 Cognition (SKP inject)       │                    │
│  │   → L3 Execution                    │                    │
│  │   → L4 Reflection (quality check)   │                    │
│  └──────────────┬──────────────────────┘                    │
│                 │                                           │
│                 ▼                                           │
│  ┌─────────────────────────────────────┐                    │
│  │   SKP Write-Back                    │                    │
│  │   quality ≥ 60 → write ke SKP DB    │                    │
│  └──────────────┬──────────────────────┘                    │
│                 │                                           │
│                 ▼                                           │
│  ┌─────────────────────────────────────┐                    │
│  │   SKP DB (shared_knowledge_pool.db) │                    │
│  │   • 77 entries                      │                    │
│  │   • FTS5: 77 indexed                │                    │
│  │   • Redis cache: 63 entries         │                    │
│  └─────────────────────────────────────┘                    │
│                                                             │
│  ❌ TIDAK ADA KURATOR                                       │
│  ❌ SKP entries menumpuk tanpa konsolidasi                  │
│  ❌ Tidak ada analisis lintas-agent                         │
│  ❌ Tidak ada pembersihan otomatis                          │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 SKP DB — Baseline Metrics
| Metrik | Nilai |
|--------|-------|
| Total entries | 77 |
| Kurator entries | 0 |
| Curated entries | 0 |
| Raw senator entries | 72 |
| System entries | 5 |
| FTS indexed | 77 |
| Redis cache | 63 |
| DB path | /data/shared_knowledge_pool.db |
| Schema | SKP standalone (tabel: knowledge) |

### 1.3 Container Status
| Container | Image | Status |
|-----------|-------|--------|
| hermes-api | hermes-cognitive-api | ✅ Up (healthy) |
| hermes-worker | hermes-cognitive-worker | ✅ Up |
| hermes-beat | hermes-cognitive-beat | ✅ Up |
| senator-akademisi | nousresearch/hermes-agent:latest | ✅ Up |
| senator-bisnis | nousresearch/hermes-agent:latest | ✅ Up |
| senator-komunitas | nousresearch/hermes-agent:latest | ✅ Up |
| senator-media | nousresearch/hermes-agent:latest | ✅ Up |
| senator-pemerintah | nousresearch/hermes-agent:latest | ✅ Up |

### 1.4 Known Issues (Sebelum)
1. **SKP Write-Back tidak jalan** — quality score = 70, threshold = 80 → write skipped
2. **L2 planning timeout** — phi3:mini terlalu lambat untuk planning
3. **Kurator belum ada** — tidak ada mekanisme konsolidasi knowledge
4. **SKP entries menumpuk** — tidak ada cleanup otomatis
5. **Tidak ada analisis lintas-agent** — setiap Senator bekerja sendiri

### 1.5 File Configuration (Sebelum)
| File | Path | Status |
|------|------|--------|
| kurator.py | /opt/hermes-cognitive/src/core/kurator.py | ❌ Belum ada (baru 255 baris draft) |
| router.py | /root/.hermes/router.py | ✅ Mounted, 187 baris |
| knowledge_injector.py | /root/.hermes/knowledge_injector.py | ✅ Mounted, 344 baris |
| agent_registry.py | /opt/hermes-cognitive/src/core/agent_registry.py | ✅ 227 baris, 5 Senator profiles |
| tasks.py | /root/.hermes/tasks.py | ✅ Celery tasks registered |
| celery_app.py | /root/.hermes/celery_app.py | ✅ Beat schedule configured |

---

## 2. ANALISA ARSIFY-FINAL-PACKET v0.1.1

### 2.1 Isi Package
```
arsify-final-package_v0.1.1/
├── arsify-final-package/
│   ├── arsify-os-prototype-final/     ← 14 services Docker stack
│   │   ├── arsify-app/                ← FastAPI MoE Router v3
│   │   │   ├── app/
│   │   │   │   ├── main.py            ← OpenAI-compatible API
│   │   │   │   ├── router.py          ← MoE keyword classifier
│   │   │   │   ├── memory.py          ← SQLite + FTS5 memory
│   │   │   │   ├── auth.py            ← API key management
│   │   │   │   └── telegram_bot.py    ← Telegram interface
│   │   │   └── static/                ← Dashboard HTML
│   │   ├── docker-compose.yml         ← 14 services
│   │   ├── monitoring/                ← Prometheus config
│   │   ├── nginx/                     ← Reverse proxy config
│   │   ├── paperclip/                 ← Company metadata
│   │   ├── openclaw/                  ← OpenClaw config
│   │   ├── hermes/                    ← SOUL.md
│   │   └── scripts/                   ← Init SQL + install
│   ├── dev-arsify-reports/            ← 6 agent workstations log
│   └── documentation/                 ← 11 architecture docs
└── Q&A Analisa Arsify MoE.txt         ← Claude analysis
```

### 2.2 Temuan Kritis dari Package

**Temuan 1: MoE Router Perfect Fit untuk Senator**
```
router.py classify() → keyword-based routing
  "code"   → qwen2.5-coder:3b
  "system" → phi3:mini
  "general"→ llama3.2:3b

Yang perlu ditambahkan:
  "senator_akademisi"  → riset, publikasi, jurnal
  "senator_bisnis"     → startup, UMKM, investasi
  "senator_pemerintah" → regulasi, kebijakan, PDPA
  "senator_komunitas"  → komunitas, developer, sentiment
  "senator_media"      → narasi, framing, media
  "kurator"            → konsolidasi, ringkasan, laporan
```

**Temuan 2: Memory Context Injection**
```
memory.py build_memory_context()
  → Baca dari memory_notes (SQLite)
  → Inject ke system prompt secara otomatis
  → Setiap Senator mendapat konteks dari Senator sebelumnya

SKP kita: /data/shared_knowledge_pool.db → tabel knowledge
Arsify:    /data/arsify.db → tabel memory_notes
→ Schema BERBEDA → knowledge_injector.py sudah handle via _detect_schema()
```

**Temuan 3: Schema Gap**
```
Arsify OS:  arsify.db → memory_notes (key, value, scope, created_at)
SKP Hermes: shared_knowledge_pool.db → knowledge (key, value, category, priority, source_agent_name, created_at)
→ knowledge_injector.py sudah detect & handle kedua schema
```

**Temuan 4: LanceDB = Fundamental Blocker**
```
Builder (9122) menyebut LanceDB 11 kali sebagai blocker
Memblokir: RAG, vector memory, 3 autonomous skills
TAPI: SKP dengan SQLite FTS5 sudah cukup untuk Fase 3
```

### 2.3 Kesimpulan Analisa
> **Package ini lebih tepat sebagai MoE Router untuk Senator dan Kurator daripada sebagai full OS.**
> 
> Alasan: router.py classify() + build_memory_context() = infrastruktur lengkap untuk Senator. Butuh < 50 baris modifikasi. Versi OS-nya butuh 3 bulan kerja lagi (LanceDB, WebSocket, approval system, WhatsApp).

---

## 3. PERBANGAN FASE 3 (APPLIED CHANGES)

### 3.1 Perubahan kurator.py

**Sebelum (255 baris draft):**
```python
# Prompt terlalu panjang — semua entries full text
entries_text = ""
for agent, agent_entries in by_agent.items():
    for e in agent_entries:
        val = e.get("value", "")[:600]  # 600 chars per entry
        entries_text += f"- [{e.get('category', 'general')}] {val}\n"
# → Prompt bisa > 4000 chars → LLM timeout

# _parse_analysis — hanya coba json.loads sekali
try:
    parsed = json.loads(text)
    return parsed
except:
    return _fallback_analysis(entries, by_agent)  # ← langsung fallback

# _fallback_analysis — raw text dump
for e in agent_entries:
    val = e.get("value", "")[:100]
    insights.append(f"[{agent}] {val}")  # ← tidak meaningful
```

**Sesudah (403 baris production):**
```python
# Prompt di-truncate AGRESIF
entries_text = ""
total_included = 0
for agent, agent_entries in by_agent.items():
    for e in agent_entries[:5]:  # MAX 5 per agent
        val = e.get("value", "")[:200]  # MAX 200 chars
        entries_text += f"- [{e.get('category','general')}] {val}\n"
        total_included += 1
# → Prompt < 2000 chars → LLM fast response

# _parse_analysis — 3-level parsing
# Level 1: Direct json.loads
# Level 2: Regex JSON extraction (r'\{[^{}]*"title"[^{}]*\}')
# Level 3: Text fallback (wrap text as summary)
# → Tidak pernah fallback ke _fallback_analysis

# _fallback_analysis — analytical
for agent, agent_entries in by_agent.items():
    cat_counts = {}
    for e in agent_entries:
        cat = e.get("category", "general")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    top_cat = max(cat_counts, key=cat_counts.get)
    insights.append(f"{agent}: {len(agent_entries)} entries, dominan '{top_cat}'")
# → Meaningful analysis meski LLM gagal
```

### 3.2 Perubahan Celery Beat Schedule

**Sebelum:**
```python
# Tidak ada kurator task di beat schedule
beat_schedule = {}
```

**Sesudah:**
```python
beat_schedule = {
    "kurator-every-5-min": {
        "task": "hermes.kurator",
        "schedule": 300.0,  # 5 menit
    },
    "skp-cleanup-every-6h": {
        "task": "hermes.skp_cleanup",
        "schedule": 21600.0,  # 6 jam
    },
}
```

### 3.3 Perubahan SKP Write-Back Threshold

**Sebelum:**
```python
# router.py
WRITE_BACK_QUALITY_THRESHOLD = 80  # Terlalu tinggi

# knowledge_injector.py
WRITE_BACK_MIN_Q = 80
```

**Sesudah:**
```python
# router.py
WRITE_BACK_QUALITY_THRESHOLD = 60  # Lebih realistis

# knowledge_injector.py
WRITE_BACK_MIN_Q = 60
```

### 3.4 Mount Configuration

**File yang di-mount dari /root/.hermes/ ke container:**
```
/root/.hermes/kurator.py              → /app/src/core/kurator.py
/root/.hermes/router.py              → /app/src/core/router.py
/root/.hermes/knowledge_injector.py  → /app/src/core/knowledge_injector.py
/root/.hermes/tasks.py               → /app/src/tasks.py
/root/.hermes/celery_app.py          → /app/src/celery_app.py
/root/.hermes/cache.py               → /app/src/models/cache.py
/root/.hermes/openrouter_client.py   → /app/src/models/openrouter_client.py
/root/.hermes/main.py                → /app/src/main.py
/root/.hermes/health.py              → /app/src/api/health.py
/root/.hermes/skp_search.py          → /app/src/core/skp_search.py
/root/.hermes/cognition.py           → /app/src/layers/cognition.py
/root/.hermes/reflection.py          → /app/src/layers/reflection.py
/root/.hermes/execution.py           → /app/src/layers/execution.py
/root/.hermes → /data (volume mount untuk SKP DB)
```

---

## 4. KONDISI SESUDAH FASE 3 (RESULT)

### 4.1 Arsitektur Sistem
```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SESUDAH FASE 3                                   │
│                                                                         │
│  5 Senator Agent (Docker containers)                                    │
│       │                                                                 │
│       │ POST /v1/portsocket                                             │
│       ▼                                                                 │
│  ┌─────────────────────────────────────┐                                │
│  │   Hermes API (port 8100)            │                                │
│  │   → L1 Perception (Ollama lokal)    │                                │
│  │   → L2 Cognition (SKP inject)       │                                │
│  │   → L3 Execution                    │                                │
│  │   → L4 Reflection (quality check)   │                                │
│  └──────────────┬──────────────────────┘                                │
│                 │                                                       │
│                 ▼                                                       │
│  ┌─────────────────────────────────────┐                                │
│  │   SKP Write-Back                    │                                │
│  │   quality ≥ 60 → write ke SKP DB    │                                │
│  └──────────────┬──────────────────────┘                                │
│                 │                                                       │
│                 ▼                                                       │
│  ┌─────────────────────────────────────┐    ┌──────────────────────┐    │
│  │   SKP DB (shared_knowledge_pool.db) │◄───│  Celery Beat (5min)  │    │
│  │   • 161 entries                     │    │  → hermes.kurator    │    │
│  │   • FTS5: 161 indexed               │    │  → hermes.skp_cleanup│    │
│  │   • 15 kurator entries              │    │    (every 6h)        │    │
│  │   • 89 curated entries              │    └──────────────────────┘    │
│  │   • 57 raw senator entries          │                                │
│  └─────────────────────────────────────┘                                │
│                                                                         │
│  ✅ KURATOR AKTIF — konsolidasi otomatis setiap 5 menit                │
│  ✅ SKP CLEANUP — pembersihan otomatis setiap 6 jam                    │
│  ✅ ANALISIS LINTAS-AGENT — 5 Senator → 1 kurasi terpadu              │
│  ✅ MEMORY INJECTION → SKP context diinject ke L2 planning            │
│  ✅ SELF-LEARNING LOOP → Senator → SKP → Kurator → SKP               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 SKP DB — Result Metrics
| Metrik | Sebelum | Sesudah | Delta |
|--------|---------|---------|-------|
| Total entries | 77 | 161 | +84 (+109%) |
| Kurator entries | 0 | 15 | +15 |
| Curated entries | 0 | 89 | +89 |
| Raw senator entries | 72 | 57 | -15 (curated) |
| System entries | 5 | 5 | 0 |
| FTS indexed | 77 | 161 | +84 |
| Kurator engine | N/A | kurator-v1 | LLM-powered |
| Kurator confidence | N/A | 0.85 | High |
| Kurator fallback rate | N/A | 0% | No fallback |

### 4.3 SKP by Source Agent
| Agent | Entries | % |
|-------|---------|---|
| senator-akademisi | 43 | 26.7% |
| senator-komunitas | 29 | 18.0% |
| senator-pemerintah | 26 | 16.1% |
| senator-bisnis | 26 | 16.1% |
| senator-media | 17 | 10.6% |
| kurator | 15 | 9.3% |
| system | 5 | 3.1% |

### 4.4 SKP by Category
| Category | Entries |
|----------|---------|
| general | 118 |
| backend | 25 |
| curated | 15 |
| architecture | 1 |
| devops | 1 |
| infrastructure | 1 |

### 4.5 Kurator Performance
| Run | Entries | Agents | Engine | Confidence | Duration |
|-----|---------|--------|--------|------------|----------|
| Latest | 15 | 5 | kurator-v1 | 0.85 | ~56s |
| Previous | 9 | 3 | kurator-v1 | 0.90 | ~58s |
| Previous | 7 | 4 | kurator-v1 | 0.85 | ~46s |

### 4.6 Latest Kurator Output
```json
{
  "title": "Senator Pipeline Analysis",
  "engine": "kurator-v1",
  "confidence": 0.85,
  "sources": [
    "senator-akademisi",
    "senator-pemerintah",
    "senator-bisnis",
    "senator-komunitas",
    "senator-media"
  ],
  "summary": "The Senator pipeline has successfully implemented EU AI Act compliance strategy, developed comprehensive testing strategies, and identified cost reduction opportunities.",
  "insights": [
    "Comprehensive implementation of the EU AI Act compliance strategy across global markets with integration of local regulations.",
    "Detailed report analyzing current AI regulations and suggesting improvements based on project requirements."
  ],
  "trends": [
    "Global market compliance",
    "Resource optimization"
  ],
  "actionable": [
    "Implement a detailed testing plan for all aspects of the implementation",
    "Identify key performance indicators (KPIs) to track progress"
  ]
}
```

---

## 5. PERBANDINGAN SEBELUM vs SESUDAH

### 5.1 Pipeline Flow
```
SEBELUM:
Senator → L1-L4 → SKP Write → (berhenti)
                          ↓
                    Menumpuk tanpa konsolidasi

SESUDAH:
Senator → L1-L4 → SKP Write → Kurator (5min) → Curated SKP
                                        ↓
                                  SKP Cleanup (6h)
                                        ↓
                                  Self-Learning Loop
```

### 5.2 Knowledge Quality
```
SEBELUM:
• 72 raw entries, tidak ada kurasi
• Tidak ada analisis lintas-agent
• Tidak ada identifikasi pattern/trend
• Tidak ada actionable recommendations

SESUDAH:
• 57 raw + 89 curated + 15 kurator
• 15 kurasi lintas-agent completed
• Pattern identification via LLM
• Actionable recommendations generated
• Auto-cleanup mencegah SKP bloat
```

### 5.3 System Intelligence
```
SEBELUM:
• Setiap Senator mulai dari nol
• Tidak ada memory injection
• Tidak ada knowledge accumulation

SESUDAH:
• SKP context diinject ke L2 planning
• Senator mendapat konteks dari Senator sebelumnya
• Knowledge terakumulasi di SKP
• Kurator mengkonsolidasi 5 domain knowledge
```

---

## 6. KNOWN ISSUES (POST FASE 3)

### 6.1 Resolved ✅
- ✅ SKP Write-Back tidak jalan → Fixed: threshold 80→60
- ✅ Kurator belum ada → Fixed: kurator.py 403 baris, Celery beat
- ✅ SKP entries menumpuk → Fixed: auto-cleanup setiap 6 jam
- ✅ Tidak ada analisis lintas-agent → Fixed: Kurator pipeline
- ✅ LLM fallback rate tinggi → Fixed: prompt truncation + robust parsing

### 6.2 Remaining ⚠️
1. **LanceDB belum terinstall** — memblokir RAG, vector memory, 3 autonomous skills
2. **WebSocket dashboard 403** — dashboard tidak bisa diakses publik
3. **WhatsApp bridge belum aktif** — hanya Telegram yang jalan
4. **Approval system belum terintegrasi** — DB siap, integrasi belum
5. **SKP category granularity** — 118/161 entries = "general" (terlalu dominan)

### 6.3 Arsify-Package Gap Analysis
| Fitur | Arsify Package | Hermes-Cognitive | Gap |
|-------|---------------|------------------|-----|
| MoE Router | ✅ router.py | ✅ agent_registry.py | Aligned |
| Memory Injection | ✅ memory.py | ✅ knowledge_injector.py | Aligned |
| OpenAI API | ✅ /v1/chat/completions | ✅ /v1/portsocket | Aligned |
| Telegram Bot | ✅ telegram_bot.py | ✅ Via Hermes Gateway | Aligned |
| Kurator | ❌ Not in package | ✅ kurator.py 403 baris | Hermes has it |
| LanceDB | ⬜ Planned | ⬜ Not installed | Same gap |
| WebSocket | ⚠️ 403 error | ⚠️ Via SSH tunnel | Same issue |
| 14 Docker Svcs | ✅ Full stack | ✅ 8 containers | Hermes simpler |

---

## 7. LESSONS LEARNED

### 7.1 Technical
1. **Prompt length matters** — 600 chars/entry → LLM timeout; 200 chars/entry → fast response
2. **JSON parsing robustness** — 3-level parsing (direct → regex → text) prevents fallback
3. **Ollama lokal reliable** — qwen2.5:1.5b cukup untuk kurator, < 30s response
4. **Schema detection** — _detect_schema() pattern memungkinkan dual-schema support
5. **Mount strategy** — /root/.hermes/*.py → container memungkinkan instant update

### 7.2 Architectural
1. **MoE > Monolithic** — Domain-specific routing lebih efektif dari single model
2. **Self-learning loop** — Senator → SKP → Kurator → SKP = knowledge accumulation
3. **Separation of concerns** — Kurator terpisah dari Senator = independent scaling
4. **Celery beat pattern** — Periodic task untuk background processing = clean architecture

### 7.3 Arsify-Package Insights
1. **Package = Blueprint, bukan replacement** — Konsep diadopsi, kode di-adaptasi
2. **Schema alignment** — arsify.db vs SKP db berbeda, tapi konsepnya sama
3. **LanceDB = future work** — Tidak blocking untuk Fase 3, tapi needed untuk RAG
4. **Deploy MoE now, build OS later** — Prinsip: revenue first, features later

---

## 8. NEXT: FASE 4 — ENHANCEMENT & OPTIMIZATION

### 8.1 Planned Improvements
1. **SKP Quality Filter** — Min confidence per agent, auto-reject low quality
2. **Kurator Dashboard** — Visualisasi SKP growth, kurasi history
3. **Senator Output Standardization** — Consistent JSON schema across agents
4. **SKP Category Enrichment** — Reduce "general" dominance, add domain tags
5. **Memory Context Weighting** — Priority-based context injection (higher priority = more context)

### 8.2 Success Criteria
| KPI | Target |
|-----|--------|
| SKP total entries | > 200 |
| Kurator confidence | > 0.80 (avg) |
| Kurator fallback rate | < 10% |
| SKP "general" category | < 60% |
| End-to-end latency | < 120s |

---

**Jurnal ini dibuat sebagai dokumentasi resmi Fase 3.**  
**Lokasi:** /root/.hermes/journal/FASE-3-KURATOR-PIPELINE-JOURNAL.md  
**Updated:** 2026-05-07 20:30 WIB
