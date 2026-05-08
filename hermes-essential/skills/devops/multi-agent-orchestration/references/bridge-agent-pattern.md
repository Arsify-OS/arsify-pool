# Bridge Agent Pattern for Hermes Instances

## Problem
Existing Hermes Agent instances (systemd-managed or Dockerized) are full Hermes Agent processes, not simple SDK agents. The SDK `AgentBase` expects to run as the main process, but we need to keep the existing Hermes instance running (for its dashboard, tools, etc.) while connecting it to the orchestrator.

## Solution: Bridge Agent
Create a separate bridge script that:
1. Inherits from SDK `AgentBase`
2. Runs as a sidecar process alongside the Hermes instance
3. Delegates task execution to the Hermes instance via subprocess calls or API

## Implementation

### 1. Bridge Script (`orchestrator_bridge.py`)

```python
"""
Orchestrator Bridge for Hermes Agent
Connects existing Hermes Agent instance to the orchestrator
"""

import os
import sys
import logging
import subprocess
import json
from typing import Dict, Any

sys.path.insert(0, '/usr/local/lib/hermes-orchestrator')

from sdk.agent_base import AgentBase
from sdk.agent_config import AgentConfig

logger = logging.getLogger(__name__)

class BridgeAgent(AgentBase):
    """Bridge agent that connects Hermes Agent to orchestrator"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.hermes_port = config.metadata.get('port', 9120)
        logger.info(f"Bridge agent initialized for {config.agent_name}")
    
    def execute_task(self, task: Dict[str, Any]) -> Any:
        task_type = task.get("type", "unknown")
        task_data = task.get("data", {})
        
        if task_type == "shell_command":
            return self._execute_shell_command(task_data)
        elif task_type == "file_read":
            return self._read_file(task_data)
        elif task_type == "file_write":
            return self._write_file(task_data)
        elif task_type == "hermes_command":
            return self._execute_hermes_command(task_data)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    def _execute_shell_command(self, data):
        command = data.get("command", "")
        if not command:
            return {"error": "No command provided"}
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=300
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}
    
    # ... other methods ...

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    config = AgentConfig.from_env(
        agent_id="upshalternal",
        agent_name="Upshalternal AI CEO"
    )
    config.capabilities = ["shell_command", "file_read", "file_write", "hermes_command"]
    config.metadata = {"version": "1.0.0", "port": 9120}
    
    agent = BridgeAgent(config)
    agent.run()
```

### 2. Systemd Service (`hermes-<agent-id>-bridge.service`)

```ini
[Unit]
Description=<Agent> Orchestrator Bridge - Hermes Agent
After=network.target hermes-<agent-id>.service
Wants=hermes-<agent-id>.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hermes-<agent-id>
Environment="ORCHESTRATOR_URL=http://localhost:8000"
Environment="ORCHESTRATOR_API_KEY=<generated_api_key>"
Environment="PYTHONPATH=/usr/local/lib/hermes-orchestrator:/opt/hermes-<agent-id>"
ExecStart=/usr/bin/python3 /opt/hermes-<agent-id>/orchestrator_bridge.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 3. Key Points

1. **Environment Variable**: Must use `ORCHESTRATOR_API_KEY` (not `HERMES_ORCHESTRATOR_KEY`)
2. **Location**: Place bridge script in agent's data directory (e.g., `/opt/hermes-upshalternal/`)
3. **Dependencies**: Bridge service should start after the main Hermes service
4. **PYTHONPATH**: Must include both orchestrator SDK and agent directory
5. **Capabilities**: Define what tasks the bridge can handle

### 4. Verification

```bash
# Check bridge service status
systemctl status hermes-<agent-id>-bridge --no-pager

# Check registration in orchestrator
cd /usr/local/lib/hermes-orchestrator
python3 manage_keys.py list  # Look for "Last Used" timestamp

# Test task submission (via orchestrator API)
curl -X POST http://localhost:8000/tasks/submit \
  -H "X-API-Key: <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"type":"shell_command","data":{"command":"echo test"}}'
```

## When to Use
- Integrating existing production Hermes instances with orchestrator
- When you need to keep the full Hermes Agent running (dashboard, tools, etc.)
- When you want to delegate orchestrator tasks to existing agents without rewriting them as pure SDK agents

## Alternatives
- **Pure SDK Agent**: Rewrite the agent as a subclass of `AgentBase` (no separate Hermes instance)
- **Direct Integration**: Modify Hermes Agent core to include orchestrator client (complex, not recommended)
