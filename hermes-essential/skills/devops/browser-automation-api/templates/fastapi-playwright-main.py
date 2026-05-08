#!/opt/my-service/venv/bin/python3
"""
Browser Automation API Service
Playwright Direct Version - Template
"""

import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Browser Automation API",
    description="Playwright-based browser automation for workers"
)

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
    return {"service": "Browser Automation API", "status": "running", "docs": "/docs"}

@app.post("/browse", response_model=BrowseResponse)
async def browse(req: BrowseRequest):
    """
    Browse a URL and extract content using Playwright directly.
    Workers call this endpoint.
    """
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Launch Chromium (headless)
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            
            page = await browser.new_page()
            
            # Navigate to URL with timeout
            await page.goto(req.url, timeout=30000, wait_until='domcontentloaded')
            
            # Extract content based on task
            # Remove scripts and styles
            await page.evaluate("""() => {
                document.querySelectorAll('script, style, noscript').forEach(el => el.remove());
            }""")
            text_content = await page.evaluate("() => document.body.innerText")
            title = await page.title()
            
            result_text = f"Title: {title}\n\n{text_content}"
            
            await browser.close()
            
            return BrowseResponse(
                success=True,
                content=result_text[:5000]  # Limit content size
            )
            
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        return BrowseResponse(
            success=False,
            error=error_detail[:1000]
        )

@app.get("/health")
async def health():
    return {"status": "healthy", "playwright": True}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Browser Automation API Service (Playwright Direct)...")
    print("   Docs: http://0.0.0.0:8090/docs")
    print("   Workers access: http://host.docker.internal:8090")
    uvicorn.run(app, host="0.0.0.0", port=8090)
