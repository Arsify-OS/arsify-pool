# Docker Compose Troubleshooting - Session 2026-05-03

## Common Issues and Solutions

### Issue 1: Agent Container Exits Immediately (Exit Code 0)

**Symptom:**
```
Container hermes-workspace-fresh-hermes-agent-1 exited (0)
dependency failed to start: container hermes-workspace-fresh-hermes-agent-1 exited (0)
```

**Logs show:**
```
Warning: Input is not a terminal (fd=0).
Goodbye! ⚕
```

**Root Cause:**
Default Docker entrypoint runs `hermes` in interactive CLI mode, which immediately exits when stdin is not a TTY.

**Solution:**
Add explicit command to run gateway mode in `docker-compose.yml`:
```yaml
hermes-agent:
  image: nousresearch/hermes-agent:latest
  command: ["hermes", "gateway", "run"]  # Override default entrypoint
  env_file:
    - .env
```

---

### Issue 2: Port 8642 Already in Use

**Symptom:**
```
Error response from daemon: failed to set up container networking: 
driver failed programming external connectivity on endpoint hermes-workspace-fresh-hermes-agent-1: 
failed to bind host port 0.0.0.0:8642/tcp: address already in use
```

**Root Cause:**
Host system already runs hermes-gateway on port 8642 (typically via PM2). Docker cannot bind the same port.

**Diagnosis:**
```bash
lsof -i :8642
# Shows: hermes  15169 root   20u  IPv4  72082  TCP 127.0.0.1:8642 (LISTEN)
```

**Solution:**
Comment out port binding in `docker-compose.yml`. Workspace container accesses agent via internal Docker network, not host port:
```yaml
hermes-agent:
  # Port 8642 commented out - already used by PM2 hermes-gateway on host
  # Workspace accesses agent via internal Docker network (hermes-agent:8642)
  # ports:
  #   - '8642:8642'
```

**Why this works:**
- Docker Compose creates internal network: `hermes-workspace-fresh_default`
- Workspace container resolves `hermes-agent` hostname to agent container IP
- Agent still listens on 8642 inside container, just not exposed to host
- `HERMES_API_URL: http://hermes-agent:8642` in workspace environment

---

### Issue 3: Workspace Not Accessible from Outside

**Symptom:**
Port 3000 listening but only on 127.0.0.1:
```bash
lsof -i :3000
# Shows: docker-pr 18527 root  8u  IPv4  93321  TCP 127.0.0.1:3000 (LISTEN)
```

**Root Cause:**
Default docker-compose.yml binds to localhost only:
```yaml
ports:
  - '127.0.0.1:3000:3000'
```

**Solution:**
Change to bind all interfaces:
```yaml
ports:
  - '0.0.0.0:3000:3000'
```

Then recreate container:
```bash
docker compose up -d --force-recreate hermes-workspace
```

**Verification:**
```bash
lsof -i :3000
# Should show: docker-pr ... TCP *:3000 (LISTEN)

curl -I http://localhost:3000
# Should return: HTTP/1.1 200 OK
```

---

### Issue 4: Gateway Shows "disconnected" in Workspace Logs

**Symptom:**
```
[gateway] gateway=http://hermes-agent:8642 mode=disconnected 
missing=[health, chatCompletions, models, streaming, ...]
```

**Diagnosis Steps:**

1. Check agent container health:
```bash
docker compose ps
# hermes-agent should show "Up X seconds (healthy)"
```

2. Test agent health endpoint from inside workspace container:
```bash
docker compose exec hermes-workspace curl -s http://hermes-agent:8642/health
# Should return: {"status":"ok"} or similar
```

3. Check agent logs:
```bash
docker compose logs hermes-agent --tail 50
# Look for "Hermes Gateway Starting..." and no errors
```

**Common Causes:**
- Agent container not healthy (check with `docker compose ps`)
- Missing API keys in `.env` (agent needs at least one provider key)
- Wrong `HERMES_API_URL` in workspace environment (should be `http://hermes-agent:8642`)
- Agent container exited (see Issue 1)

**Solution:**
Ensure agent is healthy, then restart workspace:
```bash
docker compose restart hermes-workspace
```

---

## Environment Variable Requirements

