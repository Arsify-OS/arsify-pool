# Multi-Agent Orchestration Foundation Pattern

**Session:** 2026-05-04  
**Context:** Building a centralized orchestration system for 10+ Hermes Agent instances on a VPS

## Problem

Multiple independent Hermes Agent instances (systemd services, Docker containers, PM2 processes) running on the same VPS with no coordination mechanism:
- No shared memory/context between agents
- Manual task routing and coordination
- No workflow automation
- No centralized monitoring
- Duplicated work and missed opportunities for collaboration

## Solution: Incremental Orchestration System

A phased approach to building multi-agent coordination infrastructure, starting with shared memory as the foundation.

### Architecture Overview

```
┌─────────────────────────────────────────────┐
│         ORCHESTRATOR HUB (Port 9000)        │
│  - Task Dispatcher                          │
│  - Agent Registry                           │
│  - Workflow Engine                          │
│  - Monitoring Dashboard                     │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌─────────┐         ┌─────────┐
│ Message │         │ Shared  │
│ Queue   │         │ Memory  │
│ (Redis) │         │ (SQLite)│
└────┬────┘         └────┬────┘
     │                   │
     └────────┬──────────┘
              │
    ┌─────────┼─────────┬─────────┐
    ▼         ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │
│   A    │ │   B    │ │   C    │ │   D    │
└────────┘ └────────┘ └────────┘ └────────┘
```

### Implementation Phases

**Phase 0: Shared Memory Foundation** (45 min, completed in 3 min)
- SQLite database for centralized memory storage
- Python API module with core functions
- Thread-safe concurrent access
- Full-text search capability
- Activity logging

**Phase 1: Core Orchestration** (4 hours)
- FastAPI-based Orchestrator Hub
- Redis message queue
- Agent REST API adapters
- Basic workflow engine
- Simple monitoring dashboard

**Phase 2: Skills Registry** (3 hours)
- Global skill repository
- Cross-agent skill sharing
- Skill discovery and invocation

**Phase 3: Auto-Assign** (4 hours)
- AI-powered task routing (Gemini Flash/Claude Haiku)
- Intent classification
- Automatic agent selection

**Phase 4: Advanced Workflow** (3 hours)
- DAG-based workflow definitions
- Dependency resolution
- Error handling and retry logic

**Phase 5: War Room** (4 hours, optional)
- Multi-agent collaborative discussions
- Turn-taking and state management
- Consensus building

## Phase 0 Implementation: Shared Memory

### Directory Structure

```
/root/hermes-orchestration/
├── shared-memory/
│   ├── db/
│   │   └── memory.db              # SQLite database
│   ├── api/
│   │   └── memory.py              # Core API module
│   ├── tests/
│   │   └── test_memory.py         # Test suite
│   ├── docs/
│   │   └── API.md                 # Documentation
│   └── demo.py                    # Demo script
```

### Database Schema

**memory table:**
- `id` (INTEGER PRIMARY KEY)
- `agent_id` (TEXT) - e.g., "loyx-8643"
- `agent_name` (TEXT) - e.g., "Loyx"
- `task_type` (TEXT) - e.g., "code_review", "deployment"
- `task_description` (TEXT)
- `input_data` (TEXT/JSON)
- `output_data` (TEXT/JSON)
- `status` (TEXT) - pending, in_progress, completed, failed
- `priority` (INTEGER 1-10)
- `tags` (TEXT/JSON array)
- `created_at` (REAL timestamp)
- `updated_at` (REAL timestamp)
- `completed_at` (REAL timestamp)
- `duration_seconds` (REAL)
- `metadata` (TEXT/JSON)

**memory_relations table:**
- Links parent/child tasks for workflow dependencies

**agent_activity table:**
- Audit trail of all agent actions

**Indexes:** agent_id, task_type, status, created_at, tags

### Core API Functions

```python
# Write memory after completing a task
memory_id = write_memory(
    agent_id="gamedev-8644",
    agent_name="GameDev",
    task_type="code_analysis",
    task_description="Analyze Regrow game mechanics",
    input_data={"files": ["game.py", "player.py"]},
    output_data={"issues": 2, "suggestions": 5},
    status="completed",
    priority=8,
    tags=["regrow", "analysis"]
)

# Read memories with filters
memories = read_memory(agent_id="gamedev-8644", limit=10)
memories = read_memory(task_type="code_review", status="completed")

# Search past work before starting new task
past_work = search_memory("player inventory system")

# Update memory as task progresses
update_memory(memory_id, output_data={...}, status="completed")

# Get statistics
stats = get_memory_stats()
```

### Usage Pattern: "Hive Mind"

