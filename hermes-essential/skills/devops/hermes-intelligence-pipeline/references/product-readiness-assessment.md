# Product Readiness Assessment — Pentahelix Editorial Pipeline

**Audit Date:** 8 Mei 2026  
**Auditor:** OWL (Hermes Agent)  
**Scope:** Full VPS infrastructure audit → product readiness scoring

---

## 10-Dimension Scoring Framework

| # | Dimension | Weight | Score | Notes |
|---|-----------|--------|-------|-------|
| 1 | Core Engine / Pipeline | 10% | 8/10 | End-to-end automated senator→SKP→kurator→brief→publish |
| 2 | Data Output & Storage | 10% | 7/10 | 421 SKP entries, SQLite+FTS5, JSON API. 80% category="general" un-enriched |
| 3 | Content Quality | 10% | 4/10 | Quality 70-80/100. Output descriptive/confirmatory, not deep insight. No real data feed |
| 4 | Web Dashboard / Product Surface | 10% | 5/10 | data.upshalter.com exists (dark theme HTML). Static, no filter/auth/export |
| 5 | Delivery & Notification | 10% | 4/10 | Telegram bot + deliver-intelligence.sh exist. Only 1 test subscriber, no multi-channel |
| 6 | Authentication & Billing | 10% | 2/10 | subscribers.json with tier pricing exists. No payment gateway, no per-client API key |
| 7 | Multi-tenancy / Isolation | 10% | 2/10 | All shared. No tenant isolation, no per-client data separation |
| 8 | Reliability & Monitoring | 10% | 5/10 | Health check 5min, Telegram alert, backup cron. No SLA, no uptime tracking, limited auto-recovery |
| 9 | Documentation & UX | 10% | 3/10 | Skill docs complete, journals per phase. No user guide, no API docs for clients |
| 10 | Onboarding & Client Mgmt | 10% | 2/10 | onboard-client.sh basic. No self-signup, no client portal |

**TOTAL: 42 / 100 = 42% Ready**

---

## Roadmap to 100%

### Phase A: Content Quality (+4 poin) — 2-3 hari
- A1. Prompt Engineering Overhaul: specific prompts, few-shot examples, anti-platitude
- A2. Real Data Feed: Google News RSS (done), Twitter/X API, Reddit, Kaskus scraping
- A3. Output Validation: schema validation per domain, auto-retry on low quality

### Phase B: Product Surface (+3 poin) — 2-3 hari
- B1. Dashboard: filter by domain/date/sentiment, export PDF/CSV, real-time update
- B2. REST API: `/api/v1/insights?domain=xxx&date=xxx`, API key per client, rate limiting
- B3. Authentication: login system, API key management, roles (admin/client/viewer)

### Phase C: Billing & Multi-Tenancy (+6 poin) — 3-4 hari
- C1. Payment Gateway: Stripe/Xendit/Midtrans, invoice generation, subscription management
- C2. Tenant Isolation: per-client data filter, custom domain, white-label ready
- C3. Pricing Enforcement: domain limit per tier, delivery frequency, usage tracking

### Phase D: Delivery (+4 poin) — 1-2 hari
- D1. Multi-Channel: Telegram (done), Email (SMTP/Resend), WhatsApp Business API, Webhook
- D2. Delivery Scheduling: per-client preference, digest mode, on-demand pull

### Phase E: Reliability (+3 poin) — 1-2 hari
- E1. SLA Monitoring: uptime tracking, 99.5% target, auto-alert on pipeline failure
- E2. Auto-Recovery: container auto-restart, exponential backoff retry, dead letter queue
- E3. Status Page: public status.upshalter.com, real-time component health

### Phase F: Docs & Onboarding (+6 poin) — 2-3 hari
- F1. Client Docs: getting started, API docs, pricing page, FAQ
- F2. Self-Service: signup form → auto-provision, 7-day trial, onboarding email
- F3. Client Portal: dashboard with usage/billing/settings

### Milestones
| Milestone | Score | Cumulative | Estimated |
|-----------|-------|------------|-----------|
| Current | 42% | 42% | — |
| +Phase A | +4% | 46% | Day 3 |
| +Phase B | +3% | 49% | Day 6 |
| +Phase C | +6% | 55% | Day 10 |
| +Phase D | +4% | 59% | Day 12 |
| +Phase E | +3% | 62% | Day 14 |
| +Phase F | +6% | 68% | Day 17 |

**100% = enterprise-grade. 70%+ = MVP-ready for early-stage sales.**
**MVP-Ready (70%): ~5-7 hari kerja by prioritizing A+B+D (quick wins).**

---

## Actual Infrastructure Snapshot (8 Mei 2026)

