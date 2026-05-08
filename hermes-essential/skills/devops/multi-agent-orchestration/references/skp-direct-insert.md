# SKP Direct Insert Procedure

When the Orchestrator API endpoint `POST /knowledge` is unavailable or returns "Method Not Allowed", insert knowledge entries directly into SQLite database.

## Problem
Orchestrator API may not expose a POST endpoint for creating knowledge entries. The API typically has:
- `GET /knowledge` - List entries
- `GET /knowledge/{id}` - Get specific entry  
- `GET /knowledge/search` - Search entries

But NO `POST /knowledge` for creating entries.

## Solution: Direct SQLite Insert

### Step 1: Check Database Location
```bash
grep -n "SHARED_MEMORY_DB" /usr/local/lib/hermes-orchestrator/orchestrator/config.py
# Output: SHARED_MEMORY_DB = Path("/usr/local/lib/hermes-shared-memory/db/memory.db")
```

### Step 2: Check Table Schema
```bash
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db "PRAGMA table_info(knowledge);"
```

Expected schema:
```
0|id|INTEGER|0||1
1|title|TEXT|1||0
2|content|TEXT|1||0
3|category|TEXT|1||0
4|source_agent_id|TEXT|1||0
5|source_agent_name|TEXT|1||0
6|tags|TEXT|0||0
7|priority|INTEGER|0|5|0
8|created_at|REAL|1||0
9|updated_at|REAL|1||0
10|metadata|TEXT|0||0
```

### Step 3: Insert Knowledge Entry
```bash
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
"INSERT INTO knowledge (title, content, category, source_agent_id, source_agent_name, tags, priority, created_at, updated_at) \
VALUES ('Your Title', 'Your content here', 'documentation', 'infra', 'Infra Hermes Agent', '[\"tag1\", \"tag2\"]', 10, unixepoch(), unixepoch());"
```

### Step 4: Allow API Access (CRITICAL)
Orchestrator requires entries in `knowledge_access` table for API to return them.

Check schema:
```bash
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db "PRAGMA table_info(knowledge_access);"
```

Expected schema:
```
0|id|INTEGER|0||1
1|knowledge_id|INTEGER|1||0
2|agent_id|TEXT|1||0
3|agent_name|TEXT|1||0
4|accessed_at|REAL|1||0
```

Insert access entry:
```bash
# Replace 16 with your knowledge ID
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
"INSERT INTO knowledge_access (knowledge_id, agent_id, agent_name, accessed_at) \
VALUES (16, 'infra', 'Infra Hermes Agent', unixepoch());"
```

### Step 5: Verify
```bash
# Check entry exists
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
"SELECT id, title, category, datetime(created_at, 'unixepoch') FROM knowledge WHERE id=16;"

# Check access entry exists
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
"SELECT * FROM knowledge_access WHERE knowledge_id=16;"

# Restart Orchestrator to reload
sudo systemctl restart hermes-orchestrator

# Test API access (via Nginx proxy with injected API key)
curl -s https://workstation.upshalter.com/hermes/api/knowledge/16 | python3 -m json.tool
```

## Common Pitfalls

1. **Missing knowledge_access entry**: API returns "Knowledge entry not found" even though data exists in `knowledge` table.

2. **Tags format**: Must be valid JSON array string: `'["tag1", "tag2"]'` not `'tag1,tag2'`.

3. **Content with quotes**: Escape single quotes in content:
   ```bash
   content="It'\''s a test"  # Escapes single quote
   ```

4. **Orchestrator not reloading**: Must restart service after inserting into SQLite directly.

## Batch Insert Example

For inserting documentation in batches:

```bash
# Batch 1: Overview
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
"INSERT INTO knowledge (title, content, category, source_agent_id, source_agent_name, tags, priority, created_at, updated_at) \
VALUES ('Doc Title 1', 'Content 1', 'documentation', 'infra', 'Infra Hermes Agent', '[\"hermes-project\"]', 10, unixepoch(), unixepoch());"

# Get the inserted ID
ID1=$(sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db "SELECT last_insert_rowid();")

# Add access
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
"INSERT INTO knowledge_access (knowledge_id, agent_id, agent_name, accessed_at) \
VALUES ($ID1, 'infra', 'Infra Hermes Agent', unixepoch());"

# Batch 2: Full doc
sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
"INSERT INTO knowledge (title, content, category, source_agent_id, source_agent_name, tags, priority, created_at, updated_at) \
VALUES ('Doc Title 2', 'Full content here...', 'documentation', 'infra', 'Infra Hermes Agent', '[\"hermes-project\", \"full-doc\"]', 9, unixepoch(), unixepoch());"

ID2=$(sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db "SELECT last_insert_rowid();")

sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
"INSERT INTO knowledge_access (knowledge_id, agent_id, agent_name, accessed_at) \
VALUES ($ID2, 'infra', 'Infra Hermes Agent', unixepoch());"

# Restart to reload
sudo systemctl restart hermes-orchestrator
```

## Verification Checklist

- [ ] Entry exists in `knowledge` table
- [ ] Entry exists in `knowledge_access` table  
- [ ] Orchestrator restarted after insert
- [ ] API returns entry: `curl https://workstation.upshalter.com/hermes/api/knowledge/{id}`
- [ ] Search finds entry: `curl "https://workstation.upshalter.com/hermes/api/knowledge/search?q=keyword"`
