"""
models/cache.py — LLM response cache dengan Redis + local TTL.

Cache strategy:
- Key: hash(model_name + prompt_hash + temperature)
- TTL: 1 jam untuk L2/L3, 5 menit untuk L4 (reflection berubah)
- Max cache size: 1000 entries (LRU eviction via Redis TTL)
- Graceful fallback: cache miss → normal call → store result
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

# Local in-memory cache untuk ultra-fast lookup
_local_cache: dict[str, dict] = {}
_local_cache_max = 500
_local_cache_ttl = 3600  # 1 jam

# Redis cache availability
_redis_available = False
_redis_client = None


def _get_redis():
    global _redis_available, _redis_client
    if _redis_client is not None:
        return _redis_client if _redis_available else None
    try:
        from redis import Redis
        _redis_client = Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
            socket_connect_timeout=0.5,
        )
        _redis_client.ping()
        _redis_available = True
        logger.info("cache: Redis connected")
    except Exception:
        _redis_available = False
        _redis_client = None
        logger.info("cache: Redis unavailable — using local cache only")
    return _redis_client if _redis_available else None


def _make_cache_key(model: str, prompt: str, temperature: float = 0.2) -> str:
    """Generate cache key dari model + prompt hash."""
    content = f"{model}:{prompt}:{temperature}"
    h = hashlib.md5(content.encode()).hexdigest()[:16]
    return f"hermes:llm_cache:{h}"


def _get_from_local(key: str) -> dict | None:
    entry = _local_cache.get(key)
    if entry is None:
        return None
    if time.monotonic() - entry["ts"] > entry["ttl"]:
        del _local_cache[key]
        return None
    return entry["data"]


def _set_in_local(key: str, data: dict, ttl: int = _local_cache_ttl):
    # Evict oldest if full
    if len(_local_cache) >= _local_cache_max:
        oldest_key = min(_local_cache, key=lambda k: _local_cache[k]["ts"])
        del _local_cache[oldest_key]
    _local_cache[key] = {"data": data, "ts": time.monotonic(), "ttl": ttl}


async def cached_call(
    model: str,
    prompt: str,
    fallback: str = "fallback",
    temperature: float = 0.2,
    use_cache: bool = True,
    cache_ttl: int = 3600,
) -> dict:
    """
    Cached LLM call. Check local cache → Redis → actual call.
    Returns same format as call_with_fallback().
    """
    if not use_cache:
        from models.openrouter_client import call_with_fallback
        return await call_with_fallback(model, prompt, fallback)

    key = _make_cache_key(model, prompt, temperature)

    # 1. Check local cache (fastest)
    cached = _get_from_local(key)
    if cached is not None:
        logger.debug("cache: local hit key=%s", key[:20])
        cached["_meta"]["cache_hit"] = "local"
        return cached

    # 2. Check Redis cache
    r = _get_redis()
    if r is not None:
        try:
            cached_raw = r.get(key)
            if cached_raw:
                cached = json.loads(cached_raw)
                logger.debug("cache: redis hit key=%s", key[:20])
                _set_in_local(key, cached, cache_ttl)
                cached["_meta"]["cache_hit"] = "redis"
                return cached
        except Exception:
            pass

    # 3. Cache miss → actual call
    from models.openrouter_client import call_with_fallback
    result = await call_with_fallback(model, prompt, fallback)

    # 4. Store in cache (only if no error)
    if not result.get("error") and result.get("content"):
        _set_in_local(key, result, cache_ttl)
        if r is not None:
            try:
                r.setex(key, cache_ttl, json.dumps(result, ensure_ascii=False))
            except Exception:
                pass

    result["_meta"]["cache_hit"] = "miss"
    return result


def invalidate_cache():
    """Clear all caches."""
    global _local_cache
    _local_cache = {}
    r = _get_redis()
    if r is not None:
        try:
            keys = r.keys("hermes:llm_cache:*")
            if keys:
                r.delete(*keys)
        except Exception:
            pass
    logger.info("cache: invalidated all entries")


def get_cache_stats() -> dict:
    """Get cache statistics."""
    r = _get_redis()
    redis_count = 0
    if r is not None:
        try:
            redis_count = len(r.keys("hermes:llm_cache:*"))
        except Exception:
            pass
    return {
        "local_entries": len(_local_cache),
        "local_max": _local_cache_max,
        "redis_entries": redis_count,
        "redis_available": _redis_available,
    }
