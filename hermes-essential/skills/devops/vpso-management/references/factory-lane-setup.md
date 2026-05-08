# Factory Lane Pipeline Setup (DIM-10)
Automates the CI/CD pipeline for VPSO: **Builder → Sandbox → Flowforce → Infrastructure**.

## Prerequisites
- Hermes Orchestrator API running on port `8000` with `PUT /tasks/{id}` endpoint
- Task queue (`task_queue.py`) with `update_task` method supporting `status`, `tags`, `note` updates
- Valid API key with task update permissions

## Setup Steps
### 1. Extend Orchestrator API
Add `PUT /tasks/{task_id}` endpoint to `api.py` (usually at `/usr/local/lib/hermes-orchestrator/api.py`):
```python
@app.put("/tasks/{task_id}")
async def update_task(task_id: str, request: dict):
    try:
        task = orchestrator.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        new_status = request.get("status")
        new_tags = request.get("tags")
        note = request.get("note")
        
        success = orchestrator.update_task(
            task_id=task_id,
            status=new_status,
            tags=new_tags,
            note=note
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update task")
        
        return {"task_id": task_id, "status": "updated", "message": "Task updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Add corresponding `update_task` methods to `orchestrator/orchestrator.py` and `orchestrator/task_queue.py`.

### 2. Create Transition Script
Save the transition script to `/usr/local/lib/hermes-orchestrator/factory_lane_transition.py` (full script available in `scripts/factory_lane_transition.py`). The script:
- Polls for completed tasks with relevant tags (`build`, `test`, `deploy`)
- Transitions tasks to the next stage with updated tags
- Logs transitions to stdout

### 3. Setup Cron Job
Add a cron job to run the script every minute:
```bash
(crontab -l 2>/dev/null; echo "* * * * * /usr/local/lib/hermes-orchestrator/factory_lane_transition.py >> /var/log/hermes-factory-lane.log 2>&1") | crontab -
```

### 4. End-to-End Testing
1. Submit a build task:
   ```bash
   curl -X POST "http://localhost:8000/tasks" -H "X-API-Key: <key>" -H "Content-Type: application/json" -d '{"task_type":"build","description":"Test","tags":["build"]}'
   ```
2. Mark task as completed:
   ```bash
   curl -X PUT "http://localhost:8000/tasks/<task_id>" -H "X-API-Key: <key>" -H "Content-Type: application/json" -d '{"status":"completed"}'
   ```
3. Run the transition script and verify tags update with:
   ```bash
   redis-cli HGETALL "task:<task_id>"
   ```

## Common Pitfalls
- Orchestrator API endpoints do **not** use `/api` prefix (e.g., `/tasks` not `/api/tasks`)
- Task ID field in API responses is `task_id` (not `id`)
- Task status strings are **lowercase** (e.g., `completed` not `COMPLETED`)
- Tag filter parameter is `tags` (plural) not `tag` (singular) in `GET /tasks?tags=...`
- Always verify tag storage in Redis after submitting tasks
- API key must have permissions for task updates (use `manage_keys.py` to generate valid keys)