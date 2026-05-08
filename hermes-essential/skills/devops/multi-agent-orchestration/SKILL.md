---
name: multi-agent-orchestration
description: Build multi-agent orchestration systems with shared memory, message queues, and workflow engines for coordinating autonomous AI agents
tags: [orchestration, multi-agent, shared-memory, redis, fastapi, sqlite, agent-coordination]
---

# Multi-Agent Orchestration

Build orchestration systems that coordinate multiple autonomous AI agents with shared memory, message queues, and workflow automation.

## When to Use

- Coordinating multiple Hermes agents or AI systems
- Building "Hive Mind" shared memory across agents
- Implementing automated workflows between agents
- Creating agent task distribution and load balancing
- Setting up centralized monitoring for agent fleets

## Architecture Pattern

```
Orchestrator Hub (Central Coordination)
  ↓
Message Queue (Redis) + Shared Memory (SQLite)
  ↓
Agent Adapters (REST API wrappers)
  ↓
Individual Agents (Docker/Systemd/PM2)
```

## Implementation Phases

### Phase 0: Shared Memory Foundation (45 min target, ~10 min actual)

**Objective:** Create centralized memory storage for all agents to share context.

**Architecture Choice: Task Memory vs Shared Knowledge Pool**

Two models available:

1. **Task Memory (agent-specific):** Each agent writes their own task history. Other agents can read it but memories remain agent-scoped. Results in uneven distribution (agent A has 4 memories, agent B has 1).

2. **Shared Knowledge Pool (global):** All agents read from and write to a common knowledge base. Every agent sees the same knowledge entries. Preferred for true "hive mind" behavior.

**Steps:**

1. **Database Setup**
   ```bash
   mkdir -p /usr/local/lib/hermes-shared-memory/{api,db,tests,docs}
   ```

2. **Create SQLite Schema**
   
   **For Task Memory (agent-specific):**
   - `memory` table: task tracking (id, agent_id, task_type, status, input/output data, timestamps)
   - `memory_relations` table: task dependencies
   - `agent_activity` table: activity log
   - Add indexes on: agent_id, task_type, status, created_at, tags
   
   **For Shared Knowledge Pool (global):**
   - `knowledge` table: shared knowledge (id, title, content, category, source_agent_id, tags, priority, timestamps)
   - `knowledge_access` table: tracking which agents accessed which knowledge (knowledge_id, agent_id, accessed_at)
   - Add indexes on: category, tags, created_at, agent_id
   - Categories: system, project, workflow, lesson, general

3. **Build Memory API** (`memory.py` for task memory, `knowledge.py` for shared pool)
   
   **Task Memory API:**
   - `write_memory()` - Create memory entries
   - `read_memory()` - Query with filters
   - `update_memory()` - Update existing entries
   - `search_memory()` - Full-text search
   - `get_memory_stats()` - Statistics
   - `log_activity()` - Activity logging
   - Use thread-local connections for thread safety
   
   **Shared Knowledge API:**
   - `write_knowledge(title, content, category, source_agent_id, tags, priority)` - Add knowledge
   - `read_knowledge(agent_id, category, tags, limit)` - Read knowledge (tracks access)
   - `search_knowledge(query, agent_id, category)` - Search knowledge
   - `update_knowledge(knowledge_id, ...)` - Update existing knowledge
   - `delete_knowledge(knowledge_id)` - Remove knowledge
   - `get_knowledge_stats()` - Statistics including access patterns
   - `get_agent_knowledge_access(agent_id)` - Access history per agent

4. **Create Agent Wrapper** (`agent_memory.py`)
   ```python
   class AgentMemory:
       def __init__(self, agent_id, agent_name)
       def start_task(task_type, description, input_data, priority, tags)
       def complete_task(task_id, output_data, success=True)
       def fail_task(task_id, error)
       def search(query, limit=10)
       def check_similar_work(description)
   ```

5. **Migration from Task Memory to Knowledge Pool**
   
   If starting with task memory and need to migrate:
   
   ```python
   # migrate_to_knowledge.py
   from memory import read_memory
   from knowledge import write_knowledge
   
   memories = read_memory(limit=1000)
   for mem in memories:
       category = map_task_type_to_category(mem['task_type'])
       write_knowledge(
           title=f"{mem['agent_name']}: {mem['task_description'][:80]}",
           content=format_memory_as_knowledge(mem),
           category=category,
           source_agent_id=mem['agent_id'],
           source_agent_name=mem['agent_name'],
           tags=mem.get('tags', [mem['task_type'], mem['status']]),
           priority=mem.get('priority', 5)
       )
   ```
   
   Verify migration: all agents should see same knowledge count.

6. **Testing Strategy**
   - Unit tests: Basic CRUD operations
   - Integration tests: Multi-agent concurrent access
   - Real workflow simulation: Agent A → Agent B → Agent C
   - Thread safety validation
   - **Knowledge pool validation:** All agents read same count

7. **Production Deployment**
   - Deploy to `/usr/local/lib/hermes-shared-memory/`
   - Create `hermes_memory.py` import helper (expose both APIs)
   - Write README with integration patterns
   - Test with real agent (CLI agent first)
   - For knowledge pool: verify all agents see same entries

**Key Validations:**
- ✅ Thread-safe concurrent writes
- ✅ Cross-agent memory access
- ✅ Search functionality
- ✅ Task lifecycle tracking
- ✅ Duration calculation
- ✅ **Knowledge pool: All agents see same knowledge count**
- ✅ **Access tracking works correctly**

**Success Criteria for Phase 0:**
- All agents achieve 100% knowledge coverage (for shared knowledge pool)
- Zero fragmentation (fragmentation score = 0.000)
- Perfect access parity (parity score = 1.000)
- Query performance <10ms (p99)
- 100% migration success rate (if migrating from task memory)
- Statistical significance: p < 0.0001, effect size > 0.8

### Phase 1: Orchestrator Hub (60 min actual)

**Status:** ✅ Production Ready (2026-05-04)

**Objective:** Build centralized orchestration hub with REST API, WebSocket events, and real-time agent coordination.

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                  Hermes Orchestrator Hub                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────┐  │
│  │   REST API   │───▶│  EventBus    │───▶│   Redis     │  │
│  │  (FastAPI)   │    │  (Pub/Sub)   │    │  (Broker)   │  │
│  └──────────────┘    └──────────────┘    └─────────────┘  │
│         │                    │                             │
│         ▼                    ▼                             │
│  ┌──────────────┐    ┌──────────────┐                     │
│  │  WebSocket   │    │ Knowledge    │                     │
│  │  (Real-time) │    │    Sync      │                     │
│  └──────────────┘    └──────────────┘                     │
│         │                    │                             │
│         ▼                    ▼                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │            Orchestrator Core                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │  │
│  │  │TaskQueue │  │  Agent   │  │ HealthMonitor    │  │  │
│  │  │ (Redis)  │  │ Registry │  │                  │  │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Sub-phases:**

#### Phase 1A: Orchestrator Core (36 min)
1. **Config Module** (`orchestrator/config.py`)
   - Redis connection settings
   - Database paths
   - Channel names for pub/sub
   - Shared memory integration

2. **TaskQueue** (`orchestrator/task_queue.py`)
   - Redis-based task queue with priority support
   - Task statuses: pending, assigned, in_progress, completed, failed, cancelled
   - Priority levels: low (1), normal (5), high (8), critical (10)
   - Task assignment and lifecycle management

3. **AgentRegistry** (`orchestrator/agent_registry.py`)
   - SQLite-based agent tracking
   - Agent statuses: online, offline, busy, error
   - Capability registration
   - Heartbeat monitoring
   - Activity logging

4. **HealthMonitor** (`orchestrator/health_monitor.py`)
   - Redis health checks
   - Database health checks
   - Agent status monitoring
   - Queue metrics
   - System resource monitoring (optional with psutil)

5. **Orchestrator Core** (`orchestrator/orchestrator.py`)
   - Task submission and assignment
   - Agent registration and heartbeat
   - Task-to-agent matching based on capabilities
   - System status aggregation

6. **REST API** (`api.py`)
   - FastAPI application on port 8000
   - Basic endpoints: health, status, tasks, agents

#### Phase 1B: Redis Integration (4 min)
1. **EventBus** (`orchestrator/event_bus.py`)
   - Redis Pub/Sub event system
   - Event types: knowledge.*, task.*, agent.*, system.*
   - Pattern subscription support
   - Thread-safe event publishing
   - Background listener thread

2. **Event Publishers**
   - `KnowledgeEventPublisher`: knowledge.created/updated/deleted
   - `TaskEventPublisher`: task.submitted/assigned/started/completed/failed
   - `AgentEventPublisher`: agent.registered/online/offline/heartbeat

3. **KnowledgeSync** (`orchestrator/knowledge_sync.py`)
   - Integration with Phase 0 shared memory
   - Real-time knowledge updates
   - Search and query functionality
   - Sync statistics

#### Phase 1C: API Gateway (20 min)
1. **WebSocket Integration**
   - Real-time event streaming endpoint (`/ws`)
   - Connection manager for multiple clients
   - Event broadcasting to all connected clients

2. **Knowledge Endpoints**
   - `GET /knowledge` - List knowledge entries
   - `GET /knowledge/{id}` - Get specific entry
   - `GET /knowledge/search?q=query` - Search knowledge

3. **Complete API Surface**
   - Task management: submit, query, complete
   - Agent management: register, heartbeat, list
   - Knowledge access: list, get, search
   - System monitoring: health, status

**Key Technical Fixes:**

1. **Pattern Subscription with fnmatch**
   ```python
   # EventBus._handle_message needs pattern matching
   for pattern, callbacks in self.subscribers.items():
       if '*' in pattern or '?' in pattern:
           import fnmatch
           if fnmatch.fnmatch(channel, pattern):
               for callback in callbacks:
                   callback(event)
   ```

2. **Channel Decoding**
   ```python
   # Redis returns bytes, need to decode
   channel = message.get("channel") or message.get("pattern")
   if isinstance(channel, bytes):
       channel = channel.decode('utf-8')
   ```

3. **Thread-safe WebSocket Broadcasting**
   ```python
   # Store main event loop at startup
   main_loop = None
   
   @app.on_event("startup")
   async def startup_event():
       global main_loop
       main_loop = asyncio.get_event_loop()
   
   # Broadcast from background thread
   def broadcast_event(event):
       global main_loop
       if main_loop and main_loop.is_running():
           asyncio.run_coroutine_threadsafe(
               broadcast_event_async(event), 
               main_loop
           )
   ```

**Deployment:**
```bash
# Location
/usr/local/lib/hermes-orchestrator/

# Start
./start.sh

# Stop
./stop.sh

# Status
curl http://localhost:8000/status
```

