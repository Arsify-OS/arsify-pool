# Deploying Custom Hermes Agent Containers

## Image Specifics (nousresearch/hermes-agent:latest)
- Default entrypoint syncs bundled skills before running commands. To run custom scripts, override entrypoint:
  ```yaml
  entrypoint: ["/bin/sh", "-c"]
  command: "/opt/hermes/.venv/bin/python3 /app/scripts/your_script.py"
  ```
- Python binary path: `/opt/hermes/.venv/bin/python3`
- Pre-installed modules: `requests` is included, `schedule` is NOT. Install missing deps via:
  ```bash
  /opt/hermes/.venv/bin/python3 -m pip install schedule -q
  ```
  Or simplify scripts to avoid non-included dependencies.

## Docker Compose Requirements
- Always include `extra_hosts` to access host services (e.g., Orchestrator API on port 8000):
  ```yaml
  extra_hosts:
    - "host.docker.internal:host-gateway"
  ```
- Port selection: Scan existing ports to avoid conflicts:
  ```bash
  ss -tlnp | awk '{print $4}' | grep -oE '[0-9]+$' | sort -n | uniq
  ```
  Avoid ports in use: 3000-3001, 8000, 8645, 9135-9137, 9119-9142 (update based on current VPS state).

## Credential Retrieval
- Telegram bot token: Check `/root/.hermes/.hermes_history` for lines containing "token for bot Hermes Upshalter"
- Telegram chat ID: Check `/root/.hermes/channel_directory.json` for `telegram` platform entries.

## Common Pitfalls
- **Container restarting (127/0 exit code)**: Usually missing entrypoint override or wrong Python path
- **ModuleNotFoundError**: Install deps via `python3 -m pip install` inside container, or remove unneeded dependencies
- **Port conflicts**: Always scan existing ports before assigning new ones
