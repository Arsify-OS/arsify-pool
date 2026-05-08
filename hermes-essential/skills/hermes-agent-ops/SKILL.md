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

6. **Gateway Feature Gap (enhancedChat/MCP)**: The `hermes gateway run` (port 8642) in current `nousresearch/hermes-agent:latest` is a messaging gateway, not a full API gateway. Features like `enhancedChat`, `mcp`, or `mcpFallback` are not included. If downstream services (e.g., Hermes Workspace) log `missing=[enhancedChat, mcp, mcpFallback]`:
   - Verify endpoint existence: `docker exec <hermes-agent-container> curl -sI http://localhost:8642/enhancedChat`
   - Check agent logs: `docker logs <hermes-agent-container> --tail 50 | grep -iE "enhanced|mcp"`
   - Env vars `ENHANCED_CHAT=true`/`MCP_ENABLED=true` are NOT supported in current image
   - These features may require newer image, manual config in `/opt/hermes/config.yaml` (inside container), or different deployment mode

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
- **Symlink missing in sites-enabled**: After creating Nginx config in `sites-available/`, always verify symlink exists in `sites-enabled/`. Missing symlinks cause old content (or default site) to be served. Debug: `ls -la /etc/nginx/sites-enabled/ | grep <site>` → if missing: `ln -s /etc/nginx/sites-available/<site> /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx`.
- **Content mismatch after deployment**: If file on disk is correct but `curl` returns old content: (1) Check symlinks in sites-enabled, (2) Verify no conflicting server blocks: `nginx -T 2>&1 | grep -A5 "server_name <domain>"`, (3) Compare checksums: `curl -s URL | md5sum` vs `md5sum /var/www/<site>/index.html`, (4) Reload nginx after config changes: `systemctl reload nginx`.

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

## VPSO Unit Upshalternal Management
When managing the 5 core Hermes Agent systemd services (dashboard, upshalternal, infra, builder, plaza) as part of the VPSO (Virtual Private Service Office) Unit Upshalternal:

### Rebranding Systemd Services
Update service descriptions to reflect VPSO branding:
```bash
sed -i 's/Description=.*/Description=VPSO Unit Upshalternal - [Role] (Port)/' /etc/systemd/system/hermes-<service>.service
systemctl daemon-reload
```
Example descriptions (no COO/CTO/CMO titles per user preference):
- `VPSO Unit Upshalternal - Host Agent (9119)` for hermes-dashboard
- `VPSO Unit Upshalternal - Commander (9120)` for hermes-upshalternal
- `VPSO Unit Upshalternal - Infrastructure (9121)` for hermes-Infrastructure
- `VPSO Unit Upshalternal - Builder (9122)` for hermes-builder
- `VPSO Unit Upshalternal - Plaza (9123)` for hermes-plaza
- `VPSO Unit Upshalternal - Sandbox (9129)` for hermes-sandbox
- `VPSO Unit Upshalternal - Pool (9130)` for hermes-pool
- `VPSO Unit Upshalternal - VPSO (9131)` for hermes-vpso
- `VPSO Unit Upshalternal - Internet (9132)` for hermes-internet

### Unified Management Script (vpsoctl)
Use the updated `vpsoctl` script (see `scripts/vpsoctl`) for batch control of all 5 systemd services AND Docker containers:
- `vpsoctl status`: Check all 5 services + Docker containers with formatted output (box-drawing, emoji per user preference)
- `vpsoctl start/stop/restart`: Batch control for systemd services and upshalter container
- `vpsoctl logs [service]`: View logs (auto-detects systemd or docker)
- `vpsoctl docker {ps|logs|restart}`: Docker management subcommands

Install the script:
```bash
cp scripts/vpsoctl /usr/local/bin/vpsoctl
chmod +x /usr/local/bin/vpsoctl
```

**Update**: Now includes Docker container management (hermes-loyx, hermes-gamedev). The services array includes 23 systemd services grouped into 4 functional clusters (see Clustering Agents with Coordinators). The hermes-upshalternal has been converted from Docker to native systemd service (port 8645). Example services array: `("hermes-dashboard" "hermes-upshalter" "hermes-Infrastructure" ... "hermes-upshalternal")`.

### Adding New Hermes Agent Clone (Systemd Service)
Use this workflow when cloning Hermes Agent for SPK validation or multi-agent testing. All clones are **original (asli)** - same binary `/usr/local/bin/hermes`, different ports.

**Full Workflow** (tested with 7 new clones: sandbox, pool, vpso, internet, c-suite, operation, api):

1. **Create systemd service file** (use heredoc, never sed):
   ```bash
   cat > /etc/systemd/system/hermes-<name>.service << 'EOF'
   [Unit]
   Description=VPSO Unit Upshalternal - <Role> (<port>)
   After=network.target

   [Service]
   Environment="HERMES_ALLOWED_ORIGINS=*"
   Type=simple
   User=root
   ExecStart=/usr/local/bin/hermes dashboard --host 0.0.0.0 --port <port> --no-open --insecure
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   EOF
   ```

2. **Enable and start**:
   ```bash
   systemctl daemon-reload
   systemctl enable --now hermes-<name>
   sleep 2
   ```