**File Structure:**
```
/usr/local/lib/hermes-orchestrator/
├── orchestrator/
│   ├── __init__.py
│   ├── config.py              # Configuration
│   ├── task_queue.py          # Redis task queue
│   ├── agent_registry.py      # SQLite agent registry
│   ├── health_monitor.py      # Health monitoring
│   ├── event_bus.py           # Redis Pub/Sub
│   ├── knowledge_sync.py      # Knowledge pool sync
│   └── orchestrator.py        # Core orchestrator
├── api.py                     # FastAPI REST + WebSocket
├── start.sh                   # Startup script
├── stop.sh                    # Shutdown script
├── README.md                  # Documentation
└── db/
    └── orchestrator.db        # SQLite database
```

**Success Criteria:**
- ✅ REST API operational on port 8000
- ✅ WebSocket real-time events working
- ✅ Redis Pub/Sub event broadcasting
- ✅ Knowledge pool integration
- ✅ Task submission and assignment
- ✅ Agent registration and heartbeat
- ✅ Health monitoring functional

**Debugging & Verification:**

When verifying system health after deployment or bug fixes:

1. **Check API server process:**
   ```bash
   ps aux | grep -E "(uvicorn|api.py)" | grep -v grep
   netstat -tlnp | grep :8000
   ```

2. **Health endpoint analysis:**
   ```bash
   curl -s http://localhost:8000/health | python3 -m json.tool
   ```
   - Returns detailed component status even when `healthy: false`
   - Check individual components: redis, database, agents, queue, system
   - `agents.status: unhealthy` with 0 online agents is expected when no agents running

3. **Authentication requirements:**
   - `/health`, `/docs`, `/openapi.json` are public (no auth)
   - All other endpoints require API key via `X-API-Key` header or `Authorization: Bearer` header
   - Generate test key: `python3 manage_keys.py generate <agent-id>`
   - Test authenticated endpoint: `curl -H "X-API-Key: hma_..." http://localhost:8000/agents`

4. **Common bugs and fixes:**
   
   **Bug: TypeError in list_agents() - parameter mismatch**
   - Symptom: API returns "Internal Server Error", logs show `TypeError: Orchestrator.list_agents() got an unexpected keyword argument 'status'`
   - Root cause: API layer (`api.py`) calls `orchestrator.list_agents(status=..., capability=...)` but orchestrator method only accepts `online_only` parameter
   - Fix location: `orchestrator/orchestrator.py` not `api.py` (the bug is in the orchestrator layer)
   - Solution:
     ```python
     # In orchestrator/orchestrator.py
     def list_agents(self, status: Optional[AgentStatus] = None, 
                     capability: Optional[str] = None, 
                     online_only: bool = False) -> List[Dict]:
         """List all agents with optional filters."""
         agents = self.agent_registry.list_agents(status=status, online_only=online_only)
         
         # Filter by capability if provided
         if capability:
             agents = [a for a in agents if capability in a.capabilities]
         
         return [agent.to_dict() for agent in agents]
     ```
   - Verification:
     ```bash
     # Restart server
     cd /usr/local/lib/hermes-orchestrator && ./stop.sh && ./start.sh
     
     # Test with API key
     curl -H "X-API-Key: hma_..." http://localhost:8000/agents
     curl -H "X-API-Key: hma_..." "http://localhost:8000/agents?status=offline"
     curl -H "X-API-Key: hma_..." "http://localhost:8000/agents?capability=coding"
     ```

5. **Database inspection:**
   ```bash
   # Check agents
   sqlite3 db/orchestrator.db "SELECT agent_id, status, last_heartbeat FROM agents ORDER BY last_heartbeat DESC LIMIT 10;"
   
   # Check schema
   sqlite3 db/orchestrator.db ".schema agents"
   
   # List API keys
   python3 manage_keys.py list
   ```

6. **Log analysis:**
   ```bash
   tail -50 /var/log/hermes-orchestrator/api.log
   ```
   - Look for TypeError, HTTPException, or other errors
   - Authentication errors show as "401: API key required" or "Invalid API key"

### Phase 2: Agent Integration (70 min actual)

**Status:** ✅ Production Ready (2026-05-04)

**Objective:** Build Agent SDK, authentication system, and task execution framework for multi-agent coordination.

**Architecture:**
```
┌─────────────────────────────────────┐
│      Agent Instances (SDK)          │
│  ┌────────┐  ┌────────┐            │
│  │Agent 1 │  │Agent N │            │
│  └───┬────┘  └───┬────┘            │
│      │           │                 │
│      └───────┬───┘                 │
│              │ API Key Auth        │
└──────────────┼─────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    Orchestrator Hub                 │
│  ┌──────────┐  ┌──────────┐        │
│  │Auth      │→ │Rate      │        │
│  │Middleware│  │Limiter   │        │
│  └──────────┘  └──────────┘        │
│       │              │              │
│       ▼              ▼              │
│  ┌──────────┐  ┌──────────┐        │
│  │Task      │→ │Execution │        │
│  │Router    │  │Monitor   │        │
│  └──────────┘  └──────────┘        │
└─────────────────────────────────────┘
```

**Sub-phases:**

#### Phase 2A: Agent SDK & Client Library (30 min)

**Components:**

1. **Agent Client** (`sdk/agent_client.py`)
   - HTTP client using requests library
   - WebSocket client using websockets library
   - Auto-registration on startup
   - Heartbeat mechanism (30s interval, configurable)
   - Task polling mechanism (5s interval, configurable)
   - Event subscription & handling
   - Graceful shutdown with cleanup
   - Auto-reconnect with exponential backoff
   - Thread-safe operation

2. **Agent Base Class** (`sdk/agent_base.py`)
   - Abstract base class for agent implementations
   - Lifecycle hooks: `on_start()`, `on_stop()`, `on_task_received()`, `on_task_completed()`, `on_task_failed()`
   - Abstract method: `execute_task(task)` - must be implemented by subclass
   - Task execution interface with ThreadPoolExecutor
   - Error handling & reporting
   - Signal handlers (SIGINT, SIGTERM) for graceful shutdown
   - Concurrent task execution (configurable max workers)

3. **Agent Config** (`sdk/agent_config.py`)
   - Dataclass-based configuration
   - Environment variable support via `from_env()` classmethod
   - Validation with helpful error messages
   - Configuration fields:
     - `agent_id`, `agent_name`, `orchestrator_url` (required)
     - `api_key` (optional, for authentication)
     - `capabilities` (list of strings)
     - `metadata` (dict)
     - `heartbeat_interval`, `task_poll_interval`, `max_concurrent_tasks`, `task_timeout`
     - `enable_websocket`, `log_level`

4. **Task Executor** (`sdk/task_executor.py`)
   - ThreadPoolExecutor-based parallel execution
   - Timeout handling per task
   - Result reporting with callbacks
   - Error recovery
   - Task cancellation support
   - Active task tracking

5. **Exceptions** (`sdk/exceptions.py`)
   - `AgentSDKError` (base)
   - `ConnectionError`, `AuthenticationError`, `TaskExecutionError`
   - `ConfigurationError`, `RegistrationError`, `HeartbeatError`
   - `TaskFetchError`, `WebSocketError`

**Key Implementation Details:**

- **Payload Field Naming:** Agent registration uses `agent_name` not `name` in JSON payload to match API schema
- **Metadata Handling:** Always send `metadata` as dict, use `{}` if None to avoid validation errors
- **Thread Safety:** Use separate threads for heartbeat and WebSocket, with Event-based coordination
- **WebSocket Loop:** Run in separate thread with its own asyncio event loop
- **Graceful Shutdown:** Wait for active tasks to complete before stopping

**Example Agent:**
```python
from sdk import AgentBase, AgentConfig

class MyAgent(AgentBase):
    def execute_task(self, task):
        task_type = task.get("type")
        task_data = task.get("data", {})
        # Process task
        return {"result": "success"}
    
    def on_start(self):
        print(f"Agent {self.config.agent_id} starting...")
    
    def on_task_completed(self, task, result):
        print(f"Task {task['id']} completed: {result}")

config = AgentConfig.from_env("my-agent", "My Agent")
agent = MyAgent(config)
agent.run()  # Blocking
```

#### Phase 2B: Authentication & Authorization (20 min)

**Components:**

2. **Auth Manager** (`orchestrator/auth.py`)
   - SQLite-based API key storage (`data/auth.db`)
   - API key format: `key_<16-char-hex>` (key ID), SHA256 hash stored separately
   - **Note:** Documentation previously said `hma_<32-byte-urlsafe-token>` — this was incorrect. Actual implementation uses `key_` prefix with hex identifier.
   - SHA256 key hashing before storage
   - Key generation with optional expiration
   - Key validation (checks hash, expiration, revocation)
   - Key revocation
   - Last used timestamp tracking
   - Cleanup of expired keys

2. **Auth Middleware** (`orchestrator/middleware.py`)
   - FastAPI HTTP middleware
   - API key extraction from `X-API-Key` header or `Authorization: Bearer` header
   - Validates key on every request (except `/`, `/health`, `/docs`)
   - Adds `request.state.agent_id` for authenticated requests
   - Rate limiting per agent (100 requests/minute default)
   - Response headers: `X-RateLimit-Remaining`, `X-RateLimit-Limit`
   - Returns 401 for invalid/missing keys, 429 for rate limit exceeded

3. **Rate Limiter** (`orchestrator/middleware.py`)
   - Sliding window algorithm
   - Per-agent tracking
   - Configurable limits (requests per window)
   - Thread-safe with Lock
   - Automatic cleanup of old request timestamps

4. **Key Management CLI** (`manage_keys.py`)
   - `generate <agent_id> [--expires-in SECONDS]` - Generate new key
   - `list [--agent-id AGENT_ID]` - List keys
   - `revoke <key_id>` - Revoke key
   - `cleanup` - Remove expired keys
   - Formatted output with timestamps

**Integration with FastAPI:**
```python
from orchestrator.auth import AuthManager
from orchestrator.middleware import AuthMiddleware, RateLimiter

auth_manager = AuthManager()
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
auth_middleware = AuthMiddleware(auth_manager, rate_limiter)
app.middleware("http")(auth_middleware)
```

**Key Management:**
```bash
# Generate key
python3 manage_keys.py generate my-agent

# List all keys
python3 manage_keys.py list

# Revoke key
python3 manage_keys.py revoke key_abc123

# Cleanup expired
python3 manage_keys.py cleanup
```

### Phase 2C: Task Execution Framework

The Task Execution Framework includes Task Router, Execution Monitor, and Task Executor with routing strategies (Round-Robin, Least-Loaded, Capability-Match, Priority-Based). End-to-end tests passed for agent registration and task submission.

### Phase 2C Production Rollout (Agent Integration)

Integrate production agents (systemd-managed or Dockerized) with the orchestrator after core Phase 2C is complete.

