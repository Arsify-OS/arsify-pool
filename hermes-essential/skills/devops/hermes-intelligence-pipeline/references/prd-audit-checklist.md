# PRD Audit Checklist

Systematic verification that implementation matches STRATEGY-WAVES.md and PRD deliverables.

## STRATEGY-WAVES Compliance Review

Before checking individual PRDs, assess **wave-level readiness**. Waves have dependencies — a later wave cannot start if an earlier wave's success criteria are not met.

| Wave | Target Date | Depends On | Key Success Criteria | Status |
|------|-------------|------------|---------------------|--------|
| Wave 1: PRD-001 Foundation | H-7 (7 Mei) | None | SKP entries > 0 from Senator, Ollama running | Check below |
| Wave 2: PRD-004 Demo-Ready | H-8~10 (8-10 Mai) | Wave 1 (Ollama) | chat/workspace/status all functional | Check below |
| Wave 3: PRD-002 Pentahelix | H-11~20 (11-20 Mai) | Wave 1 (Senator→SKP) | 50 entries/cycle, Kurator report | Check below |
| Wave 4: PRD-003 Service | H-15~25 (15-25 Mai) | Wave 2 (demo-ready) | Onboarding kit, sales page | Check below |
| Wave 5: PRD-005 Vox | H-20~40 (20-40 Mai) | Wave 1+3 (stable) | Brand Brain schema, waiting list | Check below |

### When to Audit

**Full audit** (all PRDs): Weekly, every Monday  
**Wave audit** (current wave only): Daily during active wave  
**Ad-hoc**: After any major fix or deployment

### Important Notes
- **Wave 3 is blocked until Wave 1 succeeds** — Senator must produce SKP entries first
- **Wave 4 is blocked until Wave 2 succeeds** — demo sites must work before selling
- Track overall completion: target 45%~60% by end of Wave 2

## PRD-001: Foundation Fix

### Success Criteria
```bash
# SKP entries > 0
docker exec hermes-worker python3 -c "
import sqlite3
conn = sqlite3.connect('/data/shared_knowledge_pool.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM knowledge')
print('knowledge:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM memory_notes')
print('memory_notes:', cur.fetchone()[0])
conn.close()
"

# Ollama running
curl -sf http://localhost:11434/api/tags | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]"

# Cron jobs
crontab -l | grep -E "senator|kurator|generate"

# hermes-upshalternal
systemctl is-active hermes-upshalternal

# Telegram
curl -s "https://api.telegram.org/bot${TOKEN}/getMe"
```

## PRD-002: Pentahelix Intelligence

### Deliverables Checklist
- [ ] `/root/upshalter-scripts/senator-cycle.sh` — exists + executable
- [ ] `/root/upshalter-scripts/kurator-review.sh` — exists + executable
- [ ] `/root/upshalter-scripts/deliver-intelligence.sh` — exists + executable
- [ ] `/root/upshalter-scripts/generate-intelligence-page.py` — exists + executable
- [ ] `/root/upshalter-config/subscribers.json` — exists + valid JSON
- [ ] `/root/upshalter-reports/sample-brief-DEMO.md` — exists
- [ ] `/var/www/data.upshalter.com/index.html` — exists + auto-generated

### Success Criteria
- [ ] Senator 10 entries/cycle (total 50 from 5 senators)
- [ ] Kurator report < 90 min after cycle
- [ ] Delivery to subscriber at 07:00 WIB
- [ ] data.upshalter.com shows 10 latest insights
- [ ] 3 pilot subscribers in 7 days
- [ ] Zero delivery failures in 7 days

## PRD-003: Implementation Service

### Deliverables Checklist
- [ ] `/root/upshalter-materials/proposal-template.md`
- [ ] `/root/upshalter-scripts/onboard-client.sh`
- [ ] `/root/upshalter-materials/client-docs-template.md`
- [ ] `/var/www/upshalter.com/services/index.html` (sales page)

## PRD-004: Managed Workspace

### Success Criteria
- [ ] chat.upshalter.com → chat UI (not JSON API)
- [ ] workspace.upshalter.com → login → chat feature active
- [ ] status.upshalter.com → real-time status dots
- [ ] 15-min demo without errors

## PRD-005: Arsify Vox

### Deliverables Checklist
- [ ] Brand Brain schema in SKP (`brand/{slug}/brain`)
- [ ] Demo: AI knows brand tone
- [ ] `/var/www/arsify.upshalter.com/vox/index.html` (waiting list)
- [ ] 50 sign-ups in 30 days
- [ ] 1 pilot client

## Container Verification

```bash
# All containers healthy
docker ps --format "table {{.Names}}\t{{.Status}}" | grep hermes

# All imports OK
docker exec hermes-worker python3 -c "
import sys; sys.path.insert(0, '/app/src')
mods = ['models.cache','models.openrouter_client','core.skp_search',
        'core.knowledge_injector','layers.cognition','layers.execution',
        'layers.reflection','tasks','core.router','core.kurator','main','api.health']
for m in mods:
    try: __import__(m); print(f'✅ {m}')
    except Exception as e: print(f'❌ {m}: {e}')
"

# Syntax check
for f in /root/.hermes/*.py; do python3 -m py_compile "$f" 2>&1 && echo "✅ $(basename $f)" || echo "❌ $(basename $f)"; done

# No duplicate mounts
grep "\- /root/.hermes" /opt/hermes-cognitive/docker-compose.yml | sort | uniq -d
```