3. **Verify service is running & responding**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:<port> && echo " - hermes-<name> (<port>)"
   systemctl status hermes-<name> --no-pager | grep -E "Active:|Description:"
   ```

4. **Add Nginx proxy** (separate server block for each agent, port 812x for agent on 912x):
   ```bash
   cat >> /etc/nginx/sites-available/hermes-agents << 'EOF'

# Proxy untuk <Role> (<port>) via port <proxy-port>
server {
    listen <proxy-port>;
    server_name localhost;

    location / {
        proxy_pass http://127.0.0.1:<port>;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header Origin $http_origin;
        proxy_read_timeout 86400s;
        proxy_buffering off;
    }
}
EOF
   nginx -t && systemctl reload nginx
   curl -s -o /dev/null -w "%{http_code}" http://localhost:<proxy-port> && echo " - proxy <proxy-port> → <name> (<port>)"
   ```
   **Note**: Appending with `cat >>` is OK here because each agent is a **separate server block**, not a location block inside existing server. The pitfall about "no cat >>" only applies to location blocks inside server {}.

5. **Update vpsoctl management script**:
   ```bash
   # 1. Add to services array
   sed -i '/services=(/a\    "hermes-<name>"' /usr/local/bin/vpsoctl
   
   # 2. Update ports display line (add <port> (<Role>) | ...)
   sed -i 's/Ports:.*8645.*/Ports: ... | <port> (<Role>) | 8645 (VPSO Manager)/' /usr/local/bin/vpsoctl
   
   # 3. Update help text Agents: line
   sed -i 's/Agents:.*/Agents: ... <name>(<port>)/' /usr/local/bin/vpsoctl
   ```
   Or edit manually for clarity (see `scripts/vpsoctl` for full updated template).

6. **Final verification**:
   ```bash
   vpsoctl status  # Should show new service as RUNNING
   ```

### Post-`hermes update` Port Conflict Fix
After running `hermes update`, old dashboard processes may still hold ports, causing systemd services to fail with "address already in use":

1. **Identify the conflict**:
   ```bash
   journalctl -u hermes-<name> --no-pager | grep "address already in use"
   lsof -i :<port> | grep LISTEN
   ```

2. **Kill old processes**:
   ```bash
   lsof -i :<port> | grep LISTEN | awk '{print $2}' | xargs -r kill -9
   ```

3. **Restart the service**:
   ```bash
   systemctl restart hermes-<name>
   sleep 2
   systemctl status hermes-<name> --no-pager | grep Active:
   ```

### Checking for GitHub Updates
Before adding clones or renaming agents, check if newer versions exist:

1. **Check hermes-agent binary**:
   ```bash
   hermes --version  # Shows current version + "Update available: X commits behind"
   # If update available: hermes update
   ```

2. **Check hermes-workspace repo** (if cloned):
   ```bash
   cd /root/hermes-workspace-fresh
   git remote -v
   git fetch origin
   git log HEAD..origin/main --oneline  # Shows new commits
   git pull origin main  # Apply updates
   ```

### Pitfalls
- write_file tool cannot write to `/etc/nginx/*` paths; always use terminal with `cat > file << 'EOF'` to edit Nginx configs.
- Never append to Nginx config files with `cat >>`; rewrite the entire file to avoid `location` directives outside `server {}` blocks.
- Always run `nginx -t` before reloading Nginx to catch syntax errors.
- vpsoctl script changes require no restart; they take effect immediately on next run.

### Docker Manager Agent Pattern
To create an agent that can manage Docker containers (like `hermes-upshalter`):

1. **docker-compose.yml with Docker socket mount**:
   ```yaml
   services:
     hermes-<name>:
       image: nousresearch/hermes-agent:latest
       container_name: hermes-<name>
       command: ["/bin/bash", "/workspace/bridge-script.sh"]
       ports:
         - "<host-port>:8642"
       volumes:
         - /root/<project>:/workspace
         - /root/<project>/config:/root/.hermes
         - /var/run/docker.sock:/var/run/docker.sock  # Docker Manager access
       environment:
         - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
         - DOCKER_MANAGER=true
         - ORCHESTRATOR_URL=http://host.docker.internal:8000
         - ORCHESTRATOR_API_KEY=${ORCHESTRATOR_API_KEY}
       extra_hosts:
         - "host.docker.internal:host-gateway"
       restart: unless-stopped
   ```

2. **Bridge script** (`bridge-script.sh`):
   ```bash
   #!/bin/bash
   echo "🚀 Starting Hermes <Name> Agent..."
   echo "Role: Docker Manager"
   if [ -S /var/run/docker.sock ]; then
       echo "✅ Docker socket accessible"
   fi
   export UNIT_UPSHALTERNAL_ROLE="Manager"
   cd /workspace
   exec hermes dashboard --host 0.0.0.0 --port 8642 --no-open --insecure
   ```

3. **Pitfall**: Never use `hermes --port 8642` or `hermes chat --host ...` as container command — these are invalid and cause immediate exit. Use `hermes dashboard --host 0.0.0.0 --port 8642 --no-open --insecure`.

### VPSO Consolidation Workflow
To consolidate legacy Hermes subdomains (hermes.upshalter.com, workspace.upshalter.com) into a single VPSO entry point (workstation.upshalter.com/hermes/):

1. **Backup Nginx configs**:
   ```bash
   cp /etc/nginx/sites-available/workstation-upshalter /etc/nginx/sites-available/workstation-upshalter.bak-$(date +%Y%m%d-%H%M%S)
   cp /etc/nginx/sites-available/hermes.upshalter.com /etc/nginx/sites-available/hermes.upshalter.com.bak-$(date +%Y%m%d-%H%M%S)
   cp /etc/nginx/sites-available/workspace.upshalter.com /etc/nginx/sites-available/workspace.upshalter.com.bak-$(date +%Y%m%d-%H%M%S)
   ```

2. **Add proxy blocks for 5 agent services** to the unified Nginx config (e.g., `/etc/nginx/sites-available/workstation-upshalter`) under the `/hermes/` path:
   ```
   location /hermes/main { proxy_pass http://127.0.0.1:9119; ... }
   location /hermes/upshalternal { proxy_pass http://127.0.0.1:9120; ... }
   location /hermes/agent1 { proxy_pass http://127.0.0.1:9121; ... }
   location /hermes/agent2 { proxy_pass http://127.0.0.1:9122; ... }
   location /hermes/agent3 { proxy_pass http://127.0.0.1:9123; ... }
   ```

3. **Create 301 redirects** for old subdomains to the new VPSO entry point:
   - For hermes.upshalter.com: redirect to `https://workstation.upshalter.com/hermes$request_uri`
   - For workspace.upshalter.com: redirect to `https://workstation.upshalter.com/hermes/workspace$request_uri`
   - Use Let's Encrypt SSL certs in the redirect server blocks.

4. **Disable old sites safely**:
   ```bash
   rm -f /etc/nginx/sites-enabled/hermes.upshalter.com
   rm -f /etc/nginx/sites-enabled/workspace.upshalter.com
   nginx -t && systemctl reload nginx
   ```
   Monitor for issues before permanently deleting config files.

5. **Update VPSO landing page** to highlight Unit Upshalternal and include all service cards.

### Pitfalls
- Always backup Nginx configs and systemd service files before modifying.
- Run `nginx -t` before reloading Nginx to catch syntax errors.
- Disable old sites by removing symlinks first; do not delete config files immediately.
- Use structured terminal output with box-drawing characters and emoji for status commands, per user preference.
- **Nginx location block placement**: Ensure `location` directives are inside a `server { ... }` block. Accidentally placing them outside causes `nginx: [emerg] "location" directive is not allowed here`.
- **Nginx config corruption recovery**: When `sed` or manual edits create duplicate blocks or broken configs, DO NOT try to fix in-place. Instead: (1) Restore from backup: `cp /etc/nginx/sites-available/file.bak /etc/nginx/sites-available/file`, (2) Rebuild clean config using `cat > file << 'EOF' ... EOF`, (3) Verify with `nginx -t` before reloading. This session corrupted config 3+ times with `sed` insertions — clean rebuild is faster and safer.

## Web Terminal Access via ttyd
When the native Hermes Agent TUI fails (npm install permission errors in Docker), use ttyd to expose the CLI via web browser. See `references/ttyd-web-terminal.md` for full setup including systemd service, firewall config, and pitfalls.

Quick setup:
```bash
apt-get install -y ttyd
ttyd -p 4860 -W /usr/local/bin/loyx chat  # Replace 'loyx' with your CLI wrapper
# Open firewall: ufw allow 4860/tcp
# Access: http://<vps-ip>:4860
```

For persistent service, create systemd unit (see reference doc).

## Browser-Use Integration (Senator Workers)

When setting up browser-use API service for Senator Workers to do web scraping with AI browser automation:

### OpenRouter Configuration
browser-use uses langchain-openai which needs explicit configuration for OpenRouter compatibility:
- Pass `api_key=os.getenv("OPENROUTER_API_KEY")`, `base_url="https://openrouter.ai/api/v1"`, and `default_headers` to `ChatOpenAI()`
- Set `OPENAI_API_KEY` env var to OpenRouter key BEFORE any imports
- Load OPENROUTER_API_KEY from `/proc/1/environ` if not in current environment

### Provider Attribute Fix
browser-use checks `llm.provider` attribute. Standard `ChatOpenAI` doesn't have this. Fix with subclass:
```python
from langchain_openai import ChatOpenAI
from pydantic import ConfigDict

class ChatOpenAIWithProvider(ChatOpenAI):
    model_config = ConfigDict(extra='allow')
    
    @property
    def provider(self):
        return "openai"
```

The `ConfigDict(extra='allow')` is required so browser-use can monkey-patch the LLM object for token tracking.

### Playwright Setup
After `pip install browser-use`:
```bash
pip install playwright
playwright install chromium
```

Verify Chromium works: `/root/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome --version`

### Common Issues
- **CDP Timeout**: browser-use may timeout on browser start (30s default) with `TimeoutError: Event handler ... timed out after 30.0s`. This is a CDP (Chrome DevTools Protocol) connection issue.
- **Pydantic Errors**: Without `ConfigDict(extra='allow')`, you'll get `"ChatOpenAI" object has no field "ainvoke"` when browser-use tries to patch the LLM.
- **Missing Playwright**: If you get `ModuleNotFoundError: No module named 'playwright'`, install it in the venv.

### API Service Structure
The browser-use API service typically runs at `/opt/browser-use-service/main.py` on port 8090. Senator containers access it via `http://host.docker.internal:8090`.

See `references/browser-use-openrouter-fix.md` for the complete working `main.py` with all fixes applied.

## CLI Access to Containerized Hermes Agent
When you need to interact with a Hermes Agent running inside a Docker container via CLI from the host:

### Create a Wrapper Script
The container's hermes binary is at `/opt/hermes/.venv/bin/hermes`. Create a host-level wrapper that handles both interactive and non-interactive modes:

```bash
cat > /usr/local/bin/<alias-name> << 'EOF'
#!/bin/bash
# Wrapper script for containerized Hermes Agent CLI access

# Detect TTY to choose correct docker exec mode
if [ -t 0 ]; then
    # Interactive mode (terminal attached)
    docker exec -it <container-name> /opt/hermes/.venv/bin/hermes "$@"
else
    # Non-interactive mode (pipe, script, automation)
    docker exec -i <container-name> /opt/hermes/.venv/bin/hermes "$@"
fi
EOF
chmod +x /usr/local/bin/<alias-name>
```

Example for container `hermes-agent-loyx-hermes-agent-1` with alias `loyx`:
```bash
cat > /usr/local/bin/loyx << 'EOF'
#!/bin/bash
if [ -t 0 ]; then
    docker exec -it hermes-agent-loyx-hermes-agent-1 /opt/hermes/.venv/bin/hermes "$@"
else
    docker exec -i hermes-agent-loyx-hermes-agent-1 /opt/hermes/.venv/bin/hermes "$@"
fi
EOF
chmod +x /usr/local/bin/loyx
```

### Usage
```bash
loyx --version                    # Check version
loyx config show                  # View configuration
loyx -z "your prompt"             # One-shot chat
loyx chat                         # Interactive chat
loyx config set model.default "openai/gpt-4o-mini"  # Change model
```

### Pitfalls
- **TTY detection is critical**: Without the `if [ -t 0 ]` check, piped input or automation will fail with "cannot attach stdin to a TTY-enabled container because stdin is not a terminal".
- **OpenRouter credit limits**: If you get HTTP 402 errors about insufficient credits, the model's max_tokens is too high for your remaining balance. Switch to cheaper models:
  - `openai/gpt-4o-mini` (cheapest, works with low credits)
  - `google/gemini-2.0-flash-thinking-exp` (free tier, may have rate limits)
  - Avoid `anthropic/claude-opus-4.6` (128k max_tokens, very expensive)
- **Container name format**: Docker Compose containers are named `<project>-<service>-<replica>`. Find the exact name with `docker ps --filter name=<project>`.
- **Config location**: Container config is at `/opt/data/config.yaml`, not `~/.hermes/config.yaml`. Use `loyx config show` to verify paths.

## Upgrading Hermes Agent Docker Containers
When upgrading a standalone Hermes Agent container (not part of Hermes Workspace) from an older image to the latest version:

### Prerequisites
- Docker Compose project directory (e.g., `/docker/hermes-agent-loyx/`)
- Existing container running old image (e.g., `ghcr.io/hostinger/hvps-hermes-agent:latest` v0.9.0)
- Target: `nousresearch/hermes-agent:latest` (current: v0.12.0)

### Upgrade Steps
1. **Update docker-compose.yml image**:
   ```yaml
   services:
     hermes-agent:
       image: nousresearch/hermes-agent:latest
       command: ["hermes", "gateway", "run"]  # Required: prevents immediate exit
       restart: unless-stopped
       ports:
         - "4860"
         - "8643:8642"  # Use different host port if 8642 is taken
   ```

2. **Configure API keys in container's .env**:
   The container mounts `/opt/data/` for persistent config. Add API keys to `/opt/data/.env` (not the host project `.env`):
   ```bash
   docker exec <container-name> sh -c "echo 'OPENROUTER_API_KEY=sk-or-v1-...' >> /opt/data/.env"
   ```

3. **Pull new image and recreate container**:
   ```bash
   cd /docker/<project-name>
   docker compose pull
   docker compose down
   docker compose up -d
   ```

4. **Verify upgrade**:
   ```bash
   docker ps | grep <container-name>  # Check status
   docker exec <container-name> cat /opt/hermes/pyproject.toml | grep "^version"  # Check version
   docker logs <container-name> --tail 30  # Check for errors
   ```

### Pitfalls
- **Port conflicts**: If host port 8642 is already in use (e.g., by another Hermes gateway), map to a different host port: `8643:8642` instead of `8642:8642`.
- **Container restart loops**: The `nousresearch/hermes-agent:latest` image defaults to interactive CLI mode, which exits immediately in non-TTY environments. **Fix**: Add `command: ["hermes", "gateway", "run"]` to keep the container running.
- **API keys in wrong location**: The container's Hermes config is at `/opt/data/`, NOT the host project's `.env`. Always exec into the container to add keys to `/opt/data/.env`.
- **Gateway warnings**: "No messaging platforms enabled" is expected if you haven't configured Telegram/Discord/etc. The gateway will still run and expose the HTTP API on port 8642 (internal).
- **Version verification**: The `hermes --version` command may not exist in the container's PATH. Use `cat /opt/hermes/pyproject.toml | grep "^version"` instead.

### Example: Upgrading hermes-agent-loyx
```bash
# 1. Update image in docker-compose.yml
cd /docker/hermes-agent-loyx
# Edit docker-compose.yml: change image to nousresearch/hermes-agent:latest, add command

# 2. Add API key to container's .env
docker exec hermes-agent-loyx-hermes-agent-1 sh -c "grep -v '^# OPENROUTER_API_KEY=' /opt/data/.env > /tmp/.env.tmp && echo 'OPENROUTER_API_KEY=sk-or-v1-...' >> /tmp/.env.tmp && mv /tmp/.env.tmp /opt/data/.env"

# 3. Pull and recreate
docker compose pull
docker compose down
docker compose up -d

# 4. Verify
docker ps | grep loyx
docker exec hermes-agent-loyx-hermes-agent-1 cat /opt/hermes/pyproject.toml | grep "^version"
# Expected: version = "0.12.0"
```

## Fixing Auxiliary LLM Errors (402 / Title Generation / Vision / Web Extract)

When auxiliary LLM calls fail with HTTP 402 or "No LLM provider configured" errors, the root cause is usually empty `api_key` fields in `config.yaml` auxiliary sections.

### Root Cause
`api_key: ''` (empty string) in auxiliary config sections **overrides** env var lookup. Even if `OPENROUTER_API_KEY` is set in the environment, Hermes will send requests with an empty key.

### Fix: Fill All Empty Auxiliary api_key Fields
```bash
# Check which auxiliary sections have empty api_key
grep -A2 "api_key:" ~/.hermes/config.yaml | grep -B1 "''"

# Fill all empty auxiliary api_key fields with OpenRouter key
python3 << 'PYEOF'
import yaml, os

config_path = "/root/.hermes/config.yaml"
key = os.environ.get("OPENROUTER_API_KEY", "")
if not key:
    print("ERROR: OPENROUTER_API_KEY not set"); exit(1)

with open(config_path) as f:
    config = yaml.safe_load(f)

filled = 0
for section in ["vision", "web_extract", "compression", "session_search", "title_generation"]:
    aux = config.get("auxiliary", {}).get(section, {})
    if aux.get("provider") == "openrouter" and not aux.get("api_key"):
        aux["api_key"] = key
        filled += 1
        print(f"  Filled api_key for auxiliary.{section}")

with open(config_path, "w") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
print(f"Total filled: {filled}")
PYEOF
```

### Also Check: Custom Provider Keys
Sections like `skills_hub`, `approval`, `mcp`, `curator` use `custom` provider (e.g., `kr/claude-sonnet-4.5`). These need their own `api_key` in the `custom_providers` section, NOT the OpenRouter key.

### Pitfalls
- **openai/ prefix models**: Avoid `openai/gpt-4o-mini` and other `openai/` prefixed models in auxiliary config on OpenRouter — use `openrouter/<model>` prefix instead.
- **Empty api_key**: `api_key: ''` overrides env var lookup. Remove empty lines.
- **Custom provider rate limits**: HTTP 402 `MONTHLY_REQUEST_COUNT` means the provider's monthly cap is hit. Switch auxiliary tasks to a different provider.
- **TTS**: Use `tts.provider: edge` (free). Remove `tts.openai.model: gpt-4o-mini-tts` from config.
5. **OPENROUTER_API_KEY placeholder**: `api_key: ''` in auxiliary config sections overrides env var lookup. Even if `OPENROUTER_API_KEY` is set, Hermes sends requests with an empty key. Fix: fill all empty auxiliary api_key fields.
6. **SKP DB Write-Back Gap (FASE 2, 2026-05-07)**: Senator tasks can succeed (with `_fallback: true`) but results are NOT persisted to SKP DB. Root cause: when all LLM calls hit rate limits and fallback mode activates, the L4 reflection layer may skip SKP write-back. Fix: ensure Ollama fallback works (recreate worker with `OPENROUTER_URL` pointing to Ollama) and verify L4 SKP write-back triggers regardless of fallback status. Detect: `sqlite3 /root/.hermes/shared_knowledge_pool.db "SELECT count(*) FROM knowledge WHERE source_agent_name LIKE '%senator%';"` — should be >0 after a senator task completes.
7. **Config backup**: Always `cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak` before editing.

## Multi-Instance Deployments
When running multiple Hermes Agent instances on a single VPS (e.g., C-suite setup with CEO/CTO/COO/CMO roles), see `references/multi-instance-troubleshooting.md` for:
- Common failure modes (missing scripts, port conflicts, restart loops)
- Diagnostic workflow for identifying all instances (Docker, systemd, PM2)
- Shared binary vs isolated container patterns
- Architecture analysis (mandiri vs shared agents)
- Port conflict resolution (lsof, kill, restart)
- Best practices for port allocation and data directory isolation

### Creating a New Independent Agent Container
To create a new isolated Hermes Agent instance (similar to Loyx orchestrator pattern), follow this recipe:

1. **Create project directory structure**:
   ```bash
   mkdir -p /docker/hermes-{name}/data
   cd /docker/hermes-{name}
   ```

2. **Create docker-compose.yml** (following Loyx pattern):
   ```yaml
   services:
     hermes-agent:
       image: nousresearch/hermes-agent:latest
       container_name: hermes-{name}
       command: ["hermes", "gateway", "run"]
       restart: unless-stopped
       ports:
         - "{host-port}:8642"  # e.g., 8644:8642
       labels:
         - traefik.enable=false
       env_file:
         - .env
       volumes:
         - ./data:/opt/data
         - /root/{project-dir}:/workspace:rw  # Optional: mount project files
       extra_hosts:
         - "host.docker.internal:host-gateway"
       working_dir: /workspace  # Optional: set if mounting project
   ```

3. **Create .env file**:
   ```bash
   cat > .env << EOF
   ADMIN_USERNAME=hermes
   ADMIN_PASSWORD={generate-secure-password}
   TRAEFIK_HOST=srv1589470.hstgr.cloud
   OPENROUTER_API_KEY={your-api-key}
   COMPOSE_PROJECT_NAME=hermes-{name}
   EOF
   ```

4. **Start container**:
   ```bash
   docker run -d \
     --name hermes-{name} \
     --restart unless-stopped \
     -p {host-port}:8642 \
     -v /docker/hermes-{name}/data:/opt/data \
     -v /root/{project-dir}:/workspace:rw \
     --add-host host.docker.internal:host-gateway \
     --env-file /docker/hermes-{name}/.env \
     -w /workspace \
     nousresearch/hermes-agent:latest \
     hermes gateway run
   ```
   
   Or use docker compose:
   ```bash
   cd /docker/hermes-{name}
   docker compose up -d
   ```

5. **Verify container is running**:
   ```bash
   docker ps | grep hermes-{name}
   docker logs hermes-{name} --tail 30
   ```

6. **Create CLI wrapper** (optional, for easy host access):
   ```bash
   cat > /usr/local/bin/{alias} << 'EOF'
   #!/bin/bash
   if [ -t 0 ]; then
       docker exec -it hermes-{name} /opt/hermes/.venv/bin/hermes "$@"
   else
       docker exec -i hermes-{name} /opt/hermes/.venv/bin/hermes "$@"
   fi
   EOF
   chmod +x /usr/local/bin/{alias}
   ```

### Pitfalls for New Independent Agents
- **Port allocation**: Each agent needs a unique host port. Common pattern: 8643 (Loyx), 8644 (GameDev), 8645 (next agent).
- **Database locks**: If mounting shared project directories, ensure only one agent accesses SQLite databases at a time. Use separate data directories (`./data:/opt/data`) for each agent.
- **Container exits immediately**: Without a command that starts a persistent process, the container will exit. The default entrypoint expects interactive mode. Use one of:
  - `command: ["hermes", "gateway", "run"]` for API gateway only.
  - `command: ["/bin/bash", "/workspace/upshalter-bridge.sh"]` with bridge script that execs `hermes dashboard --host 0.0.0.0 --port 8642 --no-open --insecure` for web UI.
  - Never use `hermes --port 8642` or `hermes chat --host ...` as these are invalid and will cause exit.
- **Missing API keys**: Container won't function without `OPENROUTER_API_KEY` in `.env`. Verify with `docker exec hermes-{name} cat /opt/data/.env`.
- **Working directory**: If mounting project files, set `working_dir: /workspace` so the agent starts in the correct context.

### Example: hermes-gamedev Agent
Real-world example from 2026-05-04 session:
```bash
# Created for Regrow Up World game development
mkdir -p /docker/hermes-gamedev/data
docker run -d --name hermes-gamedev --restart unless-stopped \
  -p 8644:8642 \
  -v /docker/hermes-gamedev/data:/opt/data \
  -v /root/regrow-up-world-dev:/workspace:rw \
  --add-host host.docker.internal:host-gateway \
  --env-file /docker/hermes-gamedev/.env \
  -w /workspace \
  nousresearch/hermes-agent:latest \
  hermes gateway run
# Result: Independent agent running on port 8644, isolated from Loyx (8643)
```

**Docker Manager Variant**: To create an agent that can manage Docker containers (like upshalter), see `references/upshalter-docker-manager.md`. It includes mounting Docker socket, setting `DOCKER_MANAGER=true`, and using `hermes dashboard` command for web UI.
```

### CLI Wrapper Creation
After creating an independent agent container, create a CLI wrapper for convenient host access:
```bash
cat > /usr/local/bin/gamedev << 'EOF'
#!/bin/bash
# Wrapper script untuk akses Hermes Agent GameDev via CLI

# Cek apakah stdin adalah terminal
if [ -t 0 ]; then
    # Interactive mode
    docker exec -it hermes-gamedev /opt/hermes/.venv/bin/hermes "$@"
else
    # Non-interactive mode (pipe, script, etc)
    docker exec -i hermes-gamedev /opt/hermes/.venv/bin/hermes "$@"
fi
EOF
chmod +x /usr/local/bin/gamedev
```

Test the wrapper:
```bash
gamedev --version
gamedev config show
gamedev --tui  # Interactive TUI mode
```

### Quick Diagnosis Commands
```bash
# Inventory all Hermes instances
docker ps -a --filter "name=hermes" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
systemctl list-units --type=service --all | grep hermes
pm2 list | grep -E "hermes|9router"

# Check restart loops
journalctl -u hermes-{name} -n 20 --no-pager

# Find port conflicts
lsof -i :{port} | grep LISTEN

# Check resource usage for all agents
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
ps aux | grep hermes | grep -v grep | awk '{sum+=$6} END {printf "Total Hermes Memory: %.2f MB\n", sum/1024}'
```

### Common Fixes
- **Missing script (exit 127)**: Stop and disable service (`systemctl stop/disable hermes-{name}`)
- **Port conflict (exit 1, "address already in use")**: 
  1. Find conflicting process: `lsof -i :{port} | grep LISTEN`
  2. Check what's using it: `ps aux | grep {PID}`
  3. Kill if safe: `kill {PID}`
  4. Common culprit: socat or duplicate hermes instances
- **Container exits immediately**: Add `command: ["hermes", "gateway", "run"]` to docker-compose.yml
- **Database locked warnings**: Multiple agents accessing same SQLite database. Ensure each agent has isolated data directory.
\n### Clustering Agents with Coordinators\n\nTo improve organization and management, group agents into functional clusters, each with a designated coordinator agent. This structure is reflected in the updated `vpsoctl status` output.\n\n**Current Clusters (4 total):**\n\n1. 🏗️ **Core Infrastructure & Management** (Coordinator: hermes-Infrastructure, port 9121)\n   - Agents: hermes-dashboard (9119), hermes-upshalter (9120), hermes-Infrastructure (9121), hermes-vpso (9131), hermes-operation (9134), hermes-api (9135), hermes-archivist (9124), hermes-upshalternal (8645 native)\n2. 💻 **Development & Builder Tools** (Coordinator: hermes-builder, port 9122)\n   - Agents: hermes-builder (9122), hermes-sandbox (9129), hermes-pool (9130), hermes-frontend (9125), hermes-backend (9126), hermes-workstation (9127), hermes-flowforce (9128)\n3. 📢 **Communication & Collaboration** (Coordinator: hermes-plaza, port 9123)\n   - Agents: hermes-plaza (9123), hermes-internet (9132), hermes-c-suite (9133)\n4. 🌐 **Domain-Specific Agents** (Coordinator: hermes-pendidikan, port 9138)\n   - Agents: hermes-pendidikan (9138), hermes-pariwisata (9139), hermes-finansial (9140), hermes-news (9141), hermes-lingkungan-hidup (9142)\n\n**Updating vpsoctl for Cluster Display:**\n\nThe `vpsoctl status` command now groups services by cluster and shows the coordinator for each. To update vpsoctl:\n\n1. Define cluster arrays in the script.\n2. Print cluster header with emoji and coordinator note.\n3. Iterate over each cluster array to display agent status.\n\nSee the updated `scripts/vpsoctl` for implementation details.\n\n### Converting Docker Agent to Native Systemd Service\n\nIf an agent is running in Docker and you want to convert it to a native systemd service (for consistency, as done with hermes-upshalternal):\n\n1. Stop and remove the Docker container: `docker stop <container> && docker rm <container>`\n2. Create a systemd service file in `/etc/systemd/system/hermes-<name>.service` with the same port (use heredoc).\n3. Reload systemd: `systemctl daemon-reload`\n4. Enable and start: `systemctl enable --now hermes-<name>`\n5. Update vpsoctl: remove from `docker_containers` array, add to `services` array, update Ports line.\n6. Verify: `vpsoctl status` and `curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>`\n\nThis ensures all agents are managed uniformly under systemd, simplifying monitoring and coordination.\n\n## Unified Knowledge Pool (Shared /root/.hermes)

When running multiple Hermes Agent instances (host-based and Docker containers), you can unify their knowledge (memory, skills, config, sessions) by pointing them to the same `~/.hermes` directory.

### Steps for Docker Containers

1. **Stop running containers**:
   ```bash
   cd /docker/<project> && docker compose down
   ```

2. **Merge existing data** (optional, if containers had separate data directories):
   ```bash
   rsync -av /docker/<project>/data/ /root/.hermes/ --ignore-existing
   ```

3. **Update docker-compose.yml**:
   - Change volume mount from `./data:/opt/data` to `/root/.hermes:/opt/data`.
   - Add `user: root` under the service to avoid permission issues (since `/root/.hermes` is owned by root).
   - Example:
     ```yaml
     services:
       hermes-agent:
         image: nousresearch/hermes-agent:latest
         user: root
         command: ["hermes", "gateway", "run"]
         volumes:
           - /root/.hermes:/opt/data
           - /root:/host/root:ro
         # ... other settings
     ```

4. **Fix permissions** (if needed):
   ```bash
   chmod -R 777 /root/.hermes
   ```

5. **Restart containers**:
   ```bash
   cd /docker/<project> && docker compose up -d
   ```

### Host Agents (hermes-cli, hermes-debug)

Host agents already use `/root/.hermes` by default. No changes needed. For a tmux-based debugging agent, create a wrapper script:

```bash
cat > /usr/local/bin/hermes-debug << 'EOF'
#!/bin/bash
SESSION_NAME="hermes-debug"
WORKDIR="/root"

tmux has-session -t "$SESSION_NAME" 2>/dev/null
if [ $? != 0 ]; then
    tmux new-session -d -s "$SESSION_NAME" -c "$WORKDIR"
    tmux send-keys -t "$SESSION_NAME" "hermes chat" Enter
    echo "✅ Started new tmux session: $SESSION_NAME"
fi
exec tmux attach -t "$SESSION_NAME"
EOF
chmod +x /usr/local/bin/hermes-debug
```

Now `hermes-debug` launches a persistent tmux session running Hermes Agent, sharing the same knowledge pool.

### Benefits

- All agents share memory, skills, and config.
- Changes made in one agent reflect in others.
- Simplifies management: single source of truth.

## Debugging Agent Disconnections (hermes-cli, hermes-debug)
When agents like `hermes-cli` or `hermes-debug` lose connection to the Hostinger VPS/orchestrator:
1. **Check tmux sessions first** (hermes-debug uses tmux for persistence, hermes-cli also runs in tmux):
   ```bash
   tmux list-sessions | grep -E "hermes-debug|hermes-cli"
   ```
   If no sessions exist, restart the agent via tmux:
   ```bash
   tmux new-session -d -s hermes-cli 'bash -c "source /root/.bashrc && hermes"'
   tmux new-session -d -s hermes-debug 'bash -c "source /root/.bashrc && hermes"'
   ```
2. **Verify ORCHESTRATOR_API_KEY** is set correctly (agents use this env var, not `HERMES_ORCHESTRATOR_KEY`):
   ```bash
   tmux send-keys -t hermes-cli 'printenv ORCHESTRATOR_API_KEY' Enter
   tmux capture-pane -t hermes-cli -p | grep ORCHESTRATOR_API_KEY
   ```
3. **Check orchestrator API health** (default port 8000 on Hostinger VPS):
   ```bash
   curl -s http://<hostinger-vps-ip>:8000/health
   ```
4. **Test network connectivity** to Hostinger VPS:
   ```bash
   ping <hostinger-vps-ip>
   traceroute <hostinger-vps-ip>
   ```
5. **Restart agents** if needed:
   ```bash
   tmux kill-session -t hermes-cli 2>/dev/null
   tmux kill-session -t hermes-debug 2>/dev/null
   # Recreate sessions as above
   ```

### Pitfalls
- `hermes-debug` relies on a persistent tmux session; if the tmux session is killed, the agent will disconnect immediately. Always check tmux first.
- Never use `HERMES_ORCHESTRATOR_KEY` for agent configs; the orchestrator SDK only reads `ORCHESTRATOR_API_KEY`.
- Tmux sessions won't inherit env vars from `.bashrc` unless restarted with `source /root/.bashrc && hermes`.

### User Preference Note
The user prefers the assistant to run all diagnostic and fix commands independently, without delegating to the user unless absolutely necessary. Automate all checks via tool calls.

## Celery + FastAPI Integration Pitfalls (2026-05-07)

When deploying Celery workers alongside FastAPI (e.g., Hermes Cognitive Engine):

1. **AsyncResult Without App Context**: `AsyncResult(task_id)` uses DisabledBackend. Must pass `app=celery`: `AsyncResult(task_id, app=celery)`. Import celery from `celery_app` module.
2. **Celery Task Registration**: `include=["tasks"]` not `include=["src.tasks"]` when `PYTHONPATH=/app/src`. Celery's `include` uses Python import paths, not filesystem paths. Rebuild Docker image after changing `celery_app.py`.
3. **Both API + Worker Must Rebuild Together**: After changing `celery_app.py` or `tasks.py`, rebuild image and recreate BOTH containers. Mismatched versions cause tasks to be submitted but never picked up.
4. **Free Model Rate Limit Cascade**: Default concurrency=4 all hitting free models (8 req/min limit per key). Fix: `--concurrency=2` and use small fast free models. Avoid large free models (70B, 120B) — they timeout and rate-limit faster.
5. **OPENROUTER_API_KEY Placeholder**: If `.env` has placeholder key, worker uses it. Fix: `sed -i "s|OPENROUTER_API_KEY=sk-or-v1-placeholder-replace-me|OPENROUTER_API_KEY=${HOST_KEY}|" /opt/hermes-cognitive/.env`

See `references/cognitive-engine-deployment.md` for full deployment reference. (planning and impact analysis for connecting isolated agents into coordinated system)
- [Multi-Instance Troubleshooting](references/multi-instance-troubleshooting.md) (C-suite deployments, port conflicts, restart loops)
- [VPS Capacity Planning](references/vps-capacity-planning.md) (resource usage patterns, scaling limits, monitoring for multi-agent setups)
- [Terminal Tool Fixes](references/terminal-tool-fixes.md) (detailed patch context)
- [ttyd Web Terminal Setup](references/ttyd-web-terminal.md) (alternative to native TUI for Docker)
- [Telegram Document Handling](references/telegram-document-handling.md) (how to locate and read documents sent via Telegram bot)
- [Official Hermes Agent Repo](https://github.com/NousResearch/hermes-agent)
- [Hermes Workspace Repo](https://github.com/outsourc-e/hermes-workspace)
- [Deploying Hermes Containers](references/deploying-hermes-containers.md) (custom container deployment tips: image entrypoint overrides, Python paths, dependency management, port scanning, credential retrieval)
- [Cognitive Engine Deployment](references/cognitive-engine-deployment.md) (FastAPI+Celery+Redis L1-L4 pipeline, Docker deployment, SKP schema, pitfalls)
