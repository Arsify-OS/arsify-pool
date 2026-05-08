#!/usr/bin/env python3
"""
skp-adapter.py — Upshalter SKP Auto-Detect Library
Versi: 1.0 — Mei 2026

Diselesaikan: 4 mismatch yang ditemukan Upshalter:
  1. Table name: memory_notes vs knowledge
  2. DB path: /data/arsify.db vs /data/shared_knowledge_pool.db
  3. Key format: akademisi/% vs senator-akademisi/execution/XXXXX
  4. Router path: /opt/arsify vs /root/.upshalter

Import di script lain: from skp_adapter import SKP
"""

import sqlite3
import os
import json
from datetime import datetime, timezone

# ── Auto-detect: DB Path ─────────────────────────────────────────────
DB_CANDIDATES = [
    os.getenv("SKP_DB_PATH", ""),
    "/data/arsify.db",                          # symlink (arsify-final)
    "/data/shared_knowledge_pool.db",            # direct (upshalter production)
    "/root/.upshalter/shared_knowledge_pool.db",    # upshalter native path
    "/root/.upshalter/knowledge.db",
    "/opt/upshalter-cognitive/data/knowledge.db",
]


def find_db() -> str:
    for path in DB_CANDIDATES:
        if path and os.path.exists(path):
            return path
    # Buat baru di path default
    default = "/data/arsify.db"
    os.makedirs(os.path.dirname(default), exist_ok=True)
    return default


# ── Auto-detect: Table Name ──────────────────────────────────────────
TABLE_CANDIDATES = ["knowledge", "memory_notes", "shared_knowledge", "notes"]


def find_table(conn: sqlite3.Connection) -> str:
    existing = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    for t in TABLE_CANDIDATES:
        if t in existing:
            return t
    # Tidak ada yang cocok — buat memory_notes sebagai default
    return "memory_notes"


# ── Auto-detect: Key Format ───────────────────────────────────────────
def detect_key_format(conn: sqlite3.Connection, table: str) -> dict:
    """
    Deteksi format key yang dipakai di sistem ini.
    Returns dict dengan prefix per domain.
    """
    # Sample beberapa key untuk mendeteksi format
    try:
        rows = conn.execute(
            f"SELECT key FROM {table} LIMIT 50"
        ).fetchall()
        keys = [r[0] for r in rows]
    except Exception:
        keys = []

    # Pola yang mungkin ada:
    # Format A (arsify-final): akademisi/temuan/YYYYMMDD-HH
    # Format B (upshalter production): senator-akademisi/execution/XXXXX
    # Format C (upshalter lain): upshalter/senator/akademisi/XXXXX

    format_a = sum(1 for k in keys if k.startswith(("akademisi/", "bisnis/", "komunitas/", "pemerintah/", "media/")))
    format_b = sum(1 for k in keys if "senator-" in k)
    format_c = sum(1 for k in keys if k.startswith("upshalter/senator"))

    if format_b > format_a and format_b > format_c:
        # Format B dominan
        return {
            "akademisi":   ["senator-akademisi/", "akademisi/"],
            "bisnis":      ["senator-bisnis/", "bisnis/"],
            "komunitas":   ["senator-komunitas/", "komunitas/"],
            "pemerintah":  ["senator-pemerintah/", "pemerintah/"],
            "media":       ["senator-media/", "media/"],
            "write_prefix": {
                "akademisi":  "senator-akademisi/temuan",
                "bisnis":     "senator-bisnis/peluang",
                "komunitas":  "senator-komunitas/isu",
                "pemerintah": "senator-pemerintah/regulasi",
                "media":      "senator-media/narasi",
            }
        }
    elif format_c > format_a:
        # Format C
        return {
            "akademisi":   ["upshalter/senator/akademisi/", "akademisi/"],
            "bisnis":      ["upshalter/senator/bisnis/", "bisnis/"],
            "komunitas":   ["upshalter/senator/komunitas/", "komunitas/"],
            "pemerintah":  ["upshalter/senator/pemerintah/", "pemerintah/"],
            "media":       ["upshalter/senator/media/", "media/"],
            "write_prefix": {
                "akademisi":  "akademisi/temuan",
                "bisnis":     "bisnis/peluang",
                "komunitas":  "komunitas/isu",
                "pemerintah": "pemerintah/regulasi",
                "media":      "media/narasi",
            }
        }
    else:
        # Format A (default / arsify-final style)
        return {
            "akademisi":   ["akademisi/", "senator-akademisi/"],
            "bisnis":      ["bisnis/", "senator-bisnis/"],
            "komunitas":   ["komunitas/", "senator-komunitas/"],
            "pemerintah":  ["pemerintah/", "senator-pemerintah/"],
            "media":       ["media/", "senator-media/"],
            "write_prefix": {
                "akademisi":  "akademisi/temuan",
                "bisnis":     "bisnis/peluang",
                "komunitas":  "komunitas/isu",
                "pemerintah": "pemerintah/regulasi",
                "media":      "media/narasi",
            }
        }


# ── Auto-detect: Router Path ──────────────────────────────────────────
ROUTER_CANDIDATES = [
    "/root/.upshalter/router.py",
    "/opt/upshalter-cognitive/src/router.py",
    "/opt/arsify/arsify-os-prototype-final/arsify-app/app/router.py",
    "/root/arsify-os-prototype-final/arsify-app/app/router.py",
    "/home/ubuntu/arsify-os-prototype-final/arsify-app/app/router.py",
]


