---
name: debug-orchestrator-task-polling
description: Debug and fix TaskStatus enum serialization + task_queue.py bugs that cause 500 errors and connection resets in the orchestrator API.
---

# Debug Orchestrator Task Polling - Connection Reset & 500 Errors

## Root Cause
Multiple bugs in `/usr/local/lib/hermes-orchestrator/orchestrator/task_queue.py` cause `/tasks` endpoint to return 500 and agents to get `ConnectionResetError`/`RemoteDisconnected`:

1. **TaskStatus enum serialization**: `to_dict()` stores `TaskStatus.PENDING` (enum repr) instead of `"pending"` (value)
2. **TaskStatus enum deserialization**: `from_dict()` doesn't convert string `"TaskStatus.PENDING"` back to enum
3. **list_tasks() iteration bug**: Only iterates `task_keys[:limit]` instead of all keys
4. **Config typo**: `Config.CHANNEL_EVENTS` used instead of `Config.CHANNEL_TASK_ASSIGNMENTS` or `CHANNEL_SYSTEM_EVENTS`

## Symptoms
- Agent logs show: `Task fetch failed: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))`
- Orchestrator `/tasks` endpoint returns HTTP 500
- `curl http://localhost:8000/tasks` returns `Internal Server Error`
- Tasks stuck with status `"TaskStatus.PENDING"` (string) in Redis

## Fix Steps

### Fix 1: TaskStatus Deserialization in `from_dict()`
File: `orchestrator/task_queue.py`, `Task.from_dict()` method

Add before priority handling:
```python
elif key == 'status':
    # Convert string status back to TaskStatus enum
    if isinstance(value, str):
        if value.startswith('TaskStatus.'):
            # Handle "TaskStatus.PENDING" format
            try:
                deserialized[key] = TaskStatus(value.split('.')[-1])
            except (ValueError, IndexError):
                deserialized[key] = TaskStatus.PENDING
        else:
            # Handle "pending" format
            try:
                deserialized[key] = TaskStatus(value)
            except ValueError:
                deserialized[key] = TaskStatus.PENDING
    else:
        deserialized[key] = value
```

### Fix 2: TaskStatus Serialization in `to_dict()`
File: `orchestrator/task_queue.py`, `Task.to_dict()` method

Change:
```python
# BEFORE:
"priority": self.priority,
"status": self.status,

# AFTER:
"priority": self.priority.value if hasattr(self.priority, 'value') else self.priority,
"status": self.status.value if hasattr(self.status, 'value') else self.status,
```

### Fix 3: list_tasks() Iteration
File: `orchestrator/task_queue.py`, `list_tasks()` method

Change:
```python
# BEFORE:
for key in task_keys[:limit]:

# AFTER:
for key in task_keys:
    if len(tasks) >= limit:
        break
```

### Fix 4: Config Typo in `assign_task()`
File: `orchestrator/task_queue.py`, `assign_task()` method around line 346

Change:
```python
# BEFORE:
Config.CHANNEL_EVENTS,

# AFTER:
Config.CHANNEL_TASK_ASSIGNMENTS,
```

## Verification After Fix

1. Test Task.from_dict() with both formats:
```python
from orchestrator.task_queue import Task, TaskStatus
data_old = {'task_id': 'test', 'status': 'TaskStatus.PENDING', ...}
t = Task.from_dict(data_old)
assert t.status == TaskStatus.PENDING
```

2. Test list_tasks():
```python
from orchestrator import Orchestrator, TaskStatus
o = Orchestrator()
tasks = o.list_tasks(status=TaskStatus.PENDING, limit=5)
print(f"Found {len(tasks)} pending tasks")
```

3. Test endpoint:
```bash
source /etc/systemd/system/hermes-upshalternal-bridge.service
curl -s "http://localhost:8000/tasks?status=pending&limit=3" \
  -H "X-API-Key: $ORCHESTRATOR_API_KEY"
# Should return 200 with JSON, not 500
```

## Restart Procedure

After applying fixes, restart both orchestrator and agents:

```bash
# Kill old orchestrator
lsof -ti:8000 | xargs -r kill -9

# Start new orchestrator
cd /usr/local/lib/hermes-orchestrator
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 &

# Restart agent bridges
systemctl restart hermes-upshalternal-bridge hermes-builder-bridge \
  hermes-infra-bridge hermes-dashboard-bridge hermes-plaza-bridge
```

## AgentStatus Enum Serialization (agent_registry.py)
Similar to TaskStatus, `AgentStatus` enum causes 500 errors on `/agents` endpoint.

### Fix 1: Status string-to-enum in `list_agents()`
File: `orchestrator/agent_registry.py`, `list_agents()` method around line 346

```python
# BEFORE:
agent = Agent(
    agent_id=row["agent_id"],
    ...
    status=row["status"],  # String from DB, not AgentStatus enum
    ...
)

# AFTER:
# Convert status string to AgentStatus enum
try:
    agent_status = AgentStatus(row["status"])
except ValueError:
    agent_status = AgentStatus.OFFLINE  # fallback

agent = Agent(
    agent_id=row["agent_id"],
    ...
    status=agent_status,
    ...
)
```

