"""
models/openrouter_client.py
────────────────────────────────────────────────────────────────────────────────
OpenRouter HTTP client for Hermes Cognitive Engine.

BUG FIXES vs original:
  - [CRITICAL] Response parsing: now extracts choices[0].message.content
    before returning, instead of returning the raw OpenRouter envelope.
  - Timeout now split per phase: connect / read / write (not a single flat 60s)
  - HTTP 429 handled as a separate case (backoff, not ignored)
  - call_with_fallback always returns dict, never raises to caller
  - _meta tracking: model_used, attempt, fallback_used
"""

import asyncio
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Model registry ─────────────────────────────────────────────────────────────

MODEL_MAP: dict[str, str] = {
    "nemotron": "nvidia/nemotron-3-super-120b-a12b",
    "minimax":  "minimax/minimax-m2.5",
    "hy3":      "tencent/hy3-preview",
    "owl":      "openrouter/owl-alpha",
    "fallback": "openai/gpt-4o-mini",   # cheap, reliable fallback
}

# Free model mapping — used when OpenRouter credits are exhausted
# These models have :free suffix and work without credits
FREE_MODEL_MAP: dict[str, str] = {
    "nemotron": "liquid/lfm-2.5-1.2b-instruct:free",   # small, fast, reliable free
    "minimax":  "liquid/lfm-2.5-1.2b-instruct:free",   # same - avoid rate limit on big models
    "hy3":      "baidu/cobuddy:free",                    # free, decent
    "owl":      "liquid/lfm-2.5-1.2b-instruct:free",   # small free model
    "fallback": "liquid/lfm-2.5-1.2b-instruct:free",   # same for reliability
}

# Set to True to force free models (no credits needed)
USE_FREE_MODELS = os.getenv("USE_FREE_MODELS", "true").lower() in ("true", "1", "yes")

# ── Timeout config ─────────────────────────────────────────────────────────────
# Separate timeouts per phase prevents a slow read from blocking indefinitely.

TIMEOUT = httpx.Timeout(
    connect=float(os.getenv("LLM_TIMEOUT_CONNECT", "8.0")),
    read=float(os.getenv("LLM_TIMEOUT_READ", "90.0")),
    write=float(os.getenv("LLM_TIMEOUT_WRITE", "8.0")),
    pool=float(os.getenv("LLM_TIMEOUT_POOL", "5.0")),
)

MAX_RETRY   = int(os.getenv("LLM_MAX_RETRY", "1"))
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")


# ── Internal: single call ──────────────────────────────────────────────────────