**Before starting a task:**
```python
# Agent searches for related past work
past_work = search_memory("similar task keywords")
if past_work:
    # Read context from previous attempts
    context = past_work[0]['output_data']
    # Use insights to inform current approach
```

**After completing a task:**
```python
# Agent writes memory entry
memory_id = write_memory(
    agent_id=self.agent_id,
    agent_name=self.agent_name,
    task_type="deployment",
    task_description="Deploy Regrow to production",
    input_data={"commit": "abc123", "environment": "prod"},
    output_data={"success": True, "url": "https://..."},
    status="completed",
    priority=9,
    tags=["deployment", "regrow", "production"]
)
```

**Workflow coordination:**
```python
# Orchestrator creates parent task
parent_id = write_memory(
    agent_id="orchestrator",
    agent_name="Orchestrator",
    task_type="workflow",
    task_description="Deploy Regrow with full pipeline",
    status="in_progress",
    priority=10
)

# Child tasks reference parent
child_id = write_memory(
    agent_id="builder-9122",
    agent_name="Builder",
    task_type="code_review",
    task_description="Review code before deploy",
    status="pending",
    priority=9,
    metadata={"parent_task_id": parent_id}
)
```

## Testing

```bash
cd /root/hermes-orchestration/shared-memory
python3 tests/test_memory.py
```

All tests should pass:
- ✅ write_memory()
- ✅ read_memory() with filters
- ✅ update_memory()
- ✅ search_memory()
- ✅ log_activity()
- ✅ get_memory_stats()

## Integration with Existing Agents

### Option 1: Direct Python Import

For agents running on the same host:

```python
import sys
sys.path.insert(0, '/root/hermes-orchestration/shared-memory/api')
from memory import write_memory, read_memory, search_memory

# Use in agent code
memory_id = write_memory(...)
```

### Option 2: REST API Wrapper (Phase 1)

For Docker containers and remote agents:

```bash
curl -X POST http://localhost:9000/api/memory \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "loyx-8643", "task_type": "test", ...}'
```

### Option 3: File-Based (Fallback)

For agents that can't access the database directly:

```bash
# Agent writes to file
echo '{"agent_id": "...", "task": "..."}' > /tmp/memory_write.json

# Orchestrator polls and imports
python3 -c "import json; from memory import write_memory; ..."
```

## Resource Impact

**Phase 0 (Shared Memory only):**
- Memory: +10 MB (SQLite + Python process)
- Disk: +50 MB (database grows with usage)
- CPU: Negligible (<1%)

**Full System (Phase 0-4):**
- Memory: +800 MB
- Disk: +500 MB
- CPU: +5-10%

## Next Steps After Phase 0

1. **Test with one agent** - Integrate Loyx (8643) first
2. **Validate real-world usage** - Run for 24 hours, check data quality
3. **Build Phase 1** - Orchestrator Hub + Redis + Agent Adapters
4. **Define first workflow** - Regrow Auto-Deploy (git push → analyze → review → deploy)

## Pitfalls

1. **Database locking** - SQLite has write serialization. For high-concurrency (>10 agents writing simultaneously), consider PostgreSQL migration.

2. **Context pollution** - Don't write trivial tasks to memory. Only write meaningful work that future agents would benefit from knowing about.

3. **Search quality** - SQLite's `LIKE` search is basic. For semantic search, consider adding vector embeddings (Phase 2+).

4. **Memory growth** - Implement retention policy (e.g., archive memories older than 90 days) to prevent unbounded growth.

5. **Thread safety** - The API uses thread-local connections. Don't share connection objects across threads.

6. **JSON serialization** - Complex objects (datetime, custom classes) need manual serialization before passing to `input_data`/`output_data`.

## Success Metrics

**Phase 0 success criteria:**
- ✅ All tests pass
- ✅ Database created and accessible
- ✅ API functions work correctly
- ✅ Demo script runs without errors
- ✅ Documentation complete

**Integration success criteria (Phase 1):**
- At least 1 agent writing memories after task completion
- Memories searchable and useful for context
- No database corruption or locking issues
- Performance acceptable (<100ms per operation)

## References

- Planning documents: `/root/hermes-orchestration/PLAN.md`
- Impact analysis: `/root/hermes-orchestration/IMPACT_ANALYSIS.md`
- Priority scoring: `/root/hermes-orchestration/PRIORITY_SCALE.md`
- Full pipeline analysis: `/root/hermes-orchestration/FULL_PIPELINE_ANALYSIS.md`
- Implementation strategy: `/root/hermes-orchestration/IMPLEMENTATION_STRATEGY.md`
