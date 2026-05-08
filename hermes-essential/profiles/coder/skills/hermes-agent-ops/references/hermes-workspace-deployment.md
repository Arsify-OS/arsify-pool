# Hermes Workspace Deployment Reference
## Prerequisites
- Node.js 22+, pnpm
- Docker & Docker Compose (optional for containerized setup)
- Nginx (for reverse proxy)

## Local (Non-Docker) Setup
### Clone & Install
```bash
git clone https://github.com/outsourc-e/hermes-workspace.git <instance-name>
cd <instance-name>
pnpm install
cp .env.example .env
```

### Configure .env for Production
```env
HERMES_AGENT_PATH=/usr/local/lib/hermes-agent
CLAUDE_AGENT_PATH=/usr/local/lib/hermes-agent
HOST=0.0.0.0
PORT=3000
CLAUDE_PASSWORD=<strong-password> # REQUIRED for remote access
TRUST_PROXY=1
COOKIE_SECURE=0 # Set to 1 after SSL setup
NODE_ENV=production
```

### Build
```bash
pnpm build # Outputs to dist/ by default
```

### Fix Build Path Mismatch
The default `start` script expects `.output/server/index.mjs`, but `vite build` outputs to `dist/`. Create a symlink:
```bash
mkdir -p .output/server
ln -sf $(pwd)/dist/server/server.js .output/server/index.mjs
```

### Stable Process Management (PM2)
Avoid raw background commands (`&`) which get blocked by the system. Use PM2 for long-lived processes:
```bash
npm install -g pm2
pm2 start "NODE_ENV=production HOST=0.0.0.0 PORT=3000 node .output/server/index.mjs" --name hermes-workspace
pm2 save
pm2 startup
```

## Docker Compose Setup
### Add Ollama Host Access
Modify `docker-compose.yml` to let the agent container reach Ollama on the host:
```yaml
services:
  hermes-agent:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

### Start Services
```bash
docker compose up -d
```

## Nginx Path-Based Reverse Proxy (/workspace)
Example config for `hermes.upshalter.com/workspace`:
```nginx
server {
    listen 80;
    server_name hermes.upshalter.com;
    
    location /workspace/ {
        rewrite ^/workspace(/.*)$ $1 break;
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
    
    location = / {
        return 301 /workspace/;
    }
}
```

## Common Pitfalls
1. **Silent Exit on Startup**: Missing `CLAUDE_PASSWORD` or using `HOST=127.0.0.1` for remote access causes immediate exit with no error output.
2. **Build Path Mismatch**: `vite build` outputs to `dist/`, but the default `start` script looks for `.output/server/index.mjs` — create the symlink above.
3. **Process Management**: Raw `&` background commands are blocked by the system. Use PM2 for stable operation.
4. **Docker Ollama Access**: Without `extra_hosts`, the agent container cannot reach Ollama running on the host.
