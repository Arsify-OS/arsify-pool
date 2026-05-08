"""
tasks.py — Celery task dengan webhook callback dan agent_id tracking.
"""

import asyncio
import logging
import os

import httpx

logger = logging.getLogger(__name__)

from celery_app import celery
def _incr_redis(key: str):
    try:
        from redis import Redis
        r = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                           decode_responses=True, socket_connect_timeout=0.5)
        r.incr(key)
    except Exception:
        pass


def _send_webhook(callback_url: str, payload: dict):
    """POST hasil ke webhook URL jika disediakan."""
    if not callback_url:
        return
    try:
        httpx.post(callback_url, json=payload, timeout=5.0)
        logger.info("task: webhook sent to %s", callback_url)
    except Exception as exc:
        logger.warning("task: webhook failed %s: %s", callback_url, exc)


@celery.task(bind=True, name="hermes.run")
def run_hermes_task(
    self,
    user_input:   str,
    api_key:      str = "",
    agent_id:     str = "default",
    callback_url: str | None = None,
) -> dict:
    """
    Run Hermes cognitive pipeline async.
    Mengirim webhook ke callback_url jika disediakan — agent tidak perlu polling.
    """
    from core.router import hermes_loop

    request_id = self.request.id or "unknown"
    logger.info("task[%s]: start agent=%s", request_id, agent_id)

    try:
        result = asyncio.run(hermes_loop(
            user_input,
            request_id=request_id,
            agent_id=agent_id,
        ))
        _incr_redis("hermes:tasks:success")
        _incr_redis(f"hermes:agent:tasks:{agent_id}")
        logger.info("task[%s]: done %dms route=%s", request_id,
                    result.get("duration_ms", 0), result.get("route"))

        # Webhook callback — agent tidak perlu polling
        _send_webhook(callback_url, {
            "task_id": request_id,
            "status":  "SUCCESS",
            "result":  result,
        })

        return result

    except Exception as exc:
        _incr_redis("hermes:tasks:failed")
        logger.error("task[%s]: failed: %s", request_id, exc, exc_info=True)

        _send_webhook(callback_url, {
            "task_id": request_id,
            "status":  "FAILURE",
            "error":   str(exc),
        })
        raise


@celery.task(name="hermes.kurator")
def run_kurator_task() -> dict:
    """
    Kurator pipeline — baca SKP entries, generate analisis, write kembali ke SKP.
    Dipanggil oleh Celery beat setiap 5 menit.
    """
    from core.kurator import run_curation
    request_id = run_kurator_task.request.id or "unknown"
    logger.info("task[%s]: kurator run start", request_id)
    try:
        result = asyncio.run(run_curation())
        _incr_redis("hermes:kurator:runs")
        logger.info("task[%s]: kurator done: %s", request_id, result)
        return result
    except Exception as exc:
        _incr_redis("hermes:kurator:failed")
        logger.error("task[%s]: kurator failed: %s", request_id, exc, exc_info=True)
        raise


@celery.task(name="hermes.skp_cleanup")
def run_skp_cleanup_task() -> dict:
    """
    SKP cleanup — hapus entries lama, duplikat, dan cap total.
    Dipanggil oleh Celery beat setiap 6 jam.
    """
    from core.kurator import cleanup_skp
    request_id = run_skp_cleanup_task.request.id or "unknown"
    logger.info("task[%s]: skp cleanup start", request_id)
    try:
        result = cleanup_skp()
        _incr_redis("hermes:skp:cleanups")
        logger.info("task[%s]: skp cleanup done: %s", request_id, result)
        return result
    except Exception as exc:
        _incr_redis("hermes:skp:cleanup_failed")
        logger.error("task[%s]: skp cleanup failed: %s", request_id, exc, exc_info=True)
        raise
