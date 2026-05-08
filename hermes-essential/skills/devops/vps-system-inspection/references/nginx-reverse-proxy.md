# Nginx Reverse Proxy Setup
## Use Case
Forward remote server ports to local VPS ports, or expose local services to external access.

## Steps
1. **Check port availability**:
   ```bash
   ss -tlnp | grep <target_port>
   ```
   If port is in use (e.g., 20128 taken by next-server), choose an alternative port.

2. **Create Nginx config**:
   Write temporary config to `/tmp`:
   ```nginx
   server {
       listen <local_port>;
       server_name localhost;

       location / {
           proxy_pass http://<remote_host>:<remote_port>;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_connect_timeout 60s;
           proxy_send_timeout 60s;
           proxy_read_timeout 60s;
       }
   }
   ```

3. **Deploy config**:
   ```bash
   sudo mv /tmp/<config_name> /etc/nginx/sites-available/<config_name>
   sudo ln -sf /etc/nginx/sites-available/<config_name> /etc/nginx/sites-enabled/
   ```

4. **Validate & reload**:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

5. **Open firewall (external access only)**:
   ```bash
   sudo ufw allow <local_port>/tcp
   ```

## Pitfalls
- Sensitive system paths like `/etc/nginx/` require `sudo` via terminal tool, not direct `write_file`
- Port conflicts will prevent Nginx from binding; always check with `ss -tlnp` first
- `localhost` is per-machine; use SSH tunnel or VPS IP for remote access