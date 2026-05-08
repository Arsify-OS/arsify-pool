# Phase 2 Debugging: API Parameter Mismatch Bug

**Date:** 2026-05-04  
**Phase:** Phase 2 (Agent Integration)  
**Component:** Orchestrator API

## Bug Report

### Symptom
- API endpoint `/agents` returns "Internal Server Error" (500)
- Health check shows all components healthy except agents (0 online - expected)
- Logs show `TypeError: Orchestrator.list_agents() got an unexpected keyword argument 'status'`

### Root Cause Analysis

**Layer mismatch:** API layer expects orchestrator to support filtering parameters, but orchestrator method signature doesn't match.

```
api.py (line 329):
  orchestrator.list_agents(status=status_enum, capability=capability)
  
orchestrator.py (line 305):
  def list_agents(self, online_only: bool = False)
  
Result: TypeError - unexpected keyword argument 'status'
```

**Why this happened:**
- API endpoint was designed with filtering in mind (`?status=offline&capability=coding`)
- Orchestrator implementation only supported basic `online_only` boolean filter
- No integration test caught the mismatch before deployment

### Investigation Steps

1. **Attempted direct API call without auth:**
   ```bash
   curl http://localhost:8000/agents
   # Result: "Internal Server Error"
   ```

2. **Checked logs:**
   ```bash
   tail -50 /var/log/hermes-orchestrator/api.log
   # Found: TypeError at line 329 in api.py
   ```

3. **Verified server running:**
   ```bash
   netstat -tlnp | grep :8000
   # Result: PID 409915 listening
   ```

4. **Checked database schema:**
   ```bash
   sqlite3 db/orchestrator.db ".schema agents"
   # Confirmed: agent_id, status, capabilities columns exist
   ```

5. **Identified auth requirement:**
   - Health endpoint works without auth
   - Other endpoints require API key
   - Generated test key: `python3 manage_keys.py generate test-cli-agent`

6. **Located bug:**
   - Read `api.py` line 329: calls with `status=` and `capability=` parameters
   - Read `orchestrator/orchestrator.py` line 305: only accepts `online_only=`
   - Bug is in orchestrator layer, not API layer

### Fix Implementation

**File:** `/usr/local/lib/hermes-orchestrator/orchestrator/orchestrator.py`

**Before:**
```python
def list_agents(self, online_only: bool = False) -> List[Dict]:
    """List all agents."""
    agents = self.agent_registry.list_agents(online_only=online_only)
    return [agent.to_dict() for agent in agents]
```

**After:**
```python
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

**Changes:**
1. Added `status: Optional[AgentStatus]` parameter
2. Added `capability: Optional[str]` parameter
3. Kept `online_only` for backward compatibility
4. Pass `status` to `agent_registry.list_agents()` (already supported)
5. Added capability filtering logic (agent_registry doesn't support this natively)

### Verification

1. **Syntax check:**
   ```bash
   python3 -m py_compile orchestrator/orchestrator.py
   # Result: No errors
   ```

2. **Restart server:**
   ```bash
   ./stop.sh && ./start.sh
   # Result: Started successfully (PID: 414927)
   ```

3. **Test endpoints with authentication:**
   ```bash
   # List all agents
   curl -H "X-API-Key: hma_BcMSewrFjGVK6q5FxY1qszTS7od-9f4ZOGgvMHnrOuY" \
        http://localhost:8000/agents
   # Result: {"agents":[...], "count":6}
   
   # Filter by status
   curl -H "X-API-Key: hma_..." \
        "http://localhost:8000/agents?status=offline"
   # Result: 6 offline agents
   
   # Filter by capability
   curl -H "X-API-Key: hma_..." \
        "http://localhost:8000/agents?capability=coding"
   # Result: Agents with "coding" capability
   ```

4. **Health check:**
   ```bash
   curl -s http://localhost:8000/health | python3 -m json.tool
   # Result: All components healthy except agents (0 online - expected)
   ```

### Lessons Learned

1. **Layer responsibility:**
   - API layer defines interface (query parameters)
   - Orchestrator layer implements business logic
   - Agent registry provides data access
   - Bug was in orchestrator layer, not API layer

2. **Authentication middleware:**
   - Public endpoints: `/`, `/health`, `/docs`, `/openapi.json`
   - All other endpoints require API key
   - Middleware checks `X-API-Key` header or `Authorization: Bearer` header
   - Returns 401 for missing/invalid keys

3. **Health endpoint design:**
   - Returns detailed component status even when overall `healthy: false`
   - Useful for debugging: can see which component is unhealthy
   - `agents.status: unhealthy` with 0 online is expected when no agents running

4. **Testing gaps:**
   - Need integration tests that call API endpoints with filters
   - Need to test parameter passing through all layers
   - Unit tests alone don't catch layer mismatch bugs

5. **Debugging workflow:**
   - Check logs first (tail /var/log/hermes-orchestrator/api.log)
   - Verify server running (netstat, ps)
   - Test with health endpoint (no auth required)
   - Generate API key for testing other endpoints
   - Read source code to find exact mismatch
   - Fix at correct layer (orchestrator, not API)
   - Verify with multiple test cases

### Prevention

**Add integration test:**
```python
# test_api_integration.py
def test_list_agents_with_filters():
    # Setup: register test agents with different capabilities
    # Test: GET /agents?status=offline
    # Test: GET /agents?capability=coding
    # Assert: correct filtering applied
```

**Add to CI/CD:**
- Run integration tests before deployment
- Test all query parameter combinations
- Verify parameter passing through layers

### Related Issues

- Agent registry already supports `status` parameter (no changes needed)
- Capability filtering not supported by agent registry (implemented in orchestrator)
- Backward compatible: existing code using `online_only` still works
