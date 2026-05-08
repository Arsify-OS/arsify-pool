# SKP knowledge_sync.py Fix

## Problem (2026-05-05)
Orchestrator API returns 404 "Knowledge entry not found" or 0 search results despite data existing in SQLite database.

## Root Cause
`knowledge_sync.py` functions were reading from wrong table and using wrong column names.

## Files Modified
`/usr/local/lib/hermes-orchestrator/orchestrator/knowledge_sync.py`

## Fix 1: Table Name (3 locations)

**Functions affected:**
- `get_knowledge_entry()` (line ~69)
- `list_knowledge_entries()` (line ~95)  
- `search_knowledge()` (line ~120)

**Change:**
```python
# BEFORE (WRONG):
cursor.execute("""
    SELECT * FROM memory
    WHERE id = ?
""", (knowledge_id,))

# AFTER (CORRECT):
cursor.execute("""
    SELECT * FROM knowledge
    WHERE id = ?
""", (knowledge_id,))
```

## Fix 2: Column Names in search_knowledge()

**Problem:** Query used old `memory` table column names.

**Change:**
```python
# BEFORE (WRONG):
cursor.execute("""
    SELECT * FROM knowledge
    WHERE task_description LIKE ? OR tags LIKE ? OR output_data LIKE ?
    ORDER BY created_at DESC
    LIMIT ?
""", (f"%{query}%", f"%{query}%", f"%{query}%", limit))

# AFTER (CORRECT):
cursor.execute("""
    SELECT * FROM knowledge
    WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
    ORDER BY created_at DESC
    LIMIT ?
""", (f"%{query}%", f"%{query}%", f"%{query}%", limit))
```

## Fix 3: knowledge_access Table Requirement

**Problem:** API returns "Knowledge entry not found" even after fixing table name.

**Cause:** Orchestrator requires entries in `knowledge_access` table for API to return knowledge entries.

**Solution:** After inserting into `knowledge` table, MUST also insert into `knowledge_access`:
```bash
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
  "INSERT INTO knowledge_access (knowledge_id, agent_id, agent_name, accessed_at) \
   VALUES (<id>, 'infra', 'Infra Hermes Agent', unixepoch());"
```

**Schema:**
```sql
CREATE TABLE knowledge_access (
    id INTEGER PRIMARY KEY,
    knowledge_id INTEGER NOT NULL,
    agent_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    accessed_at REAL NOT NULL,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
);
```

## Verification Steps

1. **Test API after fix:**
   ```bash
   sudo systemctl restart hermes-orchestrator
   sleep 3
   curl -s https://workstation.upshalter.com/hermes/api/knowledge/16 | \
     python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('title','NOT FOUND'))"
   ```

2. **Test search:**
   ```bash
   curl -s "https://workstation.upshalter.com/hermes/api/knowledge/search?q=Hermes%20Project" | \
     python3 -c "import sys,json; d=json.load(sys.stdin); print('Found:', d.get('count',0))"
   ```

3. **Direct SQLite verification:**
   ```bash
   sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
     "SELECT k.id, k.title, ka.agent_id FROM knowledge k \
      LEFT JOIN knowledge_access ka ON k.id=ka.knowledge_id WHERE k.id=16;"
   ```

## Common Mistake
Inserting only into `knowledge` table but forgetting `knowledge_access` → API returns 404 despite data existing.

## Impact
- Phase 3 Workstation deployment depends on this fix
- All agents access SKP via Orchestrator API (not direct SQLite)
- Documentation entries (ID 16, 17, 18) require this fix to be API-accessible
