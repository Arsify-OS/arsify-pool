#!/usr/bin/env python3
"""
skp-cleaner.py — Arsify Workforce OS
Hapus junk entries dari SKP: entries yang menyimpan prompt senator,
bukan hasil analisis.

Masalah yang diselesaikan:
  senator-media/analysis/48874 → "Step: Analyze and understand: Anda adalah..."
  Ini adalah prompt senator yang tersimpan, BUKAN insight.

Usage:
  DRY_RUN=true python3 skp-cleaner.py   # Preview tanpa hapus
  python3 skp-cleaner.py                 # Hapus junk entries
"""

import sqlite3, os, json, sys
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────
DB_CANDIDATES = [
    os.getenv("SKP_DB_PATH", ""),
    "/data/arsify.db",
    "/data/shared_knowledge_pool.db",
    "/root/.hermes/shared_knowledge_pool.db",
]
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

# ── Pola yang menandakan ini adalah prompt, bukan insight ─────────────
JUNK_PATTERNS = [
    # Hermes agent self-description (prompt disimpan)
    "step: analyze and understand",
    "anda adalah senator",
    "kamu adalah senator",
    "kamu adalah intelligence analyst",
    "anda adalah intelligence analyst",
    "anda adalah kurator",
    "kamu adalah kurator",
    "anda adalah arsify",
    "kamu adalah arsify",
    # Hermes agent metadata
    "## misi inti",
    "## identitas",
    "soul.md",
    "[step ",
    "step 1:",
    "step 2:",
    "step 3:",
    # Orchestrator task artifacts
    "task_id:",
    "agent_id:",
    "workflow_step",
    "executing step",
    # Empty or near-empty
]

# Pola yang menandakan ini adalah insight NYATA
INSIGHT_MARKERS = [
    # JSON dengan field bermakna
    '"temuan"',
    '"peluang"',
    '"regulasi"',
    '"isu"',
    '"narasi_dominan"',
    '"funding_tracker"',
    '"sentiment_overall"',
    # Konten nyata
    "universitas",
    "startup",
    "kementerian",
    "kominfo",
    "regulasi",
    "developer",
    "komunitas",
    "rp ",
    "usd ",
    "funding",
    "% ",
]

MIN_INSIGHT_LENGTH = 150  # Insight nyata minimal 150 karakter


def find_db():
    for p in DB_CANDIDATES:
        if p and os.path.exists(p): return p
    return None


def find_table(conn):
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    for t in ["knowledge", "memory_notes"]:
        if t in tables: return t
    return tables[0] if tables else "knowledge"


def is_junk(key: str, value: str) -> tuple[bool, str]:
    """
    Returns (is_junk, reason)
    """
    value_lower = (value or "").lower().strip()

    # Cek pola junk
    for pattern in JUNK_PATTERNS:
        if pattern in value_lower:
            return True, f"contains junk pattern: '{pattern[:40]}'"

    # Terlalu pendek untuk jadi insight nyata
    if len(value_lower) < MIN_INSIGHT_LENGTH:
        return True, f"too short ({len(value_lower)} chars)"

    # Kalau key adalah analysis/* dan value tidak punya marker insight
    if "/analysis/" in key:
        has_insight = any(m in value_lower for m in INSIGHT_MARKERS)
        if not has_insight:
            return True, "analysis key but no insight markers found"

    return False, ""


def is_real_insight(value: str) -> bool:
    """Check apakah entry ini adalah insight nyata."""
    value_lower = value.lower()
    # Punya marker insight
    marker_count = sum(1 for m in INSIGHT_MARKERS if m in value_lower)
    return marker_count >= 2


def clean_skp(conn, table, dry_run=True):
    conn.row_factory = sqlite3.Row
    rows = conn.execute(f"SELECT id, key, value FROM {table}").fetchall()

    total = len(rows)
    junk_entries = []
    keep_entries = []

    for row in rows:
        junk, reason = is_junk(row["key"], row["value"] or "")
        if junk:
            junk_entries.append((row["id"], row["key"], row["value"][:80], reason))
        else:
            keep_entries.append(row)

    print(f"Total entries: {total}")
    print(f"Junk detected: {len(junk_entries)}")
    print(f"Real insights: {len(keep_entries)}")
    print()

    if junk_entries:
        print("=== JUNK ENTRIES (akan dihapus) ===")
        for eid, key, preview, reason in junk_entries[:20]:
            print(f"  [{eid}] {key}")
            print(f"       Value: {preview!r}")
            print(f"       Reason: {reason}")
            print()
        if len(junk_entries) > 20:
            print(f"  ... dan {len(junk_entries)-20} entries lagi")

    if not dry_run and junk_entries:
        ids = [e[0] for e in junk_entries]
        placeholders = ",".join("?" * len(ids))
        conn.execute(f"DELETE FROM {table} WHERE id IN ({placeholders})", ids)
        conn.commit()
        print(f"✓ Deleted {len(junk_entries)} junk entries")

        # Show remaining
        remaining = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"✓ Remaining: {remaining} real insight entries")
    elif dry_run:
        print(f"(DRY RUN — nothing deleted)")

    return len(junk_entries), len(keep_entries)


def audit_content_quality(conn, table):
    """Show sample of real insights to verify quality."""
    rows = conn.execute(
        f"SELECT key, value FROM {table} ORDER BY rowid DESC LIMIT 10"
    ).fetchall()

    print("\n=== SAMPLE REAL ENTRIES (setelah cleanup) ===")
    for row in rows:
        val = (row[0] or "")
        print(f"\n  Key: {row[0]}")
        print(f"  Preview: {val[:150]}...")


def main():
    db = find_db()
    if not db:
        print("ERROR: SKP database not found"); sys.exit(1)

    print(f"=== SKP CLEANER ===")
    print(f"Database: {db}")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE - will delete junk'}")
    print()

    conn = sqlite3.connect(db)
    table = find_table(conn)
    print(f"Table: {table}")
    print()

    deleted, kept = clean_skp(conn, table, dry_run=DRY_RUN)

    if not DRY_RUN:
        audit_content_quality(conn, table)

    conn.close()
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
