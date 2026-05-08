# workstation.upshalter.com Final Nginx Configuration
# Deployed: 2026-05-05
# Path-based routing for Upshalter Workstation

server {
    server_name workstation.upshalter.com;
    access_log /var/log/nginx/workstation-access.log;
    error_log /var/log/nginx/workstation-error.log;

    # Workspace (port 3000)
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

    # Kanban (port 3001) - separate container
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

    # Documentation
    location /hermes/docs/ {
        alias /var/www/workstation/hermes/docs/;
        index index.html;
    }

    # Dashboard (Workforce Command Center)
    location /hermes/dashboard/ {
        alias /var/www/workstation/hermes/dashboard/;
        index index.html;
    }

    # Profile page
    location /hermes/profile/ {
        alias /var/www/workstation/hermes/profile/;
        index index.html;
    }

    # Skills page
    location /hermes/skill/ {
        alias /var/www/workstation/hermes/skill/;
        index index.html;
    }

    # Tools page
    location /hermes/tool/ {
        alias /var/www/workstation/hermes/tool/;
        index index.html;
    }

    # Arsify - Shared Knowledge Pool
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

# Important Notes:
# - /hermes/ redirects to /hermes/docs/ (documentation)
# - /hermes/docs/ : static docs (alias /var/www/workstation/hermes/docs/)
# - /hermes/dashboard/ : Workforce Command Center for agent instructions (static)
# - /hermes/profile/ : Agent profiles with live API data (static)
# - /hermes/skill/ : Skills listing (static)
# - /hermes/tool/ : Tools listing (static)
# - /hermes/arsify/ : Shared Knowledge Pool with live API (static)
# - /hermes/workspace/ : Hermes Workspace (proxy :3000, separate container)
# - /hermes/kanban/ : Hermes Kanban (proxy :3001, separate container)
# - /hermes/api/* : Orchestrator API (proxy :8000) with X-API-Key header
# - /hermes/ws : WebSocket (proxy :8000)
# - hermes.upshalter.com is no longer official; use workstation.upshalter.com/hermes/...
