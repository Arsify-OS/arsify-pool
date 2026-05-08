#!/usr/bin/env python3
"""
SENATOR FACTORY PIPELINE
Each senator runs this: Scrape → Analyze → Draft → Output to shared dirs
Similar to Hermes Internet Worker Pool pattern
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from urllib.parse import quote

# CONFIG from environment
SECTOR = os.getenv("SECTOR", "akademisi")
SENATOR_NAME = os.getenv("SENATOR_NAME", f"Senator {SECTOR.title()}")
# Telegram config — read from environment, fallback to hardcoded
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5807834405")

# Read OPENROUTER_API_KEY from file (mounted from host)
OPENROUTER_KEY = None
key_file = "/opt/data/.openrouter_key"
if os.path.exists(key_file):
    with open(key_file) as f:
        OPENROUTER_KEY = f.read().strip()
if not OPENROUTER_KEY:
    OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")  # Fallback to env var

# Paths (mounted from host)
LINKS_DIR = "/opt/data/editorial-links"
DRAFTS_DIR = "/opt/data/editorial-drafts"
DATA_DIR = "/app/data"

# LLM Model — use free model on OpenRouter (bisa di-override via env var MODEL)
MODEL = os.getenv("MODEL", "meta-llama/llama-3.3-70b-instruct:free")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def scrape_google_news(sector, max_items=10):
    """Scrape Google News RSS for sector keywords."""
    queries = {
        "akademisi": "AI research university breakthrough 2026",
        "bisnis": "AI business investment startup 2026",
        "komunitas": "AI community open source 2026",
        "pemerintah": "AI regulation government policy 2026",
        "media": "AI technology news media 2026"
    }
    
    query = queries.get(sector, "AI news 2026")
    url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
    
    log(f"Scraping Google News for: {query}")
    
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        
        # Parse RSS XML (simple regex, no BeautifulSoup needed)
        items = []
        for item in resp.text.split('<item>')[1:max_items+1]:
            title = item.split('<title>')[1].split('</title>')[0].replace('<![CDATA[', '').replace(']]>', '')
            link = item.split('<link>')[1].split('</link>')[0].replace('<![CDATA[', '').replace(']]>', '')
            pubdate = item.split('<pubDate>')[1].split('</pubDate>')[0] if '<pubDate>' in item else ''
            
            items.append({
                "title": title,
                "link": link,
                "pubDate": pubdate,
                "source": "Google News"
            })
        
        log(f"Found {len(items)} articles")
        return items
    except Exception as e:
        log(f"❌ Scraping error: {e}")
        return []

def fetch_article_content(url):
    """Fetch full article text from URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        # Simple text extraction
        from html.parser import HTMLParser
        
        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.skip = False
            
            def handle_starttag(self, tag, attrs):
                if tag in ['script', 'style', 'nav', 'footer']:
                    self.skip = True
            
            def handle_endtag(self, tag):
                if tag in ['script', 'style', 'nav', 'footer']:
                    self.skip = False
            
            def handle_data(self, data):
                if not self.skip:
                    self.text.append(data.strip())
        
        parser = TextExtractor()
        parser.feed(resp.text)
        text = ' '.join([t for t in parser.text if t])
        return text[:3000]  # Limit for LLM
    except Exception as e:
        log(f"⚠️ Failed to fetch {url[:50]}: {str(e)[:50]}")
        return ""

def call_llm(prompt, max_tokens=300):
    """Call OpenRouter API with error handling, fallback to Ollama."""
    if not OPENROUTER_KEY:
        log("❌ OPENROUTER_API_KEY not set! Falling back to Ollama...")
        return call_ollama(prompt, max_tokens)
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        if resp.status_code in (402, 429):
            log(f"⚠️ OpenRouter {resp.status_code} — fallback to Ollama...")
            return call_ollama(prompt, max_tokens)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        log(f"❌ OpenRouter Error: {e} — fallback to Ollama...")
        return call_ollama(prompt, max_tokens)

