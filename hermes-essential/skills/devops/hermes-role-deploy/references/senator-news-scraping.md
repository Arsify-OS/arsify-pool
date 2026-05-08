# Senator Pentahelix News Scraping Reference

## Overview
Senator Pentahelix is a Docker Compose stack running 5 senator containers (akademisi, bisnis, komunitas, pemerintah, media) that fetch real-time news every 30 minutes using Google News RSS.

## Key Components
- **Image**: `senator-pentahelix:latest` (built from Dockerfile in `/root/senator-pentahelix/`)
- **Script**: `/app/scripts/senator_research.py` (runs in each container)
- **Cycle Interval**: 30 minutes (1800 seconds) via env var `CYCLE_INTERVAL_SECONDS`
- **News Source**: Google News RSS (no CAPTCHA), fallback to Bing search

## Environment Variables (docker-compose.yml)
```yaml
environment:
  - SECTOR=akademisi
  - SENATOR_NAME=Senator Akademisi
  - ORCHESTRATOR_URL=http://127.0.0.1:8000
  - API_KEY=hma_xxxxxxxx
  - CYCLE_INTERVAL_SECONDS=1800  # 30 minutes for real-time news
  - DATA_DIR=/app/data
  - LOG_LEVEL=INFO
  - TELEGRAM_BOT_TOKEN=xxxx
  - TELEGRAM_CHAT_ID=xxxx
```

**Important**: Environment variable overrides script default. If script uses `os.getenv("CYCLE_INTERVAL_SECONDS", default)`, the env var takes precedence.

## Google News RSS Fetching
URL pattern:
```
https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en
```

Fetch with curl (available in containers):
```python
import subprocess, re
result = subprocess.run(
    ["curl", "-s", "-L", "-A", "Mozilla/5.0", url],
    capture_output=True, text=True, timeout=10
)
xml_data = result.stdout
# Parse items with regex
items = re.findall(r'<item>(.*?)</item>', xml_data, re.DOTALL)
for item in items[:max_results]:
    title_match = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
    link_match = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
    title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title_match.group(1)).strip()
    url = link_match.group(1).strip()
```

No BeautifulSoup needed; regex works fine.

## Updating Script in Running Containers
Since containers use an image (not volume-mounted script), updating the script on host doesn't auto-update containers. Need to:
1. Copy updated script to container:
   ```bash
   docker cp /root/senator-pentahelix/scripts/senator_research.py <container>:/app/scripts/senator_research.py
   ```
2. Restart container: `docker restart <container>` or `docker compose up -d --force-recreate`.

## Fallback Search
If Google News RSS fails, fallback to Bing search:
```python
url = f"https://www.bing.com/search?q={query}"
result = subprocess.run(["curl", "-s", "-L", "-A", "Mozilla/5.0 ...", url], ...)
# Parse with regex for <li class="b_algo"> patterns
```

## Log Verification
Check if Google News is working:
```bash
docker logs senator-akademisi --since "2026-05-06T18:00:00" 2>&1 | grep -i "Google-News"
# Should see: "[Google-News] Found XX items in RSS"
```

## Common Pitfalls
1. **Environment variable override**: Always check `docker exec <container> env | grep CYCLE_INTERVAL_SECONDS`.
2. **Script not updated**: After editing script on host, must `docker cp` to container and restart.
3. **Google News RSS format**: Title may be wrapped in `<![CDATA[...]]>`; clean with regex.
4. **Container network**: Uses `network_mode: host` so can access localhost:8000 (orchestrator).
5. **Telegram alerts**: Ensure bot token and chat ID are set; senator sends report every cycle.
