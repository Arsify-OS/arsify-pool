---
name: browser-automation-api
description: Setup browser automation API services using Playwright direct (not browser-use). Includes FastAPI wrapper, systemd service, and common pitfalls with langchain-openai + OpenRouter.
---

# Browser Automation API Service

Quick pattern for exposing browser automation as an HTTP API using **Playwright direct** (not browser-use). Covers FastAPI wrapper, systemd service, and why browser-use often fails with CDP timeouts.

## When to use

- Need to expose browser automation (scraping, content extraction) as HTTP API
- Senator/worker containers need to call browser automation via `host.docker.internal`
- browser-use fails with CDP connection timeouts
- Need reliable headless Chromium automation

## Quick Start

### 1. Install Playwright in venv

```bash
cd /opt/my-service
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn playwright
playwright install chromium
```

### 2. API Service (main.py)

Use this template - Playwright direct, NOT browser-use:

```python
#!/opt/my-service/venv/bin/python3
"""Browser Automation API - Playwright Direct"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Browser Automation API", description="Playwright-based browser automation")

class BrowseRequest(BaseModel):
    url: str
    task: str = "Extract main content from this page"
    max_steps: int = 5

class BrowseResponse(BaseModel):
    success: bool
    content: str = ""
    error: str = ""

@app.get("/health")
async def health():
    return {"status": "healthy", "playwright": True}

@app.post("/browse", response_model=BrowseResponse)
async def browse(req: BrowseRequest):
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            page = await browser.new_page()
            await page.goto(req.url, timeout=30000, wait_until='domcontentloaded')
            
            # Extract content
            await page.evaluate("""() => {
                document.querySelectorAll('script, style, noscript').forEach(el => el.remove());
            }""")
            text_content = await page.evaluate("() => document.body.innerText")
            
            await browser.close()
            return BrowseResponse(success=True, content=text_content[:5000])
            
    except Exception as e:
        import traceback
        return BrowseResponse(success=False, error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
```

### 3. Systemd Service

File: `/etc/systemd/system/browser-automation-api.service`

```ini
[Unit]
Description=Browser Automation API (Playwright)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/my-service
Environment="PATH=/opt/my-service/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=/opt/my-service/venv/bin/python3 /opt/my-service/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable & start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable browser-automation-api.service
sudo systemctl start browser-automation-api.service
```

## Why NOT browser-use

browser-use + langchain-openai + OpenRouter **fails with CDP timeouts**:

```
TimeoutError: Event handler browser_use.browser.watchdog_base.BrowserSession.on_BrowserStartEvent
timed out after 30.0s
ConnectionRefusedError: [Errno 111] Connect call failed ('127.0.0.1', 41105)
```

Root cause: CDP (Chrome DevTools Protocol) connection fails even though Chromium works manually.

### Workaround attempts that failed

1. Increase `TIMEOUT_BrowserStartEvent` to 120s → still timeout
2. Subclass `ChatOpenAI` to add `provider` property → CDP still fails
3. Set `OPENAI_API_KEY` + `OPENAI_BASE_URL` explicitly → CDP still fails

### Solution: Playwright direct

Playwright works reliably:
```bash
# This works:
chromium.launch(headless=True) → page.goto() → extract content

# browser-use fails:
Agent(llm=ChatOpenAI(...), browser=Browser(...)) → CDP timeout
```

## Pitfalls

1. **langchain-openai + OpenRouter**: Must pass `api_key` AND `base_url` explicitly:
   ```python
   ChatOpenAI(
       model="openrouter/meta-llama/llama-3.1-8b-instruct",
       api_key=os.getenv("OPENROUTER_API_KEY"),
       base_url="https://openrouter.ai/api/v1"  # REQUIRED
   )
   ```

2. **browser-use `provider` attribute**: `ChatOpenAI` doesn't have `provider` attribute. Need wrapper:
   ```python
   class ChatOpenAIWithProvider(ChatOpenAI):
       @property
       def provider(self):
           return "openai"
   ```
   But even with this, CDP timeouts persist.

3. **Chromium args**: Always include for headless:
   ```python
   args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
   ```

4. **Content extraction**: Remove scripts/styles before extracting text:
   ```python
   await page.evaluate("""() => {
       document.querySelectorAll('script, style, noscript').forEach(el => el.remove());
   }""")
   ```

## Testing

```bash
# Health check
curl http://localhost:8090/health

# Test browse
curl -X POST http://localhost:8090/browse \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","task":"Extract title"}'
```

## References

- See `references/playwright-vs-browser-use.md` for detailed comparison
- See `templates/fastapi-playwright-main.py` for full template