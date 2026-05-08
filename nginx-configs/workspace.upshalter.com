server {
    listen 443 ssl http2;
    server_name workspace.upshalter.com;

    ssl_certificate     /etc/letsencrypt/live/workspace.upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/workspace.upshalter.com/privkey.pem;

    # Hermes Workspace (Docker container)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;
    }
}

server {
    listen 80;
    server_name workspace.upshalter.com;
    return 301 https://$host$request_uri;
}
