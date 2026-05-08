# Web Search from Docker Containers — Patterns & Pitfalls

## Problem
Docker containers on VPS often have restricted outbound access. DuckDuckGo API is slow/unreliable, Wikipedia returns 403 without proper headers.

## Solution: Multi-Source Search with Fallback

```python
import requests, re

def search_wikipedia(query, max_results=3):
    """PRIMARY source — most reliable from containers."""
    headers = {"User-Agent": "SenatorPentahelix/3.0 (https://upshalter.com; research-bot)"}
    resp = requests.get("https://en.wikipedia.org/w/api.php",
        params={"action":"query","list":"search","srsearch":query,"srlimit":max_results,"format":"json"},
        headers=headers, timeout=10)
    if resp.status_code != 200:
        return []
    data = resp.json()
    results = []
    for item in data.get("query", {}).get("search", []):
        title = item.get("title", "")
        snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))[:300]
        url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        results.append({"title": title, "snippet": snippet, "url": url, "source": "Wikipedia"})
    return results

def search_duckduckgo(query, max_results=3):
    """SECONDARY source — fallback only. Use 5s timeout."""
    resp = requests.get("https://api.duckduckgo.com/",
        params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
        timeout=5)
    if resp.status_code != 200:
        return []
    data = resp.json()
    results = []
    if data.get("Abstract"):
        return [{"title": data.get("Heading", query), "snippet": data["Abstract"][:300],
                 "url": data.get("AbstractURL", ""), "source": data.get("AbstractSource", "DDG")}]
    for topic in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(topic, dict) and topic.get("Text"):
            results.append({"title": topic["Text"][:100], "snippet": topic["Text"][:300],
                           "url": topic.get("FirstURL", ""), "source": "DuckDuckGo"})
    return results

def search_web(query, max_results=3):
    """Multi-source: Wikipedia → DDG → empty."""
    results = search_wikipedia(query, max_results)
    if results:
        return results
    results = search_duckduckgo(query, max_results)
    if results:
        return results
    return []
```

## Key Findings (6 Mei 2026)

| Source | Reliability | Speed | Notes |
|--------|-------------|-------|-------|
| Wikipedia API | ★★★★★ | ~0.5s | Needs User-Agent header (403 without) |
| DuckDuckGo API | ★★☆☆☆ | 5-30s | Often times out from containers; rate-limited |
| Google (direct) | ★☆☆☆☆ | N/A | Blocked by CAPTCHA from containers |

## Wikipedia API Response Format
```json
{
  "query": {
    "search": [
      {"title": "Artificial intelligence", "snippet": "...<span>...</span>..."}
    ]
  }
}
```
- Snippets contain HTML `<span class="searchmatch">` tags — strip with `re.sub(r"<[^>]+>", "", snippet)`
- URL: `https://en.wikipedia.org/wiki/{title_with_underscores}`

## DuckDuckGo API Response Format
```json
{
  "Abstract": "Short summary text",
  "AbstractURL": "https://...",
  "Heading": "Topic Title",
  "RelatedTopics": [
    {"Text": "Description", "FirstURL": "https://..."},
    {"Topics": [{"Text": "...", "FirstURL": "..."}]}  // nested subtopics
  ]
}
```
- If `Abstract` exists, it's the best single result
- `RelatedTopics` can be nested (check for `Topics` key)
- Returns 200 even for no-results (empty fields)

## Container Network Notes
- `network_mode: host` eliminates most DNS/firewall issues
- Without host mode: need `extra_hosts: ["host.docker.internal:host-gateway"]` + UFW rules
- Wikipedia works from host network mode without any special config
- DDG is unreliable regardless of network mode (rate limiting by IP)
