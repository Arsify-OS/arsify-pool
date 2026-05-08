# Error Patterns - Orchestrator Task Polling

## Connection Reset Errors (Agent Side)

### Log Pattern 1: ConnectionResetError
```
2026-05-05 05:36:55 sdk.agent_client - ERROR - Task fetch failed: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))
2026-05-05 05:36:55 sdk.agent_base - ERROR - Task polling error: Failed to fetch task: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))
```

### Log Pattern 2: RemoteDisconnected
```
2026-05-05 05:37:06 sdk.agent_client - ERROR - Task fetch failed: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
2026-05-05 05:37:06 sdk.agent_base - ERROR - Task polling error: Failed to fetch task: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
```

**Key Observation**: Errors occur every 10-30 seconds (polling interval), indicating agent is trying but orchestrator is crashing on /tasks endpoint.

## Orchestrator 500 Error (Server Side)

### Direct curl test:
```bash
$ curl -s "http://localhost:8000/tasks?status=pending&limit=5" -H "X-API-Key: $API_KEY"
Internal Server Error
```

### Log Pattern: Unhandled errors in TaskGroup
```
ERROR:    Exception in ASGI application
  Exception Group Traceback: unhandled errors in a TaskGroup (1 sub-exception)
  File "orchestrator/middleware.py", line 89, in __call__
    raise HTTPException(status_code=401, detail="API key required")
```

**Note**: The 401 error appears when API key is missing, but 500 errors occur when endpoint crashes during processing.

## Root Cause Evidence

### Redis Status Format Issue:
```
$ redis-cli --scan --pattern 'task:*' | while read key; do redis-cli hget $key status; done
TaskStatus.PENDING   # WRONG - string repr of enum
pending              # CORRECT - enum value
assigned              # Task already assigned
```

### TaskQueue.list_tasks() Bug:
- Original code: `for key in task_keys[:limit]:` 
- Problem: Only checks first `limit` keys, not all keys
- Result: Tasks with PENDING status at position > limit are invisible

## Successful Validation Pattern

After fix, expected log output:
```
INFO: 127.0.0.1:45764 - "GET /tasks?agent_id=upshalternal&status=pending&limit=1 HTTP/1.1" 200 OK
INFO: 127.0.0.1:45766 - "GET /tasks?agent_id=builder&status=pending&limit=1 HTTP/1.1" 200 OK
```

All agents return 200 OK (not 500), no more ConnectionResetError in agent logs.