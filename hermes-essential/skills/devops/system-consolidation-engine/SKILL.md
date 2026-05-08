---
name: system-consolidation-engine
description: Full-system consolidation — read all existing systems, inventory every component, classify (KEEP/FREEZE/REMOVE/REFACTOR/MERGE), design target architecture, and generate a complete consolidation package. Trigger when user asks to "consolidate everything", "unify all systems", "clean up and redesign architecture", or "make everything coherent". NOT for simple inspection — this produces a full blueprint package.
---

# System Consolidation Engine

## Purpose
Transform fragmented infrastructure (containers, services, scripts, configs, dashboards) into ONE coherent system. Not just audit — produce a complete redesign + deployment package.

## Trigger
- "Konsolidasikan seluruh sistem"
- "Unify all infrastructure"
- "Make everything coherent"
- "Consolidate all services into one system"
- "Read everything, inventory everything, redesign architecture"

## Difference from Inspection
- `vps-system-inspection`: Reads state, reports health → STOP
- `system-consolidation-engine`: Reads state → Inventory → Classify → Design target → Write full package
- `hermes-infra-verification`: Verifies services are functional → STOP
- This skill: Verifies → THEN redesigns → THEN writes deployable blueprint

## Workflow

### Phase 1: READ ALL (comprehensive document ingestion)
```
1. Read ALL architectural docs (README, blueprints, PRDs, audits)
2. Read ALL docker-compose files
3. Read ALL nginx configs
4. Read ALL cron jobs
5. Read ALL systemd services
6. Read ALL scripts
7. Read ALL prompt/soul systems
8. Read ALL dashboard code
9. Read ALL SKP/knowledge base schemas
```

### Phase 2: INVENTORY (full system mapping)
```
Docker containers:     docker ps -a --format names+status+ports
Systemd services:      systemctl list-units --type=service --state=active
Nginx sites:           ls /etc/nginx/sites-enabled/ + read each config
Cron jobs:             crontab -l
Scripts:               ls /root/<project>-scripts/
Databases:             find *.db + sqlite3 count + schema
Python modules:        find /root/.hermes -name "*.py" | head -30
PM2 processes:         pm2 list
Disk/Memory:           df -h / /data + free -h
```

### Phase 3: CLASSIFY (every component gets a verdict)
For EVERY component, assign:
- **KEEP**: Core product, running, must preserve
- **FREEZE**: Not active now but preserve data/containers for future
- **REMOVE**: Dead/useless/safe to delete
- **REFACTOR**: Works but needs significant changes
- **MERGE**: Duplicate with another component → merge into one

### Phase 4: DESIGN TARGET ARCHITECTURE
```
1. Identify THE product (what users see/interact with)
2. Identify THE infrastructure (what runs the product)
3. Separate: Product ≠ Infrastructure
4. Define: pipeline, layers, hierarchy
5. Design: folder structure (workforce/runtime/infra/dashboard/docs/deployment)
6. Design: runtime flow (who calls whom, what depends on what)
```

### Phase 5: WRITE CONSOLIDATION PACKAGE
Always produce (minimum):
1. Executive Summary
2. System Reclassification (product vs infra)
3. Full System Inventory (with KEEP/FREEZE/REMOVE table)
4. Workforce/Agent Consolidation
5. Runtime Infrastructure Consolidation
6. Knowledge Pool Design
7. Dashboard/Console Design
8. VPS Optimization + Cleanup Plan
9. Security & Governance Plan
10. Observability Plan
11. Productization Strategy
12. Deployment Strategy + Folder Structure
13. Workforce Learning Loop
14. 30-Day Roadmap
15. Final Master Blueprint

Write to: `/root/<project>-v<version>/<project>/`

## Output Format Rules
- Structured terminal output, NOT markdown-heavy
- Box-drawing + emoji for status updates during work
- Detailed docs go in package files (separate .md files)
- Brief status: ✅ ⏳ ❌ format
- Language: Indonesian for communication, English for code/commands

## Pitfalls

### SKP Table Name Mismatch
The SKP database uses table `knowledge` (NOT `memory_notes`). Always verify:
```bash
sqlite3 /data/arsify.db ".tables"
sqlite3 /data/arsify.db "SELECT COUNT(*) FROM knowledge;"
```
Old code/docs referencing `memory_notes` or `shared_knowledge_pool.db` are OBSOLETE.

### Senator Containers
Senators are standalone Hermes agents (nousresearch/hermes-agent:latest), NOT custom Python scripts. They mount `/root/.hermes` shared volume and call Cognitive Engine API. If senator container exits, check: (1) can it reach Cognitive Engine on :8100? (2) can it reach OpenRouter? (3) is `/root/.hermes/.openrouter_key` readable?

### Auth Default-Off
Hermes Cognitive Engine has `AUTH_ENABLED` defaulting to FALSE. In consolidation, ALWAYS change default to TRUE in production.

### Prometheus Blind
Prometheus + Grafana containers may exist but if the main app doesn't expose `/metrics`, Prometheus scraping returns nothing. Always verify endpoint, don't assume monitoring works.

### Redis Underutilized
Redis is often running but the main application doesn't use it for response caching. In consolidation, add Redis caching layer — biggest single performance win.

### Dead Containers
Exited containers with code 143 = SIGTERM (normal shutdown). Code 1 = error. If code 143 and service is not needed → safe to remove.

### Nginx Site Proliferation
Often 20+ nginx sites configured but only 5-8 are live. Remove dead sites: workspace (dead container), terminal (never used), flowtask (never used), arsify-api (empty), api (empty).

### Duplicate Scripts
Multiple versions of senator-cycle.sh (v1, v2, v3) and kurator.sh. Keep only the latest. Remove: senator-cycle.sh (v1), senator-cycle-v2.sh (v2), kurator-review.sh (old).

### Shared Volume Permissions
When multiple containers mount `/root/.hermes`, permission conflicts occur. In docker-compose, add `user: root` to avoid.

## Reference Files
- `references/arsify-workforce-os-v1.md` — Full Arsify Workforce OS consolidation example (May 2026)
- `references/consolidation-checklist.md` — Pre-flight checklist before consolidation
- `references/arsify-core-readiness.md` — Arsify Core repo readiness checklist (May 2026)

## Skills List Context
Related skills:
- `vps-system-inspection` — Use for Phase 2 (inventory)
- `hermes-infra-verification` — Use for verifying current state before redesign
- `vpso-management` — Use for agent lifecycle management after consolidation
- `hermes-workspace-deployment` — Use for deploying workspace/chat/dashboard
- `hermes-role-deploy` — Use for deploying specific agent roles
