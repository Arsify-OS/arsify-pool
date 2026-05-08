# OpenClaw Architecture Reference for Hermes Internet

## Source
OpenClaw v2026.5.x — `/root/openclaw/` on VPS Upshalter
Repo: https://github.com/openclaw/openclaw
Docs: https://docs.openclaw.ai

## What is OpenClaw?

OpenClaw is a **personal AI assistant platform** you run on your own devices.
The Gateway is the control plane — the product is the assistant.

Supported channels: WhatsApp, Telegram, Slack, Discord, Google Chat, Signal, iMessage, BlueBubbles, IRC, Microsoft Teams, Feishu, LINE, Mattermost, Nextcloud Talk, Nostr, Synology Chat, Tlon, Twitch, Zalo, WeChat, QQ, WebChat.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OPENCLAW GATEWAY                          │
│                    (port 18789)                              │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   CHANNELS   │  │   PROVIDERS  │  │    EXTENSIONS    │   │
│  │              │  │              │  │                  │   │
│  │ • Telegram   │  │ • OpenAI     │  │ • Brave Search   │   │
│  │ • Discord    │  │ • Anthropic  │  │ • Google Search  │   │
│  │ • Slack      │  │ • Google     │  │ • DuckDuckGo     │   │
│  │ • WhatsApp   │  │ • Ollama     │  │ • Firecrawl      │   │
│  │ • Signal     │  │ • OpenRouter │  │ • Web Readability│   │
│  │ • iMessage   │  │ • ...        │  │ • Exa            │   │
│  │ • IRC        │  │              │  │ • Tavily         │   │
│  │ • Matrix     │  │              │  │ • SearXNG        │   │
│  │ • ...        │  │              │  │ • ... 70+        │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    AGENTS                             │   │
│  │  • Web Search (Brave, Google, DDG, Exa, Tavily)     │   │
│  │  • Web Fetch (readability, content extraction)      │   │
│  │  • Browser (full browser automation)                │   │
│  │  • Skills (blogwatcher, github, notion, ...)        │   │
│  │  • Memory (memory-core, memory-wiki, memory-lancedb)│   │
│  │  • Cron (scheduled tasks)                           │   │
│  │  • Polls (voting/decision making)                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Key Components for Hermes Internet

### 1. Web Search (`src/web-search/`)

OpenClaw's search is plugin-based. Providers are registered via `openclaw.plugin.json`:

```typescript
// src/web-search/runtime.ts — search provider resolution
function resolveSearchConfig(cfg?: OpenClawConfig): WebSearchConfig {
  return resolveWebProviderConfig(cfg, "search");
}
```

Providers resolve via `resolveRuntimeWebSearchProviders()` which reads from config.

### 2. Web Fetch (`src/web-fetch/`)

Content extraction from URLs:
- `runtime.ts` — fetch and extract content
- `content-extractors.runtime.ts` — extract article text from HTML

### 3. Browser (`src/browser-lifecycle-cleanup.ts`)

Full browser automation for complex pages.

### 4. Skills (`skills/blogwatcher/`)

Blog/RSS monitoring with `blogwatcher` CLI:
```bash
blogwatcher add "My Blog" https://example.com
blogwatcher scan
blogwatcher articles
```

### 5. Extensions (`extensions/`)

Search-related extensions:
- `extensions/brave/` — Brave Search API (requires `BRAVE_API_KEY`)
- `extensions/google/` — Google Custom Search (requires `GOOGLE_API_KEY`)
- `extensions/duckduckgo/` — DuckDuckGo (free, no key needed)
- `extensions/exa/` — Exa.ai semantic search (requires `EXA_API_KEY`)
- `extensions/tavily/` — Tavily search (requires `TAVILY_API_KEY`)
- `extensions/searxng/` — Self-hosted SearXNG (free, self-hosted)
- `extensions/firecrawl/` — Deep web scraping (requires `FIRECRAWL_API_KEY`)
- `extensions/web-readability/` — Content extraction (free)

### 6. Docker Compose

```yaml
# openclaw-gateway service
services:
  openclaw-gateway:
    image: ${OPENCLAW_IMAGE:-openclaw:local}
    build: .
    environment:
      OPENCLAW_CONFIG_DIR: /home/node/.openclaw
      OPENCLAW_WORKSPACE_DIR: /home/node/.openclaw/workspace
      OPENCLAW_GATEWAY_TOKEN: ${OPENCLAW_GATEWAY_TOKEN:-}
    volumes:
      - ${OPENCLAW_CONFIG_DIR}:/home/node/.openclaw
      - ${OPENCLAW_WORKSPACE_DIR}:/home/node/.openclaw/workspace
    extra_hosts:
      - "host.docker.internal:host-gateway"
    ports:
      - "${OPENCLAW_GATEWAY_PORT:-18789}:18789"
    cap_drop:
      - NET_RAW
      - NET_ADMIN
    security_opt:
      - no-new-privileges:true
```

## Lessons for Hermes Internet

1. **Plugin architecture**: OpenClaw keeps core lean, puts capabilities in extensions. Hermes Internet should follow this pattern.

2. **Search provider abstraction**: OpenClaw resolves providers at runtime from config. Hermes Internet should support multiple search backends with fallback.

3. **Security**: OpenClaw drops `NET_RAW`/`NET_ADMIN` capabilities and uses `no-new-privileges`. Should follow same pattern.

4. **Channel-first**: OpenClaw connects to 20+ messaging channels. Hermes Internet should focus on Telegram for now but keep channel abstraction.

5. **Skills system**: OpenClaw ships bundled skills. Hermes Internet should have skills like blogwatcher, news monitor, fact-checker.

6. **Memory**: OpenClaw has multiple memory plugins (memory-core, memory-wiki, memory-lancedb). Hermes Internet should use SKP as primary memory.

## Comparison: NanoClaw vs OpenClaw vs Hermes

| Feature | NanoClaw | OpenClaw | Hermes (current) |
|---------|----------|----------|-------------------|
| Architecture | Host + Container per session | Gateway + Plugins | Gateway + Skills |
| Channels | Telegram, Discord, Slack | 20+ channels | Telegram, Discord, Slack, WhatsApp |
| Web Search | Not built-in | Brave, Google, DDG, Exa, Tavily | via tool `web_search` |
| Web Crawl | Not built-in | Firecrawl, web-readability | via tool `browser` |
| Memory | CLAUDE.local.md | memory-core, memory-wiki | memory tool + SKP |
| Cron | Poll loop | Built-in cron | cronjob tool |
| Skills | Container skills | 50+ bundled skills | 89+ skills |
| SKP | No | No | Yes (VPSO Knowledge Pool) |
| Multi-agent | Per-session container | Extensions | delegate_task |

## Recommended Stack for Hermes Internet

Free tier (no API keys needed):
- Wikipedia API (primary)
- DuckDuckGo (fallback)
- web-readability (content extraction)
- blogwatcher (RSS monitoring)

Paid upgrade path:
- Brave Search API ($2/1000 queries)
- Exa.ai (semantic search)
- Tavily (AI-powered search)
- Firecrawl (deep scraping)

## OpenClaw Installation (if needed)

```bash
# Node 22+ required
pnpm install
pnpm openclaw onboard  # Interactive setup
pnpm openclaw gateway start
```
