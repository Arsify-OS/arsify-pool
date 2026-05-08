# Multi-Instance Hermes Agent Troubleshooting

Guide for diagnosing and fixing issues in multi-agent Hermes deployments (C-suite setups, orchestrator patterns, shared-binary architectures).

## Common Deployment Patterns

### Pattern 1: Shared Binary with Systemd Services
Multiple systemd services using the same `/usr/local/bin/hermes` executable, differentiated by:
- Port numbers (9119, 9120, 9121, 9122, 9123)
- Data directories (`/opt/hermes-{role}/data`)
- Role descriptions (CEO, CTO, COO, CMO, Dashboard)

**Example:**
```bash
# All use same binary
ExecStart=/usr/local/bin/hermes dashboard --tui --host 0.0.0.0 --port 9122 --no-open --insecure

# But different data dirs
/opt/hermes-builder/data/
/opt/hermes-infra/data/
/opt/hermes-plaza/data/
/opt/hermes-upshalternal/data/
```

**Characteristics:**
- Lightweight (shared codebase)
- Easy to update (one binary update affects all)
- Isolated data/memory per instance
- All instances share same SOUL.md prompt (standard Hermes Agent)

### Pattern 2: Isolated Docker Containers
Fully isolated instances with their own:
- Container image
- Config files
- Network namespace
- Port mappings

**Example:**
```bash
# Loyx orchestrator
docker run -d --name hermes-agent-loyx \
  -p 8643:8642 \
  nousresearch/hermes-agent:latest \
  hermes gateway run
```

**Characteristics:**
- Complete isolation
- Independent versioning
- Higher resource usage
- Easier to debug (isolated logs)

### Pattern 3: Hybrid (CLI + Containers + Systemd)
Mix of deployment methods:
- PM2-managed CLI session (interactive user access)
- Docker containers (orchestrators, specialized agents)
- Systemd services (dashboard instances, role-based agents)

## Diagnostic Workflow

### Step 1: Inventory All Instances

```bash
# Docker containers
docker ps -a --filter "name=hermes" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

# Systemd services
systemctl list-units --type=service --all | grep hermes

# PM2 processes
pm2 list | grep -E "hermes|9router"

# Raw processes
ps aux | grep -i hermes | grep -v grep
```

### Step 2: Check Service Status

For each instance, verify:
```bash
# Systemd
systemctl status hermes-{name} --no-pager -l

# Docker
docker ps | grep hermes-{name}
docker logs hermes-{name} --tail 30

# PM2
pm2 status {name}
pm2 logs {name} --lines 20
```

### Step 3: Identify Failure Patterns

#### Pattern A: Restart Loop (auto-restart)
**Symptoms:**
- Service shows "activating (auto-restart)"
- High restart counter (4000+)
- Logs show repeated startup attempts

**Common Causes:**
1. **Missing script file** (exit code 127)
   ```
   /bin/bash: /opt/hermes-telegram-bridge.sh: No such file or directory
   ```
   **Fix:** Stop and disable the service
   ```bash
   systemctl stop hermes-{name}
   systemctl disable hermes-{name}
   ```

2. **Port conflict** (exit code 1)
   ```
   ERROR: [Errno 98] error while attempting to bind on address ('0.0.0.0', 9120): address already in use
   ```
   **Fix:** Find and kill conflicting process
   ```bash
   lsof -i :9120 | grep LISTEN
   kill {PID}
   systemctl restart hermes-{name}
   ```

#### Pattern B: Container Exit Loop
**Symptoms:**
- Container status shows "Exited (1)" or "Restarting"
- Container uptime resets to 0s repeatedly

**Common Causes:**
1. **Missing command** (container exits immediately)
   ```yaml
   # Wrong - exits immediately in non-TTY
   command: ["hermes"]
   
   # Correct - keeps container running
   command: ["hermes", "gateway", "run"]
   ```

2. **Missing environment variables**
   - Check `/opt/data/.env` inside container
   - Verify API keys are present

### Step 4: Port Conflict Resolution

When multiple instances compete for the same port:

```bash
# 1. Identify what's using the port
lsof -i :{port} -P -n
ps aux | grep {PID}

# 2. Determine if it's a zombie or legitimate process
# Zombies: Old socat/proxy processes, duplicate dashboard instances
# Legitimate: Active agent with valid purpose

# 3. Kill zombie processes
kill {PID}

# 4. Verify the intended service starts
systemctl restart hermes-{name}
# or
docker restart {container-name}

# 5. Confirm port is now bound correctly
lsof -i :{port} | grep LISTEN
```

