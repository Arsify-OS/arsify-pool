---
name: hermes-agent-ops
description: "Maintain, update, and fix common issues with Hermes Agent (core agent operations)"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Hermes Agent, Maintenance, Updates, Debugging]
    related_skills: [github-repo-management]
---

# Hermes Agent Operations

Maintain, update, and troubleshoot the core Hermes Agent installation. Covers common failure modes, patches, and clean install procedures.

## Prerequisites
- Root/sudo access for system-wide installs
- `curl`, `git`, `python3.11+`, `node22+` installed

---

## 1. Clean Reinstall (Fix Stash/Update Errors)
When the official installer fails due to local uncommitted changes in `/usr/local/lib/hermes-agent` (causes stash errors):
```bash
rm -rf /usr/local/lib/hermes-agent
rm -f /usr/local/bin/hermes
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

## 2. Terminal Tool FileNotFoundError Fix
Hermes Agent's `tools/terminal_tool.py` raises `FileNotFoundError` if the current working directory is deleted when calling `os.getcwd()`.

### Patched Locations (already applied to latest agent code, included here for reference):
1. **Line ~1018 (default_cwd assignment)**:
```python
if env_type == "local":
    try:
        default_cwd = os.getcwd()
    except FileNotFoundError:
        # Fallback to /root if cwd is deleted
        default_cwd = "/root"
```

2. **Line ~1040 (docker_cwd_source assignment)**:
```python
_env_cwd = os.getenv("TERMINAL_CWD")
if _env_cwd:
    docker_cwd_source = _env_cwd
else:
    try:
        docker_cwd_source = os.getcwd()
    except FileNotFoundError:
        docker_cwd_source = "/root"
```

## 3. Verify Installation
```bash
hermes --version
hermes doctor  # Check system compatibility
```

## 4. Hermes Workspace Setup (Companion UI)
Web UI for Hermes Agent: chat, memory, skills, terminal, files in one interface. Requires Node.js 22+, pnpm, Python 3.11+:

### One-Liner Install (Recommended)
```bash
curl -fsSL https://hermes-workspace.com/install.sh | bash
```
This script:
1. Verifies Node 22+, git, pnpm
2. Installs hermes-agent via official Nous installer
3. Clones hermes-workspace to ~/hermes-workspace
4. Configures .env, installs deps, links bundled skills

### Manual Setup (If one-liner fails)
```bash
git clone https://github.com/outsourc-e/hermes-workspace.git ~/hermes-workspace
cd ~/hermes-workspace
pnpm install
```

### Critical: Enable Gateway HTTP API (Port 8642)
The Hermes Gateway does NOT enable the HTTP API server (required for workspace communication) by default. Add this to `~/.hermes/.env`:
```bash
echo "API_SERVER_ENABLED=true" >> ~/.hermes/.env
```
Restart the gateway after adding this setting.

### Configure Workspace .env
If the workspace cannot auto-detect the hermes-agent installation, add these to `~/hermes-workspace/.env`:
```bash
HERMES_AGENT_PATH=/usr/local/lib/hermes-agent
CLAUDE_AGENT_PATH=/usr/local/lib/hermes-agent
```

### Start Services
1. Start Hermes Gateway (Terminal 1):
   ```bash
   hermes gateway run
   ```
   Verify it listens on port 8642:
   ```bash
   ss -tlnp | grep 8642
   ```
2. Start Workspace UI (Terminal 2):
   ```bash
   cd ~/hermes-workspace && pnpm dev
   ```
3. Access Workspace:
   - Local machine: Open http://localhost:3000 in your browser.
   - Remote VPS: Either use SSH port forwarding (`ssh -L 3000:localhost:3000 user@vps-ip`) or open port 3000 in UFW firewall:
     ```bash
     ufw allow 3000/tcp
     ufw reload
     ```
     Then access via `http://<vps-public-ip>:3000`.

### Verify Connectivity
Test gateway health:
```bash
curl -s http://localhost:8642/health  # Should return {"status": "ok", "platform": "hermes-agent"}
```
Test workspace accessibility:
```bash
curl -s -I http://<vps-public-ip>:3000  # Should return HTTP/1.1 200
```
Check workspace-gateway connection (watch workspace logs for `[gateway] Connected to Hermes gateway at http://127.0.0.1:8642`).

### Pitfall: UFW Firewall Blocking Ports
Most VPS have UFW active by default. If you cannot access the workspace externally, check UFW status (`ufw status`) and ensure port 3000 is allowed. The gateway (port 8642) only needs to be exposed if you want external API access, otherwise keep it bound to 127.0.0.1.

### Pitfall: Gateway API is Opt-In
Never assume the gateway will listen on 8642 after a fresh install—always set `API_SERVER_ENABLED=true` in `~/.hermes/.env` first. Without this, the workspace cannot connect to the agent.

## 5. VPS Cleanup for Hermes-Only Instances
When running a VPS that only hosts Hermes Agent, clean up unnecessary resources to free disk space:
1. **Clean Docker/Containerd**: Remove unused images, containers, and volumes (typically frees 10-25GB):
   ```bash
   docker system prune -a --volumes -f
   ```
2. **Clean User Caches**: Remove cached files in /root/.cache (commonly 2-3GB from npm, pip, etc.):
   ```bash
   rm -rf /root/.cache/*
   ```
3. **Clean APT Cache**:
   ```bash
   apt clean && apt autoremove -y
   ```
4. **Verify Disk Usage**:
   ```bash
   df -h /
   du -sh /* 2>/dev/null | sort -rh | head -10
   ```

## Hermes C-Suite Docker Setup
To set up a Docker-based Hermes C-Suite instance with custom project/container names:
1. Stop existing containers: `cd /docker/<existing-project> && docker compose down`
2. Rename project directory: `mv /docker/<existing-project> /docker/hermes-c-suite`
3. Edit `docker-compose.yml` to set `container_name: agent-hermes-ceo` under the Hermes service
4. Edit `.env` in the project directory to add `COMPOSE_PROJECT_NAME=hermes-c-suite`
5. Restart containers: `cd /docker/hermes-c-suite && docker compose up -d`
6. Open UFW port for ttyd web terminal: `ufw allow 32774/tcp` (supports IPv4 and IPv6)

## Fixing Auxiliary Title Generation Errors
Error: `Auxiliary title generation failed: No LLM provider configured for task=title_generation provider=auto`
Fix steps:
1. Add OpenRouter API key to `~/.hermes/.env` (not other .env files): `echo "OPENROUTER_API_KEY=your-key" >> ~/.hermes/.env`
2. Set auxiliary provider: `hermes config set auxiliary.title_generation.provider openrouter`
3. Set auxiliary model: `hermes config set auxiliary.title_generation.model tencent/hy3-preview:free`
4. Verify configuration: `hermes doctor`

Pitfall: Never add OpenRouter API keys to Docker .env files; always use `~/.hermes/.env` for host-level Hermes configuration.

For full VPS cleanup steps tailored to Hermes-only setups, see `references/vps-cleanup.md`.

## References
- [Terminal Tool Fixes](references/terminal-tool-fixes.md) (detailed patch context)
- [Official Hermes Agent Repo](https://github.com/NousResearch/hermes-agent)
- [Hermes Workspace Repo](https://github.com/outsourc-e/hermes-workspace)
