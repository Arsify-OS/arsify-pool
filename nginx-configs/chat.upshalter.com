server {
    listen 443 ssl http2;
    server_name chat.upshalter.com;

    ssl_certificate     /etc/letsencrypt/live/chat.upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chat.upshalter.com/privkey.pem;

    # Root → serve chat UI (HTML)
    root /var/www/chat.upshalter.com;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }

    # /chat → proxy ke Arsify OS API (same-origin untuk JavaScript)
    location /chat {
        proxy_pass http://127.0.0.1:8002/chat;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    # /v1/ → OpenAI-compatible endpoint
    location /v1/ {
        proxy_pass http://127.0.0.1:8002/v1/;
        proxy_set_header Host $host;
        proxy_read_timeout 120s;
    }

    # /stats → untuk info bar di chat UI
    location /stats {
        proxy_pass http://127.0.0.1:8002/stats;
        proxy_set_header Host $host;
    }

    # /health, /models → status info
    location ~ ^/(health|models|ready)$ {
        proxy_pass http://127.0.0.1:8002/$1;
        proxy_set_header Host $host;
    }
}

server {
    listen 80;
    server_name chat.upshalter.com;
    return 301 https://$host$request_uri;
}
