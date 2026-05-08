"""
core/kurator.py
────────────────────────────────────────────────────────────────────────────────
Kurator Pipeline — Knowledge Curation Engine.

Membaca SKP entries dari Senator pipeline, menghasilkan analisis
terstruktur, dan menulis hasilnya kembali ke SKP sebagai knowledge baru.

Flow:
  1. Fetch SKP entries yang belum dikuratori (kategori: general, backend, dll)
  2. Group by agent_id (senator-akademisi, senator-bisnis, dll)
  3. Generate analisis/ringkasan per group
  4. Write hasil ke SKP dengan kategori "curated"

Trigger: Celery beat periodic task (setiap 5 menit)
"""

import json
import logging
import sqlite3
import asyncio
import time
from datetime import datetime, timedelta
from typing import Any

from models.cache import cached_call as call_with_fallback

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

DB_PATH = "/data/shared_knowledge_pool.db"
CURATED_MARKER_KEY = "kurator:last_run"
MIN_ENTRIES_TO_CURATE = 3  # Minimal entries sebelum kurator jalan
CURATE_BATCH_SIZE = 10     # Max entries per run
SKP_MAX_ENTRIES = 200      # Max total entries — oldest cleaned when exceeded
SKP_CLEANUP_AGE_HOURS = 24 # Entries older than this (non-system) get cleaned

