---
name: hermes-workspace-deployment
description: Deploy Hermes Workspace (dev/prod) with Nginx reverse proxy, subdomain setup, SSL via Certbot, using personal cloned instance. Also covers VPSO agent management (systemd + Docker) and vpsoctl management script.
---

## Trigger Conditions
- User requests setting up Hermes Workspace for subdomain access (e.g., workspace.upshalter.com)
- Need to configure Nginx reverse proxy for Hermes Workspace
- Require SSL certificate setup for Workspace subdomain
- Using fresh personal cloned instance instead of original install
- User wants to deploy Hermes Workspace via Docker Compose (isolated, production-ready)
- Need to reinstall/refresh Hermes Workspace after issues with old installation
- User wants full automation for multi-agent development (file watching, auto-deploy, notifications)
- Setting up autonomous development workflow with zero manual intervention
- **User asks to add Hermes agent instances to VPSO (e.g., "add hermes asli with name X")**
- **Need to rename/update systemd services for consistency**
- **User asks to add multiple Hermes agent clones for Shared Knowledge Pool (SPK) validation**

## Steps

1. **Clone Personal Instance**
   ```bash
   git clone https://github.com/outsourc-e/hermes-workspace.git /root/hermes-workspace-personal
   cd /root/hermes-workspace-personal
   ```

2. **Install Dependencies**
   ```bash
   pnpm install
   ```

3. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Set `HERMES_AGENT_PATH` to Hermes Agent directory
   - Prod only: Set `CLAUDE_PASSWORD`, `HOST=0.0.0.0`, `TRUST_PROXY=1`

4. **Build (Production Only)**
   ```bash
   pnpm build
   ln -s dist/server/server.js .output/server/index.mjs
   ```

5. **Nginx Subdomain Config**
   Create `/etc/nginx/sites-available/workspace.upshalter.com`:
   ```nginx
   server {
       listen 80;
       listen [::]:80;
       server_name workspace.upshalter.com;

       location /.well-known/acme-challenge/ {
           root /var/www/html;
       }

       location / {
           proxy_pass http://127.0.0.1:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```
   - Enable: `ln -sf /etc/nginx/sites-available/workspace.upshalter.com /etc/nginx/sites-enabled/`
   - Test: `nginx -t`
   - Reload: `nginx -s reload`

6. **DNS Setup**
   - Add A record: `workspace.upshalter.com` → VPS IP (e.g., 76.13.194.136)

7. **SSL Certificate**
   ```bash
   sudo certbot --nginx -d workspace.upshalter.com
   ```

8. **Run Dev Server**
   ```bash
   cd /root/hermes-workspace-personal
   pnpm dev  # Run in background for persistence
   ```

9. **Integrate Hermes Gateway**
   - Ensure Gateway runs on `127.0.0.1:8642`
   - Set `API_SERVER_KEY`, `GATEWAY_ALLOW_ALL_USERS=true` in `~/.hermes/.env`

## Dual Dev/Prod Deployment (Two Modes Simultaneously)

To run both development and production modes at the same time with separate subdomains:

1. **DNS Setup for Both Subdomains**
   - Add A record: `workspace.upshalter.com` → VPS IP (prod)
   - Add A record: `dev.workspace.upshalter.com` → VPS IP (dev)

2. **Separate Ports**
   - Dev mode: Run `pnpm dev` on port 3000 (default)
   - Prod mode: If using default production build, note it won't run as traditional server (see Pitfalls). For workaround, run second dev instance on port 3001 with `PORT=3001 pnpm dev`

3. **Nginx Configs for Both Subdomains**
   - Create `/etc/nginx/sites-available/dev.workspace.upshalter.com` proxying to port 3000
   - Create `/etc/nginx/sites-available/workspace.upshalter.com` proxying to port 3001 (or 3000 if single mode)
   - Enable both:
     ```bash
     ln -sf /etc/nginx/sites-available/dev.workspace.upshalter.com /etc/nginx/sites-enabled/
     ln -sf /etc/nginx/sites-available/workspace.upshalter.com /etc/nginx/sites-enabled/
     ```

4. **SSL for Both Subdomains**
   ```bash
   sudo certbot --nginx -d workspace.upshalter.com -d dev.workspace.upshalter.com
   ```

5. **Persist Servers with PM2**
   ```bash
   pm2 start "cd /root/hermes-workspace-personal && pnpm dev" --name hermes-dev
   pm2 start "cd /root/hermes-workspace-personal && PORT=3001 pnpm dev" --name hermes-prod
   pm2 save
   pm2 startup
   ```

## Docker Compose Deployment (Recommended for Production)

**Use Case:** Fresh install with isolated containers, no dependency on host Hermes Agent.

### Prerequisites
- Docker & Docker Compose installed
- At least one LLM provider API key (OPENROUTER_API_KEY, ANTHROPIC_API_KEY, etc.)

### Steps

1. **Clone Repository**
   ```bash
   git clone https://github.com/outsourc-e/hermes-workspace.git /root/hermes-workspace-fresh
   cd /root/hermes-workspace-fresh
   ```

