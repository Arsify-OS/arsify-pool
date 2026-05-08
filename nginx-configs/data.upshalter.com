server {
    server_name data.upshalter.com;

    # Static files for data dashboard
    location / {
        root /var/www/data.upshalter.com;
        index index.html;
        try_files $uri $uri/ =404;
        
        # Anti-cache for HTML
        location ~* \.(html|js|css)$ {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires 0;
        }
    }

    # API proxy for data fetching
    location /api/ {
        proxy_pass http://127.0.0.1:3001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/api.upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.upshalter.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = data.upshalter.com) {
        return 301 https://$host$request_uri;
    }
    listen 80;
    listen [::]:80;
    server_name data.upshalter.com;
    return 404;
}
