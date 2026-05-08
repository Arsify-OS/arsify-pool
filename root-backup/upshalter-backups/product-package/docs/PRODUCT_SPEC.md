# PENTAHELIX INTELLIGENCE PLATFORM — Product Spec v1.0

> **Status:** MVP-Ready (42% → Target 70% dalam 5-7 hari)  
> **Tanggal:** 2026-05-08  
> **Author:** OWL (Hermes Agent) untuk Upshalter  
> **Lisensi:** Proprietary — All Rights Reserved

---

## 1. EXECUTIVE SUMMARY

Pentahelix Intelligence Platform adalah sistem **AI-Powered Automated Intelligence Briefing** yang menghasilkan laporan intelijen multi-domain secara otomatis menggunakan arsitektur multi-agent.

**Satu kalimat:** *"5 AI analysts bekerja 24/7 memantau landscape Indonesia — bisnis, pemerintah, media, akademisi, komunitas — dan mengirimkan actionable insights ke inbox Anda."*

---

## 2. PROBLEM STATEMENT

| Stakeholder | Masalah |
|---|---|
| **Korporasi** | Tidak ada yang memantau landscape Indonesia secara real-time dan terstruktur |
| **Investor** | Butuh market sensing tapi terlalu mahal untuk research team |
| **Pemerintah** | Perlu policy monitoring tapi manual dan lambat |
| **Media** | Perlu trend detection tapi bergantung pada social listening tools mahal |
| **Startup** | Butuh competitive intelligence tapi tidak ada budget |

**Existing solutions** (Meltwater, Crayon, Brandwatch) mahal ($500-5000/bulan), tidak fokus Indonesia, dan tidak multi-domain.

---

## 3. SOLUTION

### 3.1 Arsitektur Tingkat Tinggi