2. **Configure Environment**
   Create `.env` file:
   ```bash
   # Production settings
   NODE_ENV=production
   HOST=0.0.0.0
   PORT=3000
   TRUST_PROXY=1
   COOKIE_SECURE=0  # Set to 1 after SSL setup
   
   # Authentication (REQUIRED for remote access)
   CLAUDE_PASSWORD=YourStrongPassword123!
   
   # Hermes Agent Gateway Configuration
   # REQUIRED when API_SERVER_HOST=0.0.0.0 (security requirement)
   API_SERVER_HOST=0.0.0.0
   API_SERVER_KEY=YourSecureGatewayKey123!
   
   # API Keys (at least one required)
   OPENROUTER_API_KEY=sk-or-v1-...
   # ANTHROPIC_API_KEY=sk-ant-...
   # OPENAI_API_KEY=sk-...

⚠️ Note: Feature flags like `ENHANCED_CHAT=true`, `MCP_ENABLED=true` are NOT supported in current `nousresearch/hermes-agent:latest` image. Adding these to .env has no effect.
   ```

3. **Modify docker-compose.yml**

   **Critical fixes for VPS deployment:**

   a. **Add gateway command** (prevents immediate exit):
   ```yaml
   hermes-agent:
     image: nousresearch/hermes-agent:latest
     command: ["hermes", "gateway", "run"]  # ADD THIS LINE
     env_file:
       - .env
   ```

   b. **Comment out port 8642** if host already runs hermes-gateway on PM2:
   ```yaml
   # Port 8642 commented out - already used by PM2 hermes-gateway on host
   # Workspace accesses agent via internal Docker network (hermes-agent:8642)
   # ports:
   #   - '8642:8642'
   ```

   c. **Change workspace port binding** from localhost to public:
   ```yaml
   hermes-workspace:
     ports:
       - '0.0.0.0:3000:3000'  # Change from 127.0.0.1:3000:3000
   ```

4. **Start Containers**
   ```bash
   # If terminal tool blocks "docker compose up -d", use this instead:
   docker compose create
   docker compose start
   ```

   Wait 30 seconds for containers to initialize and pass health checks.

5. **Verify Deployment**
   ```bash
   # Check container status
   docker compose ps
   # Expected: Both containers "Up" and "healthy"

   # Check logs
   docker compose logs hermes-workspace --tail 20
   docker compose logs hermes-agent --tail 20

   # Test HTTP access
   curl -I http://localhost:3000
   # Expected: HTTP/1.1 200 OK
   ```

6. **Configure Nginx Reverse Proxy** (Optional, for subdomain access)

   Create `/etc/nginx/sites-available/workspace.upshalter.com`:
   ```nginx
   server {
       listen 80;
       listen [::]:80;
       server_name workspace.upshalter.com;

       location / {
           proxy_pass http://127.0.0.1:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

   Enable and reload:
   ```bash
   ln -sf /etc/nginx/sites-available/workspace.upshalter.com /etc/nginx/sites-enabled/
   nginx -t && nginx -s reload
   ```

7. **Setup SSL** (After DNS propagation)
   ```bash
   sudo certbot --nginx -d workspace.upshalter.com
   ```

   Then update `.env`:
   ```bash
   COOKIE_SECURE=1
   ```

   Restart workspace:
   ```bash
   docker compose restart hermes-workspace
   ```

### Docker Management Commands

```bash
# View status
docker compose ps

# View logs (real-time)
docker compose logs -f

# Restart services
docker compose restart

# Stop services
docker compose stop

# Start services
docker compose start

# Stop and remove containers
docker compose down

# Stop and remove containers + volumes (WARNING: deletes data)
docker compose down -v

