# VPSO Bug Audit Workflow

Repeatable workflow for detecting hidden bugs in VPSO (Virtual Private Service Office) deployments, derived from the 6 May 2026 audit session.

## Pre-Check
1. Load `vps-system-inspection` skill
2. Verify VPSO memory notes are up-to-date (ports, service counts, container names)

## Step 1: Critical Process Spawning Check
Detect uncontrolled Hermes dashboard/agent process growth (fork bomb risk):
```bash
# Count all Hermes-related processes
ps aux | grep -E 'hermes|python.*agent' | grep -v grep | wc -l

# Check growth rate (run twice 30 mins apart)
watch -n 1800 'ps aux | grep "hermes dashboard" | grep -v grep | wc -l'
```
**Alert threshold**: >20 processes total, or >10% growth in 1 hour

**Investigation commands**:
```bash
# Identify parent-child relationships
ps aux | grep 'hermes dashboard' | grep -v grep | awk '{print $2, $3, $11, $12, $13}'

# Check Docker container commands
docker ps -q | xargs docker inspect --format '{{.Name}}: {{range .Config.Cmd}}{{.}} {{end}}' | grep -i dashboard

# Check orphaned processes (PPID=0)
ps aux | grep 'hermes dashboard' | grep -v grep | awk '$3 == "0.0"'
```

## Step 2: Port Mapping Validation
Catch documentation drift between memory notes and actual deployments:
```bash
# Get actual Docker port mappings
docker ps --format '{{.Names}}: {{.Ports}}'

# Cross-check with memory notes (example)
# Memory: loyx:8643, gamedev:8644
# Actual: hermes-loyx -> 0.0.0.0:9136->8642/tcp
```
**Action**: Update memory notes if mismatch found

## Step 3: Redis Data Integrity
VPSO task keys must be hash type (not list/string):
```bash
# Check all Redis key types
redis-cli KEYS '*' | xargs -I {} redis-cli TYPE {} 2>/dev/null | sort | uniq -c

# Verify task keys are hash
redis-cli KEYS 'task:*' | xargs -I {} redis-cli TYPE {} | grep -v hash
```
**Bug signal**: Any `task:*` key returning `list`/`string`/`none` indicates data corruption

## Step 4: SSH Brute Force Detection
Detect ongoing attacks that waste resources and pose security risks:
```bash
# Count failed attempts in 24h
journalctl --since '24 hours ago' -u ssh | grep 'Failed password' | wc -l

# Top attacking IPs
journalctl --since '24 hours ago' -u ssh | grep 'Failed password' | awk '{print $11}' | sort | uniq -c | sort -rn | head -5
```
**Alert threshold**: >10 failed attempts in 24h
**Fix**: Install fail2ban: `apt-get install fail2ban`

## Step 5: Systemd Service Count Validation
Catch undocumented service sprawl:
```bash
# Count Hermes-related systemd services
systemctl list-units --type=service --all | grep hermes | wc -l
```
**Action**: Update memory notes if count differs from documented number

## Post-Audit
1. Generate report using box-drawing characters + emoji per user preference
2. Save report to `/tmp/vpso_bug_report.txt`
3. Update memory notes with any corrected values (ports, service counts)
4. Prioritize fixes: 🔴 Critical (process spawning) > ⚠️ High (SSH brute force) > 📌 Low (docs)
