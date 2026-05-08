server {
    listen 443 ssl http2;
    server_name hermes.upshalter.com;

    ssl_certificate     /etc/letsencrypt/live/hermes.upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hermes.upshalter.com/privkey.pem;

    # Hermes Dashboard (proxy ke port 8645 tempat hermes-upshalternal berjalan)
    location / {
        proxy_pass http://127.0.0.1:8645;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket untuk Kanban real-time
    location /ws {
        proxy_pass http://127.0.0.1:8645/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
    }
}
server {
    listen 80;
    server_name hermes.upshalter.com;
    return 301 https://$host$request_uri;
}