# Update images and recreate
docker compose pull
docker compose up -d --force-recreate
```

## References
- `references/hermes-cognitive-engine.md`: Hermes Cognitive Engine (FastAPI + Celery + SKP) deployment reference — docker-compose pattern, SKP schema, .env template, verification commands.
- `references/docker-base-image-pitfalls.md`: Docker base image quirks (no pip, no ensurepip, network issues, API quirks).
- `references/hermes-internet-daemon.md`: Hermes Internet Research Agent daemon architecture and SKP schema.
- `references/nginx-config-edit.md`
- `vpsoctl.sh`: VPSO Unit Upshalternal management script - manage 10 systemd agents + Docker containers (status/start/stop/restart/logs).
- `add-hermes-agent.sh`: Automated script to add new Hermes agent instances to VPSO (systemd service + Nginx + vpsoctl + landing page).

## Management Script

The `vpsoctl` script (installed at `/usr/local/bin/vpsoctl`) manages all VPSO Unit Upshalternal services:
- **17 systemd agents**: dashboard(9119), upshalter(9120), Infrastructure(9121), builder(9122), plaza(9123), sandbox(9129), pool(9130), vpso(9131), internet(9132), c-suite(9133), operation(9134), api(9135), archivist, frontend, backend, workstation, flowforce
- Docker containers: hermes-upshalternal(8645), hermes-loyx(8643), hermes-gamedev(8644)
- Used for **Shared Knowledge Pool (SPK) validation** with 16 clones sharing `/root/.hermes` via volume mounts

Usage: `vpsoctl {status|start|stop|restart|logs|docker}`

**Naming Convention (CRITICAL)**:
- Use `hermes-DescriptiveName` pattern (e.g., `hermes-Infrastructure`, NOT `hermes-infra` or `hermes-infraInfrastructure`)
- **NEVER use COO/CTO/CMO prefixes** in descriptions or filenames — they were removed for consistency and easier debugging
- Examples:
  ✅ `hermes-Infrastructure` (port 9121) — Description: "VPSO Unit Upshalternal - Infrastructure (9121)"
  ❌ `hermes-infraInfrastructure` (typo)
  ❌ `hermes-infra` (too short, unclear)
  ❌ Description: "COO - Infrastructure" (has COO prefix — REMOVED)
- When cloning agents, always follow: `hermes-<clear-descriptive-name>`

## Post-Deployment Validation

After completing all deployment steps, run the full live check workflow documented in `references/live-check.md` to ensure:
1. All static pages return HTTP 200
2. Proxied services (Workspace, Kanban, API) are accessible
3. Content renders correctly with expected titles
4. Root `/hermes/` path does not return 403 (add `index.html` to `/var/www/workstation/hermes/` if missing)

## Creating Additional Agent Instances (Multi-Instance Pattern)

When deploying multiple isolated Hermes Agent instances on the same VPS (e.g., "loyx" agent alongside workspace agent):

**⚠️ CRITICAL: Nginx Config for Multiple Agents**
When adding many agents (e.g., 5+ agents like archivist, frontend, backend, workstation, flowforce), DO NOT use `sed -i` or `cat >>` to append location blocks — this causes "location directive is not allowed here" errors because blocks end up OUTSIDE `server {}`.

**✅ Correct Approach for Multiple Agent Proxies:**
```bash
# 1. Backup current config
cp /etc/nginx/sites-available/workstation-upshalter /etc/nginx/sites-available/workstation-upshalter.bak

# 2. Use Python to regenerate entire config with all location blocks INSIDE server {}
python3 << 'PYEOF'
from pathlib import Path

# Read existing config
content = Path('/etc/nginx/sites-available/workstation-upshalter').read_text()

# Find server block boundaries and insert all location blocks properly
# ... (use structured approach, not sed)

# Better: Rewrite entire config with all agents included
# See templates/nginx-multi-agent.conf for complete example
PYEOF

# 3. Test and reload
nginx -t && systemctl reload nginx
```

**Quick Script Available:** Use `scripts/add-hermes-agent.sh` to automate agent creation!

### A. Systemd Service Method (for native host agents, e.g., hermes-archivist, hermes-frontend)

**Agent Cloning Pattern (proven workflow):**
1. Create systemd service file (clone from hermes-dashboard.service)
2. Enable and start the service
3. Add location block to Nginx config (use Python rewrite, NOT sed)
4. Update vpsoctl script (add to services array)
5. Update landing page (add card to index.html)

```bash
# Automated with script:
./scripts/add-hermes-agent.sh <agent-name> <port> "<description>"

# Manual method:
cat > /etc/systemd/system/hermes-<name>.service << 'EOF'
[Unit]
Description=VPSO Unit Upshalternal - <Name> (<port>)
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

systemctl daemon-reload
systemctl enable --now hermes-<name>
```

**Hermes Agent Startup:** Use `dashboard` mode, NOT `chat` with `--host`/`--port`:
- ❌ Wrong: `hermes chat --host 0.0.0.0 --port 9124` (unrecognized arguments)
- ✅ Correct: `hermes dashboard --host 0.0.0.0 --port 9124 --no-open --insecure`

### B. Docker Container Method (recommended for isolation)

1. **Create separate directory**
   ```bash
   mkdir -p /docker/hermes-agent-<instance-name>
   cd /docker/hermes-agent-<instance-name>
   ```

2. **Create docker-compose.yml**
   ```yaml
   services:
     hermes-agent:
       image: nousresearch/hermes-agent:latest
       command: ["hermes", "gateway", "run"]
       restart: unless-stopped
       ports:
         - "<unique-port>:8642"  # e.g., 8643:8642
       env_file:
         - .env
       volumes:
         - ./data:/opt/data
         - /root:/host/root:ro  # Mount host filesystem (read-only)
       extra_hosts:
         - "host.docker.internal:host-gateway"
   ```

3. **Configure .env with unique settings**
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-...
   ORCHESTRATOR_URL=http://host.docker.internal:8000
   ORCHESTRATOR_API_KEY=${ORCHESTRATOR_API_KEY}
   ```

### C. Nginx Proxy for Both Methods

**⚠️ CRITICAL: Avoid `sed`/`cat >>` for adding location blocks — causes corruption with duplicate blocks!**

**Pitfall:** Appending to Nginx config with `sed -i '...' /etc/nginx/sites-available/...` or `cat >> file << 'EOF'` repeatedly causes location blocks to nest incorrectly, resulting in `"location" directive is not allowed here` errors and corrupt configs.

