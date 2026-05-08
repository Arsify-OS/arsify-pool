# Hermes Agent Complete Inventory Pattern

## Context
When user asks for complete inventory with roles, functions, and working environments (not just count), they want:
- Full details: name, role/function, port, home directory, workspace
- Deployment method (systemd, docker, pm2, gateway)
- Architecture overview showing how instances relate
- Single consolidated deliverable, not incremental findings

## Investigation Sequence

Execute ALL checks first, then synthesize:

### 1. Docker Containers
```bash
docker ps --filter "name=hermes" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
```

For each container, get environment and mounts:
```bash
docker inspect <container> --format '{{.Config.Env}}' | tr ' ' '\n' | grep -E 'HERMES|WORKSPACE|PROJECT'
docker inspect <container> --format '{{.Mounts}}'
```

### 2. Systemd Services
```bash
systemctl list-units --type=service --state=running | grep hermes
```

Read service files for roles/descriptions:
```bash
cat /etc/systemd/system/hermes-*.service
```

Extract: Description, ExecStart, Environment (especially HERMES_HOME), WorkingDirectory

### 3. PM2 Processes
```bash
pm2 list
```

Check for hermes-cli or related processes.

### 4. Gateway Processes
```bash
ps aux | grep -E "hermes gateway|gateway run" | grep -v grep
```

Check main gateway port:
```bash
curl -s http://localhost:8642/health
```

### 5. Configuration Files
For systemd services, check:
- HERMES_HOME environment variable (data directory)
- Port assignments (--port flag in ExecStart)

For Docker containers, check:
- Workspace mounts (host path → container path)
- Config locations (HERMES_HOME inside container)

## Output Format

Use Python `execute_code` to generate structured output (avoids terminal heredoc issues):

```python
# Structure:
# 1. Header with total count
# 2. Group by deployment method:
#    - SYSTEMD SERVICES (count)
#    - DOCKER CONTAINERS (count)
#    - PM2 MANAGED (count)
#    - GATEWAY (count)
# 3. For each instance:
#    - Name
#    - Description/Role
#    - Function (what it does)
#    - Port
#    - Home directory
#    - Workspace (if applicable)
#    - Status
# 4. Architecture diagram (4-layer model):
#    - Layer 1: Gateway & Routing
#    - Layer 2: Specialized Agents (systemd)
#    - Layer 3: Project-Specific Agents (docker)
#    - Layer 4: Interactive Interface (pm2)
# 5. Notes section with key observations
```

Use box-drawing characters (┌─├│└) and clear hierarchy.

## Language
Respond in user's language (Indonesian if user communicates in Indonesian).

## Pitfall: Incremental Delivery
**WRONG**: Run command → show output → wait for "continue" → run next command
**RIGHT**: Run ALL commands → synthesize data → deliver ONE complete report

User frustration signal: Repeated "continue" responses mean you're drip-feeding instead of completing the task.

## Example Session
2026-05-04 07:28 UTC:
- User: "mari kita hitung ada berapa jumlahan agent hermes yang ada di vps lengkap dengan tugas fungsi dan lingkungan kerja mereka"
- Required 15+ tool calls with user saying "continue" each time (BAD)
- Final result: 10 instances
  - 5 systemd (dashboard, CEO, COO, CTO, CMO)
  - 3 docker (loyx, gamedev, workspace)
  - 1 pm2 (CLI/TUI + Telegram)
  - 1 gateway (host)
- Output: Structured inventory with 4-layer architecture diagram
- Language: Indonesian

## Key Findings from Session
- Systemd services use shared host installation (/usr/local/bin/hermes) with separate HERMES_HOME
- Docker containers are isolated with own configs
- Gateway on host (port 8642) routes to all agents
- CLI agent integrates with Telegram bot (@upshalter_hermes_bot)
- Roles identified: Dashboard, CEO (strategic), COO (infra), CTO (dev), CMO (marketing)
