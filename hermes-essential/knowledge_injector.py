"""
core/knowledge_injector.py
────────────────────────────────────────────────────────────────────────────────
SKP Bridge — Upshalter Native Knowledge Foundation.

Ini adalah jantung dari klaim "We Own Knowledge":
  - READ:  L2 Cognition mengambil top-K entries relevan sebelum membuat plan
  - WRITE: L4 Reflection mengembalikan hasil bagus ke SKP sebagai knowledge baru

Dengan loop ini, setiap task yang berhasil dieksekusi memperkaya knowledge pool.
Sistem semakin pintar seiring penggunaan — tanpa training ulang model.

Kompatibel dengan dua SQLite schema:
  1. Arsify OS native (memory.db / arsify.db) — tabel: memory_notes, messages
  2. SKP standalone (knowledge.db) — tabel: knowledge
"""

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ── Config dari .env ─────────────────────────────────────────────────────────
DB_PATH          = os.getenv("SKP_DB_PATH", "/data/arsify.db")
SKP_TOP_K        = int(os.getenv("SKP_TOP_K",         "3"))
SKP_MIN_PRIORITY = int(os.getenv("SKP_MIN_PRIORITY",  "5"))
SKP_MAX_AGE_DAYS = int(os.getenv("SKP_MAX_AGE_DAYS",  "30"))
WRITE_BACK_MIN_Q = int(os.getenv("SKP_WRITE_MIN_QUALITY", "60"))  # L4 score threshold
CACHE_TTL        = int(os.getenv("SKP_CACHE_TTL", "300"))

# ── Redis cache (optional) ───────────────────────────────────────────────────
_redis = None

def _get_redis():
    global _redis
    if _redis is None:
        try:
            from redis import Redis
            r = Redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                decode_responses=True,
                socket_connect_timeout=1,
            )
            r.ping()
            _redis = r
        except Exception as exc:
            logger.warning("knowledge_injector: Redis unavailable (%s) — cache disabled", exc)
            _redis = False
    return _redis if _redis else None


def _cache_key(l1_output: dict) -> str:
    payload = json.dumps({
        "category": l1_output.get("category", "general"),
        "tags":     sorted(l1_output.get("tags", [])),
        "k":        SKP_TOP_K,
    }, sort_keys=True)
    return "skp:" + hashlib.md5(payload.encode()).hexdigest()


# ── Schema detection ─────────────────────────────────────────────────────────

def _detect_schema(conn: sqlite3.Connection) -> str:
    """
    Deteksi schema SQLite yang ada:
    - "arsify"     → tabel memory_notes (Arsify OS native)
    - "skp"        → tabel knowledge (SKP standalone)
    - "unknown"    → tidak ada tabel yang dikenal
    """
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}

    if "knowledge" in tables:
        return "skp"
    if "memory_notes" in tables:
        return "arsify"
    return "unknown"


# ── READ: ambil context untuk L2 ────────────────────────────────────────────

def _query_skp_schema(cur: sqlite3.Cursor, category: str, limit: int) -> list[dict]:
    """Query tabel knowledge (SKP standalone schema)."""
    cutoff = (datetime.utcnow() - timedelta(days=SKP_MAX_AGE_DAYS)).isoformat()

    # Phase 1: category-exact match
    cur.execute("""
        SELECT key, value, category, priority, created_at
        FROM   knowledge
        WHERE  category = ?
          AND  priority >= ?
          AND  created_at >= ?
        ORDER BY priority DESC, created_at DESC
        LIMIT  ?
    """, (category, SKP_MIN_PRIORITY, cutoff, limit))
    rows = [dict(r) for r in cur.fetchall()]

    # Phase 2: broad fallback jika kurang
    if len(rows) < limit:
        need = limit - len(rows)
        existing_keys = {r["key"] for r in rows}
        cur.execute("""
            SELECT key, value, category, priority, created_at
            FROM   knowledge
            WHERE  priority >= ?
              AND  created_at >= ?
              AND  category != ?
            ORDER BY priority DESC, created_at DESC
            LIMIT  ?
        """, (SKP_MIN_PRIORITY, cutoff, category, need))
        rows += [dict(r) for r in cur.fetchall() if dict(r)["key"] not in existing_keys]

    return rows


def _query_arsify_schema(cur: sqlite3.Cursor, category: str, limit: int) -> list[dict]:
    """Query tabel memory_notes (Arsify OS native schema)."""
    # memory_notes punya: key, value, scope, created_at
    # Kita mapping: scope='global' → priority tertinggi
    cur.execute("""
        SELECT key, value, scope, created_at
        FROM   memory_notes
        ORDER BY
            CASE scope WHEN 'global' THEN 1 WHEN 'hermes' THEN 2 ELSE 3 END,
            created_at DESC
        LIMIT  ?
    """, (limit,))
    rows = cur.fetchall()
    return [
        {
            "key":      r["key"],
            "value":    r["value"],
            "category": r["scope"],
            "priority": 7,
        }
        for r in rows
    ]


def _format_context(rows: list[dict]) -> str:
    """Format rows sebagai string untuk injection ke L2 system prompt."""
    if not rows:
        return ""
    lines = []
    for r in rows:
        lines.append(f"- [{r.get('category','?')}] {r['key']}: {r['value']}")
    return "\n".join(lines)


