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

## Hermes Workspace Deployment

### Gateway Configuration Pitfalls
1. **Duplicate .env Entries**: Manual edits to `~/.hermes/.env` often leave duplicate lines (e.g., `API_SERVER_HOST`, `API_SERVER_ENABLED`). Always clean duplicates before restarting Gateway:
   ```bash
   sort -u ~/.hermes/.env -o ~/.hermes/.env
   ```
2. **API_SERVER_HOST Binding**: Setting `API_SERVER_HOST=0.0.0.0` without `API_SERVER_KEY` will cause Gateway to refuse startup. Use `API_SERVER_HOST=127.0.0.1` for local access, or set a strong `API_SERVER_KEY` if binding to public interfaces.
3. **Open Access**: To skip user allowlist configuration, set `GATEWAY_ALLOW_ALL_USERS=true` in `~/.hermes/.env` to allow all unauthorized users.
4. **Starting Long-Lived Processes**:
   - For temporary background processes (Hermes session lifespan only): Use the `terminal` tool with `background=true` parameter, so Hermes can track and manage the process. Example:
     ```bash
     terminal(background=true, command="cd ~/.hermes && hermes gateway run")
     ```
   - For **24/7 persistent services** (survives reboots, Hermes session ends): Use PM2 process manager with bash wrapper scripts for Python-based services (see [24/7 Service Management with PM2](#24-7-service-management-with-pm2)).
   - Never use `nohup`, `disown`, `setsid`, or raw `&` for long-lived processes — PM2 is preferred for persistent services to prevent system blocks and enable auto-restart.

5. **Deprecated .env Entries**: Remove `TERMINAL_CWD` from `~/.hermes/.env` (deprecated). Move to `config.yaml` instead:
   ```yaml
   terminal:
     cwd: /your/project/path
   ```
   Then remove the old entry from `~/.hermes/.env` to suppress deprecation warnings.

For Nginx reverse proxy setup for Hermes Workspace, see `references/nginx-subdomain-workspace.md`.
See [references/hermes-workspace-deployment.md](references/hermes-workspace-deployment.md) for full deployment workflows including:
- Local production setup with PM2 process management
- Docker Compose configuration for Workspace + Agent
- Nginx path-based reverse proxy setup (e.g., `/workspace`)
- Common startup issues and fixes

## 24/7 Service Management with PM2
For services that need to run persistently (survive reboots, Hermes session ends), use PM2 process manager. This applies to Hermes Gateway, Hermes Dashboard, 9Router, and other long-lived services.

### Prerequisites
- PM2 installed globally: `npm install -g pm2`
- Existing PM2 setup: If not already configured, run `pm2 startup systemd -u root --hp /root` to enable auto-start on boot.

### Critical Pitfall: Python Services and Venv
Hermes Agent services (Gateway, Dashboard) are Python-based and require the hermes-agent venv (`/usr/local/lib/hermes-agent/venv`). PM2 cannot directly execute these services because it defaults to the Node.js interpreter. **Fix**: Create bash wrapper scripts that activate the venv before running the hermes command.

Example wrapper for Hermes Gateway (`/root/start-hermes-gateway.sh`):
```bash
#!/bin/bash
source /usr/local/lib/hermes-agent/venv/bin/activate
exec /usr/local/bin/hermes gateway run
```
Make executable: `chmod +x /root/start-hermes-gateway.sh`

Example wrapper for Hermes Dashboard (`/root/start-hermes-dashboard.sh`):
```bash
#!/bin/bash
source /usr/local/lib/hermes-agent/venv/bin/activate
exec /usr/local/bin/hermes dashboard --host 0.0.0.0 --port 9119 --no-open --insecure
```
Make executable: `chmod +x /root/start-hermes-dashboard.sh`

### Adding Services to PM2
1. **Hermes Gateway**:
   ```bash
   pm2 start /root/start-hermes-gateway.sh --name "hermes-gateway" --interpreter bash
   ```
2. **Hermes Dashboard**:
   ```bash
   pm2 start /root/start-hermes-dashboard.sh --name "hermes-dashboard" --interpreter bash
   ```
3. **9Router (Third-Party AI Proxy)**:
   Install via npm: `npm install -g 9router`
   Add to PM2: `pm2 start /usr/bin/9router --name "9router" -- --no-browser --log`
   (9Router is Node.js-based, so no wrapper needed)

### Persist PM2 State
After adding all services, save the process list to persist across reboots:
```bash
pm2 save
```

### Enable PM2 Auto-Start
Ensure PM2 starts on VPS boot:
```bash
env PATH=$PATH:/usr/bin pm2 startup systemd -u root --hp /root
systemctl enable pm2-root
```

### Handling Port Conflicts
If a service fails to start due to port in use:
1. **Identify the conflicting process**:
   ```bash
   lsof -i :<port> -P -n  # e.g., lsof -i :9119 -P -n
   ps aux | grep <PID>    # Check what's running
   ```
2. **Common scenario**: Duplicate hermes dashboard instances (one standalone PID, one PM2-managed) both trying to bind the same port. PM2 service will restart loop with "address already in use" errors.
3. **Kill the conflicting process**:
   ```bash
   kill <PID>  # e.g., kill 739
   ```
   If terminal tool fails with FileNotFoundError (cwd deleted), use execute_code with subprocess instead:
   ```python
   import subprocess
   subprocess.run(['kill', '<PID>'])
   ```
4. **Restart the PM2 service**:
   ```bash
   pm2 restart <service-name>
   ```
5. **Verify**: Check `pm2 list` for stable uptime (not 0s) and `pm2 logs <service-name>` for clean startup.

### Verify Services
Check status: `pm2 list`
Check logs: `pm2 logs <service-name> --lines 20`
Check listening ports: `ss -tlnp | grep -E "9119|8642|20128"`

### External Access (UFW Firewall)
If services are inaccessible from external networks, ensure UFW allows the required ports:
```bash
ufw allow 20128/tcp  # 9Router
ufw allow 9119/tcp  # Hermes Dashboard
ufw reload
```

## Prerequisites
- Production startup requires `CLAUDE_PASSWORD` and `HOST=0.0.0.0` — silent exit occurs if missing for remote access.
- `vite build` outputs to `dist/` but the default `start` script expects `.output/server/index.mjs` — create a symlink between the two.
- Avoid raw `&` background commands for long-lived processes; use PM2 with bash wrapper scripts for Python services to prevent system blocks and enable auto-restart.
- Docker Compose setups need `extra_hosts: "host.docker.internal:host-gateway"` added to the hermes-agent service to access Ollama running on the host.
- Hermes Agent Gateway refuses to start on `0.0.0.0` without `API_SERVER_KEY` set in `~/.hermes/.env`. Set `API_SERVER_KEY` and `API_SERVER_HOST=127.0.0.1` for local use. If starting gateway fails with "Refusing to start: binding to 0.0.0.0 requires API_SERVER_KEY", add the key to `~/.hermes/.env` and retry.
- Hermes Workspace exits silently (exit code 0) if required environment variables are missing: `HOST`, `PORT`, `CLAUDE_PASSWORD` (for remote access), `HERMES_API_URL` (pointing to Gateway at `http://127.0.0.1:8642`). Always verify Gateway is running (`curl -s http://localhost:8642/health` returns 200) before starting Workspace.
- Nginx path-based setup (e.g., `/workspace`) requires the application to handle base path correctly; Vite dev server serves at `/` by default. For easier setup, consider using a subdomain (e.g., `workspace.hermes.upshalter.com`) instead of path-based proxy.
- Docker Compose setups may pull wrong images (e.g., `hostinger/hvps-hermes-agent` instead of `nousresearch/hermes-agent`); verify image names in `docker-compose.yml` before running `docker compose up`.

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

**Personal Use Workflow**: When setting up Hermes Workspace for personal use, prefer fresh clone (`git clone https://github.com/outsourc-e/hermes-workspace.git ~/hermes-workspace-personal`) over debugging existing installs — existing installs may have conflicting configs or corrupted dependencies.

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
   curl -s http://localhost:8642/health  # Should return 200
   ```
   **If Gateway fails to start** with "Refusing to start: binding to 0.0.0.0 requires API_SERVER_KEY":
   ```bash
   echo "API_SERVER_KEY=your-secret-key" >> ~/.hermes/.env
   echo "API_SERVER_HOST=127.0.0.1" >> ~/.hermes/.env
   hermes gateway run  # Retry
   ```
2. Start Workspace UI (Terminal 2):
   ```bash
   cd ~/hermes-workspace && pnpm dev
   ```
   For production: `cd ~/hermes-workspace && NODE_ENV=production HOST=0.0.0.0 PORT=3000 CLAUDE_PASSWORD=your-password node .output/server/index.mjs`
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

### Path-Based Nginx Reverse Proxy (e.g., /workspace)
Expose Hermes Workspace at a subpath (e.g., `hermes.upshalter.com/workspace`) instead of a dedicated port/subdomain.

#### Prerequisites
- Hermes Workspace built: `cd /root/hermes-workspace && pnpm build`
- Nginx installed and running
- DNS A record set: `hermes.upshalter.com` → VPS public IP (e.g., 76.13.194.136)

#### Steps
1. **Create Nginx config**: Save the config from `references/hermes-workspace-nginx-path.conf` to `/tmp/hermes-workspace-nginx.conf`
2. **Deploy config**:
   ```bash
   cp /tmp/hermes-workspace-nginx.conf /etc/nginx/sites-available/hermes-workspace
   ln -sf /etc/nginx/sites-available/hermes-workspace /etc/nginx/sites-enabled/
   nginx -t && nginx -s reload
   ```
3. **Start Hermes Workspace** (bind to loopback for proxy):
   ```bash
   cd /root/hermes-workspace && NODE_ENV=production HOST=127.0.0.1 PORT=3000 node dist/server/server.js
   ```
   Use terminal tool with `background=true` parameter for long-running process (do NOT use `&` in command string).

#### Pitfalls
- **No `&` for background**: Always use terminal tool's `background=true` parameter for long-running services, never `&` in the command.
- **System path write restrictions**: write_file tool cannot write to `/etc/nginx/*`; use terminal with `cp`/`mv` instead.
- **Silent exits**: Hermes Workspace exits silently if `.env` is misconfigured or build failed; verify `pnpm build` succeeds first.
- **Rewrite rule required**: The `rewrite ^/workspace(/.*)$ $1 break;` line is mandatory to strip the `/workspace` prefix before proxying to the app.

#### Reference
See `references/hermes-workspace-nginx-path.conf` for the full Nginx configuration template.
See also `references/nginx-path-based-setup.md` for lessons learned from real-world /workspace setup (base path mismatches, config placement errors).

## 5. Configure Hermes Agent to Use Local LLM (Ollama)

When running Ollama as a local LLM server on the host (for CPU-only VPS or cost savings), configure Hermes Agent (host or container) to use it.

### Host Configuration

Edit `~/.hermes/config.yaml`:
```yaml
model:
  default: phi3:mini
  provider: ollama
  base_url: http://127.0.0.1:11434/v1
  api_mode: chat_completions
```

Verify Ollama is listening: `curl -s http://127.0.0.1:11434/api/tags`

### Docker Container Accessing Host Ollama

When Hermes Agent runs in Docker, use `host.docker.internal` to reach host services:

1. **Run container with `--add-host`**:
   ```bash
   docker run -d \
     --name agent-hermes-ceo \
     --add-host=host.docker.internal:host-gateway \
     -p 32776:4860 \
     ghcr.io/hostinger/hvps-hermes-agent:latest
   ```

2. **Container config (`~/.hermes/config.yaml` inside container)**:
   ```yaml
   model:
     default: phi3:mini
     provider: ollama
     base_url: http://host.docker.internal:11434/v1
     api_mode: chat_completions
   ```

3. **Verify from inside container**:
   ```bash
   docker exec agent-hermes-ceo curl -s http://host.docker.internal:11434/api/tags
   ```

### Pitfalls

- **OOM Kills on Low-Memory VPS**: Ollama loading 2-3GB models triggers OOM killer on 8GB RAM. Fix: add 4GB swap (`dd if=/dev/zero of=/swapfile bs=1M count=4096; chmod 600 /swapfile; mkswap /swapfile; swapon /swapfile`). Make permanent in `/etc/fstab`.
- **Container Can't Reach Host**: Missing `--add-host=host.docker.internal:host-gateway` during `docker run`. Without it, `host.docker.internal` won't resolve.
- **Ollama Permission Denied**: Service fails to create `/usr/share/ollama`. Fix: `mkdir -p /usr/share/ollama && chown -R ollama:ollama /usr/share/ollama`.

## 6. VPS Cleanup for Hermes-Only Instances
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

## 7. Profile Management
Hermes Agent supports multiple isolated profiles, each with their own config, API keys, sessions, skills, and memory. Use profiles to separate work contexts (e.g., personal, team, server-specific setups).

### List All Profiles
```bash
hermes profile list
```
Output shows profile name, active model, gateway status, and alias. The active profile is marked with `◆`.

### View Profile Details
Check config, paths, skills count, and alias for a specific profile:
```bash
hermes profile show <profile-name>
```
Example: `hermes profile show domain` returns path, model, gateway status, skills count, .env status, SOUL.md status, and alias path.

### Switch Active Profile
Set the default profile to use for all subsequent `hermes` commands:
```bash
hermes profile use <profile-name>
```

### Create a New Profile
```bash
hermes profile create <new-profile-name>
```
This creates a new directory under `~/.hermes/profiles/<new-profile-name>` with default config, .env, and SOUL.md.

### Delete a Profile
```bash
hermes profile delete <profile-name>
```
Warn: This removes all profile data (config, sessions, skills, memory) permanently.

### Profile Aliases
Each profile can have an alias wrapper script (created automatically on profile creation) in `~/.local/bin/`:
```bash
ls -la ~/.local/bin/ | grep <profile-name>
```
Run the alias directly to launch Hermes Agent under that profile: `domain` (instead of `hermes --profile domain`).

### Common Profile Use Cases
- Separate personal and work tasks
- Isolate team-specific configurations (e.g., `progamer-team` profile)
- Dedicated server profiles for headless VPS setups

### Pitfalls
- Profiles share the same Hermes Agent installation (/usr/local/lib/hermes-agent) but have isolated user data.
- Switching profiles does not restart running gateway instances; stop the gateway first if switching profiles for gateway use.
- Profiles created via `hermes profile create` may have fewer skills (92) than default (96) because not all enabled skills are copied to new profiles.
- Identify unused profiles by checking: empty sessions directories (`ls -la ~/.hermes/profiles/*/sessions/`), minimal logs (only startup messages in `agent.log`), and recent creation dates with no chat activity.
- Unused test profiles are safe to delete; each takes ~11MB (minimal space impact).
- See `references/profile-investigation.md` for detailed investigation patterns.

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
