server {
    server_name n8n.upshalter.com;

    location / {
        proxy_pass http://100.109.101.58:5678;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/n8n.upshalter.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/n8n.upshalter.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = n8n.upshalter.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name n8n.upshalter.com;
    return 404; # managed by Certbot


}