```
┌─────────────────────────────────────────────────────────────────┐
│                    PENTAHELIX INTELLIGENCE PLATFORM              │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │AKADEMISI │ │ BISNIS   │ │KOMUNITAS │ │PEMERINTAH│ │ MEDIA  ││
│  │ Senator  │ │ Senator  │ │ Senator  │ │ Senator  │ │ Senator││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘│
│       │             │            │             │            │     │
│       └─────────────┴────────────┼────────────┴────────────┘     │
│                                  ▼                                │
│                    ┌─────────────────────────┐                   │
│                    │   SKP KNOWLEDGE POOL    │                   │
│                    │   /data/arsify.db       │                   │
│                    │   421+ entries          │                   │
│                    └────────────┬────────────┘                   │
│                                 ▼                                 │
│                    ┌─────────────────────────┐                   │
│                    │   KURATOR v2            │                   │
│                    │   Consolidation Engine  │                   │
│                    └────────────┬────────────┘                   │
│                                 ▼                                 │
│              ┌──────────────────┼──────────────────┐             │
│              ▼                  ▼                   ▼             │
│     ┌────────────┐    ┌──────────────┐    ┌──────────────┐      │
│     │  Web Dash  │    │  API Endpoint│    │  Delivery    │      │
│     │  (HTML)    │    │  (REST)      │    │  (Telegram/  │      │
│     │            │    │              │    │   Email/WH)  │      │
│     └────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Komponen Detail

#### A. Senator Agents (5 Domain Experts)

| Senator | Domain | Output Format | Schedule |
|---------|--------|---------------|----------|
| Senator Akademisi | Riset AI, pendidikan tinggi, publikasi ilmiah | `{temuan[], sumber[], relevansi_bisnis}` | Setiap 6 jam |
| Senator Bisnis | Startup funding, UMKM digital, e-commerce, ekonomi makro | `{peluang[], risiko[], rekomendasi}` | Setiap 6 jam |
| Senator Komunitas | Sentiment developer, forum, media sosial | `{isu[], sentiment, tokoh_kunci[]}` | Setiap 6 jam |
| Senator Pemerintah | Regulasi digital, kebijakan AI, tender IT | `{regulasi[], dampak_bisnis, compliance_notes[]}` | Setiap 6 jam |
| Senator Media | Narasi berita, framing AI, trending topic | `{narasi_dominan[], framing, sentiment_publik}` | Setiap 6 jam |

**LLM Engine:** OpenRouter API (model: openrouter/owl-alpha)  
**Fallback:** Ollama lokal (CPU-only, last resort)  
**Auth:** X-API-Key header

#### B. SKP Knowledge Pool

- **Database:** SQLite (`/data/arsify.db`)
- **Table:** `knowledge` (key, value, source_agent_name, created_at)
- **Index:** FTS5 full-text search
- **Current state:** 421 entries, 5 domain categories
- **Redis cache:** 6379 (optional, untuk high-frequency reads)

#### C. Kurator Engine

- **Script:** `kurator-v2.py` (Python)
- **Input:** Semua output senator dari SKP (12 jam terakhir)
- **Proses:** Konsolidasi lintas-domain via OpenRouter
- **Output:** Markdown brief + JSON data
- **Confidence score:** 0.0 - 1.0 (berdasarkan jumlah & kualitas input)

#### D. Delivery System

| Channel | Status | Script |
|---------|--------|--------|
| Telegram Bot | ✅ Active | `telegram-alert.sh` |
| Email (SMTP) | ⚠️ Stub | `deliver-intelligence.sh` |
| WhatsApp Business | ❌ Not implemented | - |
| Webhook | ❌ Not implemented | - |
| REST API | ⚠️ Basic | `data.json` endpoint |

#### E. Web Dashboard

- **URL:** data.upshalter.com
- **Tech:** Static HTML + CSS + JS (dark theme)
- **Data source:** `data.json` (updated setiap 30 menit)
- **Features:** Senator status, insight cards, timestamps

---

## 4. FEATURE MATRIX

### 4.1 Current Features (✅ Working)

| Feature | Status | Notes |
|---------|--------|-------|
| 5-senator automated cycle | ✅ | Cron setiap 6 jam |
| SKP knowledge storage | ✅ | SQLite + FTS5 |
| Kurator consolidation | ✅ | Markdown + JSON output |
| Telegram delivery | ✅ | Bot + chat ID configured |
| Web dashboard | ⚠️ | Basic, no auth, no filter |
| PDF report generation | ✅ | fpdf2, single-page brief |
| Health monitoring | ✅ | 5-min cron + Telegram alert |
| SKP backup | ✅ | Daily cron |
| Nginx reverse proxy | ✅ | 26 subdomain configured |
| Docker containerization | ✅ | Senator + Cognitive Engine |

### 4.2 Missing Features (❌ Not Implemented)

| Feature | Priority | Effort |
|---------|----------|--------|
| User authentication | P0 | 2 hari |
| API key per client | P0 | 1 hari |
| Payment/billing system | P0 | 3 hari |
| Content quality improvement | P0 | 2 hari |
| Dashboard filtering/export | P1 | 2 hari |
| Multi-channel delivery (email, WA) | P1 | 2 hari |
| Client self-signup | P1 | 2 hari |
| Tenant isolation | P2 | 3 hari |
| SLA monitoring | P2 | 1 hari |
| Public status page | P2 | 1 hari |
| API documentation (OpenAPI) | P2 | 1 hari |
| Client onboarding flow | P2 | 2 hari |

---

## 5. PRICING TIERS

| Tier | Harga (IDR/bln) | Domain | Delivery | Channel | SLA |
|------|-----------------|--------|----------|---------|-----|
| **Starter** | 2.000.000 | 2 pilihan | Mingguan | Telegram | 95% |
| **Pro** | 5.000.000 | Semua 5 | Harian | Telegram + Email | 99% |
| **Enterprise** | Custom | Custom + API | Real-time | All + Webhook | 99.5% |

**Target market:** Korporasi Indonesia, VC/investor, lembaga pemerintah, media house.

---

## 6. TECH STACK SUMMARY

| Layer | Technology |
|-------|------------|
| Orchestration | Bash cron + Python |
| LLM | OpenRouter API (owl-alpha) |
| Storage | SQLite (FTS5) + Redis |
| Delivery | Telegram Bot API, SMTP |
| Frontend | Static HTML/CSS/JS |
| Infrastructure | Docker + Systemd + Nginx |
| Monitoring | Bash health-check + Telegram alert |
| Backup | Bash cron + SQLite dump |

---

## 7. COMPETITIVE ADVANTAGE

1. **Indonesia-first** — fokus pada landscape Indonesia, bukan global
2. **Multi-domain** — 5 domain dalam 1 platform, bukan 1 dimensi
3. **Automated end-to-end** — dari scraping sampai delivery, zero manual
4. **Affordable** — 2-5 juta/bulan vs kompetitor 500-500 USD/bulan
5. **Customizable** — bisa tambah domain baru dengan tambah senator

---

## 8. RISK & MITIGATION

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenRouter API down | Pipeline berhenti | Ollama fallback (CPU-only) |
| Content quality rendah | Client churn | Prompt engineering + validation layer |
| Single point of failure | Downtime | Docker auto-restart + health check |
| Data privacy breach | Legal | Tenant isolation + API key per client |
| Scaling limit (1 VPS) | Performance | Horizontal scaling ready (Docker) |

---

## 9. ROADMAP

### MVP (5-7 hari) — Target: Sellable
- [ ] Prompt overhaul untuk content quality
- [ ] Auth system + API keys
- [ ] Dashboard dengan filter + export
- [ ] Billing stub (manual payment)
- [ ] Email delivery
- [ ] Getting started docs

### v1.1 (2-3 minggu) — Target: Scalable
- [ ] Payment gateway integration
- [ ] Self-signup flow
- [ ] Client portal
- [ ] SLA monitoring
- [ ] Public status page

### v1.2 (1-2 bulan) — Target: Enterprise
- [ ] Multi-tenant isolation
- [ ] White-label support
- [ ] Custom domain per client
- [ ] Advanced analytics
- [ ] WhatsApp Business integration

---

*Dokumen ini adalah living document. Update setiap ada perubahan signifikan.*
