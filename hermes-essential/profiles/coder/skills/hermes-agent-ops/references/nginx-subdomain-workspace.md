## Nginx Subdomain Config for Hermes Workspace
Prefer subdomains over path-based proxies to avoid Vite dev server root path issues (Vite serves at `/`, not `/workspace`).

### Nginx Config Template
Create `/etc/nginx/sites-available/workspace.hermes.upshalter.com`:
```nginx
server {
    listen 80;
    listen [::]:80;
    server_name workspace.hermes.upshalter.com;

    location /.well-known/acert-challenge/ {
        root /var/www/html;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Setup Steps
1. Enable site: `sudo ln -sf /etc/nginx/sites-available/workspace.hermes.upshalter.com /etc/nginx/sites-enabled/`
2. Test Nginx config: `sudo nginx -t`
3. Reload Nginx: `sudo nginx -s reload`
4. Set DNS A record: `workspace -> <VPS_IP>` (e.g., 76.13.194.136)
5. Install SSL: `sudo certbot --nginx -d workspace.hermes.upshalter.com`