def find_router() -> str | None:
    for path in ROUTER_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


# ── Main SKP Class ───────────────────────────────────────────────────
class SKP:
    """
    SKP (Shared Knowledge Pool) adapter yang bekerja di semua versi sistem.
    """

    def __init__(self):
        self.db_path = find_db()
        self._conn = None
        self._table = None
        self._key_format = None

    def connect(self) -> sqlite3.Connection:
        if self._conn:
            return self._conn
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_table()
        self._table = find_table(self._conn)
        self._key_format = detect_key_format(self._conn, self._table)
        return self._conn

    def _ensure_table(self):
        """Buat tabel yang diperlukan jika belum ada."""
        conn = self._conn
        # Cek tabel yang ada
        existing = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]

        if not any(t in existing for t in TABLE_CANDIDATES):
            # Buat memory_notes sebagai default
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    scope TEXT DEFAULT 'global',
                    source_agent_name TEXT DEFAULT 'system',
                    category TEXT DEFAULT 'general',
                    tags TEXT DEFAULT '[]',
                    priority INTEGER DEFAULT 5,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_key ON memory_notes(key)")
            conn.commit()

    @property
    def table(self) -> str:
        if not self._table:
            self.connect()
        return self._table

    @property
    def key_format(self) -> dict:
        if not self._key_format:
            self.connect()
        return self._key_format

    def write(self, key: str, value: str, agent: str = "system",
              category: str = "general") -> bool:
        """Tulis entry ke SKP."""
        conn = self.connect()
        table = self.table
        now = datetime.now(timezone.utc).isoformat()

        # Cek kolom yang ada
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]

        if "source_agent_name" in cols and "category" in cols:
            # Check if scope column exists (memory_notes has it, knowledge doesn't)
            if "scope" in cols:
                conn.execute(f"""
                    INSERT OR REPLACE INTO {table}
                        (key, value, scope, source_agent_name, category, updated_at)
                    VALUES (?, ?, 'global', ?, ?, ?)
                """, (key, value[:4000], agent, category, now))
            else:
                conn.execute(f"""
                    INSERT OR REPLACE INTO {table}
                        (key, value, source_agent_name, category, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (key, value[:4000], agent, category, now))
        else:
            # Minimal insert
            conn.execute(f"""
                INSERT OR REPLACE INTO {table} (key, value)
                VALUES (?, ?)
            """, (key, value[:4000]))

        conn.commit()
        return True

    def read_recent(self, domain: str, hours: int = 12, limit: int = 10) -> list:
        """Baca entries Senator terbaru untuk domain tertentu."""
        conn = self.connect()
        table = self.table
        key_format = self.key_format

        prefixes = key_format.get(domain, [f"{domain}/"])
        results = []

        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        sel = "key, value, source_agent_name" + (", created_at" if "created_at" in cols else ", ''")

        for prefix in prefixes:
            rows = conn.execute(f"""
                SELECT {sel}
                FROM {table}
                WHERE key LIKE ?
                ORDER BY id DESC
                LIMIT ?
            """, (prefix + "%", limit)).fetchall()

            for r in rows:
                results.append({
                    "key": r[0],
                    "value": r[1][:600],
                    "agent": r[2] if len(r) > 2 else "unknown",
                    "created_at": r[3] if len(r) > 3 else ""
                })

            if results:
                break  # Gunakan prefix pertama yang menghasilkan hasil

        return results[:limit]

    def write_senator(self, domain: str, content: str, agent: str) -> str:
        """Tulis output Senator dengan key format yang benar."""
        key_format = self.key_format
        prefix = key_format["write_prefix"].get(domain, f"{domain}/temuan")
        date_key = datetime.now(timezone.utc).strftime("%Y%m%d-%H")
        key = f"{prefix}/{date_key}"
        self.write(key, content, agent, domain)
        return key

    def get_info(self) -> dict:
        """Info tentang konfigurasi yang terdeteksi."""
        conn = self.connect()
        total = conn.execute(f"SELECT COUNT(*) FROM {self.table}").fetchone()[0]
        return {
            "db_path": self.db_path,
            "table": self.table,
            "key_format": "auto-detected",
            "total_entries": total,
            "router_path": find_router(),
        }

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


# ── Convenience functions ─────────────────────────────────────────────
_default_skp = None


def get_skp() -> SKP:
    global _default_skp
    if _default_skp is None:
        _default_skp = SKP()
    return _default_skp


def skp_write(key: str, value: str, agent: str = "system", category: str = "general") -> bool:
    return get_skp().write(key, value, agent, category)


def skp_read_recent(domain: str, hours: int = 12) -> list:
    return get_skp().read_recent(domain, hours)


def skp_info() -> dict:
    return get_skp().get_info()


if __name__ == "__main__":
    print("=== SKP ADAPTER — System Detection ===")
    skp = SKP()
    info = skp.get_info()
    print(f"DB Path:     {info['db_path']}")
    print(f"Table:       {info['table']}")
    print(f"Total:       {info['total_entries']} entries")
    print(f"Router:      {info['router_path'] or 'NOT FOUND'}")
    print(f"Key format:  auto-detected")
    print()
    # Show sample keys
    conn = skp.connect()
    rows = conn.execute(f"SELECT key FROM {skp.table} LIMIT 5").fetchall()
    print("Sample keys:")
    for r in rows:
        print(f"  {r[0]}")