#### Steps
1. **Generate Agent API Key**:
   - Navigate to orchestrator directory: `cd /usr/local/lib/hermes-orchestrator`
   - Run `python3 manage_keys.py generate <agent_id>` (valid subcommand, no `--name`/`--role` flags)
   - Save the generated key (e.g., `hma_4XRGfT-...`) securely, it is only shown once.

2. **Update Systemd Service (for systemd agents)**:
   - Service files are located in `/etc/systemd/system/` with `hermes-` prefix (e.g., `hermes-upshalternal.service`)
   - Use `sudo` to modify files (patch tool will refuse sensitive system paths)
   - For existing Hermes instances, consider using a **Bridge Agent pattern** (see `references/bridge-agent-pattern.md`) to keep the full Hermes Agent running while connecting to orchestrator.
   - Add two environment variables to the `[Service]` section:
     ```
     Environment="ORCHESTRATOR_URL=http://localhost:8000"
     Environment="ORCHESTRATOR_API_KEY=<generated_api_key>"
     ```
     **CRITICAL:** SDK reads API key from `ORCHESTRATOR_API_KEY` (see `sdk/agent_config.py` line 51). Using `HERMES_ORCHESTRATOR_KEY` will cause registration failures.

### Additional Pitfalls (from 2026-05-05 session)
1. **Wrong Key Generation Subcommand**: Use `python3 manage_keys.py generate <agent-id>` (not `create`) to generate new agent API keys. The `generate` subcommand is the correct one for new agents.
2. **Capability Mismatch**: Tasks remain pending if the task's `required_capability` does not match the agent's registered capabilities. Verify via:
   ```bash
   sqlite3 /usr/local/lib/hermes-orchestrator/db/orchestrator.db "SELECT agent_id, capabilities FROM agents;"
   ```
3. **Polling Connection Errors**: If bridge agents log `Connection aborted` errors:
   - Verify orchestrator API is running: `ps aux | grep "api.py" | grep -v grep`
   - Check Redis queue directly: `redis-cli llen tasks:pending` (health check queue counts may be inaccurate)
   - Confirm `ORCHESTRATOR_URL` is correct (default: `http://localhost:8000`)
4. **Enum Serialization Bug**: `TaskStatus`/`TaskPriority` enums stored as `TaskStatus.PENDING` (repr) instead of `pending` (value). Fix `to_dict()`:
   ```python
   # In task_queue.py Task.to_dict()
   "status": self.status.value if hasattr(self.status, 'value') else self.status,
   "priority": self.priority.value if hasattr(self.priority, 'value') else self.priority,
   ```
5. **Enum Deserialization Bug**: `from_dict()` didn't handle string-to-enum conversion. Fix:
   ```python
   # In task_queue.py Task.from_dict()
   elif key == 'status':
       if isinstance(value, str):
           if value.startswith('TaskStatus.'):
               # Handle "TaskStatus.PENDING" format
               deserialized[key] = TaskStatus(value.split('.')[-1])
           else:
               # Handle "pending" format
               deserialized[key] = TaskStatus(value)
   ```
6. **list_tasks() Iteration Bug**: Only iterated `task_keys[:limit]` instead of ALL keys. Fix by iterating all keys with early break:
   ```python
   for key in task_keys:
       if len(tasks) >= limit:
           break
       # ... process task
   ```
7. **Config Typo**: `Config.CHANNEL_EVENTS` (non-existent) used instead of `Config.CHANNEL_TASK_ASSIGNMENTS` in `task_queue.py` line 346. Causes 500 error on task assignment.
8. **Redis Task Status Format**: After fixing serialization, verify task status in Redis:
   ```bash
   redis-cli hgetall "task:<uuid>" | grep status
   # Should show: status = "pending" (not "TaskStatus.PENDING")
   ```

### Phase 2C: Agent Rollout Workflow
1. Generate API key: `cd /usr/local/lib/hermes-orchestrator && python3 manage_keys.py generate <agent-id>`
2. Use the generic bridge agent template at `templates/bridge_agent.py` (inherits SDK `AgentBase`)
3. Update systemd service with env vars:
   ```systemd
   Environment="ORCHESTRATOR_URL=http://localhost:8000"
   Environment="ORCHESTRATOR_API_KEY=<generated-key>"
   Environment="PYTHONPATH=/usr/local/lib/hermes-orchestrator:/path/to/bridge/script"
   ```
4. Reload/restart: `systemctl daemon-reload && systemctl enable <agent>-bridge && systemctl start <agent>-bridge`
5. Verify: `python3 manage_keys.py list`

*Reusable generic bridge agent template available at `templates/bridge_agent.py`*
   - Reload systemd: `sudo systemctl daemon-reload`
   - Restart the agent: `sudo systemctl restart <service-name>`

3. **Dockerized Agents**:
   - Add `ORCHESTRATOR_URL` and `ORCHESTRATOR_API_KEY` to the `environment` section of the Docker Compose file
   - Use `ORCHESTRATOR_API_KEY` (not `HERMES_ORCHESTRATOR_KEY`) - see SDK `agent_config.py` line 51
   - Recreate the container: `docker-compose up -d <service-name>`

#### Pitfalls
- **manage_keys.py Syntax**: Do NOT use `create` subcommand or `--name`/`--role` arguments; only `generate <agent_id>` is valid.
- **Environment Variable Name**: The SDK reads API key from `ORCHESTRATOR_API_KEY` environment variable (`sdk/agent_config.py` line 51). Using `HERMES_ORCHESTRATOR_KEY` will cause registration failures (HTTP 500). Always verify with `grep "ORCHESTRATOR_API_KEY" sdk/agent_config.py`.
- **Port Conflicts**: If the agent fails to start with "address already in use", check conflicting processes with `sudo lsof -i :<port>` and kill them (e.g., `sudo kill -9 <pid>` for socat processes).
- **Service File Naming**: Hermes systemd services use `hermes-<agent-id>.service` format, not `<agent-id>.service`.

#### Verification
- Check service status: `systemctl status <service-name> --no-pager`
- List registered keys: `python3 manage_keys.py list` (confirm agent ID is listed with "Active" status)

1. **Task Router** (`orchestrator/task_router.py`)
   - Intelligent task assignment to agents
   - Load balancing strategies:
     - `ROUND_ROBIN` - Distribute evenly
     - `LEAST_LOADED` - Assign to agent with fewest active tasks
     - `CAPABILITY_MATCH` - Match task requirements to agent capabilities
     - `PRIORITY_BASED` - High priority → least loaded, normal → round robin
   - Agent load tracking (active tasks, max tasks, capabilities)
   - Agent availability checking
   - Capability-based filtering
   - Load percentage calculation
   - Statistics and metrics

2. **Execution Monitor** (`orchestrator/execution_monitor.py`)
   - Task execution metrics tracking
   - Per-task metrics: start time, duration, status, error
   - Per-agent metrics: tasks completed/failed, success rate, avg duration
   - System-wide metrics: active tasks, total completed/failed, success rate
   - Timeout detection
   - Historical data (configurable max history size)
   - Thread-safe with Lock

3. **Task Executor** (in SDK, see Phase 2A)
   - Used by agents to execute tasks with timeout and error handling

**Task Router Usage:**
```python
from orchestrator.task_router import TaskRouter, RoutingStrategy

router = TaskRouter(strategy=RoutingStrategy.LEAST_LOADED)

# Register agents
router.register_agent("agent-1", capabilities=["task1", "task2"], max_tasks=5)
router.register_agent("agent-2", capabilities=["task2", "task3"], max_tasks=3)

# Select agent for task
agent_id = router.select_agent(
    task={"type": "task2", "priority": "high"},
    required_capability="task2"
)

# Update load after assignment
router.increment_load(agent_id)

# After task completion
router.decrement_load(agent_id)

# Get statistics
stats = router.get_stats()
```

**Execution Monitor Usage:**
```python
from orchestrator.execution_monitor import ExecutionMonitor

monitor = ExecutionMonitor(max_history=1000)

# Track task execution
monitor.start_task("task-123", "agent-1")
# ... task executes ...
monitor.complete_task("task-123", status="completed")

# Get metrics
task_status = monitor.get_task_status("task-123")
agent_metrics = monitor.get_agent_metrics("agent-1")
system_metrics = monitor.get_system_metrics()

# Check for timeouts
timed_out = monitor.check_timeouts(timeout=300)
```

**File Structure:**
```
/usr/local/lib/hermes-orchestrator/
├── sdk/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── agent_config.py
│   ├── agent_client.py
│   ├── agent_base.py
│   └── task_executor.py
├── orchestrator/
│   ├── auth.py
│   ├── middleware.py
│   ├── task_router.py
│   └── execution_monitor.py
├── examples/
│   ├── example_agent.py
│   └── worker_agent.py
├── manage_keys.py
├── test_sdk.sh
├── test_auth.py
├── test_e2e.py
└── data/
    └── auth.db
```

**Success Criteria:**
- ✅ Agent SDK can connect to Orchestrator
- ✅ Agent can register with API key
- ✅ Agent can send heartbeat
- ✅ Agent can fetch and execute tasks
- ✅ Authentication working (API keys)
- ✅ Rate limiting working (100/min)
- ✅ Task routing working (4 strategies)
- ✅ Load balancing working
- ✅ Execution monitoring working
- ✅ End-to-end workflow tested

**Environment Variables for Agents:**
```bash
ORCHESTRATOR_URL="http://localhost:8000"
ORCHESTRATOR_API_KEY="hma_..."
AGENT_CAPABILITIES="task1,task2,task3"
AGENT_META_VERSION="1.0.0"
HEARTBEAT_INTERVAL="30"
TASK_POLL_INTERVAL="5"
MAX_CONCURRENT_TASKS="5"
TASK_TIMEOUT="300"
ENABLE_WEBSOCKET="true"
LOG_LEVEL="INFO"
```

### Incident Detection & Alerting (DIM-08, 2026-05-05)
**Objective:** Auto-detect unhealthy components and post incidents to SKP with `#incident #alert` tags.

**Implementation Steps:**
1. **Create Detection Script** at `/usr/local/lib/hermes-orchestrator/scripts/incident_detector.sh` (see `scripts/incident_detector.sh`):
   ```bash
   #!/bin/bash
   API_URL="http://localhost:8000"
   API_KEY="<dashboard-api-key>"
   HEALTH_ENDPOINT="/health"
   TASK_ENDPOINT="/tasks"
   
   HEALTH_RESPONSE=$(curl -s "${API_URL}${HEALTH_ENDPOINT}")
   
   if [[ "$HEALTH_RESPONSE" == *"\"status\":\"unhealthy\""* ]]; then
       UNHEALTHY=$(echo "$HEALTH_RESPONSE" | grep -o '"status":"unhealthy"' -B 2 | grep '"[^"]*"' | head -1 | tr -d '"')
       INCIDENT_DESC="Incident detected: $UNHEALTHY is unhealthy"
       
       curl -s -X POST "${API_URL}${TASK_ENDPOINT}" \
           -H "X-API-Key: ${API_KEY}" \
           -H "Content-Type: application/json" \
           -d "{
               \"task_type\": \"incident\",
               \"description\": \"${INCIDENT_DESC}\",
               \"priority\": \"critical\",
               \"tags\": [\"incident\", \"alert\", \"auto-detected\"],
               \"metadata\": {\"source\": \"incident-detector\", \"health_check\": ${HEALTH_RESPONSE}}
           }" > /dev/null
       
       echo "[$(date)] Incident posted: $INCIDENT_DESC"
   else
       echo "[$(date)] All systems healthy"
   fi
   ```
   - Make executable: `chmod +x /usr/local/lib/hermes-orchestrator/scripts/incident_detector.sh`