### Systemd Services — 19 hermes-*.service
| Service | Port | Status |
|---------|------|--------|
| hermes-upshalter | :9120 | ⚠️ activating (restart loop) |
| hermes-archivist | :9124 | ✅ active |
| hermes-frontend | :9125 | ✅ active |
| hermes-backend | :9126 | ✅ active |
| hermes-workstation | :9127 | ✅ active |
| hermes-flowforce | :9128 | ✅ active |
| hermes-api | :9135 | ✅ active |
| hermes-loyx | :9136 | ❌ dead |
| hermes-dev | :9137 | ❌ dead |
| hermes-orchestrator | :8000 | ✅ active |
| hermes-upshalternal | :8645 | ✅ active |
| hermes-internet | — | ✅ active |
| hermes-backup | — | ❌ dead (timing-based) |
| terminal-upshalter | — | ⚠️ activating (restart loop) |
| tunnel-upshalternal | — | ✅ active |
| hermes-Infrastructure | :9121 | EXISTS (not in original 7 role models) |
| hermes-dashboard-bridge | — | EXISTS (not in original 7 role models) |
| hermes-builder | :9122 | EXISTS (not in original 7 role models) |
| hermes-lingkungan-hidup | :9142 | EXISTS (not in original 7 role models) |
| hermes-pariwisata | :9139 | EXISTS (not in original 7 role models) |
| hermes-finansial | :9140 | EXISTS (not in original 7 role models) |
| hermes-operation | :9134 | EXISTS (not in original 7 role models) |

### Docker Containers — 12 total
| Container | Image | Status |
|-----------|-------|--------|
| hermes-api | hermes-cognitive-api | ✅ Up 13h (healthy) |
| hermes-worker | hermes-cognitive-worker | ✅ Up 12h |
| hermes-beat | hermes-cognitive-beat | ✅ Up 12h |
| senator-pemerintah | nousresearch/hermes-agent:latest | ✅ Up |
| senator-media | nousresearch/hermes-agent:latest | ✅ Up |
| senator-bisnis | nousresearch/hermes-agent:latest | ✅ Up |
| senator-komunitas | nousresearch/hermes-agent:latest | ✅ Up |
| senator-akademisi | nousresearch/hermes-agent:latest | ✅ Up |
| hermes-workspace-fresh-... | ghcr.io/outsourc-e/hermes-workspace | ❌ Exited (143) |
| hermes-gamedev | nousresearch/hermes-agent:latest | ❌ Exited (143) |
| hermes-loyx | nousresearch/hermes-agent:latest | ❌ Exited (143) |
| hermes-kanban-... | ghcr.io/outsourc-e/hermes-workspace | ❌ Exited (143) |

### SKP Database
- **Active DB:** `/data/arsify.db` → 421 entries
- **Table:** `knowledge` (NOT `memory_notes`)
- **Category distribution:** pemerintah:102, bisnis:74, komunitas:70, upshalter:67, curated:40, backend:37, akademisi:23, others:8

### Cron Jobs
| Script | Schedule |
|--------|----------|
| senator-cycle-v3.sh | every 6 hours |
| kurator-v2.sh | 1h after senator (1,7,13,19) |
| generate-intelligence-page.py | every 30 min |
| health-check.sh | every 5 min |
| daily-summary.sh | 00:00 UTC |
| backup-skp.sh | 20:00 UTC |
| ssl-check.sh | 01:00 UTC |
| log cleanup | weekly (Sunday) |

### Nginx — 26 Enabled Subdomains
hermes, workspace, api, arsify, arsify-api, chat, data, app, terminal, n8n, status, flowise, flowtask, regrow, remote-forward, workstation, local-workspaces, hermes-tailscale, hermes-agents

### Pricing Tiers (from subscribers.json)
| Tier | Price (IDR) | Price (USD) | Domains | Delivery |
|------|-------------|-------------|---------|----------|
| starter | 2,000,000 | 130 | 2 | weekly |
| pro | 5,000,000 | 330 | 5 | daily |
| enterprise | 15,000,000 | 980 | custom | API |

---

## Key Pitfalls Discovered

1. **Content Quality Gap:** Senator output is descriptive ("pipeline aktif, quality score 70/100") not actionable intelligence. Root cause: generic prompts + no real data feed.
2. **Orchestrator Bypass:** Senator cycle v3 calls OpenRouter directly, bypassing Cognitive Engine (:8100) entirely. Engine is infrastructure, not product.
3. **Container Exits:** 4 Docker containers (workspace, gamedev, loyx, kanban) exited with code 143 (SIGTERM). Not auto-recovered.
4. **Terminal Restart Loop:** terminal-upshalter.service in continuous activating→auto-restart cycle.
5. **Test Subscriber Only:** subscribers.json has 1 test entry (sub001). No real paying customers.
6. **No Payment Infrastructure:** Pricing tiers defined but no payment gateway integrated.
7. **Category Bloat:** 80.7% SKP entries are category="general" — enrichment script exists but never executed.