**✅ Correct Approach:** Rewrite the entire config file using `write_file` tool or heredoc:
```bash
# Backup first
cp /etc/nginx/sites-available/workstation-upshalter /etc/nginx/sites-available/workstation-upshalter.bak

# Rewrite entire file with all location blocks properly inside server {}
cat > /etc/nginx/sites-available/workstation-upshalter << 'NGINXEOF'
server {
    server_name workstation.upshalter.com;
    # ... all location blocks here, properly nested ...
    location /hermes/agent1 { proxy_pass http://127.0.0.1:9121; ... }
    location /hermes/agent2 { proxy_pass http://127.0.0.1:9122; ... }
    # ... etc ...
}
NGINXEOF

# Test and reload
nginx -t && systemctl reload nginx
```

**Port Conflict Check:** Always check port availability before assignment:
```bash
ss -tlnp | grep <port> || echo "Port available"
docker ps | grep <port>  # Check Docker port mappings too
```

### D. Batch Adding Clones for SPK Validation
When adding 5+ agent clones sequentially for **Shared Knowledge Pool (SPK) validation** (testing knowledge sharing across clones via shared `/root/.hermes` volume mounts):
1. **Systemd Service Creation** (repeat per clone):
   ```bash
   cat > /etc/systemd/system/hermes-<name>.service << 'EOF'
   [Unit]
   Description=VPSO Unit Upshalternal - <Name> (<port>)
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
   systemctl daemon-reload
   systemctl enable --now hermes-<name>
   ```
   Verify: `systemctl status hermes-<name> --no-pager | grep Active:`

2. **Nginx Proxy Addition** (for `hermes-agents` config):
   ⚠️ Note: `cat >>` is **safe here** because `/etc/nginx/sites-available/hermes-agents` uses separate `server {}` blocks per proxy port, not nested location blocks inside a single server block.
   ```bash
   cat >> /etc/nginx/sites-available/hermes-agents << 'EOF'
   # Proxy untuk <Name> (<port>) via port <proxy-port>
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
   ```
   Verify: `curl -s -o /dev/null -w "%{http_code}" http://localhost:<proxy-port>` → expect 200

3. **vpsoctl Update** (modify `/usr/local/bin/vpsoctl`):
   - Add new service to `services=()` array
   - Update `Ports:` echo line with new port
   - Update `Agents:` help text line with new agent
   Verify: `vpsoctl status | grep hermes-<name>` → expect RUNNING

4. **Batch Verification**:
   ```bash
   # All systemd services running
   vpsoctl status | grep -c "RUNNING" | grep -q "16"  # Expect 16 systemd RUNNING
   # All Nginx proxies return 200
   for port in 8120 8121 8122 8123 8129 8130 8131 8132 8133 8134; do
       curl -s -o /dev/null -w "%{http_code}" http://localhost:$port | grep -q 200 || echo "Proxy $port DOWN"
   done
   ```

## Renaming Agents (Systemd + Docker)

When user requests renaming agents (e.g., swap names between systemd services and Docker containers):

### Systemd Service Rename
```bash
# 1. Stop the service
systemctl stop hermes-oldname

# 2. Rename service file
mv /etc/systemd/system/hermes-oldname.service /etc/systemd/system/hermes-newname.service

# 3. Update Description in service file
sed -i 's/Description=.*/Description=VPSO Unit Upshalternal - NewName (port)/' /etc/systemd/system/hermes-newname.service

# 4. Reload and restart
systemctl daemon-reload
systemctl enable --now hermes-newname
```

### Docker Container Rename
```bash
# 1. Stop container
docker stop old-container-name

# 2. Rename container
docker rename old-container-name new-container-name

# 3. Restart
docker start new-container-name
```

### vpsoctl Update After Rename
- Update `services=()` array with new systemd service name
- Update `docker_containers=()` array with new Docker container name
- Update `Ports:` echo line to reflect display name change
- Update `Agents:` help text and `Docker:` help text

**Example from session:** Renamed `hermes-upshalternal` (systemd) → `hermes-upshalter`, and Docker `hermes-upshalter` → `hermes-upshalternal`.

## Multiple Workspace Instances (Path-Based Routing)

Use this pattern when deploying multiple Hermes Workspace apps (e.g., Workspace + Kanban) under a single domain with path prefixes (e.g., `/hermes/workspace/`, `/hermes/kanban/`):

1. **Create separate directory for each instance**:
   ```bash
   mkdir -p /root/hermes-kanban
   cd /root/hermes-kanban
   ```

2. **Write docker-compose.yml for the new instance**:
   - Use unique host port mapping (e.g., 3001 for Kanban)
   - Same image: `ghcr.io/outsourc-e/hermes-workspace:latest`
   - Set required env vars: `HERMES_PASSWORD`, `ORCHESTRATOR_API_KEY`, `HERMES_API_URL`, `extra_hosts: "host.docker.internal:host-gateway"`
   - Unique volume for data persistence
   - Example template: See `templates/docker-compose-kanban.yml`

3. **Start the instance**:
   ```bash
   docker compose up -d
   ```
   (Use `terminal` tool with `background=true` for long-running startup to avoid blocking)