### Minimal `.env` for Docker Compose

```bash
# Production settings
NODE_ENV=production
HOST=0.0.0.0
PORT=3000
TRUST_PROXY=1
COOKIE_SECURE=0

# Authentication (REQUIRED when HOST != 127.0.0.1)
CLAUDE_PASSWORD=YourStrongPassword123!

# API Keys (at least ONE required)
OPENROUTER_API_KEY=sk-or-v1-...
# OR
# ANTHROPIC_API_KEY=sk-ant-...
# OR
# OPENAI_API_KEY=sk-...
```

### Optional but Recommended

```bash
# API Server authentication (if exposing 8642 to host)
API_SERVER_KEY=your-secret-key

# API Server host binding (default: 127.0.0.1 in Docker)
API_SERVER_HOST=0.0.0.0  # Only if exposing to LAN/Tailscale

# Enable API server (already set in docker-compose.yml)
API_SERVER_ENABLED=true
```

---

## Health Check Debugging

### Check Container Health Status

```bash
docker compose ps
```

Expected output:
```
NAME                                        STATUS
hermes-workspace-fresh-hermes-agent-1       Up 2 minutes (healthy)
hermes-workspace-fresh-hermes-workspace-1   Up 2 minutes (healthy)
```

### Inspect Health Check Details

```bash
docker inspect hermes-workspace-fresh-hermes-agent-1 | grep -A 10 Health
```

Shows:
- Health check command: `curl -fsS http://localhost:8642/health`
- Interval: 10s
- Timeout: 5s
- Retries: 5
- Start period: 15s

### Manual Health Check

From host:
```bash
docker compose exec hermes-agent curl -s http://localhost:8642/health
```

From workspace container:
```bash
docker compose exec hermes-workspace curl -s http://hermes-agent:8642/health
```

---

## Network Debugging

### List Docker Networks

```bash
docker network ls | grep hermes-workspace-fresh
```

### Inspect Network

```bash
docker network inspect hermes-workspace-fresh_default
```

Shows container IPs and connectivity.

### Test DNS Resolution

From workspace container:
```bash
docker compose exec hermes-workspace ping -c 3 hermes-agent
```

Should resolve to agent container IP (e.g., 172.18.0.2).

---

## Clean Reinstall Procedure

If containers are in bad state:

```bash
# Stop and remove everything
cd /root/hermes-workspace-fresh
docker compose down -v  # -v removes volumes (WARNING: deletes data)

# Remove old directory
cd /root
rm -rf hermes-workspace-fresh

# Fresh clone
git clone https://github.com/outsourc-e/hermes-workspace.git hermes-workspace-fresh
cd hermes-workspace-fresh

# Create .env (see above)
nano .env

# Apply docker-compose.yml fixes (see Issues 1, 2, 3)
nano docker-compose.yml

# Start fresh
docker compose up -d

# Wait for health checks
sleep 30

# Verify
docker compose ps
curl -I http://localhost:3000
```

---

## Session Context (2026-05-03)

**User Environment:**
- VPS: 76.13.194.136 (hermes.upshalter.com)
- OS: Linux (Ubuntu/Debian)
- Existing PM2 services: hermes-gateway (port 8642), hermes-dashboard (9119), 9router (20128)
- User language: Indonesian
- User preference: Fresh install over fixing old installations

**What Worked:**
1. Uninstall old hermes-workspace and hermes-workspace-personal directories
2. Fresh clone to /root/hermes-workspace-fresh
3. Add `command: ["hermes", "gateway", "run"]` to agent service
4. Comment out port 8642 binding (conflict with PM2)
5. Change workspace port to `0.0.0.0:3000:3000`
6. Copy OPENROUTER_API_KEY from /root/.hermes/.env to workspace .env
7. Set CLAUDE_PASSWORD for authentication

**Final Result:**
- Both containers healthy
- Workspace accessible at http://76.13.194.136:3000
- Password: HermesWorkspace2026!
- Agent gateway running in Docker, separate from PM2 gateway

**Key Insight:**
Docker Compose deployment is fully isolated from host Hermes Agent. The agent container runs its own gateway instance, separate from any PM2-managed gateway on the host. This is why port 8642 conflict occurs and why commenting it out is the correct solution.
