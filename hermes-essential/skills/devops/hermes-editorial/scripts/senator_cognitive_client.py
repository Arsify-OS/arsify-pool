#!/usr/bin/env python3
"""
senator_cognitive_client.py
────────────────────────────────────────────────────────────────────────────────
Senator Integration Client — connects Senator Factory Pipeline to
Hermes Cognitive Engine via /v1/portsocket.

Uses only Python stdlib (urllib) — no external dependencies.

Modified: Added random startup delay to avoid rate limit cascade.

Usage:
    python3 senator_cognitive_client.py --sector akademisi --input "..."
    python3 senator_cognitive_client.py --sector akademisi --scrape
"""

import argparse
import json
import os
import random
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────────

COGNITIVE_ENGINE_URL = os.getenv("COGNITIVE_ENGINE_URL", "http://host.docker.internal:8100")
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "hermes-secret-change-me-in-production")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")  # Fallback only

# Agent ID maps to profile in agent_registry.py (complexity_threshold=1 → always cognitive)
SECTOR_TO_AGENT = {
    "akademisi": "senator-akademisi",
    "bisnis": "senator-bisnis",
    "komunitas": "senator-komunitas",
    "pemerintah": "senator-pemerintah",
    "media": "senator-media",
}

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5807834405")

# Paths (mounted from host)
LINKS_DIR = os.getenv("LINKS_DIR", "/opt/data/editorial-links")
DRAFTS_DIR = os.getenv("DRAFTS_DIR", "/opt/data/editorial-drafts")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ── HTTP helpers (stdlib only) ─────────────────────────────────────────────────

def http_request(method, url, data=None, headers=None, timeout=30):
    """Make HTTP request using stdlib urllib. Returns (status, body)."""
    req = urllib.request.Request(url, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if data:
        req.data = data.encode("utf-8") if isinstance(data, str) else data
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


def http_post(url, payload, headers=None, timeout=30):
    """POST JSON. Returns (status, dict)."""
    data = json.dumps(payload)
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    status, body = http_request("POST", url, data=data, headers=h, timeout=timeout)
    try:
        return status, json.loads(body)
    except Exception:
        return status, {"raw": body}


def http_get(url, headers=None, timeout=10):
    """GET JSON. Returns (status, dict)."""
    h = headers or {}
    status, body = http_request("GET", url, headers=h, timeout=timeout)
    try:
        return status, json.loads(body)
    except Exception:
        return status, {"raw": body}


# ── Cognitive Engine Client ────────────────────────────────────────────────────

def submit_to_cognitive(agent_id, user_input, callback_url=None):
    """Submit task to Hermes Cognitive Engine. Returns dict with task_id."""
    url = f"{COGNITIVE_ENGINE_URL}/v1/portsocket"
    headers = {
        "X-API-Key": HERMES_API_KEY,
        "X-Agent-ID": agent_id,
    }
    payload = {"input": user_input}
    if callback_url:
        payload["callback_url"] = callback_url

    status, data = http_post(url, payload, headers=headers, timeout=10)

    if status == 200:
        task_id = data.get("task_id", "")
        route = data.get("route", "unknown")
        log(f"Task submitted: {task_id} route={route}")
        return data
    else:
        log(f"❌ Submit failed: HTTP {status} — {data}")
        return {"error": f"http_{status}", "detail": data}


def poll_result(task_id, max_wait=600, interval=10):
    """Poll task result from Cognitive Engine."""
    url = f"{COGNITIVE_ENGINE_URL}/v1/result/{task_id}"
    headers = {"X-API-Key": HERMES_API_KEY}
    start = time.time()

    while time.time() - start < max_wait:
        status, data = http_get(url, headers=headers, timeout=10)
        task_status = data.get("status", "")

        if task_status == "SUCCESS":
            elapsed = int(time.time() - start)
            log(f"✅ Task completed in {elapsed}s")
            return data
        elif task_status == "FAILURE":
            log(f"❌ Task failed: {data.get('error', 'unknown')}")
            return data
        else:
            elapsed = int(time.time() - start)
            log(f"  ⏳ {task_status} ({elapsed}s elapsed)")

        time.sleep(interval)

    log(f"❌ Timeout after {max_wait}s")
    return {"error": "timeout"}


def call_cognitive_engine(agent_id: str, user_input: str, max_wait: int = 600):
    """High-level: submit + poll. Returns cognitive result or error."""
    for attempt in range(3):
        submit_data = submit_to_cognitive(agent_id, user_input)
        if "error" in submit_data:
            if attempt < 2:
                log(f"  ⚠️ Submit failed, retrying in 10s...")
                time.sleep(10)
                continue
            return submit_data

        task_id = submit_data.get("task_id")
        if not task_id:
            if attempt < 2:
                log(f"  ⚠️ No task_id, retrying in 10s...")
                time.sleep(10)
                continue
            return {"error": "no_task_id"}

        # Wait for worker to pick up the task
        time.sleep(5)

        result = poll_result(task_id, max_wait=max_wait)

        # If task was not registered (worker issue), retry
        if "error" in result and "NotRegistered" in str(result.get("error", "")):
            if attempt < 2:
                log(f"  ⚠️ Task not registered by worker, retrying in 15s...")
                time.sleep(15)
                continue

        return result

    return {"error": "max_retries_exceeded"}


# ── Fallback: Direct OpenRouter (when Cognitive Engine unavailable) ────────────

def call_openrouter_fallback(prompt, max_tokens=500):
    """Fallback to direct OpenRouter call if Cognitive Engine is unavailable."""
    if not OPENROUTER_KEY:
        log("❌ No OpenRouter key for fallback")
        return None

    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }

    status, data = http_post(
        "https://openrouter.ai/api/v1/chat/completions",
        payload,
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
        timeout=60,
    )

    if status == 200:
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return None
    elif status == 429:
        log("⚠️ Rate limited, waiting 30s...")
        time.sleep(30)
        status, data = http_post(
            "https://openrouter.ai/api/v1/chat/completions",
            payload,
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            timeout=60,
        )
        if status == 200:
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                return None
    else:
        log(f"❌ Fallback HTTP {status}: {data}")
        return None


