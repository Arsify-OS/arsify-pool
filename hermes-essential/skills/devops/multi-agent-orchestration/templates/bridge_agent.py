#!/usr/bin/env python3
"""
Generic Orchestrator Bridge Agent Template
Connects Hermes Agent instances to the orchestrator
Supports multiple agents via environment variables
"""

import os
import sys
import logging
import subprocess
import json
from typing import Dict, Any

# Add orchestrator SDK to path
sys.path.insert(0, '/usr/local/lib/hermes-orchestrator')

from sdk.agent_base import AgentBase
from sdk.agent_config import AgentConfig

logger = logging.getLogger(__name__)

class GenericBridgeAgent(AgentBase):
    """Generic bridge agent for Hermes Agent instances"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.hermes_port = config.metadata.get('port', 9000)
        self.hermes_api_base = f"http://localhost:{self.hermes_port}"
        logger.info(f"Bridge agent initialized for {config.agent_name} on port {self.hermes_port}")
    
    def execute_task(self, task: Dict[str, Any]) -> Any:
        """Execute task by delegating to appropriate handler"""
        
        task_type = task.get("type", "unknown")
        task_data = task.get("data", {})
        
        logger.info(f"Executing task type: {task_type}")
        
        # Route task to appropriate handler
        handlers = {
            "shell_command": self._execute_shell_command,
            "file_read": self._read_file,
            "file_write": self._write_file,
            "hermes_command": self._execute_hermes_command,
            "system_info": self._get_system_info,
        }
        
        handler = handlers.get(task_type)
        if handler:
            return handler(task_data)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    def _execute_shell_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a shell command"""
        command = data.get("command", "")
        if not command:
            return {"error": "No command provided"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": str(e)}
    
    def _read_file(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file"""
        path = data.get("path", "")
        if not path or not os.path.exists(path):
            return {"error": "Invalid file path"}
        
        try:
            with open(path, 'r') as f:
                content = f.read()
            return {"content": content}
        except Exception as e:
            return {"error": str(e)}
    
    def _write_file(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Write to a file"""
        path = data.get("path", "")
        content = data.get("content", "")
        
        try:
            with open(path, 'w') as f:
                f.write(content)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    def _execute_hermes_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Hermes Agent command via its API"""
        endpoint = data.get("endpoint", "/")
        method = data.get("method", "GET")
        
        try:
            import requests
            response = requests.request(
                method,
                f"{self.hermes_api_base}{endpoint}",
                **data.get("request_kwargs", {})
            )
            return {
                "status_code": response.status_code,
                "response": response.text
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_system_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get basic system info"""
        import platform
        return {
            "platform": platform.platform(),
            "hostname": platform.node(),
            "python_version": platform.python_version()
        }

if __name__ == "__main__":
    # Load configuration from environment variables
    config = AgentConfig(
        agent_id=os.getenv("BRIDGE_AGENT_ID", "generic-bridge"),
        agent_name=os.getenv("BRIDGE_AGENT_NAME", "Generic Bridge Agent"),
        orchestrator_url=os.getenv("ORCHESTRATOR_URL", "http://localhost:8000"),
        api_key=os.getenv("ORCHESTRATOR_API_KEY"),
        capabilities=["shell_command", "file_read", "file_write", "hermes_command", "system_info"],
        metadata={
            "port": int(os.getenv("BRIDGE_PORT", "9000"))
        }
    )
    
    # Initialize and run the agent
    agent = GenericBridgeAgent(config)
    agent.run()