2. **Add Cron Job** (every 5 minutes):
   ```bash
   (crontab -l -u root 2>/dev/null; echo "*/5 * * * * /usr/local/lib/hermes-orchestrator/scripts/incident_detector.sh >> /var/log/hermes-incidents.log 2>&1") | crontab -u root -
   ```
   - Verify: `crontab -l -u root | grep incident`

**Pitfalls:**
- **Health endpoint format:** Check actual JSON structure from `curl http://localhost:8000/health` – component status is nested under `checks.*.status`, not top-level.
- **API key permissions:** Use a key with write access to `/tasks` (e.g., dashboard or infra key).
- **Cron persistence:** Always verify cron job is added correctly; `crontab -l` output must show the new entry.

### SOTK Label Customization (DIM-06, 2026-05-05)
**Objective:** Update `vpsoctl` status output to reflect SOTK roles (Presiden, CTO, COO, CMO, CDO) alongside Coordinator labels.

**Implementation Steps:**
1. **Edit `/usr/local/bin/vpsoctl`** to add role labels:
   - Core Infrastructure cluster: Add `🏷️ CTO: hermes-Infrastructure (9121)` before Coordinator line
   - Development cluster: Add `🏷️ COO: hermes-builder (9122)` before Coordinator line
   - Communication cluster: Add `🎖️ Presiden: hermes-c-suite (9133)` and `🏷️ CMO: hermes-plaza (9123)` before Coordinator line
   - Domain cluster: Add `🏷️ CDO: hermes-pendidikan (9138)` before Coordinator line

2. **Verify:** Run `vpsoctl status` and confirm labels appear.

**Pitfalls:**
- **Preserve Coordinator labels:** Keep 📌 Coordinator lines intact for backward compatibility.
- **Port alignment:** Ensure role assignments match actual agent ports (e.g., CTO = 9121, COO = 9122).

### Phase 2D: Tag-Based Routing (2026-05-05)

**Objective:** Add tag-based routing to task queue for fine-grained task assignment and coordination.

**Implementation Steps:**

1. **Update Task class** (`orchestrator/task_queue.py`):
   - Add `tags: List[str] = None` parameter to `__init__`
   - Store as `self.tags = tags or []`
   - Update `to_dict()`: include `"tags": self.tags`
   - Update `from_dict()`: deserialize tags from JSON string if needed (handle both string and list formats)

2. **Update TaskQueue methods** (`orchestrator/task_queue.py`):
   - `submit_task()`: add `tags: Optional[List[str]] = None` parameter, pass to Task constructor
   - `list_tasks()`: add `tags: Optional[List[str]] = None` parameter, filter tasks that have at least one matching tag (use `any(tag in task.tags for tag in tags)`)

3. **Update Orchestrator wrapper** (`orchestrator/orchestrator.py`):
   - `submit_task()`: pass `tags` parameter to `task_queue.submit_task()`
   - `list_tasks()`: pass `tags` parameter to `task_queue.list_tasks()`

4. **Update API endpoints** (`api.py`):
   - `TaskSubmitRequest`: add `tags: Optional[List[str]] = None` field
   - `submit_task()` endpoint: pass `request.tags` to `orchestrator.submit_task()`
   - `list_tasks()` endpoint: add `tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)")` parameter, parse comma-separated string to list, pass to `orchestrator.list_tasks()`

**Pitfalls:**
- **Forgetting to update all layers:** Tags must be added to Task class, TaskQueue, Orchestrator, and API. Missing any layer causes 500 errors.
- **Wrapper method sync:** Always update `Orchestrator` wrapper methods in `orchestrator/orchestrator.py` when modifying `TaskQueue` methods to avoid silent parameter loss (e.g., adding `tags` to `submit_task()` in TaskQueue but not in Orchestrator wrapper).
- **Serialization:** When storing task data in Redis, tags must be JSON-serialized. In `to_dict()`, include tags as list. In `from_dict()`, handle both JSON string and list formats.
- **API query parameter:** Tags in query string are comma-separated, need to parse into list in endpoint.
- **Filter logic:** `list_tasks()` with tags should return tasks that have at least one matching tag.
- **Redis serialization:** In `submit_task()`, when serializing task to Redis, ensure tags are JSON-encoded if they are a list.

**Testing:**
```bash
# Submit task with tags
curl -X POST "http://localhost:8000/tasks" \
  -H "X-API-Key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"task_type": "test", "description": "Test", "tags": ["infra", "urgent"]}'

# Query by tags
curl "http://localhost:8000/tasks?tags=infra" -H "X-API-Key: <key>"
curl "http://localhost:8000/tasks?tags=infra,urgent" -H "X-API-Key: <key>"
```

**Success Criteria:**
- ✅ Tasks can be submitted with tags
- ✅ Tags are stored and retrieved correctly in Redis
- ✅ Filtering by tags works (single and multiple tags)
- ✅ Integration with existing task queue and API
- ✅ Orchestrator wrapper methods pass tags correctly

### Phase 3: Workstation Command Center (Completed 2026-05-05)

**⚠️ Phase Numbering Confusion:** This "Phase 3" is the **Workstation Nginx Setup**, NOT the original Phase 3 from FASE2_COMPLETE.md. The original Phase 3 "Advanced Features" includes:
- Agent plugins & extensions
- Custom task types & handlers  
- Workflow orchestration
- Agent collaboration & communication
- Resource scheduling & optimization
- Agent auto-scaling

**Status as of 2026-05-05:** Those "Advanced Features" (original Phase 3) are **NOT YET IMPLEMENTED**.

**Objective:** Build centralized web-based command center for monitoring and managing all Hermes agents, avoiding Docker networking timeouts via host-level Nginx proxy.

**Architecture:**
```
workstation.upshalter.com/hermes/ (Base Path)
├── /                          → Static Dashboard (HTML/JS/CSS)
├── /workspace/               → Proxy to Hermes Workspace (:3000)
├── /kanban/                  → Proxy to Kanban Board (:3000)
├── /api/*                    → Proxy to Orchestrator Hub (:8000) with API key injection
└── /ws                       → WebSocket Proxy to Orchestrator (:8000)
```

**Key Features:**
1. **Path-Based Namespace:** All Hermes ecosystem under `/hermes/` for clear separation.
2. **Nginx API Key Injection:** API keys are added by Nginx proxy headers (not exposed to browsers).
3. **Docker Timeout Fix:** Bypasses `host.docker.internal` networking issues by proxying directly to `127.0.0.1` on the host.
4. **Static Dashboard:** Lightweight HTML/JS dashboard fetching data from `/hermes/api/*`.
5. **Shared Knowledge Pool (SKP) Integration:** Documentation saved to SKP via direct SQLite insert (see `references/skp-direct-insert.md`).

**Nginx Configuration:**
- Template available at `templates/workstation-hermes-nginx.conf`
- Critical: Add `X-API-Key` header in `/hermes/api/` location block to avoid exposing keys.
- WebSocket support for real-time updates.
- **Path Rewriting:** Use `rewrite ^/hermes/api(/.*)$ $1 break;` to strip `/hermes/` prefix before proxying.

**Pre-Deployment Resource Check (Phase 3 Readiness):**
Verify VPS resources are sufficient before deployment:
```bash
# Check available RAM (need ≥4GB)
free -h | grep Mem | awk '{print "Available RAM: " $7}'
# Check available disk space (need ≥50GB)
df -h / | tail -1 | awk '{print "Available Disk: " $4}'
# Check CPU load (need <0.5 average)
uptime | awk -F'load average:' '{print "Load Average: " $2}'
```

**Deployment Steps (Updated 2026-05-05):**
1. (Optional) If Nginx config for `workstation.upshalter.com` is not present: Create from template `cp templates/workstation-hermes-nginx.conf /etc/nginx/sites-available/workstation-upshalter` (Existing Upshalter VPS already has this config with correct `/hermes/` alias, `/hermes/api/` proxy, and `/hermes/ws` WebSocket support)
2. Create documentation and Phase 3 dashboard directories:
   ```bash
   mkdir -p /var/www/workstation/hermes/workforce
   ```
3. Deploy public documentation to root `/hermes/`:
   ```bash
   cp /path/to/documentation-index.html /var/www/workstation/hermes/index.html
   ```
   *Note: Root `/hermes/` should be static documentation about the Upshalter Workstation, not the real-time dashboard*
4. Deploy Phase 3 Workforce Dashboard to `/hermes/workforce/`:
   ```bash
   cp /root/Konsep\ Workforce/hermes-workforce.html /var/www/workstation/hermes/workforce/index.html
   ```
   *Note: `hermes-workforce.html` already has correct `API_BASE = '/hermes/api'` and dynamic `WS_URL` pointing to `/hermes/ws`*
5. (If Nginx config was modified) Test config: `nginx -t`
6. (If Nginx config was modified) Reload Nginx: `nginx -s reload`
7. Verify all endpoints:
   ```bash
   curl -s -o /dev/null -w "Docs: %{http_code}\n" https://workstation.upshalter.com/hermes/
   curl -s -o /dev/null -w "Dashboard: %{http_code}\n" https://workstation.upshalter.com/hermes/workforce/
   curl -s -o /dev/null -w "API: %{http_code}\n" https://workstation.upshalter.com/hermes/api/agents -H "X-API-Key: <your-api-key>"
   ```

**Pitfalls:**
1. **Docker Networking Timeout:** Containers cannot reach `host.docker.internal:8000` reliably. Fix: Use Nginx proxy to `127.0.0.1:8000` on the host.
2. **Docker Agent Heartbeat 422 Error:** Bridge scripts missing `Content-Type: application/json` header cause 422 Unprocessable Entity. Fix in bridge script:
   ```bash
   send_heartbeat() {
       curl -s -X POST "$ORCHESTRATOR_URL/agents/heartbeat" \
           -H "X-API-Key: $ORCHESTRATOR_API_KEY" \
           -H "Content-Type: application/json" \
           -d "{\"agent_id\": \"$AGENT_ID\"}"
   }
   ```
   Verify: `journalctl -u hermes-orchestrator | grep "422"` should show no errors.
