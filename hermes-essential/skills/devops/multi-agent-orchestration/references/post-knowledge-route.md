# Orchestrator API — POST /api/knowledge Route

## Problem
The orchestrator had GET `/knowledge` routes (list, search, get by ID) but NO POST route to create entries. Agents trying to store knowledge got HTTP 405 "Method Not Allowed".

## Solution

### Step 1: Add create_knowledge to KnowledgeSync

File: `orchestrator/knowledge_sync.py`

Add `import json` to imports, then add method:

```python
def create_knowledge(self, title, content, category, source_agent_id,
                     source_agent_name, tags=None, priority=5,
                     metadata=None):
    """Create a new knowledge entry. Returns knowledge_id or None."""
    if not self.shared_memory_db.exists():
        self.shared_memory_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.shared_memory_db))
        conn.execute("""CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, content TEXT NOT NULL,
            category TEXT NOT NULL, source_agent_id TEXT NOT NULL,
            source_agent_name TEXT NOT NULL, tags TEXT,
            priority INTEGER DEFAULT 5, created_at REAL NOT NULL,
            updated_at REAL NOT NULL, metadata TEXT
        )""")
        conn.commit(); conn.close()
    try:
        conn = sqlite3.connect(str(self.shared_memory_db))
        cursor = conn.cursor()
        now = time.time()
        tags_str = ",".join(tags) if tags else ""
        metadata_str = json.dumps(metadata) if metadata else "{}"
        cursor.execute("""INSERT INTO knowledge
            (title, content, category, source_agent_id, source_agent_name,
             tags, priority, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, content, category, source_agent_id, source_agent_name,
             tags_str, priority, now, now, metadata_str))
        knowledge_id = cursor.lastrowid
        conn.commit(); conn.close()
        return knowledge_id
    except Exception as e:
        print(f"[KnowledgeSync] Error: {e}")
        return None
```

### Step 2: Add Pydantic Models to api.py

```python
class KnowledgeEntryRequest(BaseModel):
    title: str
    content: str
    category: str = "research"
    source_agent_id: str
    source_agent_name: str
    tags: Optional[List[str]] = None
    priority: int = 5
    metadata: Optional[Dict] = None

class KnowledgeEntryResponse(BaseModel):
    knowledge_id: int
    status: str
    message: str
```

### Step 3: Add POST Routes (both root and /api prefix)

```python
@app.post("/knowledge", response_model=KnowledgeEntryResponse)
async def create_knowledge(request: KnowledgeEntryRequest):
    knowledge_id = orchestrator.knowledge_sync.create_knowledge(
        title=request.title, content=request.content,
        category=request.category, source_agent_id=request.source_agent_id,
        source_agent_name=request.source_agent_name, tags=request.tags,
        priority=request.priority, metadata=request.metadata)
    if knowledge_id is None:
        raise HTTPException(status_code=500, detail="Failed to create")
    return KnowledgeEntryResponse(
        knowledge_id=knowledge_id, status="created",
        message="Knowledge entry created successfully")

# Same for api_router (prefix=/api)
@api_router.post("/knowledge", response_model=KnowledgeEntryResponse)
async def api_create_knowledge(request: KnowledgeEntryRequest):
    # Same implementation
    ...
```

### Step 4: Register Router at Module Level

```python
# CRITICAL: At module level, NOT inside if __name__
app.include_router(api_router)
```

## Verification

```bash
curl -s -X POST http://localhost:8000/api/knowledge \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <valid_key>" \
  -d '{"title":"Test","content":"Content","category":"test",
       "source_agent_id":"test","source_agent_name":"Test"}'
# Expected: {"knowledge_id":N,"status":"created","message":"..."}
```

## Auth Middleware Whitelist

When adding new public GET endpoints, update the whitelist in `middleware.py`:

```python
if request.method == "GET" and request.url.path in [
    "/api/tasks", "/api/agents", "/api/knowledge"
]:
    return await call_next(request)
```

POST endpoints should generally require auth (don't add to whitelist).