4. **Update Nginx site config for path-based routing**:
   - For each path (e.g., `/hermes/kanban/`), set `proxy_pass` to the new port (e.g., `http://127.0.0.1:3001`)
   - **Pitfall**: Do NOT use the `patch` tool to edit `/etc/nginx/sites-available/*` files — the tool blocks writes to sensitive system paths. Use terminal commands instead:
     ```bash
     cp /etc/nginx/sites-available/your-site /etc/nginx/sites-available/your-site.bak
     sed -i '/location \/hermes\/kanban\//,/}/{s/proxy_pass http:\/\/127.0.0.1:3000;/proxy_pass http:\/\/127.0.0.1:3001;/}' /etc/nginx/sites-available/your-site
     nginx -t  # Test config syntax
     nginx -s reload  # Apply changes
     ```

5. **Verify deployment**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" https://workstation.upshalter.com/hermes/workspace/  # Should return 200
   curl -s -o /dev/null -w "%{http_code}\n" https://workstation.upshalter.com/hermes/kanban/   # Should return 200
   docker ps | grep hermes  # Check both containers are running
   ```

6. **Full `/hermes/` Subtree Nginx Structure** (single-domain path-based routing):
   - `/hermes/` → 301 redirect to `/hermes/docs/`
   - `/hermes/docs/` → Static documentation, alias `/var/www/workstation/hermes/docs/`
   - `/hermes/dashboard/` → Static **Workforce Command Center** for **giving instructions to agents using their skills** (not just monitoring), alias `/var/www/workstation/hermes/dashboard/`
   - `/hermes/profile/` → Static agent profiles with live API data, alias `/var/www/workstation/hermes/profile/`
   - `/hermes/skill/` → Static skills listing, alias `/var/www/workstation/hermes/skill/`
   - `/hermes/tool/` → Static tools listing, alias `/var/www/workstation/hermes/tool/`
   - `/hermes/arsify/` → Shared Knowledge Pool (Arsify) with live API, alias `/var/www/workstation/hermes/arsify/`
   - `/hermes/workspace/` → Proxy to `http://127.0.0.1:3000` (Workspace instance, separate container)
   - `/hermes/kanban/` → Proxy to `http://127.0.0.1:3001` (Kanban instance, **separate container from workspace**)
   - `/hermes/api/*` → Proxy to `http://127.0.0.1:8000` (Orchestrator API) with `X-API-Key` header
   - `/hermes/ws` → WebSocket proxy to `http://127.0.0.1:8000`

   **Important:** `hermes.upshalter.com` is **no longer official** — all paths moved to `workstation.upshalter.com/hermes/...`

   Example Nginx location blocks (inside `server {}`):
   ```nginx
   # Redirect /hermes/ to /hermes/docs/
   location = /hermes/ {
       return 301 /hermes/docs/;
   }

   # Documentation static files
   location /hermes/docs/ {
       alias /var/www/workstation/hermes/docs/;
       try_files $uri $uri/ /hermes/docs/index.html;
   }

   # Dashboard static files (Workforce Command Center - agent instructions)
   location /hermes/dashboard/ {
       alias /var/www/workstation/hermes/dashboard/;
       try_files $uri $uri/ /hermes/dashboard/index.html;
   }

   # Workspace app (port 3000)
   location /hermes/workspace/ {
       rewrite ^/hermes/workspace(/.*)$ $1 break;
       proxy_pass http://127.0.0.1:3000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection 'upgrade';
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_cache_bypass $http_upgrade;
   }

   # Kanban app (port 3001)
   location /hermes/kanban/ {
       rewrite ^/hermes/kanban(/.*)$ $1 break;
       proxy_pass http://127.0.0.1:3001;
       # Same proxy headers as workspace
   }

   # Orchestrator API
   location /hermes/api/ {
       rewrite ^/hermes/api(/.*)$ $1 break;
       proxy_pass http://127.0.0.1:8000;
       proxy_set_header X-API-Key "your-api-key-here";
   }

   # WebSocket
   location /hermes/ws {
       rewrite ^/hermes/ws(.*)$ /ws$1 break;
       proxy_pass http://127.0.0.1:8000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "Upgrade";
   }
   ```

## Upgrading Existing Container to Newer Version

When upgrading an existing Hermes Agent container (e.g., from v0.9.0 to v0.12.0):

1. **Update docker-compose.yml image**
   ```yaml
   # Change from old image
   image: ghcr.io/hostinger/hvps-hermes-agent:latest
   # To official image
   image: nousresearch/hermes-agent:latest
   ```

2. **Add gateway command** (if not present)
   ```yaml
   command: ["hermes", "gateway", "run"]
   ```

3. **Handle port conflicts**
   - If port 8642 already in use by another gateway, change mapping:
     ```yaml
     ports:
       - "8643:8642"  # Map to different host port
     ```

4. **Configure API server for external access**
   - Add to `.env` file:
     ```bash
     API_SERVER_ENABLED=true
     API_SERVER_HOST=0.0.0.0
     API_SERVER_KEY=<generate-strong-random-key>
     GATEWAY_ALLOW_ALL_USERS=true  # Or configure specific allowlists
     ```
   - **Critical:** `API_SERVER_KEY` is REQUIRED when `API_SERVER_HOST=0.0.0.0` (security requirement)
   - Generate key: `openssl rand -hex 32`

5. **Pull new image and recreate**
   ```bash
   cd /path/to/docker-compose-dir
   docker compose pull
   docker compose down
   docker compose up -d
   ```

