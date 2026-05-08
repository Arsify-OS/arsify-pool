# Connection Storm / TIME-WAIT Diagnosis

## When to Use
- User reports "lost connection", "connection drops", "intermittent disconnects"
- Services are running but connections feel unstable
- High TIME-WAIT count observed during routine checks
- Port binding conflicts (errno 98 "address already in use")

## Root Cause Patterns (in order of frequency)

### 1. Redis IPv6 Connection Storm (MOST COMMON on this VPS)
**Symptom**: 10,000+ TIME-WAIT connections, majority to `[::1]:6379`
**Cause**: Redis binds to both `0.0.0.0` AND `[::]` (IPv6). Docker containers resolve `host.docker.internal` to IPv6 `::1`. Every Celery heartbeat/result-check opens a new TCP socket that goes to IPv6 localhost.
**Diagnosis**:
```bash
# Check TIME-WAIT destinations
ss -tan | grep TIME-WAIT | awk '{print $5}' | sort | uniq -c | sort -rn | head -10

# If you see thousands to [::1]:6379, this is the cause
ss -tan6 | grep -c TIME-WAIT

# Check Redis bind config
grep '^bind' /etc/redis/redis.conf
# BAD:  bind 0.0.0.0 -::
# GOOD: bind 0.0.0.0
```
**Fix**:
```bash
# 1. Disable Redis IPv6
sed -i 's/^bind 0\.0\.0\.0 -::/bind 0.0.0.0/' /etc/redis/redis.conf
systemctl restart redis-server

# 2. Verify IPv6 listener is gone (should show only 0.0.0.0:6379)
ss -tlnp | grep 6379

# 3. Restart all Redis-dependent containers
docker restart hermes-api hermes-worker
docker restart senator-akademisi senator-bisnis senator-pemerintah senator-media senator-komunitas

# 4. Wait 30-60s for old TIME-WAIT to drain, then verify
ss -tan | grep -c TIME-WAIT
```

### 2. Zombie Process Holding Port (errno 98)
**Symptom**: Service in restart loop, "address already in use" in logs
**Cause**: A stale process (often `socat`, old `hermes` instance, or crashed process) holds the port
**Diagnosis**:
```bash
# Find who owns the port
ss -tlnp | grep <PORT>
lsof -i :<PORT>

# Check for restart loops
systemctl show <service> -p NRestarts --value
journalctl -u <service> --since "10 min ago" --no-pager | grep -E "address already in use|errno 98"
```
**Fix**:
```bash
# Kill the zombie
kill -9 <PID>

# Stop the restarting service first to prevent race
systemctl stop <service>
sleep 2
systemctl start <service>

# Verify
systemctl is-active <service>
ss -tlnp | grep <PORT>
```

### 3. TCP TIME-WAIT Accumulation
**Symptom**: Thousands of TIME-WAIT connections, conntrack table filling
**Cause**: Default time_wait timeout is 120s. With many containers making frequent connections, the table accumulates.
**Diagnosis**:
```bash
# Check current state
ss -s
cat /proc/sys/net/netfilter/nf_conntrack_tcp_timeout_time_wait
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max
```
**Fix** (apply via `/etc/sysctl.d/99-hermes-tuning.conf`):
```ini
net.netfilter.nf_conntrack_max=524288
net.netfilter.nf_conntrack_tcp_timeout_time_wait=30
net.netfilter.nf_conntrack_tcp_timeout_close_wait=30
net.netfilter.nf_conntrack_tcp_timeout_fin_wait=30
net.ipv4.tcp_fin_timeout=5
net.ipv4.tcp_tw_reuse=1
net.ipv4.tcp_max_tw_buckets=20000
net.ipv4.tcp_keepalive_time=60
net.ipv4.tcp_keepalive_intvl=10
net.ipv4.tcp_keepalive_probes=3
```
```bash
sysctl --system
```

### 4. CLOSE-WAIT Leak (Socket Not Closed)
**Symptom**: Persistent CLOSE-WAIT connections (7+), not draining
**Cause**: Application opens sockets but never calls close(). Common with Telegram API connections and long-running Python processes.
**Diagnosis**:
```bash
ss -tanp | grep CLOSE-WAIT
```
**Fix**: Usually requires restarting the offending process. Low impact unless count grows.

### 5. Senator / Celery Rate Limit Storm
**Symptom**: All senator containers hitting 429 simultaneously, retry every 30s
**Cause**: Free-tier OpenRouter models have tight rate limits. 5 senators hitting the API at once triggers cascading 429s.
**Diagnosis**:
```bash
docker logs --tail 20 senator-akademisi 2>&1 | grep -i "rate limit\|429"
```
**Mitigation**: Use smaller free models (e.g., `lfm-2.5-1.2b-instruct:free`), increase `CYCLE_INTERVAL_SECONDS`, or stagger senator start times.

## Quick Diagnostic Script
Run all checks in sequence for a complete connection health picture:
```bash
echo "=== TCP Summary ===" && ss -s
echo "" && echo "=== TIME-WAIT count ===" && ss -tan | grep -c TIME-WAIT
echo "" && echo "=== IPv6 TIME-WAIT ===" && ss -tan6 | grep -c TIME-WAIT
echo "" && echo "=== CLOSE-WAIT ===" && ss -tan | grep -c CLOSE-WAIT
echo "" && echo "=== Top TIME-WAIT destinations ===" && ss -tan | grep TIME-WAIT | awk '{print $5}' | sort | uniq -c | sort -rn | head -10
echo "" && echo "=== Redis listeners ===" && ss -tlnp | grep 6379
echo "" && echo "=== Redis bind config ===" && grep '^bind' /etc/redis/redis.conf
echo "" && echo "=== Conntrack ===" && echo "count: $(cat /proc/sys/net/netfilter/nf_conntrack_count) / max: $(cat /proc/sys/net/netfilter/nf_conntrack_max)"
echo "" && echo "=== Port conflicts ===" && ss -tlnp | awk '{print $4}' | sort | uniq -d
echo "" && echo "=== Systemd restart loops ===" && systemctl list-units --type=service --state=auto-restarting 2>/dev/null | grep -v "0 loaded"
```

## Expected Healthy State
- TIME-WAIT: < 200 (after draining)
- CLOSE-WAIT: 0-3 (some Telegram connections are normal)
- Redis: IPv4 only (`0.0.0.0:6379`, NO `[::]:6379`)
- Conntrack: < 50% of max
- No services in auto-restarting state