async def _call_model_raw(model_id: str, prompt: str) -> dict[str, Any]:
    """
    POST to LLM endpoint (OpenRouter atau Ollama).
    Returns full response envelope.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    is_ollama = "localhost" in OPENROUTER_URL or "127.0.0.1" in OPENROUTER_URL or "host.docker.internal" in OPENROUTER_URL
    
    headers = {}
    if not is_ollama and api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["HTTP-Referer"] = os.getenv("APP_URL", "https://arsify.dev")
        headers["X-Title"] = "Arsify Hermes Cognitive Engine"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        res = await client.post(
            OPENROUTER_URL,
            headers=headers,
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": TEMPERATURE,
            },
        )
        res.raise_for_status()
        return res.json()


# ── Internal: extract content ──────────────────────────────────────────────────

def _extract_content(envelope: dict[str, Any]) -> str:
    """
    Extract text content from OpenRouter response envelope.

    BUG FIX: previous code returned the full envelope dict, which caused
    safe_json_parse() to succeed (it IS a dict) but with wrong shape,
    silently breaking all downstream layer prompts.
    """
    try:
        return envelope["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Malformed OpenRouter response: {exc} | envelope={str(envelope)[:200]}")


# ── Public: single call (no fallback) ─────────────────────────────────────────

async def call_model(model: str, prompt: str) -> str:
    """
    Single call to a named model. Returns content string.
    Raises on network error or malformed response.
    Use call_with_fallback() for production paths.
    """
    model_id = MODEL_MAP.get(model, model)
    envelope = await _call_model_raw(model_id, prompt)
    return _extract_content(envelope)


# ── Public: call with fallback chain ──────────────────────────────────────────

async def call_with_fallback(
    primary:     str,
    prompt:      str,
    fallback:    str = "fallback",
    max_retries: int = MAX_RETRY,
) -> dict[str, Any]:
    """
    Attempt primary model. On failure: exponential backoff, then fallback model.
    HTTP 429 (rate limited) gets longer backoff before retry.

    Always returns a dict:
      Success → {"content": str, "_meta": {...}}
      Failure → {"error": str, "_meta": {...}}

    Never raises to caller.
    """
    models_to_try = [primary, fallback] if primary != fallback else [primary]
    last_error    = "unknown"

    # Choose model map based on config
    is_ollama = "localhost" in OPENROUTER_URL or "127.0.0.1" in OPENROUTER_URL or "host.docker.internal" in OPENROUTER_URL
    
    for attempt in range(max_retries):
        for model_name in models_to_try:
            if is_ollama:
                # Ollama: gunakan model name langsung (dari env atau default)
                model_id = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
            else:
                active_model_map = FREE_MODEL_MAP if USE_FREE_MODELS else MODEL_MAP
                model_id = active_model_map.get(model_name, MODEL_MAP.get(model_name, model_name))
            try:
                envelope = await _call_model_raw(model_id, prompt)
                content  = _extract_content(envelope)
                logger.info(
                    "call_with_fallback: success model=%s attempt=%d", model_name, attempt
                )
                return {
                    "content": content,
                    "_meta": {
                        "model_used":    model_name,
                        "model_id":      model_id,
                        "attempt":       attempt,
                        "fallback_used": model_name != primary,
                    },
                }

            except httpx.TimeoutException as exc:
                last_error = f"timeout:{exc}"
                wait = 2 ** attempt
                logger.warning("call_with_fallback: timeout model=%s, wait=%ds", model_name, wait)
                await asyncio.sleep(wait)

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429:
                    # Rate limit — read Retry-After header if available
                    retry_after = exc.response.headers.get("Retry-After")
                    if retry_after:
                        wait = int(retry_after) + 1
                    else:
                        wait = 15 * (attempt + 1)  # free model: 8 req/min → 15s backoff
                    logger.warning(
                        "call_with_fallback: rate limited model=%s, wait=%ds", model_name, wait
                    )
                    await asyncio.sleep(wait)
                    last_error = "rate_limited"
                elif status == 401:
                    # Invalid key / model not available — skip immediately
                    last_error = "http_401"
                    logger.error(
                        "call_with_fallback: HTTP 401 model=%s — key invalid or model unavailable, skipping",
                        model_name,
                    )
                    break
                elif status == 402:
                    # Insufficient credits — skip to fallback
                    last_error = "http_402"
                    logger.error(
                        "call_with_fallback: HTTP 402 model=%s — insufficient credits, skipping",
                        model_name,
                    )
                    break
                else:
                    # Other 4xx — skip model
                    last_error = f"http_{status}"
                    logger.error(
                        "call_with_fallback: HTTP %d model=%s — skipping",
                        status, model_name,
                    )
                    break

            except ValueError as exc:
                # Malformed response
                last_error = f"malformed_response:{exc}"
                logger.error("call_with_fallback: malformed response model=%s: %s", model_name, exc)
                await asyncio.sleep(2 ** attempt)

            except Exception as exc:
                last_error = f"unexpected:{type(exc).__name__}"
                logger.exception("call_with_fallback: unexpected error model=%s", model_name)
                await asyncio.sleep(2 ** attempt)

    logger.error("call_with_fallback: all attempts failed. last_error=%s", last_error)
    return {
        "error":   last_error,
        "content": None,
        "_meta":   {"model_used": None, "fallback_used": True, "attempt": max_retries},
    }
