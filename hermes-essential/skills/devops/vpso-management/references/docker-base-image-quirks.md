# Docker Base Image Quirks: nousresearch/hermes-agent:latest

## Python Environment
- Python 3.13.5 venv at `/opt/hermes/.venv/bin/python3`
- **NO pip or ensurepip** — `python3 -m pip` and `python3 -m ensurepip` both fail with `ModuleNotFoundError`
- `requests` is pre-installed (v2.33.1) — no need to install
- `beautifulsoup4` and `lxml` are NOT pre-installed and CANNOT be installed via pip
- Workaround: avoid dependencies that need pip; use stdlib + requests only

## Entrypoint Behavior
- The image entrypoint is the `hermes` CLI, which intercepts ALL commands
- `docker run nousresearch/hermes-agent:latest python3 /app/script.py` will NOT work — hermes CLI catches it
- **Fix**: Override entrypoint in Dockerfile: `ENTRYPOINT ["/usr/bin/tini", "--"]` or `ENTRYPOINT ["/bin/sh", "-c"]`
- In docker-compose, use `command:` to specify the actual script to run

## Skill Sync on Every Run
- Container syncs 89+ bundled skills from base image on every startup
- Adds ~10s to startup time — this is normal
- Skills are synced to `~/.hermes/skills/` inside the container

## Network Access to Host
- `extra_hosts: "host.docker.internal:host-gateway"` allows DNS resolution
- But UFW may still block specific ports (e.g., 8000)
- **Best fix**: Use `network_mode: host` in docker-compose — eliminates DNS and firewall issues entirely
- Trade-off: no port mapping, containers share host network namespace
- With `network_mode: host`, use `ORCHESTRATOR_URL=http://127.0.0.1:8000` (localhost)

## Web Search from Containers
- DuckDuckGo Instant Answer API (`https://api.duckduckgo.com/`) is slow from containers — often times out at 10s
- Wikipedia API (`https://en.wikipedia.org/w/api.php`) returns 403 without User-Agent header
- **Working config**:
  ```python
  # Wikipedia (primary — most reliable with UA header)
  headers = {"User-Agent": "SenatorPentahelix/3.0 (https://upshalter.com; research-bot)"}
  resp = requests.get(url, params=params, headers=headers, timeout=10)
  
  # DuckDuckGo (fallback — use short timeout)
  resp = requests.get(url, params=params, timeout=5)  # 5s to fail fast
  ```
- Search order: Wikipedia first (with UA), DDG second (short timeout), then placeholder

## Healthcheck Pattern
```dockerfile
COPY healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh
```
```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "/app/healthcheck.sh"]
  interval: 30m
  timeout: 10s
  retries: 3
  start_period: 30s
```
Healthcheck script checks heartbeat file touched by agent's main loop.

## Signal Handling
- Use `tini` as PID 1 for proper signal forwarding: `ENTRYPOINT ["/usr/bin/tini", "--"]`
- Python script should handle SIGTERM/SIGINT for graceful shutdown
- Sleep in small chunks (30s) to respond to signals quickly

## Poll-Loop Pattern for Long-Running Agents
```python
import signal, time

_shutdown_requested = False
def _handle_signal(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)

while not _shutdown_requested:
    do_work()
    remaining = CYCLE_INTERVAL_SECONDS
    while remaining > 0 and not _shutdown_requested:
        time.sleep(min(30, remaining))
        remaining -= 30
        touch_heartbeat()
```
