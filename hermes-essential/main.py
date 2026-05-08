"""
main.py — Hermes Cognitive Engine v0.1.0
────────────────────────────────────────────────────────────────────────────────
Arsify OS Dual Mode:
  Fast Path    → POST /chat          (Ollama lokal, < 5s, complexity < threshold)
  Cognitive    → POST /v1/portsocket (OpenRouter L1-L4, planning + reflection)

Hermes Agent tidak memilih mode — sistem yang memutuskan berdasarkan
X-Agent-ID profile dan complexity score dari L1 Perception.
"""

import logging
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.portsocket import router as portsocket_router
from api.health import router as health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Hermes Cognitive Engine",
    description = (
        "Upshalter MoE Gateway — Dual Mode\n\n"
        "**Fast Path** `/chat` → Ollama lokal (inferensi cepat)\n\n"
        "**Cognitive Path** `/v1/portsocket` → L1→L2→L3→L4 + SKP knowledge loop"
    ),
    version     = "0.1.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portsocket_router)
app.include_router(health_router)

# ── Request tracing middleware ────────────────────────────────────────────────
@app.middleware("http")
async def trace_requests(request: Request, call_next):
    rid      = str(uuid.uuid4())
    request.state.request_id = rid
    start    = time.monotonic()
    response = await call_next(request)
    ms       = (time.monotonic() - start) * 1000
    response.headers["X-Request-ID"]    = rid
    response.headers["X-Response-Time"] = f"{ms:.1f}ms"
    logger.info("trace: %s %s %d %.1fms", request.method, request.url.path,
                response.status_code, ms)
    _update_p99(ms)
    return response

def _update_p99(ms: float):
    try:
        from redis import Redis
        r = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                           decode_responses=True, socket_connect_timeout=0.1)
        cur = r.get("hermes:latency:p99_ms")
        new = ms if cur is None else float(cur) * 0.95 + ms * 0.05
        r.set("hermes:latency:p99_ms", round(new, 2))
    except Exception:
        pass


# ── Fast Path: /chat (Arsify OS mode — Ollama lokal) ─────────────────────────
@app.post("/chat")
async def fast_chat(request: Request):
    """
    Fast Path — langsung ke Ollama lokal via Arsify MoE Router.
    Untuk task dengan complexity rendah yang tidak butuh planning.

    Forward ke Arsify OS /chat endpoint yang sudah ada.
    """
    body = await request.json()
    agent_id = request.headers.get("X-Agent-ID", "default")

    try:
        import httpx
        arsify_url = os.getenv("ARSIFY_URL", "http://arsify:8000")
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{arsify_url}/chat",
                json=body,
                headers={"X-Agent-ID": agent_id},
            )
            result = r.json()
            result["route"]    = "fast"
            result["agent_id"] = agent_id
            return result
    except Exception as exc:
        logger.error("fast_chat: Arsify unreachable: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "error":   "Arsify OS fast path unavailable",
                "detail":  str(exc),
                "fallback": "Use POST /v1/portsocket for cognitive path",
            }
        )


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    from core.knowledge_injector import get_skp_stats
    skp = get_skp_stats()
    return {
        "service":     "Hermes Cognitive Engine",
        "version":     "0.1.0",
        "dual_mode": {
            "fast_path":      "POST /chat → Ollama lokal",
            "cognitive_path": "POST /v1/portsocket → L1-L4 + OpenRouter",
        },
        "skp": {
            "total_knowledge": skp.get("total", 0),
            "schema":          skp.get("schema", "unknown"),
        },
        "docs":  "/docs",
        "audit": "/audit/efeknomis",
    }
