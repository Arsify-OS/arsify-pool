#!/usr/bin/env python3
"""
HERMES EDITORIAL AI - Analysis & Drafting Engine
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
MODEL = "meta-llama/llama-3.1-8b-instruct"  # Valid model di OpenRouter (tested)

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

def analyze_news(news_items):
    """Cluster topics & score virality."""
    # Ambil 5 berita teratas buat dianalisis (biar hemat token)
    sample = news_items[:5]
    
    # Handle source yang bisa berupa string atau dict
    articles_sample = []
    for x in sample:
        src = x.get("source", "Unknown")
        if isinstance(src, dict):
            src = src.get("title", "Unknown")
        articles_sample.append({"title": x.get("title", ""), "source": src})
    
    prompt = f"""Analyze these 5 news articles about AI. Provide:
1. **Topic Cluster** (e.g., "AI Regulation", "AI Creative Tools")
2. **Viral Score** (1-100) with reason
3. **3-sentence engaging summary** for tech audience

Articles:
{json.dumps(articles_sample, indent=2)}

Format:
TOPIC: [Cluster Name]
SCORE: [1-100]
SUMMARY: [3 sentences]
"""
    return call_llm(prompt, max_tokens=300)

def draft_article(summary):
    """Humanize & rewrite for engagement."""
    prompt = f"""Rewrite this news summary to be:
- Engaging & slightly provocative (hook reader)
- Professional but conversational
- Include "Why This Matters" (1 sentence)
- Max 150 words

Original: {summary}

Draft:"""
    return call_llm(prompt, max_tokens=200)

def notify_curator(topic, score, draft):
    """Send draft to Telegram for approval."""
    msg = f"""📰 *HERMES EDITORIAL DRAFT*

🌐 *Topic:* {topic}
🔥 *Viral Score:* {score}/100
📅 *Date:* {datetime.now().strftime('%Y-%m-%d %H:%M')}

📝 *Draft:*
{draft}

---
Reply 'APPROVE' to publish or 'EDIT [feedback]'."""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print("✅ Draft sent to Curator via Telegram!")
        return True
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: editorial_ai.py <json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        sys.exit(1)
    
    print(f"📰 [1/3] Loading news from {json_file}...")
    with open(json_file) as f:
        news = json.load(f)
    
    print(f"🧠 [2/3] Analyzing {len(news)} articles with LLM...")
    analysis = analyze_news(news)
    
    if not analysis:
        print("❌ Analysis failed!")
        sys.exit(1)
    
    print("\n--- ANALYSIS RESULT ---")
    print(analysis)
    print("--- END ANALYSIS ---\n")
    
    # Parse analysis (simple)
    lines = analysis.split('\n')
    topic = next((l.replace('TOPIC:', '').strip() for l in lines if l.startswith('TOPIC:')), 'Unknown')
    score = next((l.replace('SCORE:', '').strip() for l in lines if l.startswith('SCORE:')), '50')
    summary = next((l.replace('SUMMARY:', '').strip() for l in lines if l.startswith('SUMMARY:')), analysis)
    
    print(f"✍️ [3/3] Drafting engaging content...")
    draft = draft_article(summary)
    
    if not draft:
        print("❌ Drafting failed!")
        sys.exit(1)
    
    print(f"\n--- DRAFT ---")
    print(draft)
    print("--- END DRAFT ---\n")
    
    print(f"📲 Sending to Curator...")
    notify_curator(topic, score, draft)

if __name__ == "__main__":
    main()