3. **SKP API Returns "Not Found"**: Orchestrator requires entries in `knowledge_access` table for API to return knowledge entries. After inserting into `knowledge` table:
   ```bash
   sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db \
     "INSERT INTO knowledge_access (knowledge_id, agent_id, agent_name, accessed_at) \
      VALUES (<id>, 'infra', 'Infra Hermes Agent', unixepoch());"
   ```
   Restart Orchestrator after: `sudo systemctl restart hermes-orchestrator`
2. **API Key Exposure:** Never include API keys in client-side JavaScript. Always inject via Nginx proxy headers.
3. **Path Rewriting:** Ensure `rewrite` rules correctly strip `/hermes/` prefix for proxied services.
4. **WebSocket Proxy:** Requires `Upgrade` and `Connection` headers set correctly in Nginx.
5. **SKP API Access:** `knowledge_sync.py` may query wrong table (`memory` instead of `knowledge`) and use wrong columns in search. Ensure functions `get_knowledge_entry()`, `list_knowledge_entries()`, and `search_knowledge()` reference `knowledge` table and columns `title`, `content`, `tags`. See `references/skp-knowledge-sync-fix.md`.

8. **Documentation vs Dashboard Separation:** Do not overwrite the root `/hermes/index.html` (public documentation) with the Phase 3 real-time dashboard. Deploy documentation to root `/hermes/`, and the Phase 3 dashboard to `/hermes/workforce/` subpath.

**Success Criteria:**
- ✅ `/hermes/` documentation (static HTML) returns 200 OK
- ✅ `/hermes/workforce/` Phase 3 dashboard returns 200 OK
- ✅ `/hermes/api/agents` returns agent list (with Nginx-injected API key)
- ✅ `/hermes/workspace/` proxies to Hermes Workspace (:3000)
- ✅ `/hermes/kanban/` proxies to Kanban Board (:3000)
- ✅ All 5 Tier-1 agents + 2 Tier-2 agents visible in dashboard
- ✅ Documentation saved to SKP (verify via `sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db "SELECT * FROM knowledge WHERE category='documentation';"`)

**SKP Integration:**
- When API endpoint `POST /knowledge` is unavailable, insert directly into SQLite:
  ```bash
  sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db "INSERT INTO knowledge (title, content, category, source_agent_id, source_agent_name, tags, priority, created_at, updated_at) VALUES (...);"
  ```
- **CRITICAL Pitfall:** Orchestrator requires entries in `knowledge_access` table for API to return them. After inserting into `knowledge`, you MUST also insert into `knowledge_access`:
  ```bash
  sqlite3 /usr/local/lib/hermes-shared-memory/db/memory.db "INSERT INTO knowledge_access (knowledge_id, agent_id, agent_name, accessed_at) VALUES (<id>, 'infra', 'Infra Hermes Agent', unixepoch());"
  ```
- See `references/skp-direct-insert.md` for full procedure.
- Restart Orchestrator after direct SQLite inserts: `sudo systemctl restart hermes-orchestrator`
- If API returns "Knowledge entry not found" despite correct `knowledge_access`, verify `knowledge_sync.py` uses `knowledge` table and correct columns (title, content, tags). See `references/skp-knowledge-sync-fix.md`.

## Phase 3: Advanced Features (2026-05-06)

**Objective:** Add DAG workflows, agent auto-scaling, and distributed tracing to the multi-agent orchestration system.

**Status:** ✅ Implemented

### 3.1 DAG Workflows
- Task model extended with `dependencies` and `workflow_id` fields
- Redis structures: `hermes:dag:blocked_tasks` (set), `hermes:dag:dependents:{task_id}` (set)
- Key methods in TaskQueue: `_get_dependents()`, `_activate_task()`, `_process_dependents()`
- Flow: Task with deps → blocked → on completion of dependency → automatically unblocked and queued
- See `references/phase3-implementation.md` for code snippets and test script

### 3.2 Agent Auto-scaling
- Monitoring script: `/usr/local/lib/hermes-orchestrator/auto_scaling.py`
- Threshold-based: scale out if queue > 10, scale in if queue < 2
- Tracks active agents via AgentRegistry
- Prints recommendations (actual scaling requires systemd/Docker integration)

### 3.3 Distributed Tracing
- OpenTelemetry integrated into FastAPI (`api.py`)
- Packages: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`
- ConsoleSpanExporter for initial testing (ready for Jaeger/Tempo)
- See `references/phase3-implementation.md` for setup code

**Success Criteria:**
- ✅ Tasks with dependencies properly blocked until dependencies complete
- ✅ Task completion automatically triggers dependent task activation
- ✅ Queue depth monitoring functional
- ✅ API tracing capture with OpenTelemetry

See `references/phase3-implementation.md` for full implementation details.

## External Tool Integrations

### OpenSwarm (Local Multi-Agent Orchestrator)
Local path: `/root/openswarm` (already cloned from https://github.com/openswarm-ai/openswarm.git)

**Key Features Relevant to Hermes Setups (Senator Pentahelix):**
- **Spatial Dashboard**: Infinite canvas to monitor all agents (5 Senators + Kurator) in real-time
- **Persistent Agent History**: Task history survives restarts (fixes task loss from Celery restarts)
- **Human-in-the-Loop**: Approve/deny agent tool calls (useful for Kurator before sending subscriber reports)
- **Agent Modes**: Custom system prompts per domain (akademisi, bisnis, etc.)
- **MCP & Skills Library**: Syncs with `~/.hermes/skills/` (consistent with Hermes ecosystem)
- **Cost Tracking**: Monitor API usage per agent session (critical for OpenRouter free tier)

**Integration Steps (Senator Pentahelix):**
1. Start OpenSwarm backend: `bash /root/openswarm/backend/run.sh` (runs on port 8324)
2. Define Senator agent templates with domain-specific prompts (e.g., `senator-akademisi` with prompt for riset akademisi)
3. Use OpenSwarm dashboard to monitor Senator cycles, task status, and rate limit usage
4. Configure Kurator as a custom agent mode with prompt to consolidate SKP entries into reports

See `references/openswarm-integration.md` for detailed feature breakdown and setup steps.

## Integration Pattern

### Task Memory (Agent-Specific)

For tracking agent's own tasks:

```python
import sys
sys.path.insert(0, '/usr/local/lib/hermes-shared-memory')

from hermes_memory import AgentMemory

# Initialize once at startup
memory = AgentMemory("agent-id", "Agent Name")

# When handling a task
def handle_task(description, data):
    # Check past work
    similar = memory.check_similar_work(description)
    
    # Start tracking
    task_id = memory.start_task(
        task_type="your_type",
        description=description,
        input_data=data,
        priority=8,
        tags=["tag1", "tag2"]
    )
    
    try:
        result = do_work(data)
        memory.complete_task(task_id, output_data=result)
        return result
    except Exception as e:
        memory.fail_task(task_id, str(e))
        raise
```

### Shared Knowledge Pool (Global)

For reading/writing knowledge accessible to all agents:

```python
import sys
sys.path.insert(0, '/usr/local/lib/hermes-shared-memory')

from hermes_memory import read_knowledge, write_knowledge, search_knowledge

AGENT_ID = "my-agent-id"
AGENT_NAME = "My Agent"

# Read all knowledge (every agent sees the same entries)
def get_context():
    knowledge = read_knowledge(
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        limit=50
    )
    return knowledge

# Search for specific knowledge
def find_deployment_info():
    results = search_knowledge(
        query="docker deployment",
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        limit=10
    )
    return results

# Filter by category
def get_workflows():
    workflows = read_knowledge(
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        category="workflow",
        limit=20
    )
    return workflows

# Write new knowledge (immediately available to all agents)
def save_lesson_learned(title, lesson):
    knowledge_id = write_knowledge(
        title=title,
        content=lesson,
        category="lesson",
        source_agent_id=AGENT_ID,
        source_agent_name=AGENT_NAME,
        tags=["lesson-learned", "troubleshooting"],
        priority=7
    )
    return knowledge_id

# Example: Agent learns something and shares it
def handle_error_and_learn(error_msg, solution):
    # Save for all agents
    write_knowledge(
        title=f"Solution: {error_msg[:60]}",
        content=f"Error: {error_msg}\n\nSolution: {solution}",
        category="lesson",
        source_agent_id=AGENT_ID,
        source_agent_name=AGENT_NAME,
        tags=["error", "solution"],
        priority=8
    )
