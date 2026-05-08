# Senator Pentahelix v3 — Complete Architecture Reference

## Overview
Senator Pentahelix is a 5-sector research agent system (akademisi, bisnis, komunitas, pemerintah, media) that gathers web research, stores findings to the VPSO Orchestrator Knowledge Pool (SKP), and sends Telegram reports — all running as Docker containers with a 6-hour research cycle.

## File Locations
| File | Path |
|------|------|
| Research script | `/root/senator-pentahelix/scripts/senator_research.py` |
| Dockerfile | `/root/senator-pentahelix/Dockerfile` |
| Docker Compose | `/root/senator-pentahelix/docker-compose.yml` |
| Healthcheck | `/root/senator-pentahelix/healthcheck.sh` |
| Data volume | Docker volume `senator-data` (mounted at `/app/data`) |
| Orchestrator API | `/usr/local/lib/hermes-orchestrator/api.py` |
| Knowledge Sync | `/usr/local/lib/hermes-orchestrator/orchestrator/knowledge_sync.py` |
| Auth Manager | `/usr/local/lib/hermes-orchestrator/orchestrator/auth.py` |
| Middleware | `/usr/local/lib/hermes-orchestrator/orchestrator/middleware.py` |

## Architecture

```
Docker Containers (network_mode: host)
├── senator-akademisi  → research cycle every 6h
├── senator-bisnis     → research cycle every 6h
├── senator-komunitas  → research cycle every 6h
├── senator-pemerintah → research cycle every 6h
├── senator-media      → research cycle every 6h
│
├── Wikipedia API (primary search) → en.wikipedia.org/w/api.php
├── DuckDuckGo API (fallback) → api.duckduckgo.com
│
├── POST /api/knowledge → Orchestrator SKP (shared memory)
├── Local JSON backup → /app/data/research_<sector>_<timestamp>.json
└── Telegram report → @upshalter_hermes_bot
```

## Key Design Decisions

### 1. Poll-Loop Pattern (not one-shot)
Script runs indefinitely with `while not _shutdown_requested`. Sleep is chunked (30s) to respond to SIGTERM. This prevents Docker restart loops.

### 2. Multi-Source Web Search
- **Wikipedia first** (most reliable, free, no API key) — requires User-Agent header
- **DuckDuckGo second** (fallback) — 5s timeout to fail fast
- **Placeholder last** — ensures cycle never produces zero findings

### 3. network_mode: Host
Containers use `network_mode: host` in docker-compose to reliably access `127.0.0.1:8000` (orchestrator). Eliminates DNS resolution and UFW issues.

### 4. API Key Authentication
Keys must be generated via `AuthManager.generate_key()` — hardcoded strings don't work. Format: `hma_*`.

### 5. Knowledge Pool Storage
POST to `/api/knowledge` with valid API key. Falls back to local JSON if API unavailable.

## Research Topics per Sector
- **akademisi**: AI research trends, international journals, academic collaboration, ML conferences
- **bisnis**: Tech market analysis, unicorn valuations, digital investment trends, VC funding
- **komunitas**: Digital society issues, open source movement, tech adoption
- **pemerintah**: AI regulation, digital transformation policy, gov-private cooperation, cybersecurity
- **media**: Trending tech news, social media AI coverage, public digital narrative

## Telegram Report Format
```
📡 LAPORAN PENTAHELIX — SEKTOR <SECTOR>
🕐 HH:MM WIB | DD Mon YYYY

1. <Title>
   🔗 <URL>
   📝 <Snippet>...

━━━━━━━━━━━━━━━━━━
📊 N temuan dari sektor <SECTOR>
💾 Tersimpan di SKP: N entri

#<sector> #pentahelix #senator #research
```

## Verification Commands
```bash
# Check all senators healthy
docker ps --format "table {{.Names}}\t{{.Status}}" | grep senator

# Check research cycle logs
docker logs senator-akademisi 2>&1 | tail -20

# Verify SKP storage
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
  "SELECT id, title, source_agent_name, created_at FROM knowledge ORDER BY created_at DESC LIMIT 10;"

# Test API knowledge creation
curl -s -X POST http://localhost:8000/api/knowledge \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <valid_key>" \
  -d '{"title":"Test","content":"Test","category":"test",
       "source_agent_id":"test","source_agent_name":"Test"}'
```

## Common Issues and Fixes

### Issue: All senators in restart loop
**Cause**: Script exits after first cycle (no proper poll-loop)
**Fix**: Ensure `senator_research.py` has proper signal handling and `while not _shutdown_requested` loop

### Issue: SKP store returns 405
**Cause**: No POST route for `/knowledge` in api.py
**Fix**: Add `create_knowledge` method to KnowledgeSync + POST routes (see vpso-management skill)

### Issue: SKP store returns 401
**Cause**: Invalid API key (hardcoded string not in auth DB)
**Fix**: Generate key via `AuthManager.generate_key('senator-pentahelix')`

### Issue: Web search returns empty
**Cause**: DDG API slow/blocked from container; Wikipedia needs User-Agent
**Fix**: Use Wikipedia as primary (with UA header), DDG as fallback (5s timeout)

### Issue: Container can't reach orchestrator on port 8000
**Cause**: UFW blocking Docker bridge, or DNS resolution failure
**Fix**: Use `network_mode: host` + `ORCHESTRATOR_URL=http://127.0.0.1:8000`

### Issue: pip install fails in Dockerfile
**Cause**: `nousresearch/hermes-agent:latest` has no pip/ensurepip
**Fix**: Don't install Python packages; use stdlib + pre-installed `requests` only

## Cycle Timing
- **Startup**: ~10s (skill sync from base image)
- **Research**: ~4 topics × 1s timeout each = ~5s
- **SKP store**: ~1s per finding
- **Telegram**: ~15s
- **Total cycle**: ~30s including retries
- **Sleep between cycles**: 6 hours (21600s)
