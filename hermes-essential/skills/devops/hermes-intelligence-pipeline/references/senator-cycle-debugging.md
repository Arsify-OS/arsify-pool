# Senator Cycle Debugging Guide

**Created:** 8 Mei 2026  
**Symptom:** `senator-cycle.sh` runs but 0/5 senators succeed — "Failed to submit"

---

## Root Cause: Hermes Gateway Not Running

The senator cycle script creates kanban tasks via `hermes kanban create`. These tasks sit in `kanban.db` with status `ready` but are **never dispatched** unless `hermes gateway` is running.

### Diagnosis

```bash
# Check if gateway is running
hermes gateway status 2>/dev/null || echo "Gateway not running"

# Check port 8000
curl -sf http://localhost:8000/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" || echo "Port 8000 not responding"

# Check kanban for stuck tasks
hermes kanban list --board research --status ready 2>/dev/null | head -20

# Check senator log for "Failed to submit"
tail -30 /opt/data/editorial-logs/cron-senator.log
```

### Log Pattern Indicating This Issue

```
[00:00:07] 📋 Starting senator-akademisi...
[00:00:08] ❌ Failed to submit — 
[00:01:10] 📋 Starting senator-bisnis...
[00:01:11] ❌ Failed to submit — 
...
[00:04:18] 🏛️ Senator Cycle v3 complete: 0/5 success, 5 failed
```

### Fix Options

**Option A: Start Hermes Gateway (preferred if kanban dispatch needed)**
```bash
hermes gateway start
# Verify
hermes gateway status
# Re-run senator cycle
/root/upshalter-scripts/senator-cycle.sh
```

**Option B: Bypass Kanban — Direct Cognitive Engine API Call**
```bash
# Replace kanban create with direct API call:
curl -s --max-time 10 \
    -X POST "http://host.docker.internal:8100/v1/portsocket" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${HERMES_API_KEY}" \
    -H "X-Agent-ID: senator-akademisi" \
    -d '{"input": "Riset topik AI, pendidikan, dan inovasi teknologi di Indonesia terbaru..."}'
```

**Option C: Use Celery Task Directly**
```python
from tasks import senate_research_task
result = senate_research_task.delay(sector='akademisi', topic='AI Indonesia')
```

### Prevention

- Add gateway check to senator-cycle.sh: before creating tasks, verify gateway is running
- Add monitoring: alert if gateway goes down
- Consider making senator-cycle.sh call Cognitive Engine API directly (removes kanban dependency)

---

## Other Common Issues

### Senator Container Not Running
```bash
docker ps | grep senator
# If stopped:
docker start senator-akademisi senator-bisnis senator-komunitas senator-pemerintah senator-media
```

### Cognitive Engine Not Responding
```bash
# From host:
curl -sf http://localhost:8100/health
# From container:
docker exec hermes-worker curl -sf http://localhost:8100/health
```

### SKP Write Failure
```bash
# Verify DB writable
docker exec hermes-worker python3 -c "
import sqlite3
conn = sqlite3.connect('/data/shared_knowledge_pool.db')
conn.execute('INSERT OR IGNORE INTO knowledge (key, value, source_agent_name, category, priority) VALUES (\'test/debug\', \'test\', \'debug\', \'general\', 1)')
conn.commit()
print('Write OK, rows:', conn.execute('SELECT COUNT(*) FROM knowledge').fetchone()[0])
conn.close()
"
```