def fetch_relevant_context(l1_output: dict) -> str:
    """
    READ path: ambil konteks dari SKP untuk L2 Cognition.
    Return string kosong jika DB tidak ada — pipeline tetap jalan.
    """
    # Try cache
    redis = _get_redis()
    if redis:
        cached = redis.get(_cache_key(l1_output))
        if cached is not None:
            return cached

    if not os.path.exists(DB_PATH):
        logger.debug("knowledge_injector: DB not found at %s", DB_PATH)
        return ""

    try:
        conn   = sqlite3.connect(DB_PATH, timeout=2.0)
        conn.row_factory = sqlite3.Row
        schema = _detect_schema(conn)
        cur    = conn.cursor()

        category = l1_output.get("category", "general")

        if schema == "skp":
            rows = _query_skp_schema(cur, category, SKP_TOP_K)
        elif schema == "arsify":
            rows = _query_arsify_schema(cur, category, SKP_TOP_K)
        else:
            logger.warning("knowledge_injector: unknown schema in %s", DB_PATH)
            conn.close()
            return ""

        conn.close()
        result = _format_context(rows)

        # Cache result
        if redis and result:
            redis.setex(_cache_key(l1_output), CACHE_TTL, result)

        logger.info(
            "knowledge_injector: injected %d entries for category=%s",
            len(rows), category
        )
        return result

    except Exception as exc:
        logger.error("knowledge_injector: query failed: %s", exc)
        return ""


# ── WRITE: simpan hasil bagus ke SKP ────────────────────────────────────────

def write_knowledge_entry(
    key:        str,
    value:      str,
    category:   str,
    agent_id:   str,
    quality:    int,
    source:     str = "hermes_cognitive",
) -> bool:
    """
    WRITE path: simpan hasil eksekusi L3 yang berkualitas ke SKP.

    Dipanggil setelah L4 mengevaluasi dan quality_score >= WRITE_BACK_MIN_Q.

    Ini adalah implementasi konkret dari "We Own Knowledge":
    setiap task yang berhasil memperkaya knowledge pool Upshalter.

    Returns True jika berhasil disimpan.
    """
    if quality < WRITE_BACK_MIN_Q:
        logger.debug(
            "knowledge_injector: skip write quality=%d < threshold=%d",
            quality, WRITE_BACK_MIN_Q
        )
        return False

    if not os.path.exists(DB_PATH):
        logger.warning("knowledge_injector: DB not found — write skipped")
        return False

    try:
        conn   = sqlite3.connect(DB_PATH, timeout=2.0)
        schema = _detect_schema(conn)
        cur    = conn.cursor()
        now    = datetime.utcnow().isoformat()

        if schema == "skp":
            cur.execute("""
                INSERT OR REPLACE INTO knowledge
                    (key, value, category, priority, source_agent_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                key,
                value[:2000],   # cap agar tidak bloat DB
                category,
                min(quality // 10, 10),  # quality 80 → priority 8
                agent_id,
                now,
            ))

        elif schema == "arsify":
            # Gunakan memory_notes dengan scope='hermes'
            cur.execute("""
                INSERT OR REPLACE INTO memory_notes (key, value, scope, created_at)
                VALUES (?, ?, ?, ?)
            """, (key, value[:2000], "hermes", now))

        conn.commit()
        conn.close()

        # Invalidate cache untuk category ini
        redis = _get_redis()
        if redis:
            pattern = "skp:*"
            for k in redis.scan_iter(pattern):
                redis.delete(k)

        logger.info(
            "knowledge_injector: ✓ wrote entry key='%s' category=%s agent=%s quality=%d",
            key[:40], category, agent_id, quality
        )
        return True

    except Exception as exc:
        logger.error("knowledge_injector: write failed: %s", exc)
        return False


# ── Stats ────────────────────────────────────────────────────────────────────

def get_skp_stats() -> dict:
    """Return SKP statistics untuk Efeknomis dan dashboard."""
    if not os.path.exists(DB_PATH):
        return {"total": 0, "categories": 0, "agents": 0, "schema": "not_found"}

    try:
        conn   = sqlite3.connect(DB_PATH, timeout=2.0)
        schema = _detect_schema(conn)
        cur    = conn.cursor()

        if schema == "skp":
            cur.execute("SELECT COUNT(*) FROM knowledge")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT category) FROM knowledge")
            cats = cur.fetchone()[0]
            try:
                cur.execute("SELECT COUNT(DISTINCT source_agent_name) FROM knowledge")
                agents = cur.fetchone()[0]
            except Exception:
                agents = 0

        elif schema == "arsify":
            cur.execute("SELECT COUNT(*) FROM memory_notes")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT scope) FROM memory_notes")
            cats = cur.fetchone()[0]
            agents = 0

        else:
            total = cats = agents = 0

        conn.close()
        return {
            "total":      total,
            "categories": cats,
            "agents":     agents,
            "schema":     schema,
            "db_path":    DB_PATH,
        }

    except Exception as exc:
        return {"total": 0, "error": str(exc)}


# ── FTS Setup ─────────────────────────────────────────────────────────────────

def _setup_fts_on_startup():
    """Setup FTS5 index on module load (idempotent)."""
    try:
        from core.skp_search import setup_fts
        setup_fts()
    except Exception as exc:
        logger.warning("knowledge_injector: FTS setup skipped: %s", exc)


# Auto-setup on import
_setup_fts_on_startup()