_KURATOR_SYSTEM = """You are Kurator — Knowledge Curation Engine of Hermes AI.
Version: v1.0 | Temperature: 0.3

Task:
- Read the knowledge entries from Senator pipeline
- Synthesize them into a structured analysis
- Identify patterns, trends, and actionable insights
- Write in Indonesian (Bahasa Indonesia)

Rules:
- Return JSON ONLY
- Be analytical and insightful
- Connect dots between different entries
- Provide actionable conclusions

Output schema (strict):
{
  "version": "v1.0",
  "engine": "kurator-v1",
  "title": "<analysis title>",
  "summary": "<2-3 sentence summary>",
  "insights": ["<insight 1>", "<insight 2>", "<insight 3>"],
  "trends": ["<trend 1>", "<trend 2>"],
  "actionable": ["<action 1>", "<action 2>"],
  "sources": ["<source_agent_1>", "<source_agent_2>"],
  "confidence": <float 0-1>
}"""


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_uncurated_entries(limit: int = CURATE_BATCH_SIZE) -> list[dict]:
    """
    Ambil entries yang belum dikuratori.
    Criteria: entries tanpa prefix 'kurator:' di key, dibuat > 5 menit lalu.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cutoff = (datetime.utcnow() - timedelta(minutes=5)).isoformat()

        cur.execute("""
            SELECT key, value, category, source_agent_name, priority, created_at
            FROM   knowledge
            WHERE  key NOT LIKE 'kurator:%'
              AND  created_at >= ?
              AND  created_at <= ?
            ORDER BY created_at DESC
            LIMIT  ?
        """, (cutoff, datetime.utcnow().isoformat(), limit))

        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as exc:
        logger.error("kurator: fetch failed: %s", exc)
        return []


def mark_as_curated(keys: list[str]):
    """Tandai entries sudah dikuratori dengan prefix 'curated:'."""
    if not keys:
        return
    try:
        conn = _get_conn()
        cur = conn.cursor()
        updated = 0
        for key in keys:
            # Skip if already curated
            if key.startswith("curated:") or key.startswith("kurator:"):
                continue
            new_key = f"curated:{key}"
            # Check if target key already exists
            cur.execute("SELECT COUNT(*) FROM knowledge WHERE key = ?", (new_key,))
            if cur.fetchone()[0] > 0:
                # Target exists — just delete the old entry
                cur.execute("DELETE FROM knowledge WHERE key = ?", (key,))
            else:
                cur.execute("UPDATE knowledge SET key = ? WHERE key = ?", (new_key, key))
            updated += 1
        conn.commit()
        conn.close()
        logger.info("kurator: marked %d entries as curated", updated)
    except Exception as exc:
        logger.error("kurator: mark curated failed: %s", exc)


def write_curated_result(title: str, analysis: dict, sources: list[str]):
    """Tulis hasil kuratoran ke SKP."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        key = f"kurator:{hash(title) % 100000:05d}"
        value = json.dumps(analysis, ensure_ascii=False, indent=2)[:3000]

        cur.execute("""
            INSERT OR REPLACE INTO knowledge
                (key, value, category, priority, source_agent_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            key,
            value,
            "curated",
            9,  # High priority for curated content
            "kurator",
            now,
        ))
        conn.commit()
        conn.close()
        logger.info("kurator: ✓ wrote curated analysis '%s' (key=%s)", title[:50], key)
        return True
    except Exception as exc:
        logger.error("kurator: write failed: %s", exc)
        return False


# ── SKP Maintenance ───────────────────────────────────────────────────────────

def cleanup_skp() -> dict:
    """
    Bersihkan SKP dari entries lama dan duplikat.
    - Hapus entries non-system yang older than SKP_CLEANUP_AGE_HOURS
    - Hapus duplicate values (same value, different key)
    - Cap total entries at SKP_MAX_ENTRIES (remove oldest first)
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        removed = {"old": 0, "dupes": 0, "capped": 0}

        # 1. Remove old non-system entries
        cutoff = (datetime.utcnow() - timedelta(hours=SKP_CLEANUP_AGE_HOURS)).isoformat()
        cur.execute("""
            DELETE FROM knowledge
            WHERE created_at < ?
              AND key NOT LIKE 'system:%'
              AND key NOT LIKE 'kurator:%'
              AND source_agent_name NOT IN ('system', 'kurator')
        """, (cutoff,))
        removed["old"] = cur.rowcount

        # 2. Remove duplicate values (keep newest)
        cur.execute("""
            DELETE FROM knowledge
            WHERE rowid NOT IN (
                SELECT MAX(rowid)
                FROM knowledge
                GROUP BY value
            )
        """)
        removed["dupes"] = cur.rowcount

        # 3. Cap total entries — remove oldest non-system
        cur.execute("SELECT COUNT(*) FROM knowledge")
        total = cur.fetchone()[0]
        if total > SKP_MAX_ENTRIES:
            excess = total - SKP_MAX_ENTRIES
            cur.execute("""
                DELETE FROM knowledge
                WHERE rowid IN (
                    SELECT rowid FROM knowledge
                    WHERE key NOT LIKE 'system:%'
                      AND key NOT LIKE 'kurator:%'
                    ORDER BY created ASC
                    LIMIT ?
                )
            """, (excess,))
            removed["capped"] = cur.rowcount

        conn.commit()
        conn.close()
        logger.info("kurator: cleanup done — removed=%s", removed)
        return {"status": "ok", "removed": removed}
    except Exception as exc:
        logger.error("kurator: cleanup failed: %s", exc)
        return {"status": "error", "error": str(exc)}


# ── Main curation logic ───────────────────────────────────────────────────────

async def run_curation() -> dict:
    """
    Main Kurator pipeline.
    Returns result dict dengan status dan jumlah entries yang diproses.
    """
    start = time.monotonic()
    logger.info("kurator: starting curation run")

    # 1. Fetch uncurated entries
    entries = fetch_uncurated_entries()
    if len(entries) < MIN_ENTRIES_TO_CURATE:
        logger.info("kurator: not enough entries (%d < %d) — skipping",
                     len(entries), MIN_ENTRIES_TO_CURATE)
        return {"status": "skipped", "reason": "not_found", "entries_found": len(entries)}

    logger.info("kurator: found %d entries to curate", len(entries))

    # 2. Group by source agent
    by_agent: dict[str, list[dict]] = {}
    for e in entries:
        agent = e.get("source_agent_name", "unknown")
        by_agent.setdefault(agent, []).append(e)

    # 3. Build prompt dengan content yang ditruncasi AGRESIF
    # Maks 200 chars per entry, maks 5 entries per agent → prompt < 2000 chars
    entries_text = ""
    total_included = 0
    for agent, agent_entries in by_agent.items():
        entries_text += f"\n## {agent}\n"
        for e in agent_entries[:5]:  # Max 5 per agent
            val = e.get("value", "")
            if "--- RESULT ---" in val:
                result_start = val.index("--- RESULT ---") + len("--- RESULT ---")
                result_end = val.index("--- META ---") if "--- META ---" in val else len(val)
                val = val[result_start:result_end].strip()[:200]
            else:
                val = val[:200]
            entries_text += f"- [{e.get('category','general')}] {val}\n"
            total_included += 1

    prompt = (
        f"Analisis {total_included} knowledge entries dari Senator pipeline.\n\n"
        f"Entries:\n{entries_text}\n\n"
        f"Tugas:\n"
        f"1. Identifikasi tema common di semua entries\n"
        f"2. Extract key insights per agent\n"
        f"3. Temukan koneksi antar agent\n"
        f"4. Berikan 2-3 rekomendasi actionable\n\n"
        f"Output HANYA JSON valid (tanpa markdown):\n"
        f'{{\n'
        f'  "title": "<50 chars>",\n'
        f'  "summary": "<100 chars>",\n'
        f'  "insights": ["insight1", "insight2", "insight3"],\n'
        f'  "trends": ["trend1", "trend2"],\n'
        f'  "actionable": ["action1", "action2"],\n'
        f'  "confidence": <0.0-1.0>\n'
        f'}}'
    )

    # 4. Call LLM — prioritaskan Ollama lokal (cepat, gratis)
    analysis = None
    try:
        # Coba Ollama lokal dulu via call_with_fallback
        result = await asyncio.wait_for(
            call_with_fallback("nemotron", prompt, fallback="fallback"),
            timeout=60.0  # 60s timeout — Ollama lokal harusnya < 30s
        )
        if not result.get("error") and result.get("content"):
            analysis = _parse_analysis(result["content"], entries, by_agent)
            logger.info("kurator: LLM success model=%s", result.get("_meta", {}).get("model_used"))
        else:
            logger.warning("kurator: LLM call failed (%s) — using fallback", result.get("error"))
    except asyncio.TimeoutError:
        logger.warning("kurator: LLM call timed out — using fallback")

    if analysis is None:
        analysis = _fallback_analysis(entries, by_agent)

    # 5. Write to SKP
    title = analysis.get("title", "Kurator Analysis")
    sources = list(by_agent.keys())
    success = write_curated_result(title, analysis, sources)

    # 6. Mark entries as curated
    mark_as_curated([e["key"] for e in entries])

    duration = time.monotonic() - start
    logger.info("kurator: done in %.1fs — %d entries curated, write=%s",
                duration, len(entries), success)

    return {
        "status": "success" if success else "write_failed",
        "entries_curated": len(entries),
        "agents": sources,
        "title": title,
        "duration_s": round(duration, 1),
        "engine": analysis.get("engine", "unknown"),
        "confidence": analysis.get("confidence", 0),
    }


def _parse_analysis(content: str, entries: list[dict], by_agent: dict) -> dict:
    text = content.strip()

    # Strip markdown code blocks (```json ... ```)
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1 if lines[0].startswith("```") else 0
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[start:end]).strip()

    # Try direct parse
    try:
        parsed = json.loads(text)
        parsed.setdefault("version", "v1.0")
        parsed.setdefault("engine", "kurator-v1")
        parsed.setdefault("sources", list(by_agent.keys()))
        parsed.setdefault("confidence", 0.7)
        return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    # Try to find JSON object within text (e.g. "Here's the analysis: {...}")
    import re
    json_match = re.search(r'\{[^{}]*"title"[^{}]*\}', text, re.DOTALL)
    if not json_match:
        # Try broader search for any JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            parsed.setdefault("version", "v1.0")
            parsed.setdefault("engine", "kurator-v1")
            parsed.setdefault("sources", list(by_agent.keys()))
            parsed.setdefault("confidence", 0.6)
            return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    # Fallback: wrap the text as a summary
    logger.warning("kurator: _parse_analysis could not parse LLM response, using text fallback")
    return {
        "version": "v1.0",
        "engine": "kurator-v1-text",
        "title": f"Kurator — {len(entries)} entries dari {len(by_agent)} agent",
        "summary": text[:300] if text else "LLM response could not be parsed as JSON",
        "insights": [text[:200]] if text else ["Tidak ada insight"],
        "trends": [],
        "actionable": [],
        "sources": list(by_agent.keys()),
        "confidence": 0.4,
        "_parse_fallback": True,
    }


def _fallback_analysis(entries: list[dict], by_agent: dict) -> dict:
    """Fallback ketika LLM gagal — buat analisis sederhana dari entries."""
    insights = []
    for agent, agent_entries in by_agent.items():
        cat_counts = {}
        for e in agent_entries:
            cat = e.get("category", "general")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        top_cat = max(cat_counts, key=cat_counts.get) if cat_counts else "general"
        insights.append(f"{agent}: {len(agent_entries)} entries, dominan kategori '{top_cat}'")

    return {
        "version": "v1.0",
        "engine": "kurator-v1-fallback",
        "title": f"Kurator — {len(entries)} entries dari {len(by_agent)} agent",
        "summary": f"Agregasi {len(entries)} knowledge entries dari {len(by_agent)} Senator agent. Analisis otomatis (LLM unavailable).",
        "insights": insights if insights else ["Tidak cukup data untuk analisis"],
        "trends": [f"{len(by_agent)} agent aktif berkontribusi"],
        "actionable": ["Tingkatkan kualitas input Senator untuk analisis lebih baik"],
        "sources": list(by_agent.keys()),
        "confidence": 0.3,
        "_fallback": True,
    }