```

**When to use which:**
- **Task Memory:** Track your own work history, task lifecycle, agent-specific state
- **Knowledge Pool:** Share insights, lessons, procedures, configurations that benefit all agents

### Ingesting External Knowledge into SKP
When adding external structured/unstructured knowledge (e.g., thesis lists, research datasets) to the Shared Knowledge Pool for all Hermes agents to access:
1. **Create structured storage**: Use `/root/.hermes/knowledge/` (shared via volume mount to all agents). Always create subdirs first with `mkdir -p /root/.hermes/knowledge/<subdir>` to avoid `FileNotFoundError`.
2. **Parse to structured formats**: Convert raw text/data to JSON (for programmatic access) and CSV (for tabular queries). Include consistent fields: id, main_category, sub_category, title, author, supervisor, degree, year, keywords, source.
3. **Insert into SKP DB**: Use sqlite3 to add a dedicated table to `/root/.hermes/shared_knowledge_pool.db`. Example table: `romi_theses` with fields matching the structured data.
4. **Update memory**: Add the new knowledge source to the memory tool so all future sessions are aware.
5. **Pitfall**: Never assume target directories exist under `/root/.hermes/` — always run `mkdir -p` first before writing files.

Example workflow (Romi Satria Wahono Thesis List, 83 entries):
- Created `/root/.hermes/knowledge/romi-wahono-theses.json` and `.csv`
- Parsed raw text into structured JSON with fields: id, main_category, sub_category, title, author, supervisor, degree, program, university, year, keywords, source
- Inserted into `romi_theses` table in `/root/.hermes/shared_knowledge_pool.db`
- Updated memory to reflect new knowledge source

## Deployment Considerations

**For Docker agents:**
- Mount `/usr/local/lib/hermes-shared-memory` as volume with **read-write** access
- Add to docker-compose.yml volumes section:
  ```yaml
  volumes:
    - /usr/local/lib/hermes-shared-memory:/usr/local/lib/hermes-shared-memory:rw
  ```
- **Critical:** Use `:rw` not `:ro` — SQLite needs write access to directory for lock files
- After updating docker-compose.yml, recreate containers (not just restart):
  ```bash
  docker compose down
  docker compose up -d
  ```
- Verify write access inside container:
  ```bash
  docker exec <container> touch /usr/local/lib/hermes-shared-memory/db/test.txt
  ```

**For Systemd agents:**
- Already have access to `/usr/local/lib`
- Just add import and restart service

**Database location:**
- `/usr/local/lib/hermes-shared-memory/db/memory.db`
- All agents share this single database
- Automatic initialization on first import

**Database permissions for multi-container access:**
```bash
chmod 666 /usr/local/lib/hermes-shared-memory/db/memory.db
chmod 777 /usr/local/lib/hermes-shared-memory/db/
```
These permissions allow all containers (running as different users) to write to the shared database.

## Testing Checklist

Before proceeding to next phase:
- [ ] Unit tests pass (100%)
- [ ] Integration tests pass (concurrent access)
- [ ] Real workflow simulation successful
- [ ] Production deployment validated
- [ ] At least one real agent integrated
- [ ] Documentation complete

## Pitfalls

**Thread Safety:**
- Use thread-local connections for SQLite
- Test concurrent writes explicitly
- Don't share connection objects

**Phase0 Audit Bugs (2026-05-05):**
- **Endpoint mismatch:** `agent_client.py` polls `/tasks?agent_id=X` but `api.py` doesn't accept `agent_id` param → returns 422 or wrong tasks
- **Queue inconsistency:** Tasks stored as `task:<uuid>` hashes but NOT in `hermes:queue:tasks` list → agents can't fetch them
- **Health check inaccuracy:** `/health` reports "12 tasks in queue" but `redis-cli llen hermes:queue:tasks` returns 0
- **Fixes:** See `references/phase0-audit-bugs.md` for complete bug details and patches

**Docker Integration:**
- Shared memory must be accessible from containers
- Use volumes with `:rw` flag (not `:ro`) — SQLite needs write access to directory for lock files
- After changing docker-compose.yml volumes, must `docker compose down` then `up -d` (restart alone won't remount)
- Test cross-container memory access
- Verify write access: `docker exec <container> touch /usr/local/lib/hermes-shared-memory/db/test.txt`
- If getting "attempt to write a readonly database" error, check:
  1. Volume mounted with `:rw` not `:ro`
  2. Container was recreated after volume change (not just restarted)
  3. Database file permissions: `chmod 666 memory.db` and `chmod 777 db/`

**Performance:**
- Add indexes on frequently queried columns
- Keep memory entries lean (don't store huge blobs)
- Consider archiving old memories

**API Key Format Mismatch:**\n- Documentation says `hma_<32-byte-urlsafe-token>` but actual implementation uses `key_<16-char-hex>` for key ID\n- Fix: Auth manager (`orchestrator/auth.py`) generates keys with `key_` prefix, not `hma_`\n- When validating API issues, check actual key format in `data/auth.db` with: `sqlite3 data/auth.db \"SELECT * FROM api_keys;\"`\n- Don't assume documentation format is correct — verify against running system\n\n**Phase 0-2 Complete ≠ Production Integrated:**\n- Phase 0-2 "Production Ready" means the ORCHESTRATOR CODE is complete and tested\n- It does NOT mean production agents (hermes-dashboard, hermes-infra, etc.) are registered\n- After Phase 2 completion, you MUST still:\n  1. Generate API keys for each production agent: `python3 manage_keys.py generate <agent-id>`\n  2. Add `ORCHESTRATOR_URL` and `API_KEY` to agent environment (systemd/Docker)\n  3. Restart agents to trigger registration\n- Validation: `curl -H \"X-API-Key: <key>\" http://localhost:8000/agents` should show agents online\n\n**EventBus Pattern Subscription:**
- Redis Pub/Sub returns channel names as bytes, must decode to string
- Pattern matching (e.g., `hermes:*`) requires explicit fnmatch logic in message handler
- Don't rely on Redis pattern subscription alone—implement pattern matching in `_handle_message()`
- See `references/phase1-eventbus-fixes.md` for complete implementation

**WebSocket Broadcasting from Background Threads:**
- FastAPI runs in asyncio event loop, but EventBus listener runs in background thread
- Cannot use `asyncio.create_task()` from background thread—no event loop in that thread
- Solution: Store main event loop reference at startup, use `asyncio.run_coroutine_threadsafe()`
- Pattern:
  ```python
  main_loop = None  # Global
  
  @app.on_event("startup")
  async def startup():
      global main_loop
      main_loop = asyncio.get_event_loop()
  
  def broadcast_from_thread(event):
      if main_loop and main_loop.is_running():
          asyncio.run_coroutine_threadsafe(async_broadcast(event), main_loop)
  ```
- See `references/phase1-websocket-threading.md` for details

**Validation:**\n- Always test integration before building next phase\n- Validate with real agent workflows, not just synthetic tests\n- Ensure thread safety under concurrent load\n- **For knowledge pool: Verify all agents see same knowledge count**\n  ```bash\n  # Test script should show all agents with identical counts\n  python3 test_shared_knowledge.py\n  # Expected: All agents report same number of knowledge entries\n  ```\n\n**Production Integration Validation Pattern:**\nWhen checking if Phase 0-2 is "damaged" vs "not yet configured":\n1. **Check knowledge base** - Load the `multi-agent-orchestration` skill, review Phase status\n2. **Check session history** - Use `session_search` for "Phase 0", "Phase 1", "Phase 2" to confirm completion dates\n3. **Check actual code** - Verify bug fixes documented in skill are actually in the code\n4. **Check database** - `sqlite3 orchestrator.db "SELECT * FROM agents;"` to see if real agents registered\n5. **Check API keys** - `python3 manage_keys.py list` to verify key format matches docs\n6. **Distinguish damage from configuration gaps:**\n   - System damage: Code bugs, database corruption, API 500 errors from unpatched bugs\n   - Not configured: Phase complete but production agents not registered, missing `ORCHESTRATOR_URL`, API keys not distributed\n\n**Common confusion:** Phase 0-2 "Production Ready" means the CODE is ready, NOT that production agents are integrated. Agent registration is a SEPARATE step (configure `ORCHESTRATOR_URL` + API key, then restart agents).

**Celery + FastAPI Integration (2026-05-07):**

**AsyncResult Without App Context (CRITICAL)**
- Symptom: `AttributeError: 'DisabledBackend' object has no attribute '_get_task_meta_for'` or task results never resolve
- Cause: `AsyncResult(task_id)` without `app=celery` uses a default DisabledBackend
- Fix: Always pass the celery app instance: `AsyncResult(task_id, app=celery)`
- Location: In FastAPI route handlers that poll task results

**Celery Worker Concurrency + Free LLM Rate Limits**
- Symptom: All workers hit 429 simultaneously, tasks stall for minutes
- Cause: Default concurrency=4 all hitting free-tier LLM (8 req/min limit per key)
- Fix: Reduce concurrency to 2 for free-tier usage: `--concurrency=2`
- Fix: Use small fast free models (e.g., `liquid/lfm-2.5-1.2b-instruct:free`)
- Production: Top-up OpenRouter credits for reliable access

**Celery Task Registration — include path vs PYTHONPATH**
- Symptom: `NotRegistered: ['hermes.run']` in Redis task results
- Cause: `include=["src.tasks"]` but `PYTHONPATH=/app/src` means importable as `tasks`, not `src.tasks`
- Fix: Set `include=["tasks"]` (matching Python import path, not filesystem path)
- Rebuild required: `docker compose build api` after changing `celery_app.py`
- Restart required: Recreate (not just restart) both API and worker containers
- Verify: `docker exec worker sh -c "cd /app && PYTHONPATH=/app/src python3 -c 'from celery_app import celery; print([t for t in celery.tasks if \"hermes\" in t])'"`
- When using the `patch` action on files with identical repeated blocks (e.g., vpsoctl had 4 identical cluster status blocks), the patch will fail with "Found X matches for old_string"
- Solution: Provide more context in `old_string` to make it unique, or use `replace_all=true` only if all matches should be replaced
- Alternative: Rewrite the entire file with `write_file` instead of patching for files with non-unique sections

**Adding New Agent Instances (2026-05-05):**
- Do NOT chain service file creation and `systemctl daemon-reload` in a single heredoc — write service files first, then reload to avoid partial failures
- Port conflicts: Check with `lsof -i :<port>` before assigning new ports
- Naming consistency: Avoid corporate titles (COO/CTO/CMO) in service descriptions for easier debugging
- Docker port alignment: Use 9136+ for project-isolated Docker agents to align with systemd port range (9119-9135)
- vpsoctl update: Always update vpsoctl after adding new agents/ports to maintain accurate status output

## Documentation for Publication
**Documentation for Publication:**
- When documenting Phase 0 improvements for academic publication, collect comprehensive experimental data
- Create baseline measurements BEFORE migration (agent distribution, fragmentation score, access patterns)
- Create post-migration measurements AFTER migration (same metrics for comparison)
- Perform statistical significance testing (paired t-test, effect size, p-values)
- Document in structured format: BASELINE_DATA.txt, POST_MIGRATION_DATA.txt, COMPARATIVE_ANALYSIS.txt
- Write scientific paper following standard academic structure (Abstract, Introduction, Related Work, Methodology, Evaluation, Discussion, Conclusion)
- See `references/scientific-paper-methodology.md` for complete methodology
- See `references/research-paper-arxiv-workflow.md` for workflows integrating arXiv references into research papers.
- **Compiling Full 3-Layer Architecture Papers:**
  1. First check existing project folders for phase reports and data:
     - `/usr/local/lib/hermes-shared-memory/` (Phase 0 data, SCIENTIFIC_PAPER.txt, experimental-data/)
     - `/usr/local/lib/hermes-orchestrator/` (Phase 1/2 reports, FASE2_COMPLETE.md, data/auth.db)
  2. Create dedicated paper folder with subdirs: `data/`, `references/`, `figures/`
  3. Copy existing experimental data, phase reports, and baseline data to the folder
  4. Use `arxiv` skill to fetch additional references for Related Work (search: multi-agent orchestration, shared memory, collective intelligence)
  5. Structure paper with 3 layers corresponding to Phases 0 (Shared Knowledge), 1 (Event Coordination), 2 (Task Execution)
  6. Integrate metrics from all phases: coverage, fragmentation, latency, routing strategies, success rates

## Celery Task Registration — include path vs PYTHONPATH (2026-05-07)

**ERROR**: `NotRegistered: ['hermes.run']` — Celery worker doesn't register tasks
**CAUSE**: `celery_app.py` uses `include=["src.tasks"]` but container has `PYTHONPATH=/app/src`. Celery's `include` parameter uses Python import paths, not filesystem paths. When `PYTHONPATH=/app/src`, the module is importable as `from tasks import ...`, not `from src.tasks import ...`.
**FIX**: Set `include=["tasks"]` (matching the import path, not the filesystem path)
**REBUILD REQUIRED**: After changing `celery_app.py`, must rebuild Docker image: `docker compose build api`
**RESTART REQUIRED**: Must recreate (not just restart) both API and worker containers
**VERIFY**: `docker exec worker sh -c "cd /app && PYTHONPATH=/app/src python3 -c 'from celery_app import celery; print([t for t in celery.tasks if \"hermes\" in t])'"`
**NOTE**: This is a general Celery + Docker + PYTHONPATH interaction pattern, not specific to any one project.
- **Pitfall:** When compiling research papers from existing project phases, always verify phase reports and experimental data are already present in project directories before proposing additional data collection skills (e.g., data-science) — users often have completed data collection in prior phases.

