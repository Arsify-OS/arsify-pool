"""celery_app.py — Celery + Redis broker configuration."""

import os
from celery import Celery

celery = Celery(
    "hermes",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["tasks"],  # auto-register tasks from tasks.py
)

# Explicit import to ensure tasks are registered
import tasks  # noqa: F401

# Redis connection pool settings for stability
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    result_expires=3600,          # keep results 1 hour
    worker_prefetch_multiplier=1, # fair scheduling for long tasks
    broker_transport_options={
        "visibility_timeout": 3600,
        "socket_timeout": 30,
        "socket_connect_timeout": 10,
    },
    result_backend_transport_options={
        "socket_timeout": 30,
        "socket_connect_timeout": 10,
    },
    # ── Beat Schedule ────────────────────────────────────────────────────────
    beat_schedule={
        "kurator-every-5-min": {
            "task": "hermes.kurator",
            "schedule": 300.0,  # 5 menit
            "args": (),
        },
        "skp-cleanup-every-6h": {
            "task": "hermes.skp_cleanup",
            "schedule": 21600.0,  # 6 jam
            "args": (),
        },
    },
)