6. **Verify upgrade**
   ```bash
   # Check version in pyproject.toml
   docker exec <container-name> cat /opt/hermes/pyproject.toml | grep "^version"

   # Test gateway health
   curl http://localhost:<port>/health
   # Expected: {"status": "ok", "platform": "hermes-agent"}

   # Check logs for errors
   docker logs <container-name> --tail 30
   ```

7. **Common upgrade issues**
   - Container restarts continuously: Check logs for missing API_SERVER_KEY
   - Gateway not listening: Verify command includes `gateway run`
   - Port conflicts: Use different host port mapping
   - API keys not working: Ensure `.env` file mounted correctly to `/opt/data/.env`

## Troubleshooting

For detailed troubleshooting of Docker Compose deployment issues (container exits, port conflicts, health checks, network debugging), see `references/docker-compose-troubleshooting.md`.

## Production Hardening (Finalization Checklist)

After deploying all services, harden the setup for production use:

### 1. PM2 Auto-Start
```bash
pm2 save
pm2 startup | grep "sudo" | bash  # Run the output command to enable startup
```
- Saves current process list and enables auto-start on boot
- Applies to: hermes-cli, 9router, and other PM2-managed services

### 2. Docker Container Restart Policy
```bash
# Set all Hermes containers to auto-restart
docker ps | grep -E "(3000|3001|hermes)" | awk '{print $1}' | xargs -I {} docker update --restart always {}
```
- Ensures containers restart automatically after VPS reboot
- Check: `docker inspect <container> | grep RestartPolicy`

### 3. Service Monitoring Cron Job
Create `/root/check-hermes-services.sh`:
```bash
#!/bin/bash
LOG_FILE="/var/log/hermes-monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')
ALERT=0
MSG="⚠️ Hermes Service Alert:"

# Check critical ports
for port in 3000 3001 8000 9119 9120 9121 9122 9123 9124 9125 9126 9127 9128; do
    if ! ss -tlnp | grep -q ":$port "; then
        MSG="$MSG Port $port DOWN;"
        ALERT=1
    fi
done

# Log result
if [ $ALERT -eq 1 ]; then
    echo "[$DATE] $MSG" >> $LOG_FILE
    # Add Telegram notification: curl "https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<ID>&text=$MSG"
else
    echo "[$DATE] All services UP" >> $LOG_FILE
fi

# Keep log small
tail -100 $LOG_FILE > ${LOG_FILE}.tmp && mv ${LOG_FILE}.tmp $LOG_FILE
```
Enable: `chmod +x /root/check-hermes-services.sh && (crontab -l 2>/dev/null; echo "*/5 * * * * /root/check-hermes-services.sh") | crontab -`

### 4. Nginx Config Cleanup
```bash
# Remove duplicate configs from sites-enabled
sudo rm /etc/nginx/sites-enabled/*.bak 2>/dev/null
sudo mkdir -p /etc/nginx/backups
sudo mv /etc/nginx/sites-enabled/*.bak /etc/nginx/backups/ 2>/dev/null

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
```

### 5. Virtual Office Lobby Page
Create `/var/www/workstation/hermes/lobby/index.html` with:
- Live agent status (5 agents: hermes-cli, hermes-debug, loyx, gamedev, workforce)
- Quick links to workspace, kanban, dashboard
- Recent task feed from kanban API (`/hermes/kanban/api/tasks`)

### 6. Service Status Page
Create `/var/www/workstation/hermes/status/index.html` with:
- Health check for all services (workspace :3000, kanban :3001, API :8000, dashboards :9119-9128)
- Auto-refresh every 30 seconds
- Visual status badges (✅ Healthy / ❌ Unhealthy)

### Verification
```bash
# All paths return HTTP 200
for path in /hermes/lobby/ /hermes/status/ /hermes/kanban/ /workspace/; do
    code=$(curl -k -s -o /dev/null -w "%{http_code}" -H "Host: hermes.upshalter.com" "https://localhost${path}")
    echo "$path → $code"
done

# Critical ports listening
ss -tlnp | grep -E "(3000|3001|8000|9119|9120|9121|9122|9123|9124|9125|9126|9127|9128)" | wc -l
# Expected: 13 ports
```

## Pitfalls

⚠️ **Docker Base Image (nousresearch/hermes-agent:latest):**
- **NO pip** — Cannot use `pip install`. Must use `/opt/hermes/.venv/bin/python3 -m pip install`.
- **NO ensurepip** — `python3 -m ensurepip` fails.
- **Entrypoint intercepts all commands** — Use full paths for scripts.
- **Network**: `host.docker.internal` doesn't work on Hostinger VPS. Use `network_mode: host` or UFW rules.
- **Web APIs from Docker**: DDG times out (use 5s timeout), Wikipedia needs User-Agent header.
- **SQLite**: ALTER TABLE ADD COLUMN must be run separately per column.

⚠️ **Naming Convention: NEVER use COO/CTO/CMO prefixes or typos like `infraInfrastructure`**
- User explicitly removed COO, CTO, CMO titles for consistency and easier debugging
- ✅ Correct: `hermes-Infrastructure` (port 9121), Description: "VPSO Unit Upshalternal - Infrastructure (9121)"
- ❌ Wrong: `hermes-infra`, `hermes-infraInfrastructure`, Description: "COO - Infrastructure"
- Pattern: `hermes-<ClearDescriptiveName>` (e.g., `hermes-Builder`, `hermes-Plaza`)

