"""
api/health.py — Pipeline health monitoring endpoint.

GET /health → Full pipeline status: SKP stats, Celery queue, Redis, recent tasks
GET /health/skp  → SKP database detailed stats
GET /health/queue → Celery queue status
"""

import logging
import sqlite3
import os
from datetime import datetime, timedelta

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()

DB_PATH = os.getenv("SKP_DB_PATH", "/data/shared_knowledge_pool.db")


def _get_skp_stats() -> dict:
    try:
        conn = sqlite3.connect(DB_PATH, timeout=2.0)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM knowledge")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM knowledge WHERE key LIKE 'kurator:%'")
        kurator_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM knowledge WHERE key LIKE 'curated:%'")
        curated_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM knowledge WHERE source_agent_name LIKE 'senator%'")
        senator_count = cur.fetchone()[0]

        cur.execute("SELECT source_agent_name, COUNT(*) as cnt FROM knowledge GROUP BY source_agent_name ORDER BY cnt DESC LIMIT 10")
        by_source = {r[0]: r[1] for r in cur.fetchall()}

        cur.execute("SELECT category, COUNT(*) as cnt FROM knowledge GROUP BY category ORDER BY cnt DESC")
        by_category = {r[0]: r[1] for r in cur.fetchall()}

        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        cur.execute("SELECT COUNT(*) FROM knowledge WHERE created_at >= ?", (one_hour_ago,))
        last_hour = cur.fetchone()[0]

        cur.execute("SELECT key, created_at FROM knowledge ORDER BY created_at DESC LIMIT 5")
        latest = [{"key": r[0][:60], "created_at": r[1]} for r in cur.fetchall()]

        conn.close()
        return {
            "total_entries": total,
            "kurator_entries": kurator_count,
            "curated_entries": curated_count,
            "senator_entries": senator_count,
            "entries_last_hour": last_hour,
            "by_source": by_source,
            "by_category": by_category,
            "latest_entries": latest,
            "status": "ok",
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _get_queue_stats() -> dict:
    try:
        from redis import Redis
        r = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                           decode_responses=True, socket_connect_timeout=1.0)

        queue_len = r.llen("celery")
        active = r.get("hermes:tasks:active") or "0"
        success = r.get("hermes:tasks:success") or "0"
        failed = r.get("hermes:tasks:failed") or "0"
        kurator_runs = r.get("hermes:kurator:runs") or "0"
        skp_cleanups = r.get("hermes:skp:cleanups") or "0"

        # Per-agent stats
        agent_stats = {}
        for key in r.scan_iter("hermes:agent:tasks:*"):
            agent = key.split(":")[-1]
            val = r.get(key) or "0"
            agent_stats[agent] = int(val)

        r.close()
        return {
            "queue_length": queue_len,
            "active_tasks": int(active),
            "total_success": int(success),
            "total_failed": int(failed),
            "kurator_runs": int(kurator_runs),
            "skp_cleanups": int(skp_cleanups),
            "agent_tasks": agent_stats,
            "status": "ok",
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/health")
async def health_check():
    """Full pipeline health status."""
    skp = _get_skp_stats()
    queue = _get_queue_stats()

    overall = "healthy"
    if skp.get("status") == "error" or queue.get("status") == "error":
        overall = "degraded"

    return JSONResponse({
        "status": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "skp": skp,
        "queue": queue,
        "version": "v0.1.0",
        "engine": "hermes-cognitive",
    })


@router.get("/health/skp")
async def skp_health():
    """SKP database detailed stats."""
    return JSONResponse(_get_skp_stats())


@router.get("/health/queue")
async def queue_health():
    """Celery queue status."""
    return JSONResponse(_get_queue_stats())


@router.get("/health/cache")
async def cache_health():
    """LLM cache statistics."""
    from models.cache import get_cache_stats
    return JSONResponse(get_cache_stats())


@router.get("/health/search")
async def search_health():
    """SKP search test."""
    from core.skp_search import search_count
    return JSONResponse({
        "fts_available": True,
        "total_indexed": search_count("*"),
    })


@router.get("/search")
async def search_skp(q: str, limit: int = 10, category: str = None, agent: str = None):
    """Full-text search di SKP."""
    from core.skp_search import search, search_count
    results = search(q, limit=limit, category=category, agent=agent)
    return JSONResponse({
        "query": q,
        "results_count": len(results),
        "total_matches": search_count(q),
        "results": results,
    })