**Common Port Conflicts:**
- Port 9120: socat proxy vs hermes-upshalternal
- Port 8642: Multiple gateway instances
- Port 3000: Hermes Workspace vs other Node apps

## Architecture Analysis

### Identifying Agent Types

**Mandiri (Independent):**
- Isolated execution environment (Docker container or PM2 session)
- Own configuration and dependencies
- Can run different Hermes versions
- Examples: Loyx (Docker), hermes-cli (PM2)

**Shared Binary:**
- Multiple services using same `/usr/local/bin/hermes`
- Separate data directories
- Same version across all instances
- Examples: hermes-builder, hermes-infra, hermes-plaza, hermes-upshalternal, hermes-dashboard

**Not Agents:**
- Hermes Workspace: Web UI frontend (Node.js app, not AI agent)
- 9Router: Third-party AI proxy service
- Nginx: Reverse proxy

### Verification Commands

```bash
# Check if services share the same binary
systemctl cat hermes-{name} | grep ExecStart

# Check data directory isolation
ls -la /opt/hermes-*/data/

# Check SOUL.md (agent personality/prompt)
find /opt/hermes-*/data -name "SOUL.md" -exec head -1 {} \;

# Check container images
docker inspect {container} --format '{{.Config.Image}}'
```

## Best Practices

### Port Allocation
- Reserve port ranges per agent type:
  - 8640-8649: Gateway/orchestrator agents
  - 9119-9129: Dashboard instances
  - 3000-3099: Web UIs
- Document port assignments in `/etc/hosts` or project README

### Service Naming
- Use descriptive names: `hermes-{role}` not `hermes-1`, `hermes-2`
- Include role in systemd Description field
- Match container names to their function

### Data Directory Structure
```
/opt/
├── hermes-builder/data/     # CTO agent
├── hermes-infra/data/       # COO agent
├── hermes-plaza/data/       # CMO agent
└── hermes-upshalternal/data/ # CEO agent
```

### Monitoring
- Set up health checks for each instance
- Monitor restart counters (high counts = problem)
- Log aggregation for multi-instance debugging
- Use `journalctl -u hermes-* -f` to watch all systemd services

## Troubleshooting Checklist

When an instance fails:
- [ ] Check service status (`systemctl status` / `docker ps`)
- [ ] Read recent logs (`journalctl -u` / `docker logs`)
- [ ] Verify port availability (`lsof -i :{port}`)
- [ ] Check file existence (for script-based services)
- [ ] Verify environment variables (`.env` files)
- [ ] Test connectivity (curl health endpoints)
- [ ] Check resource usage (memory, CPU)
- [ ] Review restart counter (high = recurring issue)

## Common Fixes Summary

| Issue | Symptom | Fix |
|-------|---------|-----|
| Missing script | Exit code 127, "No such file" | Stop and disable service |
| Port conflict | Exit code 1, "address already in use" | Kill conflicting process |
| Container exits | Status "Exited (1)" | Add proper `command` in docker-compose.yml |
| Missing API key | "No LLM provider configured" | Add key to `/opt/data/.env` (container) or `~/.hermes/.env` (host) |
| High restart count | Service never stable | Check logs for root cause, fix underlying issue |

## Investigation Example

Real-world troubleshooting session (2026-05-04):

**Initial State:**
- 8 Hermes instances detected
- 2 in restart loop (hermes-telegram-bridge, hermes-upshalternal)
- 6 running normally

**Diagnosis:**
```bash
# hermes-telegram-bridge
journalctl -u hermes-telegram-bridge -n 20
# Result: /opt/hermes-telegram-bridge.sh not found (exit 127)

# hermes-upshalternal
journalctl -u hermes-upshalternal -n 30
# Result: Port 9120 already in use (exit 1)

lsof -i :9120
# Result: socat PID 757 listening on 9120
```

**Resolution:**
```bash
# Fix 1: Stop broken service
systemctl stop hermes-telegram-bridge
systemctl disable hermes-telegram-bridge

# Fix 2: Kill port conflict
kill 757
# hermes-upshalternal auto-restarted and bound to 9120 successfully
```

**Final State:**
- 7 active instances (1 disabled)
- All running normally
- 0 restart loops

## Related Skills
- `vps-system-inspection` - System health checks
- `hermes-agent` - Core Hermes configuration
- `github-repo-management` - Managing Hermes source updates
