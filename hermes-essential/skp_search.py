"""
core/skp_search.py — Full-text search untuk SKP knowledge pool.

Menggunakan SQLite FTS5 untuk fast text search di knowledge entries.
Auto-sync dari knowledge table via trigger.
"""

import logging
import sqlite3
import os

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("SKP_DB_PATH", "/data/shared_knowledge_pool.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def setup_fts():
    """Setup FTS5 table dan triggers untuk auto-sync."""
    conn = _get_conn()
    cur = conn.cursor()

    # Create FTS5 virtual table
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
            key,
            value,
            category,
            source_agent_name,
            content='knowledge',
            content_rowid='id'
        )
    """)

    # Triggers untuk auto-sync
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge BEGIN
            INSERT INTO knowledge_fts(rowid, key, value, category, source_agent_name)
            VALUES (NEW.id, NEW.key, NEW.value, NEW.category, NEW.source_agent_name);
        END
    """)

    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, key, value, category, source_agent_name)
            VALUES('delete', OLD.id, OLD.key, OLD.value, OLD.category, OLD.source_agent_name);
        END
    """)

    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, key, value, category, source_agent_name)
            VALUES('delete', OLD.id, OLD.key, OLD.value, OLD.category, OLD.source_agent_name);
            INSERT INTO knowledge_fts(rowid, key, value, category, source_agent_name)
            VALUES (NEW.id, NEW.key, NEW.value, NEW.category, NEW.source_agent_name);
        END
    """)

    # Rebuild FTS index dari existing data
    cur.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")

    conn.commit()
    conn.close()
    logger.info("skp_search: FTS5 setup complete")


def search(query: str, limit: int = 10, category: str = None, agent: str = None) -> list:
    """
    Full-text search di SKP.
    
    Args:
        query: Search query (supports FTS5 syntax: AND, OR, NOT, *)
        limit: Max results
        category: Filter by category
        agent: Filter by source agent
    
    Returns:
        List of matching knowledge entries
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()

        # Build query dengan optional filters
        sql = """
            SELECT k.key, k.value, k.category, k.source_agent_name, k.priority, k.created_at,
                   rank AS search_rank
            FROM knowledge_fts fts
            JOIN knowledge k ON k.id = fts.rowid
            WHERE knowledge_fts MATCH ?
        """
        params = [query]

        if category:
            sql += " AND k.category = ?"
            params.append(category)
        if agent:
            sql += " AND k.source_agent_name = ?"
            params.append(agent)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        cur.execute(sql, params)
        results = [dict(r) for r in cur.fetchall()]
        conn.close()
        return results
    except Exception as exc:
        logger.error("skp_search: search failed: %s", exc)
        return []


def search_count(query: str) -> int:
    """Count search results."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        # FTS5 doesn't support * wildcard, use a common word or count all
        if query == "*":
            cur.execute("SELECT COUNT(*) FROM knowledge_fts")
        else:
            cur.execute("SELECT COUNT(*) FROM knowledge_fts WHERE knowledge_fts MATCH ?", (query,))
        count = cur.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def rebuild_index():
    """Rebuild FTS index dari scratch."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
    conn.commit()
    conn.close()
    logger.info("skp_search: FTS index rebuilt")
