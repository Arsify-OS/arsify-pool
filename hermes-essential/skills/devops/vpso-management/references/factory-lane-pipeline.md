# Factory Lane Pipeline (DIM-10)

Automated CI/CD pipeline for VPSO: Builder → Sandbox → Flowforce → Infrastructure.

## Overview

Factory Lane implements automated task transitions between VPSO units based on completion status and tags:
- **Builder** (9127): Receives tasks with `#build` tag
- **Sandbox** (9126): Receives tasks with `#test` tag after builder completes
- **Flowforce** (9128): Receives tasks with `#deploy` tag after sandbox passes
- **Infrastructure** (9129): Receives tasks with `#infra` tag for production deployment

## Implementation Files

### 1. Transition Script
**Location**: `/usr/local/lib/hermes-orchestrator/factory_lane_transition.py`

**Purpose**: Polls tasks by tag and transitions them to next stage when status is `completed`.

**Key Functions**:
- `get_tasks_by_tag(tag)`: Fetch tasks with specific tag via API
- `update_task_status(task_id, status, new_tags, note)`: Update task via PUT /tasks/{id}
- `process_build_to_test()`: build → test/sandbox
- `process_test_to_deploy()`: test → deploy/flowforce  
- `process_deploy_to_infra()`: deploy → infra/production

**API Key**: Uses `factory-lane-test` agent key (stored in script)

### 2. API Endpoint Added
**File**: `/usr/local/lib/hermes-orchestrator/api.py`

**Endpoint**: `PUT /tasks/{task_id}`
```python
@app.put("/tasks/{task_id}")
async def update_task(task_id: str, request: dict):
    # Updates task status, tags, note
    # Calls orchestrator.update_task()
```

### 3. Orchestrator Method
**File**: `/usr/local/lib/hermes-orchestrator/orchestrator/orchestrator.py`

**Method**: `update_task(task_id, status, tags, note)`
- Converts status string to TaskStatus enum
- Calls task_queue.update_task()

### 4. Task Queue Method
**File**: `/usr/local/lib/hermes-orchestrator/orchestrator/task_queue.py`

**Method**: `update_task(task_id, status, tags, note)`
- Updates Redis hash for task
- Publishes `task_updated` event to Redis channel
- Handles metadata notes (appends to existing)

## Automation

### Cron Job
```bash
# Runs every 1 minute
* * * * * /usr/local/lib/hermes-orchestrator/factory_lane_transition.py >> /var/log/hermes-factory-lane.log 2>&1
```

Check with: `crontab -l`

## Tag-Based Routing

Tasks move through pipeline via tag updates:
1. Task submitted with `tags: ["build"]`
2. Builder completes → script changes tags to `["test", "sandbox"]`, status to `pending`
3. Sandbox completes → script changes tags to `["deploy", "flowforce"]`, status to `pending`
4. Flowforce completes → script changes tags to `["infra", "production"]`, status to `pending`
5. Infrastructure picks up final task

## Pitfalls Encountered

1. **API Endpoint Path**: Initially used `/api/tasks` but correct path is `/tasks` (FastAPI root at `/`)
   
2. **Status String Case**: 
   - Wrong: `'COMPLETED'`, `'PENDING'` (enum names)
   - Correct: `'completed'`, `'pending'` (enum values)
   
3. **Task ID Field**:
   - Wrong: `task.get('id')`
   - Correct: `task.get('task_id')`
   
4. **Redis Tags Storage**: Ensure `task.to_dict()` includes `tags` field and `serialized` dict properly JSON-encodes lists:
   ```python
   if isinstance(value, (dict, list)):
       serialized[key] = json.dumps(value)
   ```

5. **API Key Authentication**: Must use valid agent API key (generate via `manage_keys.py generate <agent_id>`)

## Testing

```bash
# 1. Create task with build tag
curl -X POST "http://localhost:8000/tasks" \
  -H "X-API-Key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"task_type":"test","description":"Test","tags":["build"]}'

# 2. Mark as completed
curl -X PUT "http://localhost:8000/tasks/<task_id>" \
  -H "X-API-Key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"status":"completed"}'

# 3. Run transition script
python3 /usr/local/lib/hermes-orchestrator/factory_lane_transition.py

# 4. Verify tag changed to "test"
curl "http://localhost:8000/tasks/<task_id>" -H "X-API-Key: <key>"
```

## User Control Principle

While transitions are automated, the user retains control:
- Can manually update task tags/status via API
- Can disable cron job: `crontab -e` (comment the line)
- Factory Lane is recommendation engine, not forced pipeline
- User can insert approval gates (e.g., Flowforce waits for user sign-off before `#infra` transition)
