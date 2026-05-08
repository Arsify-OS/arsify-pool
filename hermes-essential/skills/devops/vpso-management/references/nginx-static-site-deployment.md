# Nginx Static Site Deployment Guide
Step-by-step process for deploying static HTML sites (e.g., mockups, landing pages) as new subdomains under Upshalter VPSO infrastructure.

## Prerequisites
- Domain/subdomain DNS already pointed to VPS IP (verify with `dig +short <domain>`)
- Nginx installed and running
- Certbot installed for SSL

## Step 1: Prepare Site Files
1. Locate or create your static HTML file (e.g., `upshalter-app-mockup.html`)
2. Create directory in `/var/www/<domain>`:
   ```bash
   mkdir -p /var/www/<domain>
   ```
3. Copy files to directory and set correct ownership:
   ```bash
   cp /path/to/your/file.html /var/www/<domain>/index.html
   chown -R www-data:www-data /var/www/<domain>
   chmod -R 755 /var/www/<domain>
   ```
   ⚠️ **NEVER use /root for site files** - Nginx's www-data user cannot reliably access /root even with chmod.

## Step 2: Create Nginx Config
Use terminal heredoc (write_file tool blocks /etc/nginx/ paths):
```bash
cat > /etc/nginx/sites-available/<domain> << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name <domain>;

    root /var/www/<domain>;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    access_log /var/log/nginx/<domain>.access.log;
    error_log /var/log/nginx/<domain>.error.log;
}
EOF
```

Enable the site:
```bash
ln -sf /etc/nginx/sites-available/<domain> /etc/nginx/sites-enabled/
nginx -t  # Verify config syntax
systemctl reload nginx
```

## Step 3: Test HTTP
Use explicit IPv4 to avoid IPv6 resolution issues:
```bash
curl -sI http://127.0.0.1 -H "Host: <domain>" | head -5
# Expect HTTP/1.1 200 OK
```

## Step 4: Setup SSL with Certbot
If `certbot --nginx` fails with connection resets, use standalone mode:
```bash
systemctl stop nginx
certbot certonly --standalone -d <domain> --non-interactive --agree-tos --email <admin@domain>
systemctl start nginx
```

Update Nginx config to add HTTPS block:
```bash
cat > /etc/nginx/sites-available/<domain> << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name <domain>;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name <domain>;

    ssl_certificate /etc/letsencrypt/live/<domain>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<domain>/privkey.pem;

    root /var/www/<domain>;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    access_log /var/log/nginx/<domain>.access.log;
    error_log /var/log/nginx/<domain>.error.log;
}
EOF
```

Reload Nginx:
```bash
nginx -t && systemctl reload nginx
```

## Step 5: Verify HTTPS
```bash
curl -sI https://<domain> | head -5
# Expect HTTP/2 200
curl -sI http://<domain> | head -5
# Expect 301 redirect to HTTPS
```

## Troubleshooting
- **404 Errors**: Check file ownership in /var/www/<domain> (must be www-data:www-data)
- **Certbot Fails**: Use standalone mode as above
- **IPv6 Issues**: Always test with 127.0.0.1 instead of localhost
- **Config Write Errors**: Use terminal heredoc, not write_file tool for /etc/nginx/ paths