def call_ollama(prompt, max_tokens=300):
    """Fallback to local Ollama LLM."""
    try:
        resp = requests.post(
            "http://host.docker.internal:11434/api/generate",
            json={"model": "phi3:mini", "prompt": prompt, "max_tokens": max_tokens},
            timeout=300  # Increase timeout to 5 minutes
        )
        resp.raise_for_status()
        # Ollama returns streaming JSON lines; extract the response
        lines = resp.text.strip().split('\n')
        full_response = ''
        for line in lines:
            if line:
                obj = json.loads(line)
                full_response += obj.get('response', '')
                if obj.get('done'):
                    break
        return full_response.strip()
    except Exception as e:
        log(f"❌ Ollama Error: {e}")
        return None

def analyze_and_draft(articles):
    """Analyze articles and create editorial draft."""
    # Combine article titles + links
    articles_text = "\n".join([f"- {a['title']} ({a['link']})" for a in articles])
    
    prompt = f"""You are {SENATOR_NAME}. Analyze these news articles about {SECTOR} sector.

Articles:
{articles_text}

Create an EDITORIAL DRAFT in Indonesian that:
1. Summarizes key developments (2-3 sentences)
2. Provides sector-specific insights
3. Highlights why this matters for {SECTOR} sector
4. Professional but engaging tone
5. Max 200 words

Write the draft in Indonesian:"""
    
    return call_llm(prompt, max_tokens=300)

def write_outputs(articles, draft):
    """Write links and draft to shared directories."""
    # Ensure dirs exist
    os.makedirs(LINKS_DIR, exist_ok=True)
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    
    # Write links file
    links_file = os.path.join(LINKS_DIR, f"senator-{SECTOR}.txt")
    with open(links_file, 'w') as f:
        for a in articles:
            f.write(f"{a['link']}\n")
    log(f"✅ Links written to {links_file}")
    
    # Write draft file
    draft_file = os.path.join(DRAFTS_DIR, f"senator-{SECTOR}-draft.md")
    with open(draft_file, 'w') as f:
        f.write(f"# Editorial Draft - {SENATOR_NAME}\n\n")
        f.write(f"**Sector:** {SECTOR}\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"---\n\n{draft}\n")
    log(f"✅ Draft written to {draft_file}")
    
    return links_file, draft_file

def send_telegram_notification(draft):
    """Notify curator that draft is ready."""
    msg = f"📰 *{SENATOR_NAME}* selesai bikin draft editorial!\n\nSector: {SECTOR}\nDraft sudah di-share ke shared dirs.\n\nMain pipeline bakal proses jadi Policy Brief soon! 🚀"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        log("✅ Telegram notification sent!")
    except Exception as e:
        log(f"⚠️ Telegram notification failed: {e}")

def main():
    log(f"🏭 {SENATOR_NAME} Factory Pipeline STARTED")
    log(f"Sector: {SECTOR}")
    
    # Step 1: Scrape
    log("📰 [1/4] Scraping news...")
    articles = scrape_google_news(SECTOR)
    if not articles:
        log("❌ No articles found!")
        sys.exit(1)
    
    # Step 2: Analyze & Draft
    log("🧠 [2/4] Analyzing with LLM & creating draft...")
    draft = analyze_and_draft(articles)
    if not draft:
        log("⚠️ LLM analysis failed (possibly rate limited or credit issue)")
        log("⚠️ Continuing with title-only draft (no LLM)...")
        # Create a simple draft from article titles (no LLM needed)
        draft = f"## Ringkasan Berita {SECTOR.title()}\n\n"
        for i, a in enumerate(articles[:5], 1):
            draft += f"{i}. {a['title']}\n   Sumber: {a['link']}\n\n"
        draft += f"\n*Draft ini dibuat tanpa LLM analysis karena keterbatasan kredit.*"
        log(f"--- DRAFT PREVIEW (no LLM) ---\n{draft[:200]}...\n")
    else:
        log(f"\n--- DRAFT PREVIEW ---\n{draft[:200]}...\n")
    
    # Step 3: Write outputs
    log("📝 [3/4] Writing links & draft to shared dirs...")
    links_file, draft_file = write_outputs(articles, draft)
    
    # Step 4: Notify
    log("📲 [4/4] Sending notification...")
    send_telegram_notification(draft)
    
    log(f"✅ {SENATOR_NAME} Pipeline COMPLETE!")
    log(f"Links: {links_file}")
    log(f"Draft: {draft_file}")

if __name__ == "__main__":
    main()