### Fix 2: Enum serialization in `Agent.to_dict()`
File: `orchestrator/agent_registry.py`, `Agent.to_dict()` method

```python
# BEFORE:
"status": self.status,

# AFTER:
"status": self.status.value if isinstance(self.status, AgentStatus) else self.status,
```

## API Key Validation Fix (auth.py)
`validate_key()` was rejecting `key_*` format keys (from `manage_keys.py`) because it only accepted `hma_*` format.

### Fix: Accept both key formats
File: `orchestrator/auth.py`, `validate_key()` method

```python
# BEFORE:
if not key or not key.startswith("hma_"):
    return None
key_hash = hashlib.sha256(key.encode()).hexdigest()
cursor.execute("SELECT ... WHERE key_hash = ?", (key_hash,))

# AFTER:
if not key:
    return None

conn = sqlite3.connect(self.db_path)
cursor = conn.cursor()

if key.startswith("key_"):
    # Look up by key_id (for key_* format from manage_keys.py)
    cursor.execute("SELECT agent_id, expires_at, revoked FROM api_keys WHERE key_id = ?", (key,))
    lookup_identifier = key
else:
    # Hash the key for lookup (for hma_* format)
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    cursor.execute("SELECT agent_id, expires_at, revoked FROM api_keys WHERE key_hash = ?", (key_hash,))
    lookup_identifier = key_hash[:16] + "..."

row = cursor.fetchone()
# ... handle revoked/expired checks with lookup_identifier
# Update last_used_at based on format:
if key.startswith("key_"):
    cursor.execute("UPDATE api_keys SET last_used_at = ? WHERE key_id = ?", (time.time(), key))
else:
    cursor.execute("UPDATE api_keys SET last_used_at = ? WHERE key_hash = ?", (time.time(), key_hash))
```

## Docker Agent Bridge Pattern
Docker containers running `hermes gateway run` don't connect to orchestrator. Use bridge scripts instead.

### Bridge Script Template
Create `/root/regrow-up-world-dev/<agent>-bridge.sh`:

```bash
#!/bin/bash
# <Agent> Agent Bridge - Connect to Orchestrator

ORCHESTRATOR_URL="${ORCHESTRATOR_URL:-http://host.docker.internal:8000}"
ORCHESTRATOR_API_KEY="${ORCHESTRATOR_API_KEY}"
AGENT_ID="<agent-id>"
AGENT_NAME="<Agent Name>"
CAPABILITIES='["shell_command", "file_read", "file_write", "hermes_command", "system_info"]'

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

register_agent() {
    log "Registering agent: $AGENT_ID"
    curl -s -X POST "$ORCHESTRATOR_URL/agents/register" \
        -H "X-API-Key: $ORCHESTRATOR_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"agent_id\": \"$AGENT_ID\", \"agent_name\": \"$AGENT_NAME\", \"capabilities\": $CAPABILITIES}"
}

send_heartbeat() {
    curl -s -X POST "$ORCHESTRATOR_URL/agents/heartbeat" \
        -H "X-API-Key: $ORCHESTRATOR_API_KEY" \
        -d "{\"agent_id\": \"$AGENT_ID\"}" > /dev/null
}

log "Starting <Agent> Agent Bridge"
register_agent
while true; do send_heartbeat; sleep 30; done
```

### Docker Compose Update
```yaml
services:
  hermes-<agent>:
    image: nousresearch/hermes-agent:latest
    container_name: hermes-<agent>
    command: ["/bin/bash", "/workspace/<agent>-bridge.sh"]
    volumes:
      - /root/regrow-up-world-dev:/workspace
      - /root/regrow-up-world-dev/<agent>-config:/root/.hermes
      - /root/regrow-up-world-dev/<agent>-bridge.sh:/workspace/<agent>-bridge.sh
    environment:
      - ORCHESTRATOR_URL=http://host.docker.internal:8000
      - ORCHESTRATOR_API_KEY=${ORCHESTRATOR_API_KEY}
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
```

## UFW Firewall Rules for Docker
Orchestrator on port 8000 needs UFW rules to allow Docker networks:

```bash
# Check Docker network ranges
docker network inspect bridge | grep Subnet  # Usually 172.17.0.0/16
docker network inspect <custom-network> | grep Subnet  # May be 172.22.0.0/16

# Add UFW rules
ufw allow from 172.17.0.0/16 to any port 8000 comment 'Allow Docker bridge to orchestrator'
ufw allow from 172.22.0.0/16 to any port 8000 comment 'Allow Docker network to orchestrator'

# Verify
ufw status | grep 8000
```

Test connectivity from container:
```bash
docker exec <container> bash -c "timeout 3 curl -s http://172.17.0.1:8000/health"
```

