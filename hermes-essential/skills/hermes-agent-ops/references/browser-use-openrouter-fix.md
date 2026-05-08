# Browser-Use + OpenRouter Integration Fix

## Complete Working main.py

Location: `/opt/browser-use-service/main.py`

```python
#!/opt/browser-use-venv/bin/python3
"""
Browser-Use API Service
Wrapper untuk browser-use yang bisa dipanggil senator containers.
Jalan di host, senator akses via host.docker.internal.
"""

import os

# CRITICAL: Set OpenAI API key BEFORE any imports (especially langchain-openai)
# Get OPENROUTER_API_KEY from environment
openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

# If not in env, try to get from /proc/1/environ (system env)
if not openrouter_key:
    try:
        with open("/proc/1/environ", "r") as f:
            env_data = f.read()
            for line in env_data.split("\0"):
                if line.startswith("OPENROUTER_API_KEY="):
                    openrouter_key = line.split("=", 1)[1]
                    break
    except:
        pass

# Set for langchain-openai
if openrouter_key:
    os.environ["OPENAI_API_KEY"] = openrouter_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import traceback

from browser_use import Agent, Browser
from browser_use import Controller, ActionResult
from langchain_openai import ChatOpenAI
from pydantic import ConfigDict

# Subclass ChatOpenAI to add 'provider' property that browser-use expects
# and allow extra attributes (for browser-use token tracking)
class ChatOpenAIWithProvider(ChatOpenAI):
    model_config = ConfigDict(extra='allow')
    
    @property
    def provider(self):
        return "openai"

app = FastAPI(title="Browser-Use API", description="Browser automation for Senator Workers")

class BrowseRequest(BaseModel):
    url: str
    task: str = "Extract main content from this page"
    max_steps: int = 5

class BrowseResponse(BaseModel):
    success: bool
    content: str = ""
    error: str = ""
    screenshot_path: str = ""

@app.get("/")
async def root():
    return {"service": "Browser-Use API", "status": "running", "docs": "/docs"}

@app.post("/browse", response_model=BrowseResponse)
async def browse(req: BrowseRequest):
    """
    Browse a URL and extract content using browser-use AI agent.
    Senator containers call this endpoint.
    """
    try:
        # Use OpenRouter via langchain-openai
        # Explicitly pass api_key and base_url to avoid langchain-openai issues
        llm = ChatOpenAIWithProvider(
            model="openrouter/meta-llama/llama-3.1-8b-instruct",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://upshalter.com",
                "X-Title": "Upshalter Senator Research",
            }
        )
        
        # Use headless browser
        browser = Browser(
            headless=True,
        )
        
        agent = Agent(
            task=f"{req.task}. URL: {req.url}",
            llm=llm,
            browser=browser,
            max_steps=req.max_steps
        )
        
        result = await agent.run()
        
        # Extract content from result
        content = ""
        if result and hasattr(result, 'final_result'):
            content = str(result.final_result())
        
        await browser.close()
        
        return BrowseResponse(
            success=True,
            content=content[:5000]  # Limit content size
        )
        
    except Exception as e:
        error_detail = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        return BrowseResponse(
            success=False,
            error=error_detail[:1000]
        )

@app.get("/health")
async def health():
    return {"status": "healthy", "browser_use_installed": True}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Browser-Use API Service...")
    print("   Docs: http://0.0.0.0:8090/docs")
    print("   Senator access: http://host.docker.internal:8090")
    uvicorn.run(app, host="0.0.0.0", port=8090)
```

## Setup Commands

```bash
# Create venv
python3 -m venv /opt/browser-use-venv

# Activate and install
source /opt/browser-use-venv/bin/activate
pip install browser-use langchain-openai fastapi uvicorn

# Install Playwright
pip install playwright
playwright install chromium

# Run service
cd /opt/browser-use-service
OPENROUTER_API_KEY="sk-or-v1-..." /opt/browser-use-venv/bin/python3 main.py
```

## Test Endpoint

```bash
curl -X POST http://localhost:8090/browse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "task": "Extract the main heading", "max_steps": 3}'
```

## Known Unresolved Issue

**CDP Timeout**: The browser-use agent may timeout during browser startup (30s default). Error:
```
TimeoutError: Event handler browser_use.browser.watchdog_base.BrowserSession.on_BrowserStartEvent#... timed out after 30.0s
```

This appears to be a Chrome DevTools Protocol connection issue. May require:
- Increasing timeout in `browser_use/browser/watchdog_base.py`
- Checking Chromium permissions
- Verifying Playwright browser installation at `/root/.cache/ms-playwright/`
