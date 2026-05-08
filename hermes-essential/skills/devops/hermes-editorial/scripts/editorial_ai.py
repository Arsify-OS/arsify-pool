#!/usr/bin/env python3
"""
HERMES EDITORIAL AI - Analysis & Drafting Engine (Validated Version)
Processes raw news JSON -> LLM Analysis -> Draft -> Telegram Notification
"""
import json
import os
import sys
import requests
from datetime import datetime

# CONFIG
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_TOKEN = "8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU"
TELEGRAM_CHAT_ID = "5807834405"
MODEL = "meta-llama/llama-3.1-8b-instruct"  # Validated model

def fetch_article_content(url):
    """Fetch and extract main text from URL (for links sent by Senators)."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        # Simple HTML text extraction (no BeautifulSoup needed)
        import re
        text = resp.text
        # Remove script and style tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:3000]  # Limit to 3000 chars for LLM processing
    except Exception as e:
        print(f"⚠️ Failed to fetch {url}: {str(e)[:50]}")
        return ""

def call_llm(prompt, max_tokens=500):
    """Call OpenRouter API."""
    if not OPENROUTER_KEY:
        print("❌ OPENROUTER_API_KEY not set!")
        return None
    
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
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return None

def analyze_news(articles_text):
    """Cluster topics & score virality from raw article texts."""
    prompt = f"""Analyze these news article texts (combined). Do:
1. **Topic Cluster** (in Indonesian, e.g., "AI Regulation Updates")
2. **Viral Score** (1-100) with short reason (keywords: breakthrough, banned, trillion, top sources)
3. **3-sentence engaging summary in Indonesian** for tech-savvy audience

Article Texts:
{articles_text[:4000]}  # Limit input to 4000 chars

Format:
TOPIC: [Cluster Name]
SCORE: [1-100] | Reason: [short reason]
SUMMARY: [3 sentences in Indonesian]
"""
    return call_llm(prompt, max_tokens=300)

def create_policy_brief(fetched_text, senator_drafts):
    """Create Policy Brief from fetched content + senator drafts."""
    prompt = f"""You are a policy analyst. Create a POLICY BRIEF in Indonesian based on:

1. FETCHED ARTICLE CONTENT:
{fetched_text[:3000]}

2. SENATOR EDITORIAL DRAFTS:
{senator_drafts[:2000]}

Format the Policy Brief as:
📋 *HERMES POLICY BRIEF*

*Executive Summary* (2-3 sentences in Indonesian)

*Key Findings* (bullet points, Indonesian)
- Finding 1
- Finding 2
- Finding 3

*Policy Implications* (2-3 sentences, Indonesian)

*Recommendations* (numbered, Indonesian)
1. Rec 1
2. Rec 2
3. Rec 3

*Sources* (list the URLs/topics from senators)
"""
    return call_llm(prompt, max_tokens=500)

def notify_curator(topic, score, draft):
    """Send ONLY editorial draft to Curator (no links, no raw data)."""
    msg = f"""{draft}"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print("✅ Editorial draft sent to Curator via Telegram!")
        return True
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: editorial_ai.py <links_file> <drafts_dir>")
        print("  links_file: text file with one URL per line")
        print("  drafts_dir: directory containing senator-*-draft.md files")
        sys.exit(1)
    
    links_file = sys.argv[1]
    drafts_dir = sys.argv[2]
    
    # === STEP 1: Fetch content from links ===
    if not os.path.exists(links_file):
        print(f"❌ Links file not found: {links_file}")
        sys.exit(1)
    
    with open(links_file) as f:
        links = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
    
    print(f"📰 [1/4] Fetching content from {len(links)} links...")
    articles_text = []
    for i, url in enumerate(links, 1):
        print(f"  [{i}/{len(links)}] Fetching {url[:50]}...")
        content = fetch_article_content(url)
        if content:
            articles_text.append(content)
    
    fetched_content = "\n\n".join(articles_text) if articles_text else ""
    
    # === STEP 2: Read senator editorial drafts ===
    print(f"📝 [2/4] Reading senator drafts from {drafts_dir}...")
    senator_drafts = []
    if os.path.exists(drafts_dir):
        for draft_file in os.listdir(drafts_dir):
            if draft_file.endswith('-draft.md') or draft_file.endswith('.md'):
                with open(os.path.join(drafts_dir, draft_file)) as f:
                    senator_drafts.append(f"--- {draft_file} ---\n{f.read()}")
    
    if not senator_drafts:
        print("⚠️ No senator drafts found, using fetched content only")
        drafts_text = ""
    else:
        drafts_text = "\n\n".join(senator_drafts)
        print(f"   Found {len(senator_drafts)} draft(s)")
    
    # === STEP 3: Create Policy Brief ===
    print(f"🧠 [3/4] Creating Policy Brief from {len(articles_text)} articles + {len(senator_drafts)} senator drafts...")
    policy_brief = create_policy_brief(fetched_content, drafts_text)
    
    if not policy_brief:
        print("❌ Policy Brief creation failed!")
        sys.exit(1)
    
    print(f"\n--- POLICY BRIEF ---")
    print(policy_brief)
    print("--- END POLICY BRIEF ---\n")
    
    # === STEP 4: Send to Curator ===
    print(f"📲 [4/4] Sending Policy Brief to Curator...")
    notify_curator("Policy Brief", "N/A", policy_brief)

if __name__ == "__main__":
    main()
