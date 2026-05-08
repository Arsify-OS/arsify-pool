# Phase 0 Audit - Critical Bugs Found (2026-05-05)

## Overview
During a comprehensive audit of Phase 0 (Infrastructure & API Setup) on 2026-05-05, two critical bugs were discovered that prevent the multi-agent orchestration system from functioning in production, despite "Phase 0-2 Complete" status.

## Bug #1: Endpoint Mismatch (agent_client.py vs api.py)

### Symptom
- Bridge agents log `Connection aborted` or `Connection reset by peer` errors when polling for tasks
- Tasks remain in "pending" or "assigned" status forever
- Manual curl tests return 422 Validation Error or empty task lists

### Root Cause
**agent_client.py** (SDK) polls tasks with:
```python
url = f"{self.config.orchestrator_url}/tasks"
params = {
    "agent_id": self.config.agent_id,
    "status": "pending",
    "limit": 1
}
response = self.session.get(url, params=params)
```

**api.py** endpoint only accepts:
```python
@app.get("/tasks")
async def list_tasks(
    status: Optional[str] = Query(None),
    limit: int = Query(50)
):
    # NO agent_id parameter!
```

### Impact
- Agent sends `agent_id` param → FastAPI returns 422 (validation error)
- OR server ignores `agent_id` → returns ALL tasks, not just tasks for that agent
- Agent can never fetch tasks assigned to it

### Fix
Update `api.py` to add `agent_id` parameter:
```python
@app.get("/tasks")
async def list_tasks(
    agent_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50)
):
    # Filter by agent_id if provided
    if agent_id:
        tasks = [t for t in tasks if t.get("assigned_agent") == agent_id]
```

## Bug #2: Task Queue Architecture Inconsistency

### Symptom
- `redis-cli keys "task:*"` shows 12+ task hashes
- `redis-cli llen "hermes:queue:tasks"` returns 0 (empty!)
- Tasks exist in Redis but are never processed

### Root Cause
**task_queue.py** `submit_task()` correctly stores task data:
```python
# Store task data
self.redis.hset(f"task:{task_id}", mapping=serialized)

# Add to queue based on priority
if priority >= TaskPriority.HIGH:
    self.redis.zadd(Config.QUEUE_PRIORITY, {task_id: priority})
else:
    self.redis.rpush(Config.QUEUE_TASKS, task_id)  # Uses Config.QUEUE_TASKS
```

**BUT** the actual queue key is `hermes:queue:tasks` (from `Config.QUEUE_TASKS = "hermes:queue:tasks"`), while the health check reports `redis-cli llen "hermes:queue:tasks"` as "12 tasks in queue" when the actual count is 0.

**Additional Issue:** Task assignment changes task status to "assigned" and sets `assigned_agent`, but does NOT remove task from the pending queue (or the queue is empty to begin with).

### Impact
- Tasks submitted but never appear in pending queue
- Workers can't pickup tasks (nothing to LPOP)
- Tasks get "assigned" by router but agents can't fetch them

### Fix
1. Verify `submit_task()` actually LPUSHes to correct queue:
   ```python
   # Should be:
   self.redis.rpush("hermes:queue:tasks", task_id)
   ```

2. Fix task assignment to remove from pending queue:
   ```python
   def assign_task(self, task_id, agent_id):
       # Remove from pending queue
       self.redis.lrem("hermes:queue:tasks", 0, task_id)
       # Update task status
       self.redis.hset(f"task:{task_id}", "status", "assigned")
       self.redis.hset(f"task:{task_id}", "assigned_agent", agent_id)
   ```

## Audit Checklist

When verifying Phase 0 infrastructure, always check:

```bash
# 1. API server running and bound to correct interface
ps aux | grep "api.py" | grep -v grep
ss -tlnp | grep 8000  # Should be 0.0.0.0:8000, NOT 127.0.0.1:8000

# 2. Endpoint compatibility
grep -A 10 "def fetch_task" /usr/local/lib/hermes-orchestrator/sdk/agent_client.py
grep -A 30 "@app.get(\"/tasks\")" /usr/local/lib/hermes-orchestrator/api.py
# Compare params - they should match!

# 3. Task queue consistency
redis-cli keys "task:*" | wc -l  # Task hashes
redis-cli llen "hermes:queue:tasks"  # Pending queue
# These should be in sync (hashes count >= queue length)

# 4. Task status verification
TASK_ID=$(redis-cli keys "task:*" | head -1 | tr -d '"')
redis-cli hgetall "$TASK_ID"
# Look for: status, assigned_agent, created_at

# 5. Manual polling test
curl -s "http://localhost:8000/tasks?agent_id=test&status=pending&limit=1" \
  -H "X-API-Key: $(cd /usr/local/lib/hermes-orchestrator && python3 manage_keys.py list | grep -m1 key_ | awk '{print $2}')" \
  | python3 -m json.tool
# Should return tasks, NOT 422 error
```

## Redis Task Storage Architecture

```
task:<uuid> (hash)
  ├─ task_id
  ├─ task_type
  ├─ description
  ├─ status (pending/assigned/in_progress/completed/failed)
  ├─ assigned_agent
  ├─ created_at
  └─ updated_at

hermes:queue:tasks (list - FIFO)
  └─ [task_id_1, task_id_2, ...]  ← LPUSH/RPOP for pending tasks

hermes:queue:priority (sorted set)
  └─ {task_id: priority_score}  ← For high-priority tasks
```

**Key Insight:** Tasks must be in BOTH the hash (for data) AND the queue list (for processing).

## Health Check Inaccuracy

The `/health` endpoint reports:
```json
"queue": {
  "details": {
    "pending_tasks": 12,
    "total_tasks": 12
  }
}
```

But this is calculated from task hashes, NOT the actual queue. The `pending_tasks` count includes ALL tasks with `status: pending`, even if they're not in the processing queue.

**Fix:** Health check should also verify queue consistency:
```python
pending_count = redis.llen("hermes:queue:tasks")
actual_pending_tasks = redis.keys("task:*")  # Then filter by status
if pending_count != actual_pending_tasks:
    health_status = "unhealthy"
    message = f"Queue inconsistency: {pending_count} in queue, {actual_pending_tasks} pending"
```
