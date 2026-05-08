# workstation-upshalter Nginx Config — Final Working Version

Full Nginx configuration for `workstation.upshalter.com` with path-based routing for all Hermes services.

## Complete Config File

Location: `/etc/nginx/sites-available/workstation-upshalter`

```nginx
server {
    server_name workstation.upshalter.com;
    access_log /var/log/nginx/workstation-access.log;
    error_log /var/log/nginx/workstation-error.log;

    # Workspace (port 3000) — Separate Container
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
        proxy_read_timeout 86400;
    }

    # Kanban (port 3001) — Separate Container (NOT shared with workspace)
    location /hermes/kanban/ {
        rewrite ^/hermes/kanban(/.*)$ $1 break;
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Orchestrator API (port 8000)
    location /hermes/api/ {
        rewrite ^/hermes/api(/.*)$ $1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-API-Key "hma_kUjTtoP_NUBD9EAxlpIjedkc7aNnKYZ1XbgN4_vAjf0";
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket
    location /hermes/ws {
        rewrite ^/hermes/ws(.*)$ /ws$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    # Documentation (static)
    location /hermes/docs/ {
        alias /var/www/workstation/hermes/docs/;
        index index.html;
    }

    # Dashboard - Workforce Command Center (static, for agent instructions)
    location /hermes/dashboard/ {
        alias /var/www/workstation/hermes/dashboard/;
        index index.html;
    }

    # Profile page (static with live API)
    location /hermes/profile/ {
        alias /var/www/workstation/hermes/profile/;
        index index.html;
    }

    # Skills page (static)
    location /hermes/skill/ {
        alias /var/www/workstation/hermes/skill/;
        index index.html;
    }

    # Tools page (static)
    location /hermes/tool/ {
        alias /var/www/workstation/hermes/tool/;
        index index.html;
    }

    # Arsify - Shared Knowledge Pool (static with live API)
    location /hermes/arsify/ {
        alias /var/www/workstation/hermes/arsify/;
        index index.html;
    }

    # Redirect /hermes/ to /hermes/docs/
    location = /hermes/ {
        return 301 /hermes/docs/;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/workstation.upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/workstation.upshalter.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = workstation.upshalter.com) {
        return 301 https://$host$request_uri;
    }
    listen 80;
    server_name workstation.upshalter.com;
    return 404;
}
```

## Key Points

1. **All `location` blocks MUST be inside `server {}`** — placing them outside causes `location directive is not allowed here` error
2. **Static paths use `alias`** — `/hermes/docs/`, `/hermes/dashboard/`, `/hermes/profile/`, `/hermes/skill/`, `/hermes/tool/`, `/hermes/arsify/`
3. **Proxy paths use `proxy_pass`** — `/hermes/workspace/`, `/hermes/kanban/`, `/hermes/api/`, `/hermes/ws`
4. **Two separate apps** — Workspace on port 3000, Kanban on port 3001 (separate Docker containers)
5. **`hermes.upshalter.com` deprecated** — use `workstation.upshalter.com/hermes/...`

## Docker Compose for Kanban (:3001)

```yaml
# /root/hermes-kanban/docker-compose.yml
services:
  hermes-kanban:
    image: ghcr.io/outsourc-e/hermes-workspace:latest
    environment:
      HERMES_API_URL: http://host.docker.internal:8642
      HERMES_API_TOKEN: ${API_SERVER_KEY:-}
      HERMES_PASSWORD: ${KANBAN_PASSWORD:-kanban123}
      COOKIE_SECURE: 0
      TRUST_PROXY: 1
      ORCHESTRATOR_API_KEY: hma_kUjTtoP_NUBD9EAxlpIjedkc7aNnKYZ1XbgN4_vAjf0
      ORCHESTRATOR_URL: http://host.docker.internal:8000
    extra_hosts:
      - "host.docker.internal:host-gateway"
    ports:
      - '0.0.0.0:3001:3000'
    volumes:
      - kanban-data:/opt/data
    restart: unless-stopped

volumes:
  kanban-data:
```

## Verification Commands

```bash
# Test all paths return HTTP 200 (or 301 for /hermes/)
for path in "/hermes/" "/hermes/docs/" "/hermes/dashboard/" "/hermes/profile/" \
             "/hermes/skill/" "/hermes/tool/" "/hermes/arsify/" \
             "/hermes/workspace/" "/hermes/kanban/"; do
    code=$(curl -s -o /dev/null -w "%{http_code}" "https://workstation.upshalter.com${path}")
    echo "$path → HTTP $code"
done

# Check containers
docker ps | grep -E "workspace|kanban"

# Test API
curl -s https://workstation.upshalter.com/hermes/api/agents \
  -H "X-API-Key: hma_kUjTtoP_NUBD9EAxlpIjedkc7aNnKYZ1XbgN4_vAjf0"
```