## Prevention
- Always use `.value` when storing enum to Redis/JSON
- Always handle both `"pending"` and `"TaskStatus.PENDING"` formats in from_dict()
- Run `redis-cli --scan --pattern 'task:*'` to check status formats after changes
- Test `/agents` endpoint after any `AgentStatus` changes: `curl -s -H "X-API-Key: <key>" http://127.0.0.1:8000/agents`
- Verify API key format compatibility: `manage_keys.py` uses `key_*` format, `validate_key()` must accept both `key_*` and `hma_*`
- Always check UFW rules when Docker containers can't reach host services

## KnowledgeSync.create_knowledge() — Adding POST /knowledge

When agents need to store research findings, the KnowledgeSync class needs a `create_knowledge()` method. The SKP shared memory DB is at `/usr/local/lib/hermes-shared-memory/db/memory.db` with table:
```sql
CREATE TABLE knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL, content TEXT NOT NULL, category TEXT NOT NULL,
    source_agent_id TEXT NOT NULL, source_agent_name TEXT NOT NULL,
    tags TEXT, priority INTEGER DEFAULT 5,
    created_at REAL NOT NULL, updated_at REAL NOT NULL, metadata TEXT
);
```

Add `create_knowledge()` to `knowledge_sync.py` and POST `/knowledge` + POST `/api/knowledge` routes to `api.py`. See `vpso-management/references/senator-pentahelix-architecture.md` for full pattern.

## Multi-Agent Hierarchy Pattern (PIC Structure)

When deploying multiple related agents (e.g., research senators), register them with a PIC (Person In Charge) hierarchy:
1. Top-level manager agent (e.g., Upshalternal AI CEO)
2. Mid-level kurator agent (e.g., Kurator Pentahelix) — `capabilities: ['curation', 'oversight', 'quality_control']`
3. Worker agents (e.g., Senator Akademisi, Senator Bisnis) — `capabilities: ['research', '<sector>']`

Store PIC relationship in metadata: `{'pic': 'kurator-pentahelix', 'type': 'senator-pentahelix'}`. Update metadata via direct SQL: `UPDATE agents SET metadata = ? WHERE agent_id = ?`.

## Telegram send_message Target Format

The `send_message` tool requires `target` in format `telegram:<numeric_chat_id>`. The channel directory at `~/.hermes/channel_directory.json` contains the mapping. Extract numeric ID: `jq '.platforms.telegram[0].id' ~/.hermes/channel_directory.json`.

## API Route Prefix Pitfall (2026-05-06)

Nginx proxies `/api/` → `http://127.0.0.1:8000/api/` but FastAPI routes were all at root level (`/tasks`, `/agents`). Requests to `/api/tasks` returned 401/500 because no matching route existed.

**Fix**: Add `APIRouter(prefix="/api")` and register duplicate routes:
```python
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")
# ... define api_router.get("/tasks"), etc ...
app.include_router(api_router)  # at module level, NOT inside if __name__
```

**Critical**: `app.include_router()` must be at module level, not inside `if __name__ == "__main__"`, because `uvicorn api:app` does not execute the `__main__` block.

## Systemd Python Path Pitfall

Systemd service used `/usr/bin/python3` (system Python) but orchestrator dependencies (opentelemetry, fastapi, etc.) are in the venv. Service failed silently with `ModuleNotFoundError`.

**Fix**: Update `ExecStart` in systemd service to use venv python:
```ini
ExecStart=/usr/local/lib/hermes-orchestrator/venv/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port 8000
```

## Docker→Host Network Access

Docker containers with `extra_hosts: "host.docker.internal:host-gateway"` can ping host but may still get connection timeout on specific ports due to UFW.

**Fix**: Add UFW rules for Docker bridge network:
```bash
ufw allow from 172.17.0.0/16 to any port 8000 comment 'Docker to host orchestrator'
```

**Better fix**: Use `network_mode: host` in docker-compose for containers that need reliable host access. This eliminates DNS resolution and firewall issues entirely. Trade-off: no port mapping, containers share host network.

## Auth Middleware Whitelist

The `AuthMiddleware` in `middleware.py` only whitelists `["/", "/health", "/docs", "/openapi.json"]`. All other paths require valid API key. When adding new public endpoints, update the whitelist:
```python
if request.url.path in ["/", "/health", "/status", "/docs", "/openapi.json"]:
    return await call_next(request)
# Also whitelist GET read-only endpoints
if request.method == "GET" and request.url.path in ["/api/tasks", "/api/agents", "/api/knowledge"]:
    return await call_next(request)
```

## Generating Valid API Keys

The `AuthManager` generates keys in `hma_*` format via `generate_key()`. Hardcoded keys like `hermes-orchestrator-key-2026` are NOT valid — they must be generated and stored in the auth database:
```python
from orchestrator.auth import AuthManager
am = AuthManager()
key = am.generate_key('agent-id')  # Returns hma_* key
# Store this key — it's the only time it's visible
```
