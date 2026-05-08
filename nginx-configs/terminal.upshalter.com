server {
    server_name terminal.upshalter.com;

    # Static files for dashboard
    location / {
        root /var/www/terminal.upshalter.com;
        index index.html;
        try_files $uri $uri/ =404;
        # Anti-cache headers for HTML/JS/CSS
        location ~* \.(html|js|css)$ {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires 0;
        }
    }

    # API endpoints - proxy to Node.js server
    location /api/ {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        return 200 '{"status": "ok", "service": "terminal-upshalter"}';
        add_header Content-Type application/json;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/terminal.upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/terminal.upshalter.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = terminal.upshalter.com) {
        return 301 https://$host$request_uri;
    }
    listen 80;
    listen [::]:80;
    server_name terminal.upshalter.com;
    return 404;
}