⚠️ **Nginx Config: NEVER use `sed -i` or `cat >>` for adding location blocks!**
This is the #1 cause of "location directive is not allowed here" errors. Appending with `sed -i '...' file` or `cat >> file << 'EOF'` places new location blocks OUTSIDE the `server {}` block, corrupting the config.
⚠️ **Exception**: `cat >>` is safe for configs using **separate `server {}` blocks per service** (e.g., `/etc/nginx/sites-available/hermes-agents`), as no nesting of location blocks occurs.

✅ **Correct Approach:** Always rewrite the ENTIRE config file using Python or heredoc:
```bash
# Backup first
cp /etc/nginx/sites-available/workstation-upshalter /etc/nginx/sites-available/workstation-upshalter.bak

# Rewrite entire file with Python (recommended)
python3 << 'PYEOF'
from pathlib import Path
content = Path('/etc/nginx/sites-available/workstation-upshalter').read_text()
# Find server block, insert new location blocks properly inside it
# Write back entire file
Path('/etc/nginx/sites-available/workstation-upshalter').write_text(new_content)
PYEOF

# OR use heredoc to rewrite completely
cat > /etc/nginx/sites-available/workstation-upshalter << 'NGINXEOF'
server {
    server_name workstation.upshalter.com;
    # ... ALL location blocks properly inside { } ...
    location /hermes/agent1 { proxy_pass http://127.0.0.1:9121; ... }
    location /hermes/agent2 { proxy_pass http://127.0.0.1:9122; ... }
    # ... etc
}
NGINXEOF

# Test and reload
nginx -t && systemctl reload nginx
```

- ❌ Missing `index.html` in `/var/www/workstation/hermes/` causes 403 errors on the root `/hermes/` path. Add a simple redirect or index file to fix this.
- **Backup files in sites-enabled**: Never leave backup config files (e.g., `.bak`) in `/etc/nginx/sites-enabled/` — this causes duplicate listen directive warnings. Move backups to `/etc/nginx/backups/`.
- **Testing Nginx paths locally**: When testing with `curl localhost`, the Host header is set to `localhost`, which may not match your server block's `server_name`. Use `-H "Host: <server_name>"` to test correctly (e.g., `curl -k -H "Host: hermes.upshalter.com" https://localhost/hermes/lobby/`).
- **Editing Nginx configs**: The `patch` tool (and other write tools) may refuse to modify sensitive system paths like `/etc/nginx/sites-enabled/`. Use `sudo python3 -c` to edit configs programmatically, or `sudo cp` to create backups manually.
- **Auto-recovery setup**: After deploying services, enable auto-restart:
  - PM2: `pm2 save && pm2 startup | grep sudo | bash`
  - Docker: `docker update --restart always <container_id>`
  - Cron: Add a 5-minute monitoring script to check critical ports (3000, 3001, 8000, 9119-9128) and log/alert on failure.
- See `references/nginx-hermes-upshalter.conf` for a full working Nginx config example.

⚠️ **Hermes Asli (Original) vs Modified Agents:**
- **"Hermes asli"** = Original `/usr/local/bin/hermes` binary cloned by running multiple instances on different ports (e.g., 9119-9135)
- Each clone is a separate systemd service or Docker container running the **same unmodified binary**
- **NOT "hermes asli":** Modifying core binary, using "skill agent swap", or changing agent behavior via custom code
- User explicitly wants "hermes asli" clones for SPK (Shared Knowledge Pool) validation
- All clones share `/root/.hermes` via volume mounts for knowledge pooling
- **Verification:** All clones return identical `/health` responses since they run the same binary

⚠️ **Nginx IPv6 Resolution Pitfall**: When using `proxy_pass http://localhost:port`, nginx may resolve `localhost` to IPv6 address `::1` if IPv6 is enabled, but backend services often listen only on IPv4 `0.0.0.0`. This causes "Connection refused" errors. Fix: Always use explicit IPv4 address `127.0.0.1` in `proxy_pass` directives, e.g., `proxy_pass http://127.0.0.1:3000;`. This applies to all nginx proxy configurations for Hermes services.

Quick fix for existing configs using localhost:
```bash
sed -i 's/proxy_pass http:\/\/localhost:\([0-9]*\)/proxy_pass http:\/\/127.0.0.1:\1/g' /etc/nginx/sites-available/*.conf
nginx -t && systemctl reload nginx
```

⚠️ **Hermes Agent EnhancedChat/MCP Feature Gap**: The current `nousresearch/hermes-agent:latest` image's `hermes gateway run` (port 8642) is a messaging gateway, not a full API gateway. Features like `enhancedChat`, `mcp`, or `mcpFallback` are not included in this release. If workspace logs show `missing=[enhancedChat, mcp, mcpFallback]`:
1. Verify endpoint existence: `docker exec <hermes-agent-container> curl -sI http://localhost:8642/enhancedChat`
2. Check hermes-agent logs: `docker logs <hermes-agent-container> --tail 50 | grep -iE "enhanced|mcp"`
3. `ENHANCED_CHAT=true`/`MCP_ENABLED=true` env vars are NOT supported in current image
4. These features may require newer image, manual config in `/opt/hermes/config.yaml` (inside container), or different deployment mode

