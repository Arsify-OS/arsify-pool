server {
    listen 80;
    listen [::]:80;
    server_name app.upshalter.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name app.upshalter.com;

    ssl_certificate /etc/letsencrypt/live/app.upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.upshalter.com/privkey.pem;

    root /var/www/app.upshalter.com;
    index upshalter-app-mockup.html index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    access_log /var/log/nginx/app.upshalter.com.access.log;
    error_log /var/log/nginx/app.upshalter.com.error.log;
}
