# Docker Base Image Pitfalls — nousresearch/hermes-agent

## Key Facts

- **NO pip** — The base image does NOT have pip installed. Cannot use `pip install`.
- **NO ensurepip** — `python3 -m ensurepip` fails with "No module named ensurepip".
- **Entrypoint intercepts ALL commands** — Must use full path: `/opt/hermes/.venv/bin/python3 -m pip install ...`
- **Python 3.13.5** — Located at `/opt/hermes/.venv/bin/python3`
- **requests already installed** — `import requests` works out of the box (v2.33.1)
- **bs4/lxml NOT installed** — Must install manually if needed

## Installing Packages

```bash
# CORRECT — use python3 -m pip via full venv path
RUN /opt/hermes/.venv/bin/python3 -m pip install --no-cache-dir \
    beautifulsoup4 \
    lxml

# WRONG — pip not in PATH
RUN pip install requests

# WRONG — ensurepip not available
RUN python3 -m ensurepip
```

## Network: host.docker.internal

- Does NOT work from Docker containers on this VPS (Hostinger).
- Ping works (network OK) but port connections time out.
- **Solution**: Use `network_mode: host` in docker-compose, OR add UFW rules:
  ```bash
  ufw allow from 172.17.0.0/16 to any port 8000 proto tcp comment "Docker to host"
  ```

## Web API Quirks from Docker Containers

- **DuckDuckGo Instant Answer API**: Times out from Docker containers. Use short timeout (5s) and fallback.
- **Wikipedia API**: Returns 403 without User-Agent header. Always set `User-Agent: YourBot/1.0`.
- **Reddit JSON API**: Works without auth. Use `https://www.reddit.com/r/{sub}/hot.json?limit=N`.
- **Nitter**: Works without API key for Twitter monitoring.

## SQLite ALTER TABLE

- SQLite does not support multiple ADD COLUMN in one statement on older versions.
- Must run each ALTER separately:
  ```sql
  ALTER TABLE knowledge ADD COLUMN feedback TEXT DEFAULT '';
  ALTER TABLE knowledge ADD COLUMN rating INTEGER DEFAULT 0;
  ```