For broader papers covering the full 3-layer architecture (Shared Knowledge Pool + Real-Time Event Coordination + Autonomous Task Execution), Phase 1 and 2 experimental data is also available:
- Phase 1 (Orchestrator Hub) data: `/usr/local/lib/hermes-orchestrator/README.md`, API endpoint performance metrics, Redis Pub/Sub event logs, WebSocket `/ws` latency records
- Phase 2 (Agent Integration) data: `/usr/local/lib/hermes-orchestrator/FASE2_COMPLETE.md`, `test_e2e.py` end-to-end results, `data/auth.db` API key metrics, SDK task execution success rates
- Retrieve all phases' data via `session_search` with queries like "fase 1", "fase 2", "orchestrator", "multi-agent"
- Example 3-layer architecture paper title: *"From Fragmented Memory to Collective Action: A Three-Layer Architecture for End-to-End Multi-Agent Orchestration with Shared Knowledge, Real-Time Event Coordination, and Autonomous Task Execution"*

**Architecture Decision:**
- If agents need true "hive mind" (all see same knowledge), use **Shared Knowledge Pool**
- If agents need individual task tracking with optional cross-agent visibility, use **Task Memory**
- Both can coexist: Task Memory for work tracking + Knowledge Pool for shared insights

## Success Metrics

**Phase 0:**
- Memory write/read latency < 10ms
- Concurrent access works without corruption
- Real agent can use memory successfully
- Search returns relevant results

**Full System:**
- Task distribution time < 100ms
- Agent coordination overhead < 5%
- Workflow execution reliability > 99%
- Cross-agent context sharing working

## Upshalter VPS Example
For a real-world 17-agent VPS setup (2026-05-05 updated):
- **Systemd Agents (14 services, native clones)**: dashboard (9119), upshalter (9120), Infrastructure (9121), builder (9122), plaza (9123), sandbox (9129), pool (9130), vpso (9131), internet (9132), c-suite (9133), operation (9134), api (9135), archivist, frontend, backend, workstation, flowforce
- **Docker Agents (3 containers, project-isolated)**: upshalternal (8645), loyx (9136), gamedev (9137) — ports aligned with systemd range (9136+ for Docker project agents)
- **Port Alignment Rule**: Systemd native agents use 9119-9135; Docker project-isolated agents use 9136+ to maintain adjacency
- **Shared Memory**: `/root/.hermes` mounted to all Docker agents with `:rw` access
- **Bridge Services**: All agents connect to Orchestrator via `ORCHESTRATOR_API_KEY`
- **vpsoctl**: Updated to reflect all new ports/services (run `vpsoctl status` to verify)
- **Full Config**: See `hermes-agent-ops` skill reference `upshalter-agent-configs.md`
- **Backup & Recovery**: Hourly SQLite backups via `scripts/hermes-backup.sh` cron job (see Phase 4)
- **Inter-Service Security**: Firewall rules for port 8000, API keys stored in `/etc/hermes/secrets/` (see Phase 4)

### Adding New Agent Instances
#### Systemd Native Agents (Recommended for core clones)
1. Create service file in `/etc/systemd/system/hermes-<name>.service`:
   ```ini
   [Unit]
   Description=VPSO Unit Upshalternal - <Name> (<port>)
   After=network.target
   
   [Service]
   Environment="HERMES_ALLOWED_ORIGINS=*"
   Type=simple
   User=root
   ExecStart=/usr/local/bin/hermes dashboard --host 0.0.0.0 --port <port> --no-open --insecure
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```
   - Port must be in 9119-9135 range
   - Use descriptive name without corporate titles (e.g., "Sandbox" not "COO Sandbox")
2. Reload systemd and start:
   ```bash
   systemctl daemon-reload
   systemctl enable --now hermes-<name>
   ```
3. Update vpsoctl to list the new port/service.

#### Docker Project-Isolated Agents (Recommended for external projects)
1. Assign port in 9136+ range (aligned with systemd)
2. Update docker-compose.yml with port mapping and extra_hosts if needed:
   ```yaml
   services:
     hermes-<name>:
       ports:
         - "<port>:3000"
       extra_hosts:
         - "host.docker.internal:host-gateway"
   ```
3. Recreate container:
   ```bash
   docker compose down && docker compose up -d hermes-<name>
   ```
4. Update vpsoctl to reflect new Docker port.

#### Verification
- Check service status: `systemctl status hermes-<name> --no-pager`
- Check Docker status: `docker ps | grep hermes-<name>`
- Verify HTTP 200: `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:<port>`
- Confirm vpsoctl: `vpsoctl status | grep <name>`

## Phase 4: Production Hardening (2026-05-05)

**Objective:** Secure and backup multi-agent orchestration infrastructure.

### 4.1 Backup & Recovery (Priority 1 - Critical)

**SQLite Databases to Backup:**
- `/usr/local/lib/hermes-orchestrator/db/orchestrator.db` (orchestrator state)
- `/usr/local/lib/hermes-orchestrator/data/auth.db` (API keys)
- `/root/.hermes/response_store.db` (agent responses)
- `/root/.hermes/kanban.db` (task board)
- `/root/.hermes/state.db` (agent state)