# ── Senator Research Task Builder ─────────────────────────────────────────

def load_prompt_file(sector):
    """Load prompt JSON from /opt/data/prompts/senator-{sector}.json"""
    prompt_path = f"/opt/data/prompts/senator-{sector}.json"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"⚠️ Could not load prompt file: {e}")
        return None

def build_research_prompt(sector, articles=None):
    """Build a research prompt for the Cognitive Engine.
    Uses JSON prompt file with Few-Shot, Chain-of-Thought, Constrained Output.
    """
    sector_names = {
        "akademisi": "Academic Research & Education",
        "bisnis": "Business & Economy",
        "komunitas": "Community & Open Source",
        "pemerintah": "Government & Policy",
        "media": "Media & Technology",
    }

    articles = articles or []
    articles_text = "\n".join([
        f"- {a.get('title', 'N/A')} ({a.get('source', 'N/A')})"
        for a in articles[:10]
    ]) if articles else "- No specific articles, use general knowledge"

    # Try to load prompt file
    prompt_data = load_prompt_file(sector)
    
    if prompt_data:
        # Use JSON prompt file with Few-Shot + CoT + Constrained Output
        system_prompt = prompt_data.get("system_prompt", "")
        few_shot = prompt_data.get("few_shot_examples", [])
        output_schema = prompt_data.get("output_schema", {})
        constraints = prompt_data.get("constraints", [])
        
        # Build Few-Shot section
        few_shot_text = ""
        for i, example in enumerate(few_shot[:3], 1):  # Max 3 examples
            input_text = example.get("input", "")
            cot = example.get("chain_of_thought", "")
            output = example.get("output", {})
            few_shot_text += f"\n--- Example {i} ---\n"
            few_shot_text += f"Input: {input_text}\n"
            few_shot_text += f"Chain-of-Thought: {cot}\n"
            few_shot_text += f"Output: {json.dumps(output, ensure_ascii=False)}\n"
        
        # Build constraints text
        constraints_text = "\n".join([f"- {c}" for c in constraints]) if constraints else ""
        
        # Build output schema text
        schema_props = output_schema.get("properties", {})
        required = output_schema.get("required", [])
        schema_text = "Output JSON must have these fields:\n"
        for prop, details in schema_props.items():
            desc = details.get("description", "")
            schema_text += f"- {prop}: {desc}\n"
        schema_text += f"\nRequired fields: {', '.join(required)}\n"
        
        prompt = f"""{system_prompt}

SECTION 1: FEW-SHOT EXAMPLES
{few_shot_text}

SECTION 2: CURRENT TASK
Analyze the latest developments in {sector_names.get(sector, sector)} based on these recent headlines:

{articles_text}

SECTION 3: OUTPUT REQUIREMENTS
{constraints_text}

{schema_text}

IMPORTANT: Output ONLY valid JSON. No markdown ```json```. No extra text.
"""
    else:
        # Fallback: generic prompt (original behavior)
        prompt = f"""Research Task: {sector_names.get(sector, sector)}

Analyze the latest developments in {sector_names.get(sector, sector)} based on these recent headlines:

{articles_text}

Provide:
1. **Key Trends**: 3-5 major trends identified (in Indonesian)
2. **Impact Analysis**: How these trends affect Indonesia's AI/tech ecosystem
3. **Recommendations**: 2-3 actionable recommendations for Upshalter
4. **Risk Assessment**: Any risks or threats to monitor

Format your response in Indonesian, structured with clear headings.
"""
    
    return prompt

