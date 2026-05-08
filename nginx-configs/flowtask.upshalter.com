server {
    server_name flowtask.upshalter.com;

    location / {
        # Temporary: return placeholder page
        # Nanti akan diarahkan ke FlowTaks Dashboard (port 3002)
        return 200 '<!DOCTYPE html><html><head><title>FlowTaks - Integration Hub</title></head><body style="font-family:sans-serif;text-align:center;padding:50px;"><h1>🚀 FlowTaks Integration Hub</h1><p>Integrating n8n ↔ Flowise ↔ Hermes</p><p><a href="https://n8n.upshalter.com">n8n</a> | <a href="https://flowise.upshalter.com">Flowise</a> | <a href="https://hermes.upshalter.com">Hermes</a></p></body></html>';
        add_header Content-Type text/html;
    }

    listen [::]:443 ssl; # managed by Certbot
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/flowtask.upshalter.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/flowtask.upshalter.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = flowtask.upshalter.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    server_name flowtask.upshalter.com;

    listen 80;
    listen [::]:80;
    return 404; # managed by Certbot


}