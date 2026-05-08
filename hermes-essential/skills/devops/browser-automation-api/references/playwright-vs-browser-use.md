# Playwright Direct vs browser-use Comparison

## Test Results Summary

### browser-use + langchain-openai + OpenRouter
**Status: ❌ FAILED**

#### Error Pattern
```
TimeoutError: Event handler browser_use.browser.watchdog_base.BrowserSession.on_BrowserStartEvent
timed out after 30.0s and interrupted any processing of 2 child events
```

#### Root Cause
CDP (Chrome DevTools Protocol) connection fails:
```python
# Error trace
aiohttp.client_exceptions.ClientConnectorError: Cannot connect to host 127.0.0.1:41105
ConnectionRefusedError: [Errno 111] Connect call failed ('127.0.0.1', 41105)
```

Chromium launches successfully (verified manually), but browser-use can't connect via CDP.

#### Attempted Workarounds (All Failed)
1. **Increased timeout**: Set `TIMEOUT_BrowserStartEvent=120.0` → Still timeout
2. **Added provider attribute**: Created `ChatOpenAIWithProvider` subclass → CDP still fails
3. **Explicit API key + base_url**: Set in `ChatOpenAI()` and env vars → No effect
4. **Set OPENAI_API_KEY**: Mapped OPENROUTER_API_KEY → No effect

#### Test Command
```bash
/opt/browser-use-venv/bin/python3 test_browser_use2.py
# Result: Always fails at CDP connection stage
```

---

### Playwright Direct
**Status: ✅ SUCCESS**

#### Working Pattern
```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    page = await browser.new_page()
    await page.goto('https://example.com', timeout=30000)
    content = await page.content()
    await browser.close()
```

#### Test Result
```bash
$ curl -X POST http://localhost:8090/browse \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","task":"Extract title"}'

{"success":true,"content":"Title: Example Domain\n\nExample Domain..."}
```

#### Advantages
1. **No CDP issues**: Direct browser control, no protocol overhead
2. **Simple**: Fewer moving parts than browser-use
3. **Reliable**: Works consistently after initial setup
4. **Fast**: No timeout issues

---

## Recommendation

**Use Playwright Direct** for browser automation API services.

Only consider browser-use if you specifically need:
- AI agent that navigates complex multi-step workflows
- Built-in LLM-based decision making
- But expect to debug CDP connection issues