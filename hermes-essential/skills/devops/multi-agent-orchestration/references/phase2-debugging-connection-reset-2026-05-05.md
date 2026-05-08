# Debugging Connection Reset Errors in Multi-Agent Orchestrator
# Date: 2026-05-05
# Symptom: Agent SDK logs "Connection aborted" / "Remote end closed connection"

## Quick Diagnosis Checklist

1. **Check if orchestrator API is running**
   ```bash
   ps aux | grep "uvicorn\|api.py" | grep -v grep
   curl -s http://localhost:8000/health | python3 -m json.tool
   ```

2. **Check for 500 errors**
   ```bash
   # Test with valid API key
   API_KEY=$(cd /usr/local/lib/hermes-orchestrator && python3 manage_keys.py list --agent-id upshalternal | grep hma_ | head -1 | awk '{print $NF}')
   curl -v "http://localhost:8000/tasks?status=pending&limit=1" -H "X-API-Key: $API_KEY" 2>&1 | grep "HTTP/"
   ```

3. **If 500 error, check orchestrator logs**
   ```bash
   # If running in background
   cat /tmp/orchestrator.log | tail -50
   # Or check systemd
   journalctl -u hermes-orchestrator --no-pager -n 50
   ```

## Common Root Causes (from 2026-05-05 session)

### 1. Enum Serialization Bug
**Symptom:** Tasks stored in Redis with status = "TaskStatus.PENDING" instead of "pending"

**Root cause:** `Task.to_dict()` stores enum repr instead of value
```python
# WRONG (in task_queue.py Task.to_dict())
"status": self.status,  # Stores "TaskStatus.PENDING" (repr)
"priority": self.priority,  # Stores "TaskPriority.NORMAL" (repr)
```

**Fix:**
```python
# CORRECT (in task_queue.py Task.to_dict())
"status": self.status.value if hasattr(self.status, 'value') else self.status,
"priority": self.priority.value if hasattr(self.priority, 'value') else self.priority,
```

### 2. Enum Deserialization Bug
**Symptom:** `Task.from_dict()` fails to convert string status back to enum

**Root cause:** `from_dict()` doesn't handle string-to-enum conversion

**Fix:** Add status handling in `from_dict()`:
```python
elif key == 'status':
    if isinstance(value, str):
        if value.startswith('TaskStatus.'):
            # Handle "TaskStatus.PENDING" format
            deserialized[key] = TaskStatus(value.split('.')[-1])
        else:
            # Handle "pending" format
            deserialized[key] = TaskStatus(value)
```

### 3. list_tasks() Iteration Bug
**Symptom:** `list_tasks(status=PENDING)` returns 0 tasks even when pending tasks exist

**Root cause:** Only iterates first `limit` keys instead of ALL keys
```python
# WRONG (in task_queue.py list_tasks())
for key in task_keys[:limit]:  # Only checks first 'limit' keys
    # ...
```

**Fix:**
```python
# CORRECT
for key in task_keys:
    if len(tasks) >= limit:
        break
    # ...
```

### 4. Config Typo
**Symptom:** 500 error with "type object 'Config' has no attribute 'CHANNEL_EVENTS'"

**Root cause:** Using wrong constant name
```python
# WRONG (in task_queue.py)
Config.CHANNEL_EVENTS  # Doesn't exist
```

**Fix:**
```python
# CORRECT
Config.CHANNEL_TASK_ASSIGNMENTS  # Or CHANNEL_SYSTEM_EVENTS
```

## Step-by-Step Debugging Process (from session)

1. **Reproduce the error**
   ```bash
   journalctl -u hermes-upshalternal-bridge --no-pager -n 30 | grep ERROR
   ```

2. **Test orchestrator API directly**
   ```bash
   curl -v "http://localhost:8000/tasks?status=pending&limit=3" -H "X-API-Key: $API_KEY"
   ```

3. **If 500 error, test components individually**
   ```bash
   cd /usr/local/lib/hermes-orchestrator
   python3 -c "
   import sys
   sys.path.insert(0, '.')
   from orchestrator.task_queue import TaskQueue, TaskStatus
   tq = TaskQueue()
   print('Pending tasks:', tq.get_pending_tasks(limit=5))
   "
   ```

4. **Check Redis directly**
   ```bash
   redis-cli keys "task:*" | head -5
   redis-cli hgetall "task:<uuid>" | grep status
   ```

5. **Test enum serialization**
   ```bash
   python3 -c "
   from orchestrator.task_queue import Task, TaskStatus
   t = Task(task_id='test', task_type='test', description='test')
   print('to_dict status:', t.to_dict()['status'])
   print('Type:', type(t.to_dict()['status']))
   "
   ```

6. **Apply fixes and restart**
   ```bash
   # Kill old orchestrator
   lsof -ti:8000 | xargs -r kill -9
   
   # Start new orchestrator
   cd /usr/local/lib/hermes-orchestrator
   python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 &
   
   # Restart agent bridges
   systemctl restart hermes-upshalternal-bridge hermes-builder-bridge
   ```

7. **Verify fixes**
   ```bash
   # Test API
   curl -s "http://localhost:8000/tasks?status=pending&limit=3" -H "X-API-Key: $API_KEY"
   
   # Check agent logs (should have no ERROR)
   journalctl -u hermes-upshalternal-bridge --since "5 minutes ago" | grep ERROR
   ```

## Verification Script

Save as `verify_fixes.py`:
```python
import sys
sys.path.insert(0, '/usr/local/lib/hermes-orchestrator')

from orchestrator.task_queue import TaskQueue, TaskStatus, Task

print("=== Verification Script ===\n")

# 1. Test enum serialization
print("1. Testing Task.to_dict() serialization...")
t = Task(task_id='test-1', task_type='test', description='Test', status=TaskStatus.PENDING)
d = t.to_dict()
assert d['status'] == 'pending', f"FAIL: status = {d['status']}"
assert d['priority'] == 5, f"FAIL: priority = {d['priority']}"
print("   PASS: Enum serialization correct\n")

# 2. Test enum deserialization
print("2. Testing Task.from_dict() deserialization...")
data_old = {'task_id': 'test-2', 'task_type': 'test', 'description': 'Test', 'status': 'TaskStatus.PENDING', 'priority': '5'}
t2 = Task.from_dict(data_old)
assert t2.status == TaskStatus.PENDING, f"FAIL: status = {t2.status}"
print("   PASS: Old format (TaskStatus.PENDING) handled\n")

data_new = {'task_id': 'test-3', 'task_type': 'test', 'description': 'Test', 'status': 'pending', 'priority': '5'}
t3 = Task.from_dict(data_new)
assert t3.status == TaskStatus.PENDING, f"FAIL: status = {t3.status}"
print("   PASS: New format (pending) handled\n")

# 3. Test list_tasks iteration
print("3. Testing TaskQueue.list_tasks() iteration...")
tq = TaskQueue()
tasks = tq.list_tasks(status=TaskStatus.PENDING, limit=10)
print(f"   Found {len(tasks)} pending tasks\n")

print("=== All verifications passed! ===")
```

Run with: `python3 verify_fixes.py`

## Key Learnings

1. **Enum serialization matters** - Always use `.value` when storing enums to Redis/JSON
2. **Handle both formats** - Old code may have stored repr(), new code stores value
3. **Iterate ALL keys** - Don't assume relevant data is in first N keys
4. **Config typos are silent killers** - Double-check constant names against config.py
5. **Connection reset ≠ network issue** - Usually indicates API crash (500 error)
