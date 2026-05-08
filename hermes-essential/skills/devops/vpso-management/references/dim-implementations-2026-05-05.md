# VPSO DIM Implementations - 5 Mei 2026

## Technical Steps for DIM-07: Rotasi Koordinator
1. **CLI Tool**: `/usr/local/bin/hermes-rotate-coordinator`
   - Manual rotation: `hermes-rotate-coordinator --domain <domain> --new-coord <agent> --project <project>`
   - Status check: `hermes-rotate-coordinator --status [domain]`
2. **Automated Rotation**: `/usr/local/lib/hermes-orchestrator/auto-rotate-coordinator.py`
   - Policies: `per_project` (rotates on project completion), `fixed` (no auto-rotation), `periodic` (every 7 days)
   - Checks task completion via API: `GET /tasks?tags=<domain>`
3. **Cron Job**: `*/15 * * * * /usr/bin/python3 /usr/local/lib/hermes-orchestrator/auto-rotate-coordinator.py >> /var/log/hermes-auto-rotate.log 2>&1`
4. **State File**: `/usr/local/lib/hermes-orchestrator/rotation_state.json`
   - Structure: `domains.<domain>.current_coordinator`, `.rotation_policy`, `.rotation_history[]`

## Technical Steps for DIM-09: Sanksi Pembekuan 24 Jam
1. **API Endpoints** (added to `api.py`):
   - `POST /agents/{agent_id}/freeze`: Sets `frozen=true` in agent metadata, sets status to OFFLINE
   - `POST /agents/{agent_id}/unfreeze`: Clears `frozen` flag
2. **Agent Registry Methods** (added to `agent_registry.py`):
   - `set_agent_frozen(agent_id, frozen)`: Updates metadata with `frozen` and `frozen_since` timestamps
   - `is_agent_frozen(agent_id)`: Checks metadata for `frozen=true`
3. **Task Queue Protection**: Modified `get_available_agents()` to skip agents where `metadata.frozen=true`
4. **CLI Integration**: Updated `hermes-freeze-agent` and `hermes-unfreeze-agent` to call API endpoints after systemd service stop/start
5. **Auto-Unfreeze**: Systemd timer `hermes-unfreeze-{agent}.timer` triggers after 24h, runs `hermes-unfreeze-agent --name {agent} --auto`

## Technical Steps for DIM-04: hermes-new-agent Integration
1. **Fixed API Key Generation**:
   - Correct syntax: `python3 manage_keys.py generate "hermes-${AGENT_NAME}"` (positional arg, not `--agent`)
   - Extraction: `API_KEY=$(echo "$KEY_OUTPUT" | grep "API Key:" | awk '{print $NF}')`
2. **Fixed API Endpoint**: Registration at `POST /agents/register` (not `/api/agents/register`)
   - Correct payload: `{"agent_id": "...", "agent_name": "...", "capabilities": [...], "metadata": {...}}`
3. **Fixed Registry Connection**: All `agent_registry.py` methods use local `sqlite3.connect()` instead of non-existent `self.conn`
4. **Verification**: Tested with `hermes-new-agent --name testfull --port 9192 --type swarm --cluster test`

## Common Fixes
- **Syntax Check**: All Python scripts validated with `python3 -m py_compile <file>`
- **Service Restart**: `systemctl restart hermes-orchestrator` requires user approval for system service changes
- **Error Debugging**: API errors checked via `journalctl -u hermes-orchestrator --no-pager -n 50 | grep -A10 "ERROR"`