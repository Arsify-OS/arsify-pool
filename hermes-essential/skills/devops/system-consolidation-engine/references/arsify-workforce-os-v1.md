# Arsify Workforce OS v1.0 — Consolidation Pattern Reference
# For: system-consolidation-engine skill
# Session: 2026-05-08

## What Was Consolidated

Input: Fragmented VPS with 12 containers (8 up, 4 exited), 20 nginx sites (6 dead),
15+ scripts (3 versions each), 4 PRD documents, multiple audit docs, no unified architecture.

Output: Arsify Workforce OS v1.0 — single coherent system with 15-document blueprint.

## Architecture Pattern (Generalizable)

```
USER/ORG
  ↓
ARSIFY WORKFORCE OS (Product)
  ├── Workforce Layer     → Persistent analysts (senators)
  ├── Intelligence Layer  → Knowledge pool + synthesis (kurator)
  └── Delivery Layer      → Dashboard + API + Telegram
        ↓
HERMES RUNTIME (Infrastructure)
  ├── Orchestration       → Cognitive engine + policy + routing
  ├── Services            → Redis + LLM + Telegram
  └── Platform            → Docker + Nginx + Systemd
        ↓
VPS                     → Compute + Storage + Network
```

## Key Classification Decisions

### KEPT (Core Product)
- 5 Senator containers (standalone Hermes agents)
- Hermes Cognitive Engine :8100 (FastAPI L1-L4 pipeline)
- Hermes Orchestrator :8000 (agent management)
- SKP Database /data/arsify.db (421 entries, knowledge table)
- Redis, Nginx, PM2, Telegram integration

### REMOVED (Dead Weight)
- hermes-workspace, hermes-loyx, hermes-kanban (exited, not product)
- 6 dead nginx sites (workspace, terminal, flowtask, api, arsify-api, hermes)
- Old script versions (senator-cycle v1/v2, kurator-review v1)

### FROZEN (Preserve, Don't Delete)
- hermes-gamedev (Regrow Up World game project)
- flowise/n8n proxies (experimental)

### REFACTORED (Needs Changes)
- SKP schema (missing institutional memory fields)
- Auth (default-off → default-on)
- Response caching (zero → Redis-backed)
- Kurator (basic → strategic synthesis)
- Dashboard (static → real-time console)
- Rate limiting (in-memory → Redis-backed)

## Critical Knowledge

### SKP Schema Disconnect
The v0.1 code references table `memory_notes` but the ACTUAL table is `knowledge`.
The v0.1 code references DB path `/root/.hermes/shared_knowledge_pool.db` but
the ACTUAL path is `/data/arsify.db` (symlink). ALWAYS verify with:
```bash
sqlite3 /data/arsify.db ".tables"
sqlite3 /data/arsify.db ".schema knowledge"
```

### Senator Container Architecture
Senators are NOT custom Python scripts. They're standalone Hermes Agent containers
(nousresearch/hermes-agent:latest) that mount /root/.hermes shared volume and call
Cognitive Engine API (:8100). If senator fails: check COGNITIVE_ENGINE_URL first.

### 9router PM2 Process
There's a "9router" process managed by PM2. Investigate and document role — may be
a separate Node.js API router or the Cognitive Engine entry point.

## Folder Structure That Worked

```
/root/<project>-v<version>/<project>/
  docs/                          ← 15 consolidation documents
  config/                        ← domains.yml, senators.yml, system.yml
  workforce/
    senators/{domain}/
      SOUL.md                    ← Per-senator identity
      prompt.json                ← Analysis prompt template
    kurator/                     ← Synthesis engine
    memory/                      ← SKP adapter, entity tracker
    orchestration/               ← Gateway, dispatcher
    delivery/                    ← Telegram, PDF, subscriber mgmt
    automation/                  ← Canonical scripts
  runtime/
    hermes-api/                  ← Existing cognitive engine src
    policy-engine/               ← Auth, rate limiter
    quality-engine/              ← Validator, hallucination check
    observability/               ← Metrics, logging
    gateway/                     ← LLM router, fallback
  infrastructure/
    docker/, nginx/, systemd/, monitoring/, backup/
  dashboard/
    index.html, assets/{css,js,img}/
  deployment/
    deploy.sh, setup.sh, migrate.sh, rollback.sh
  scripts/
    senator-cycle.sh, kurator-cycle.sh, health-check.sh, backup.sh
```

## 30-Day Roadmap Pattern

- Phase 1 (Day 1-7):   Security + Cleanup + SKP Migration + Senator Verification
- Phase 2 (Day 8-14):  Kurator Upgrade + Dashboard + Observability
- Phase 3 (Day 15-21): Fault Tolerance + Data Pipeline + Performance
- Phase 4 (Day 22-28): Delivery System + Onboarding Kit + Pilot
- Phase 5 (Day 29-30): Learning Loop + Month-2 Planning

## Productization Pattern (Indonesian Market)

- Starter:    Rp 15jt/bln — 2 domains, weekly report, Telegram
- Standard:   Rp 35jt/bln — 5 domains, daily report, dashboard
- Enterprise: Rp 75jt/bln — custom, API, SLA, dedicated support