**Backup Script:**
- Location: `scripts/hermes-backup.sh` (in this skill's directory)
- Copies DBs to `/backup/hermes/` with timestamps
- Uses `sqlite3 .backup` for consistent backups (falls back to `cp` if sqlite3 missing)
- Retention: 7 days (auto-cleanup)
- Integrity check: Runs `PRAGMA integrity_check` on backups

**Cron Setup:**
```bash
# Copy script to ~/.hermes/scripts/ (required for cronjob tool)
mkdir -p ~/.hermes/scripts
cp scripts/hermes-backup.sh ~/.hermes/scripts/hermes-backup.sh
chmod +x ~/.hermes/scripts/hermes-backup.sh

# Create cron job (hourly)
# Use cronjob tool with no_agent=true, script=hermes-backup.sh
```

**Verification:**
```bash
# Test backup
bash ~/.hermes/scripts/hermes-backup.sh

# Check backups
ls -la /backup/hermes/

# Verify integrity
sqlite3 /backup/hermes/orchestrator-*.db "PRAGMA integrity_check;"
```

### 4.2 Inter-Service Security

**Problem:** Orchestrator binds to 0.0.0.0:8000 by default, API keys sent via HTTP plain text, inline API keys in systemd services.

**Mitigations:**

#### A. Firewall Rules (UFW)
Restrict port 8000 access to localhost and Docker bridge only:
```bash
# Deny external access
ufw deny 8000 comment 'Deny external access to orchestrator'

# Allow localhost
ufw allow from 127.0.0.1 to any port 8000 comment 'Allow localhost to orchestrator'

# Allow Docker bridge (default: 172.17.0.0/16)
ufw allow from 172.17.0.0/16 to any port 8000 comment 'Allow Docker bridge to orchestrator'

ufw reload
```

**Verify:**
```bash
ufw status numbered | grep 8000
```

#### B. Secrets Management
Move API keys from inline systemd service files to secure secrets directory:
```bash
# Create secrets directory
mkdir -p /etc/hermes/secrets
chmod 700 /etc/hermes/secrets

# Extract API keys from systemd services
for svc in dashboard infra upshalternal builder plaza; do
  key=$(grep ORCHESTRATOR_API_KEY /etc/systemd/system/hermes-${svc}-bridge.service | cut -d= -f2- | tr -d '"')
  echo "ORCHESTRATOR_API_KEY=$key" > /etc/hermes/secrets/bridge-${svc}.env
  chmod 600 /etc/hermes/secrets/bridge-${svc}.env
done
```

**Update Systemd Services:**
Replace inline `Environment="ORCHESTRATOR_API_KEY=..."` with `EnvironmentFile=...`:
```ini
# In /etc/systemd/system/hermes-<agent>-bridge.service
[Service]
EnvironmentFile=/etc/hermes/secrets/bridge-<agent>.env
# Remove the inline ORCHESTRATOR_API_KEY line
```

**Apply Changes:**
```bash
systemctl daemon-reload
systemctl restart hermes-*-bridge
```

#### C. Orchestrator Systemd Service (Critical - 2026-05-05)

**Problem:** Orchestrator was running via manual script (`start.sh`), NOT as systemd service. No auto-restart on crash.

**Solution:** Create systemd service with Redis dependency:

```ini
# /etc/systemd/system/hermes-orchestrator.service
[Unit]
Description=Hermes Multi-Agent Orchestrator
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/usr/local/lib/hermes-orchestrator
Environment="PYTHONPATH=/usr/local/lib/hermes-orchestrator"
ExecStartPre=/usr/bin/redis-cli ping
ExecStart=/usr/bin/python3 -m uvicorn api:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Deployment:**
```bash
systemctl daemon-reload
systemctl enable hermes-orchestrator.service
systemctl start hermes-orchestrator.service
systemctl status hermes-orchestrator.service
```

**Pitfalls:**
- **Port conflict:** Kill old orchestrator process before starting service: `kill $(pgrep -f "uvicorn api:app")`
- **ExecStartPre:** Uses `redis-cli ping` to verify Redis is ready before starting
- **Host binding:** Uses `127.0.0.1` (not `0.0.0.0`) for localhost-only access (see Firewall section)

#### D. Redis Persistence (Critical - 2026-05-05)

**Problem:** Redis had `appendonly no` and `aof_enabled:0`. Task queue would be LOST on Redis restart/crash.

**Solution:** Enable AOF persistence:

```bash
# Check current config
redis-cli CONFIG GET appendonly
redis-cli INFO persistence | grep aof_enabled

# Enable AOF
redis-cli CONFIG SET appendonly yes
redis-cli CONFIG SET appendfsync everysec
redis-cli CONFIG REWRITE  # Persist to redis.conf
```

**Verification:**
```bash
redis-cli CONFIG GET appendonly  # Should return "yes"
redis-cli INFO persistence | grep aof_enabled  # Should return "aof_enabled:1"
```

**Pitfalls:**
- **RDB only:** Default Redis config uses RDB snapshots (e.g., `save 3600 1`). Data from last hour is NOT saved without AOF.
- **CONFIG REWRITE:** Required to persist AOF setting across Redis restarts.
- **Task safety:** With AOF enabled, task queue survives Redis crashes.

#### E. API Key .env File Format Bug (2026-05-05)

**Problem:** Generated `.env` files had DOUBLE PREFIX:
```
ORCHESTRATOR_API_KEY=ORCHESTRATOR_API_KEY=hma_xxx  ← WRONG!
```

**Correct format:**
```
ORCHESTRATOR_API_KEY=hma_xxx  ← CORRECT
```

**Fix script:**
```bash
cd /etc/hermes/secrets
for name in dashboard infra upshalternal builder plaza; do
  key=$(grep -oP '(?<=ORCHESTRATOR_API_KEY=).*' bridge-${name}.key)
  echo "ORCHESTRATOR_API_KEY=$key" > bridge-${name}.env
done
chmod 600 *.env
```

**Pitfalls:**
- **Systemd EnvironmentFile=** reads the entire line, so `ORCHESTRATOR_API_KEY=ORCHESTRATOR_API_KEY=xxx` sends wrong value.
- **Verification:** `cat /etc/hermes/secrets/bridge-dashboard.env` should show single `ORCHESTRATOR_API_KEY=hma_...`

#### F. Optional: Bind Orchestrator to Localhost
For stronger isolation, modify the Orchestrator startup to bind to 127.0.0.1 instead of 0.0.0.0:
```bash
# Edit /usr/local/lib/hermes-orchestrator/start.sh
# Change --host 0.0.0.0 to --host 127.0.0.1
# Add Docker bridge IP (172.17.0.1) if needed for container access
```

**Pitfalls:**
- Docker containers need `extra_hosts: "host.docker.internal:host-gateway"` to reach 127.0.0.1 on host
- Binding to 127.0.0.1 only breaks external access (e.g., if Orchestrator needs to be accessed from other hosts)

### Agent Management CLIs (2026-05-05)
**Objective:** Provide CLI tools for adding new agents and rotating domain coordinators in VPSO orchestration.

#### 1. hermes-new-agent
- Location: `scripts/hermes-new-agent` (deployed to `/usr/local/bin/hermes-new-agent`)
- Usage: `hermes-new-agent --name <name> --port <port> --type [swarm|domain] --cluster <cluster>`
- Function: Automates systemd service creation, API key generation, and Orchestrator registration
- Prerequisites: `jq`, `systemctl`, Orchestrator API running on :8000

#### 2. hermes-rotate-coordinator
- Location: `scripts/hermes-rotate-coordinator` (deployed to `/usr/local/bin/hermes-rotate-coordinator`)
- Usage:
  - Check status: `hermes-rotate-coordinator --status [domain]`
  - Rotate coordinator: `hermes-rotate-coordinator --domain <domain> --new-coord <agent> --project <project>`
- Function: Manages coordinator rotation state in `/usr/local/lib/hermes-orchestrator/rotation_state.json`
- Policy: Per-project rotation for domain coordinators (user-controlled, per SOTK)
- Prerequisites: `jq`, `python3` with timezone support

#### Pitfalls
- **State file dependency:** Both CLIs require `/usr/local/lib/hermes-orchestrator/rotation_state.json` for rotation tracking
- **API registration failure:** Orchestrator may not have `/api/agents/register` endpoint; verify before use
- **API key generation:** Falls back to default key if `manage_keys.py` fails

## Cron-Based Agent Workflows (no_agent=true) — 2026-05-06

**When to Use:**
- Running agent tasks without containers (when `nousresearch/hermes-agent` image has entrypoint issues)
- Coordinating multiple data collectors + a PIC filter/processor
- Intermediate file storage before SKP API (when API unreliable)
- Following user-provided JUKLAK (execution plan) that specifies PIC roles

**Architecture Pattern (Senator Pentahelix Example):**
```
Cron Job 1 (every 6h) → run_all_senators.py
   ↓
   - Collects research for all 5 sectors (akademisi, bisnis, komunitas, pemerintah, media)
   - Stores to SKP via API (if available)
   - Writes to local JSON: /root/senator-pentahelix/data/research_latest.json
   ↓
Cron Job 2 (every 6h, +10 min) → hermes_internet_filter.py
   ↓
   - Reads latest research JSON
   - Filters top 3 viral per sector (engagement metrics)
   - Sends formatted Telegram report (JUKLAK format)
   - Archives processed file
```

**Implementation Steps:**

1. **Create Collector Script** (e.g., `run_all_senators.py`):
   ```python
   # Must be placed in ~/.hermes/scripts/ for cron jobs
   import os, json, requests, datetime
   
   SECTORS = ['akademisi', 'bisnis', 'komunitas', 'pemerintah', 'media']
   ORCHESTRATOR_URL = os.getenv('ORCHESTRATOR_URL', 'http://localhost:8000')
   API_KEY = os.getenv('API_KEY', 'hermes-orchestrator-key-2026')
   
   def gather_research(sector):
       # ... research logic ...
       return findings
   
   def store_to_skp(findings, sector):
       # Try SKP API first
       url = ORCHESTRATOR_URL + '/api/knowledge'
       headers = {'X-API-Key': API_KEY, 'Content-Type': 'application/json'}
       # ... POST to SKP ...
   
   def append_to_local_file(findings, sector):
       # Fallback: write to local JSON
       local_file = '/root/senator-pentahelix/data/research_latest.json'
       # ... append to JSON ...
   
   for sector in SECTORS:
       findings = gather_research(sector)
       store_to_skp(findings, sector)
       append_to_local_file(findings, sector)
   ```

2. **Create Filter Script** (e.g., `hermes_internet_filter.py`):
   ```python
   # Reads local JSON, filters top 3 per sector, sends Telegram
   import json, glob, os
   
   DATA_DIR = '/root/senator-pentahelix/data'
   
   def read_latest_data():
       pattern = os.path.join(DATA_DIR, 'research_*.json')
       files = glob.glob(pattern)
       latest_file = max(files, key=os.path.getctime)
       with open(latest_file, 'r') as f:
           return json.load(f), latest_file
   
   def filter_top3_per_sector(data):
       # Group by sector, sort by engagement, return top 3
       ...
   
   def send_telegram(message):
       # Format JUKLAK report and send via Telegram API
       ...
   
   data, source_file = read_latest_data()
   top_data = filter_top3_per_sector(data)
   message = format_telegram_message(top_data)  # JUKLAK format
   send_telegram(message)
   # Archive: move to data/archive/
   ```

3. **Create Cron Jobs** (using `cronjob` tool with `no_agent=true`):
   ```bash
   # IMPORTANT: Scripts MUST be in ~/.hermes/scripts/ (not absolute paths)
   cp run_all_senators.py ~/.hermes/scripts/
   cp hermes_internet_filter.py ~/.hermes/scripts/
   
   # Cron job 1: Collector (every 6 hours at minute 0)
   # Use: cronjob create --name senator-pentahelix-research --no_agent true --schedule "0 */6 * * *" --script run_all_senators.py
   
   # Cron job 2: Filter (every 6 hours at minute 10)
   # Use: cronjob create --name hermes-internet-filter --no_agent true --schedule "10 */6 * * *" --script hermes_internet_filter.py
   ```

**Pitfalls:**
- **Script Path Requirement:** Cron jobs with `no_agent=true` REQUIRE scripts in `~/.hermes/scripts/`. Absolute paths (e.g., `/root/senator-pentahelix/scripts/...`) will fail with error: "Script path must be relative to ~/.hermes/scripts/".
- **Container Entrypoint Issues:** `nousresearch/hermes-agent` image has a custom entrypoint that makes running custom Python scripts as container commands difficult (causes constant restarts with exit code 0). Solution: Use host-level cron jobs instead of containers.
- **Module Availability:** The `schedule` module is NOT available in `nousresearch/hermes-agent` image. Use `time.sleep()` instead of `schedule.every().hours.do()`.
- **SKP API Reliability:** If `POST /api/knowledge` returns "Internal Server Error", have a fallback to local JSON files. The filter script can process local files independently.
- **JUKLAK Compliance:** User may provide detailed JUKLAK (execution plan) specifying PIC roles (e.g., `hermes-internet` as filter). Follow the JUKLAK structure for Telegram reports (sector grouping, top 3 per sector, engagement metrics, tag format).

**Success Criteria:**
- ✅ Scripts placed in `~/.hermes/scripts/`
- ✅ Cron jobs created with `no_agent=true`
- ✅ Collector writes to local JSON (fallback) + tries SKP API
- ✅ Filter reads JSON, sends formatted Telegram report
- ✅ File archiving after processing

**User Preferences (Indonesian Context):**
- Communicate in Indonesian
- Use structured terminal output with box-drawing (┌─ ──┐) and emoji (✅ ⏳ ❌)
- Brief status updates during rapid implementation, detailed docs in summaries
- Thorough validation before proceeding to next phase

## User Preferences (Upshalter - 2026-05-05)

**Communication Style:**
- Language: Indonesian (Bahasa Indonesia)
- Format: Brief status updates during rapid implementation
- Visual: Structured terminal output with box-drawing (┌─ ──┐) and emoji (✅ ⏳ ❌)
- Preference: Minimal explanation inline, detailed documentation goes in summaries
- Validation: Values thorough testing before proceeding to next phase

**Deployment Preferences:**
- Prefers fresh clone over fixing old installs (e.g., Hermes Workspace)
- Prefers subdomain access (workspace.upshalter.com) over path-based
- Uses PM2 for Node.js processes (not raw & background commands)
- Docker containers need `extra_hosts: "host.docker.internal:host-gateway"` for Ollama access
- Core Linux system files (/usr, /boot) and Hermes Agent installation files left untouched during VPS cleanup

**Environment:**
- VPS: upshalter.com
- Telegram: @upshalter_hermes_bot
- Workspace: /root/hermes-workspace-personal (personal clone)
- Critical: Orchestrator reads API key from `ORCHESTRATOR_API_KEY` (not `HERMES_ORCHESTRATOR_KEY`)

## Resources

- SQLite documentation: https://www.sqlite.org/docs.html
- FastAPI: https://fastapi.tiangolo.com/
- Redis pub/sub: https://redis.io/docs/manual/pubsub/
- Shared Knowledge Pool implementation: `references/shared-knowledge-pool.md`
- Phase 0 justification methodology: `references/phase0-justification-methodology.md`
- Scientific paper methodology: `references/scientific-paper-methodology.md` (for documenting improvements for academic publication)
- Phase 1 EventBus pattern subscription fixes: `references/phase1-eventbus-fixes.md`
- Phase 1 WebSocket threading solution: `references/phase1-websocket-threading.md`
- Phase 0 audit critical bugs (2026-05-05): `references/phase0-audit-bugs.md`
- **NEW (2026-05-05):** Phase 3 Workstation Nginx template: `templates/workstation-hermes-nginx.conf`
- **NEW (2026-05-05):** SKP direct insert procedure: `references/skp-direct-insert.md`
- **NEW (2026-05-07):** External knowledge ingestion example (Romi Wahono thesis list): `references/skp-external-knowledge-ingestion.md`
