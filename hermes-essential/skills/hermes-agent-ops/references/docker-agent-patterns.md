# Docker Agent Deployment — Advanced Patterns

## Base Image: nousresearch/hermes-agent:latest — Critical Quirks

See `vpso-management/references/docker-base-image-quirks.md` for full details. Key takeaways:

1. **No pip/ensurepip** — cannot install Python packages. Use stdlib + pre-installed `requests` only.
2. **Entrypoint intercepts all commands** — override with `ENTRYPOINT ["/usr/bin/tini", "--"]` in Dockerfile.
3. **Skill sync on every run** — adds ~10s startup, normal behavior.
4. **Web search from containers** — Wikipedia needs User-Agent header (403 without); DDG is slow (use 5s timeout).

## network_mode: host vs Bridge

For containers that MUST reliably access host services (orchestrator, databases):

```yaml
# RECOMMENDED for reliability
network_mode: host
environment:
  - ORCHESTRATOR_URL=http://127.0.0.1:8000  # localhost = host

# AVOID for critical services — DNS/firewall issues
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Trade-off with `host`: no port mapping, containers share host network namespace.

## UFW Rules for Docker

If NOT using `network_mode: host`, add UFW rules for Docker bridge:
```bash
ufw allow from 172.17.0.0/16 to any port 8000 comment 'Docker to host orchestrator'
```

## Long-Running Agent Pattern (Poll-Loop)

Docker containers with `restart: unless-stopped` will restart if the main process exits. For agents that should run indefinitely:

```python
import signal, time

_shutdown = False
def _handler(signum, frame):
    global _shutdown
    _shutdown = True

signal.signal(signal.SIGTERM, _handler)
signal.signal(signal.SIGINT, _handler)

while not _shutdown:
    do_work()
    # Sleep in chunks to respond to SIGTERM quickly
    remaining = CYCLE_INTERVAL
    while remaining > 0 and not _shutdown:
        time.sleep(min(30, remaining))
        remaining -= 30
        touch_heartbeat()
```

## Multi-Source Web Search Pattern

When agents need web search from Docker containers:

```python
def search_wikipedia(query, max_results=3):
    """Primary — most reliable, requires User-Agent header."""
    headers = {"User-Agent": "AgentName/1.0 (https://domain.com; research-bot)"}
    resp = requests.get("https://en.wikipedia.org/w/api.php",
        params={"action":"query","list":"search","srsearch":query,
                "srlimit":max_results,"format":"json"},
        headers=headers, timeout=10)
    # Parse results...

def search_duckduckgo(query, max_results=3):
    """Fallback — use short timeout to fail fast."""
    resp = requests.get("https://api.duckduckgo.com/",
        params={"q":query,"format":"json","no_html":"1"},
        timeout=5)  # 5s — fail fast if slow
    # Parse results...

def search_web(query, max_results=3):
    """Multi-source with fallback."""
    results = search_wikipedia(query, max_results)
    if results:
        return results
    results = search_duckduckgo(query, max_results)
    if results:
        return results
    return []  # No results from any source
```

## Healthcheck Pattern

```dockerfile
COPY healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh
```

```yaml
healthcheck:
  test: ["CMD", "/app/healthcheck.sh"]
  interval: 30m
  timeout: 10s
  retries: 3
  start_period: 30s
```

Healthcheck script:
```bash
#!/bin/bash
HEARTBEAT="/tmp/senator-${SECTOR}.heartbeat"
if [ -f "$HEARTBEAT" ]; then
    AGE=$(( $(date +%s) - $(stat -c %Y "$HEARTBEAT") ))
    [ "$AGE" -lt 28800 ] && exit 0  # 8h margin on 6h cycle
fi
pgrep -f "senator_research.py" > /dev/null 2>&1
```
