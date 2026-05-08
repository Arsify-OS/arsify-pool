server {
    listen 80;
    server_name arsify.upshalter.com;
    
    # Redirect ke HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name arsify.upshalter.com;
    
    ssl_certificate     /etc/letsencrypt/live/upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/upshalter.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Static landing page
    root /var/www/arsify.upshalter.com;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Health endpoint (proxy ke backend)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # OpenAI-compatible API (proxy ke backend)
    location /v1/ {
        proxy_pass http://127.0.0.1:8000/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout untuk streaming
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Docs
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }
    
    # Deny admin/control dari public internet
    location /admin {
        return 403 "Access denied: Admin panel only available via Tailscale";
    }
    
    location /control {
        return 403 "Access denied: Control panel only available via Tailscale";
    }
}