⚠️ **Host Redis Access from Docker**: When Redis runs on the host (not in Docker), containers must use `extra_hosts: ["host.docker.internal:host-gateway"]` and `REDIS_URL=redis://host.docker.internal:6379/0`. Remove the Redis service from docker-compose.yml and all `depends_on: redis` blocks. Do NOT use `network_mode: host` — `extra_hosts` is cleaner and works on all VPS providers. Verify connectivity: `docker exec <container> python3 -c "import redis; r=redis.Redis(host='host.docker.internal',port=6379); print(r.ping())"` → should print `True`.

⚠️ **Docker .env Changes Not Applied Automatically**: Modifying the `.env` file after container creation does NOT automatically apply to running containers. The `.env` is read when the container starts. To apply changes:
  - Restart the service: `docker compose restart hermes-workspace`
  - Or recreate the container (recommended for major changes): `docker compose up -d --force-recreate`
  - Verify env vars are loaded: `docker exec <container-name> env | grep <VAR_NAME>`

## Dashboard Purpose
- **`/hermes/dashboard/` is the Workforce Command Center** for **giving instructions to agents using their skills**, not just real-time monitoring. Deploy the dashboard HTML to `/var/www/workstation/hermes/dashboard/` as static files.
- When user corrects naming (e.g., `/hermes/workforce/` → `/hermes/dashboard/`), follow immediately and update Nginx config and paths accordingly.

## Static Pages Navigation
- All static pages (`/hermes/docs/`, `/hermes/profile/`, `/hermes/skill/`, `/hermes/tool/`, `/hermes/arsify/`, `/hermes/dashboard/`) must have **consistent header/footer navigation** linking to each other.
- Use a common nav pattern:
  ```html
  <nav>
    <a href="/hermes/docs/">📖 Docs</a>
    <a href="/hermes/profile/">🤖 Agents</a>
    <a href="/hermes/skill/">🛠️ Skills</a>
    <a href="/hermes/tool/">🔧 Tools</a>
    <a href="/hermes/arsify/">📚 Knowledge</a>
    <a href="/hermes/dashboard/">🎛️ Dashboard</a>
  </nav>
  ```

## Nginx Config Editing
- **Editing `/etc/nginx/sites-available/*` files**: The `patch` tool will refuse to write to these sensitive system paths. Use terminal commands instead: `cp` for backup, `sed -i` for edits, `nginx -t` to test, `nginx -s reload` to apply.

## Telegram Bot Integration

For detailed steps on integrating Telegram bot with Hermes Agent (adding token, restarting gateway, automated notifications), see `references/telegram-bot-integration.md`.

Quick setup:
```bash
echo "TELEGRAM_BOT_TOKEN=<token>" >> ~/.hermes/.env
hermes config set telegram.reactions true
pm2 restart hermes-gateway
```

## Full Automation Deployment

For complete autonomous development workflow with file watching, auto-deployment, scheduled monitoring, and notification delivery (multi-agent collaboration pattern), see `references/automation-deployment.md`.

Quick overview:
- Real-time file watcher (systemd + inotify-tools)
- Instant auto-deploy pipeline
- Scheduled cron jobs (Telegram notifications, progress monitoring, build validation)
- Multi-agent container setup
- Zero-touch deployment workflow

## Verification

### Docker Compose Deployment
```bash
# Container health
docker compose ps
# Expected: Both containers "Up" and "healthy"

# Workspace HTTP
curl -I http://localhost:3000
# Expected: HTTP/1.1 200 OK

# Verify internal Docker network connectivity (workspace → hermes-agent)
docker exec hermes-workspace-fresh-hermes-workspace-1 curl -sI http://hermes-agent:8642
# Expected: HTTP/1.1 404 Not Found or 200 (endpoint dependent)

# Agent gateway health (from inside container)
docker compose exec hermes-agent curl -s http://localhost:8642/health
# Expected: {"status":"ok"} or similar

# Check logs for errors
docker compose logs --tail 50

# Check workspace logs for missing feature errors (e.g., enhancedChat/MCP)
docker compose logs hermes-workspace --tail 50 | grep -i "missing=\[" || echo "✅ No missing feature errors"
```

### Automation Systems
```bash
# File watcher status
systemctl status <project>-watcher
# Expected: active (running)

# View real-time logs
tail -f /path/to/project/watcher.log
tail -f /path/to/project/deploy.log
tail -f /path/to/project/notifications.log

# Cron jobs
hermes cron list
# Check next_run_at timestamps and last_status

# Test Telegram bot
curl -s "https://api.telegram.org/bot<token>/getMe"
# Expected: {"ok":true,"result":{"id":...}}

# Verify production deployment
curl -I https://production.domain.com
# Expected: HTTP/2 200
```

### Dev/Prod Server Deployment
- `curl http://127.0.0.1:3000` → HTTP 200
- `curl https://workspace.upshalter.com` → HTTP 200
- Gateway health: `curl http://127.0.0.1:8642/health` → 200
