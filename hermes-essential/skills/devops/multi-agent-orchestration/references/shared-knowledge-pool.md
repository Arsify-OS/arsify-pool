# Shared Knowledge Pool Implementation

Session: 2026-05-04
Task: Migrate from task memory to shared knowledge pool

## Problem

Initial implementation used "task memory" model where each agent wrote their own task history. This resulted in:
- Agent A: 4 memories
- Agent B: 3 memories  
- Agent C: 1 memory
- Total: 15 memories distributed unevenly across 7 agents

User asked: "apakah seluruh agent sudah memiliki memory yang sama" (do all agents have the same memory?)

Answer was NO - each agent had different memory counts.

## Solution: Shared Knowledge Pool

Migrated to a global knowledge pool where all agents read from the same knowledge base.

### Database Schema

```sql
-- Shared knowledge table
CREATE TABLE knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL,  -- system, project, workflow, lesson, general
    source_agent_id TEXT NOT NULL,
    source_agent_name TEXT NOT NULL,
    tags TEXT,  -- JSON array
    priority INTEGER DEFAULT 5,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    metadata TEXT  -- JSON
);

-- Access tracking
CREATE TABLE knowledge_access (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_id INTEGER NOT NULL,
    agent_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    accessed_at REAL NOT NULL,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
);

-- Indexes
CREATE INDEX idx_knowledge_category ON knowledge(category);
CREATE INDEX idx_knowledge_tags ON knowledge(tags);
CREATE INDEX idx_knowledge_created ON knowledge(created_at);
CREATE INDEX idx_knowledge_access_agent ON knowledge_access(agent_id);
CREATE INDEX idx_knowledge_access_knowledge ON knowledge_access(knowledge_id);
```

### API Implementation

File: `/usr/local/lib/hermes-shared-memory/api/knowledge.py`

Key functions:
- `write_knowledge(title, content, category, source_agent_id, source_agent_name, tags, priority, metadata)` → knowledge_id
- `read_knowledge(agent_id, agent_name, knowledge_id, category, tags, limit, offset, track_access)` → List[Dict]
- `search_knowledge(query, agent_id, agent_name, category, limit)` → List[Dict]
- `update_knowledge(knowledge_id, ...)` → bool
- `delete_knowledge(knowledge_id)` → bool
- `get_knowledge_stats()` → Dict
- `get_agent_knowledge_access(agent_id, limit)` → List[Dict]

### Migration Script

File: `/usr/local/lib/hermes-shared-memory/migrate_to_knowledge.py`

Process:
1. Read all task memories from `memory` table
2. Map task_type to category:
   - deployment → system
   - code_review → workflow
   - analysis → project
   - configuration → system
   - testing → workflow
   - documentation → project
   - (default) → general
3. Convert each memory to knowledge entry
4. Write to `knowledge` table with metadata tracking original memory_id

Result: 15 task memories → 15 knowledge entries

### Testing

File: `/usr/local/lib/hermes-shared-memory/test_shared_knowledge.py`

Tests all agents (8 total) can read same knowledge:
- hermes-cli
- loyx-8643
- gamedev-8644
- builder-9122
- infra-9121
- plaza-9123
- upshalternal-9120
- dashboard-9119

Expected result: All agents report 15 knowledge entries (identical count)

### Verification Commands

```bash
# Run migration
cd /usr/local/lib/hermes-shared-memory
python3 migrate_to_knowledge.py

# Test all agents see same knowledge
python3 test_shared_knowledge.py

# Check stats
python3 -c "
import sys
sys.path.insert(0, '.')
from hermes_memory import get_knowledge_stats
import json
print(json.dumps(get_knowledge_stats(), indent=2))
"
```

### Integration Example

```python
import sys
sys.path.insert(0, '/usr/local/lib/hermes-shared-memory')

from hermes_memory import read_knowledge, write_knowledge

AGENT_ID = "my-agent"
AGENT_NAME = "My Agent"

# Read all knowledge (same for all agents)
knowledge = read_knowledge(
    agent_id=AGENT_ID,
    agent_name=AGENT_NAME,
    limit=50
)

# Write new knowledge (immediately available to all agents)
knowledge_id = write_knowledge(
    title="How to configure Nginx for Hermes",
    content="Steps: 1. Create config in /etc/nginx/sites-available/...",
    category="workflow",
    source_agent_id=AGENT_ID,
    source_agent_name=AGENT_NAME,
    tags=["nginx", "deployment", "configuration"],
    priority=8
)
```

## Results

After migration:
- ✅ All 8 agents can access 15 knowledge entries (identical)
- ✅ Access tracking works (120 total accesses: 8 agents × 15 knowledge)
- ✅ Categories: general (12), system (1), workflow (2)
- ✅ Search functionality works
- ✅ Thread-safe concurrent access

## Key Differences: Task Memory vs Knowledge Pool

| Aspect | Task Memory | Knowledge Pool |
|--------|-------------|----------------|
| Scope | Agent-specific | Global |
| Visibility | Agent sees own + can query others | All agents see same entries |
| Use Case | Task tracking, work history | Shared insights, lessons, procedures |
| Distribution | Uneven (1-4 per agent) | Even (all agents see all) |
| Table | `memory` | `knowledge` |
| Tracking | Task lifecycle (pending→completed) | Access tracking (who read what) |

## Categories

- **system**: Infrastructure, configuration, system setup
- **project**: Project-specific knowledge, codebase info
- **workflow**: Processes, procedures, how-to guides
- **lesson**: Lessons learned, pitfalls, solutions
- **general**: Uncategorized knowledge

## Files Created

- `/usr/local/lib/hermes-shared-memory/api/knowledge.py` - Knowledge pool API
- `/usr/local/lib/hermes-shared-memory/migrate_to_knowledge.py` - Migration script
- `/usr/local/lib/hermes-shared-memory/test_shared_knowledge.py` - Test script
- `/usr/local/lib/hermes-shared-memory/example_usage.py` - Usage examples
- `/usr/local/lib/hermes-shared-memory/README.md` - Full documentation

Updated:
- `/usr/local/lib/hermes-shared-memory/hermes_memory.py` - Added knowledge API exports
