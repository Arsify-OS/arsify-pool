# VPS CPU Throttle Diagnosis & Remediation

## When: Hostinger Throttle Scenario
VPS is throttled due to high CPU usage (typically 70-100% sustained on 2-core).
hPanel shows top processes consuming CPU. This diagnostic identifies and fixes the root causes
while distinguishing temporary spikes (e.g., senator cycle) from chronic issues.

## Phase 1: Identify Top CPU Consumers

Run via execute_code (ps aux in terminal inflates CPU by 40-80% due to measurement overhead):

```python
import subprocess
result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
lines = result.stdout.strip().split("\n")[1:]
totals = {"hermes":0,"ollama":0,"uvicorn":0,"celery":0,"redis":0,"container":0,"senator":0,"zombie":0,"other":0}
total = 0
for line in lines:
    cols = line.split()
    cpu = float(cols[2])
    cmd = " ".join(cols[10:])
    total += cpu
    if "defunct" in cmd or "runc]" in cmd: totals["zombie"] += cpu
    elif "ollama" in cmd: totals["ollama"] += cpu
    elif "uvicorn" in cmd: totals["uvicorn"] += cpu
    elif "celery" in cmd: totals["celery"] += cpu
    elif "redis" in cmd: totals["redis"] += cpu
    elif any(k in cmd for k in ["containerd","docker","tini"]): totals["container"] += cpu
    elif "senator" in cmd: totals["senator"] += cpu
    elif "hermes" in cmd: totals["hermes"] += cpu
    else: totals["other"] += cpu
for k,v in totals.items(): print(f"{k}: {v:.1f}%")
print(f"TOTAL: {total:.1f}% ({total/2:.0f}% of 2-core)")
```

> **IMPORTANT:** The `ps aux` command itself and its parent shell appear as 40-80% CPU.
> This is measurement overhead, NOT real load. Ignore `bash`, `sh`, and the `ps` process itself.

## Phase 2: Diagnose Each Component

### 2A: Ollama Check
```bash
systemctl is-active ollama
curl -sf http://localhost:11434/api/tags -m 3 && echo "MASIH JALAN" || echo "BERHENTI"
grep provider ~/.hermes/config.yaml
```
**Fix if unnecessary:**
```bash
systemctl stop ollama; systemctl disable ollama
```

### 2B: Orchestrator Diagnosis
```bash
curl -sf http://localhost:8000/health -m 5 | python3 -m json.tool
# Health endpoint is authoritative — shows pending/assigned/completed counts
sqlite3 /usr/local/lib/hermes-orchestrator/db/orchestrator.db "SELECT status, COUNT(*) FROM tasks GROUP BY status" 2>/dev/null || echo "no tasks table"
```

**Key insight:** Orchestrator with 7-8% steady-state CPU since days ago is NORMAL.
Tasks in `assigned` state with 0 agents online = stale from previous cycle, not causing CPU load.

### 2C: Celery Queue Diagnosis
```bash
redis-cli LLEN celery 2>/dev/null
redis-cli KEYS "celery-task-meta-*" | wc -l
ps aux | grep celery | grep -v grep
```
**Fix if stale (no active workers processing):**
```bash
redis-cli DEL celery   # Purges the main queue
```

### 2D: Health Check Script Diagnosis
The monitoring health-check.sh (cron every 5 min) can ITSELF cause CPU spikes:
- Checking dead services without timeout = blocking 30+ seconds per service
- Multiple concurrent invocations = process pileup

```bash
head -30 /root/upshalter-scripts/health-check.sh
pgrep -f health-check
crontab -l | grep health
```

**Fix:** Edit `/root/upshalter-scripts/health-check.sh`:
1. Remove services no longer running (e.g., :9124-9135)
2. Add `--max-time 3` to all curl commands
3. Only check services actually deployed

### 2E: Zombie Process Cleanup
```bash
ps aux | grep defunct | grep -v grep
ps -o ppid= -p <zombie_pid>
kill -9 <parent_pid>   # Zombies can't be killed directly
```

### 2F: Redundant Hermes Dashboard Processes
```bash
ps aux | grep "hermes dashboard" | grep -v grep
# Kill all except :8645
for pid in $(ps aux | grep "hermes dashboard" | grep -v "8645" | grep -v grep | awk '{print $2}'); do
  kill $pid 2>/dev/null
done
```

### 2G: Old Hermes CLI Sessions
```bash
ps aux | grep "/usr/local/bin/hermes" | grep -v "dashboard\|orchestrator\|gateway\|uvicorn"
# Kill sessions from days ago (etime shows "May04", "May06")
```

## Phase 3: Distinguish Temporary vs Chronic CPU

### Normal Temporary Spikes (DO NOT FIX)
- **Senator cycle**: 5+ `senator_cognitive_client.py` + `hermes_sandbox_*` processes
  - CPU: 50-100% of 2-core during active scraping
  - Duration: 15-30 min per cycle, every 6 hours
  - **Action**: Wait for cycle to complete, then re-measure base CPU

### Chronic Issues (FIX)
- Ollama running when not the active provider
- Health check script blocking on dead services
- Redundant dashboard processes (9+ instances)
- Zombie processes ([runc] <defunct>)
- Celery queue with stale unprocessed tasks

## Phase 4: Post-Intervention Measurement

After fixing chronic issues, wait for any active senator cycle to complete, then measure base CPU.
Target: Base CPU < 60% of 2-core (< 120% in ps aux total).
Hostinger typically removes throttle within 1-3 hours after sustained CPU < 80%.

## Common Patterns on This VPS

| Component | Normal CPU | Chronic Issue Threshold |
|-----------|-----------|------------------------|
| hermes-orchestrator | 5-8% steady | >15% sustained |
| hermes CLI (active session) | 10-20% | Multiple sessions >30% total |
| ollama | 0% (disabled) | >5% = shouldn't be running |
| celery workers | 0.3-0.5% | >2% = stuck tasks |
| redis | 0.3-0.5% | >2% = connection storm |
| containerd | 0.2-0.5% | >2% = container churn |
| senator cycle | 0% (idle) | 30-70% during cycle (normal) |
| health-check.sh | 0% (idle) | >5% = blocking on dead services |
