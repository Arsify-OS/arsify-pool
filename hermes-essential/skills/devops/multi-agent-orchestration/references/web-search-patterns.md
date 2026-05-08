# Web Search Patterns for Dockerized Research Agents

## Problem: Web Search from Docker Containers

Docker containers often have network issues reaching external APIs:
- DuckDuckGo API times out (30s+ from container)
- Wikipedia returns 403 without User-Agent header
- `host.docker.internal` unreliable on Linux Docker Engine

## Solution: Multi-Source Fallback with Proper Headers

```python
import requests
import re

def search_wikipedia(query, max_results=3):
    """Wikipedia API — most reliable, free, needs User-Agent."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query", "list": "search",
        "srsearch": query, "srlimit": max_results, "format": "json",
    }
    headers = {
        "User-Agent": "SenatorPentahelix/3.0 (https://upshalter.com; research-bot)"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    if resp.status_code != 200:
        return []
    data = resp.json()
    results = []
    for item in data.get("query", {}).get("search", []):
        title = item.get("title", "")
        snippet = re.sub(r"<[^>]+>", "", item.get("snippet", "")[:300])
        url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        results.append({"title": title, "snippet": snippet, "url": url, "source": "Wikipedia"})
    return results

def search_duckduckgo(query, max_results=3):
    """DDG Instant Answer — free, rate-limited, often slow from containers."""
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = []
        if data.get("Abstract"):
            return [{"title": data.get("Heading", query), "snippet": data["Abstract"][:300],
                      "url": data.get("AbstractURL", ""), "source": data.get("AbstractSource", "DuckDuckGo")}]
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({"title": topic["Text"][:100], "snippet": topic["Text"][:300],
                               "url": topic.get("FirstURL", ""), "source": "DuckDuckGo"})
        return results
    except Exception:
        return []

def search_web(query, max_results=3):
    """Multi-source fallback: Wikipedia first, then DDG."""
    results = search_wikipedia(query, max_results)
    if results:
        return results
    return search_duckduckgo(query, max_results)
```

## Key Pitfalls

1. **Wikipedia 403**: Always send `User-Agent` header. Without it, Wikipedia blocks requests.
2. **DDG timeout**: Use `timeout=5` (not 10+). DDG is often slow from Docker. Fail fast.
3. **DDG rate limit**: DDG aggressively rate-limits from container IPs. Use as fallback only.
4. **network_mode: host**: Most reliable for container-to-host access. Avoids `host.docker.internal` issues.
5. **extra_hosts**: Alternative to host network. Add `extra_hosts: ["host.docker.internal:host-gateway"]` in docker-compose.

## OpenClaw Search Architecture Reference

OpenClaw uses a plugin-based search provider system:
- `extensions/brave/` — Brave Search API (requires API key)
- `extensions/google/` — Google Custom Search (requires API key)
- `extensions/duckduckgo/` — DuckDuckGo (free)
- `extensions/exa/` — Exa.ai (AI-powered, requires API key)
- `extensions/tavily/` — Tavily (requires API key)
- `extensions/searxng/` — SearXNG (self-hosted, free)
- `extensions/web-readability/` — Content extraction from URLs
- `extensions/firecrawl/` — Deep web scraping

For Upshalter, recommended free stack: Wikipedia + DuckDuckGo + web-readability.
For paid upgrade: Add Brave or Exa for better results.