# ── Telegram Notification ──────────────────────────────────────────────────────

def send_telegram(message):
    """Send message to Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log("⚠️ Telegram not configured")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message[:4000],
        "parse_mode": "Markdown",
    }

    status, data = http_post(url, payload, timeout=10)
    if status == 200:
        log("📨 Telegram sent")
    else:
        log(f"❌ Telegram error: HTTP {status}")


# ── Main Pipeline ──────────────────────────────────────────────────────────────

def run_senator_pipeline(sector, use_cognitive=True):
    """Full senator pipeline: scrape → cognitive → save → telegram."""
    sector_name = sector.title()
    log(f"🏛️ Senator {sector_name} starting pipeline...")

    # Step 1: Scrape (reuse existing scraper if available)
    try:
        sys.path.insert(0, "/opt/editorial-scripts")
        from senator_factory_pipeline import scrape_google_news
        articles = scrape_google_news(sector, max_items=10)
    except ImportError:
        log("⚠️ senator_factory_pipeline not found, using empty articles")
        articles = []

    if not articles:
        log("⚠️ No articles scraped, using generic prompt")
        articles = [{"title": f"Latest {sector} developments", "source": "general"}]

    # Step 2: Build prompt
    prompt = build_research_prompt(sector, articles)
    log(f"📝 Prompt built ({len(prompt)} chars)")

    # Step 3: Process via Cognitive Engine or fallback
    agent_id = SECTOR_TO_AGENT.get(sector, "default")
    result = None

    if use_cognitive:
        log(f"🧠 Submitting to Cognitive Engine as {agent_id}...")
        result = call_cognitive_engine(agent_id, prompt, max_wait=600)
        if "error" in result:
            log(f"⚠️ Cognitive Engine error: {result['error']}, trying fallback...")
            result = None

    if not result:
        log("🔄 Using OpenRouter fallback...")
        content = call_openrouter_fallback(prompt)
        result = {"content": content, "route": "fallback"}

    # Step 4: Save results
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    draft_file = f"{DRAFTS_DIR}/{sector}-{timestamp}.json"

    output = {
        "sector": sector,
        "timestamp": timestamp,
        "articles_count": len(articles),
        "result": result,
    }

    with open(draft_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    log(f"💾 Draft saved: {draft_file}")

    # Step 5: Telegram summary
    content = ""
    if "content" in result and result["content"]:
        content = str(result["content"])[:3000]
    elif "result" in result and isinstance(result["result"], dict):
        results_list = result["result"].get("results", [])
        if results_list:
            step = results_list[0]
            exec_data = step.get("execution", {})
            content = str(exec_data.get("result", ""))[:3000]

    if content:
        emoji_map = {
            "akademisi": "🎓", "bisnis": "💼", "komunitas": "🤝",
            "pemerintah": "🏛️", "media": "📰"
        }
        emoji = emoji_map.get(sector, "🏛️")
        telegram_msg = f"{emoji} *Senator {sector_name} Report*\n\n{content}"
        send_telegram(telegram_msg)

    log(f"✅ Senator {sector_name} pipeline complete")
    return result


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Random startup delay to avoid rate limit cascade
    stagger = random.randint(0, 60)
    print(f"[startup] Random delay: {stagger}s to avoid rate limit...", flush=True)
    time.sleep(stagger)
    
    parser = argparse.ArgumentParser(description="Senator → Cognitive Engine Client")
    parser.add_argument("--sector", required=True, choices=list(SECTOR_TO_AGENT.keys()))
    parser.add_argument("--input", help="Custom input (skip scraping)")
    parser.add_argument("--scrape", action="store_true", help="Scrape and process")
    parser.add_argument("--no-cognitive", action="store_true", help="Use OpenRouter fallback only")
    parser.add_argument("--max-wait", type=int, default=600, help="Max poll wait (seconds)")
    args = parser.parse_args()

    if args.input:
        agent_id = SECTOR_TO_AGENT.get(args.sector, "default")
        result = call_cognitive_engine(agent_id, args.input, max_wait=args.max_wait)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        run_senator_pipeline(args.sector, use_cognitive=not args.no_cognitive)
