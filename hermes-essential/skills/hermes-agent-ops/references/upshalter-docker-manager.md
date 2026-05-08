# Upshalter Docker Manager - Complete Setup

## Overview
Pattern for creating a Hermes Agent that can manage Docker containers (like `hermes-upshalter`). Includes Docker socket mount for full container management capabilities.

## docker-compose-upshalter.yml
```yaml
version: '3.8'

services:
  hermes-upshalter:
    image: nousresearch/hermes-agent:latest
    container_name: hermes-upshalter
    command: ["/bin/bash", "/workspace/upshalter-bridge.sh"]
    ports:
      - "8645:8642"
    volumes:
      - /root/regrow-up-world-dev:/workspace
      - /root/regrow-up-world-dev/upshalter-config:/root/.hermes
      - /root/regrow-up-world-dev/upshalter-bridge.sh:/workspace/upshalter-bridge.sh
      - /var/run/docker.sock:/var/run/docker.sock  # Docker Manager access
      - /root/.hermes:/root/.hermes-shared  # Shared Knowledge Pool
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - ORCHESTRATOR_URL=http://host.docker.internal:8000
      - ORCHESTRATOR_API_KEY=${ORCHESTRATOR_API_KEY}
      - DOCKER_MANAGER=true
      - UNIT_UPSHALTERNAL_ROLE=Manager
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
```

## upshalter-bridge.sh
```bash
#!/bin/bash
# upshalter-bridge.sh - Unit Upshalternal Manager + Docker Manager

set -e

echo "🚀 Starting Hermes Upshalter Agent..."
echo "Role: Unit Upshalternal Manager & Docker Manager"
echo "Port: 8642 (internal container)"
echo ""

# Check Docker socket access
if [ -S /var/run/docker.sock ]; then
    echo "✅ Docker socket accessible"
    docker ps >/dev/null 2>&1 && echo "✅ Docker daemon responsive" || echo "⚠️  Docker daemon not responding"
else
    echo "⚠️  Docker socket not found - Docker management disabled"
fi

# Unit Upshalternal context
export UNIT_UPSHALTERNAL_ROLE="Manager"
export VPSO_ENABLED="true"

# Start Hermes Agent in dashboard mode (serves HTTP on port)
cd /workspace
exec hermes dashboard --host 0.0.0.0 --port 8642 --no-open --insecure
```

Make executable: `chmod +x /root/regrow-up-world-dev/upshalter-bridge.sh`

## Key Features
- **Docker Socket Mount**: `/var/run/docker.sock:/var/run/docker.sock` gives container full access to host Docker
- **Docker Manager Env**: `DOCKER_MANAGER=true` signals capability
- **Orchestrator Connection**: Connects to VPSO orchestrator API at `:8000`
- **Shared Knowledge Pool**: Mounts `/root/.hermes` for unified memory across agents

## Nginx Proxy
Add to workstation-upshalter config:
```nginx
location /hermes/VPSO {
    proxy_pass http://127.0.0.1:8645;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

Access: `https://workstation.upshalter.com/hermes/VPSO`

## Pitfalls
- **Container exits immediately**: Never use `hermes --port 8642` or `hermes chat --host ...` as container command — these are invalid. Use `hermes dashboard --host 0.0.0.0 --port 8642 --no-open --insecure`.
- **Port conflicts**: If 8645 is taken, use different host port (8646, etc.) and update Nginx proxy accordingly.
- **Docker socket permissions**: Container may need `user: root` in docker-compose.yml if permission denied errors occur.

## Management
```bash
# Start container
cd /root/regrow-up-world-dev
docker compose -f docker-compose-upshalter.yml up -d

# Check status
docker ps | grep upshalter
curl -s -o /dev/null -w "%{http_code}" https://workstation.upshalter.com/hermes/VPSO

# View logs
docker logs hermes-upshalter --tail 50 -f

# Restart
docker restart hermes-upshalter
```
