# Nginx Path-Based Setup for Hermes Workspace
## Lessons from hermes.upshalter.com/workspace Setup

### Problem
Trying to serve Hermes Workspace at a subpath (e.g., `hermes.upshalter.com/workspace`) instead of a subdomain or dedicated port.

### Key Issues Encountered
1. **App Base Path Mismatch**: Hermes Workspace (Vite dev server) serves the app at `/` (root), not `/workspace/`. The `rewrite ^/workspace(/.*)$ $1 break;` rule strips the `/workspace` prefix, but the app's client-side routing still expects to be at root.
2. **Silent Failures**: Nginx proxy returns 404 if the app doesn't handle the base path correctly.
3. **Config Placement Errors**: Accidentally placing location blocks outside server blocks (common when appending to configs programmatically).

### Working Nginx Snippet (For Reference)
```nginx
server {
    listen 80;
    server_name hermes.upshalter.com;

    # Path-based setup for /workspace
    location /workspace/ {
        rewrite ^/workspace(/.*)$ $1 break;
        
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Redirect root to /workspace
    location = / {
        return 301 /workspace/;
    }
}
```

### Recommendations
- **Prefer Subdomain**: For easier setup, use `workspace.hermes.upshalter.com` instead of path-based. No rewrite rules needed, app works at root.
- **If Path-Based Required**: Configure Vite's `base` option in `vite.config.ts` to `'/workspace/'`, then rebuild the app.
- **Verify Proxy**: Test with `curl -s -o /dev/null -w "%{http_code}" http://localhost/workspace/` — should return 200 if working.

### Pitfalls
- Never use `cat >> config` to append location blocks — always insert inside the correct `server {}` block.
- Run `nginx -t` after every config change to catch syntax errors.
- Remove conflicting symlinks in `/etc/nginx/sites-enabled/` to avoid "conflicting server name" warnings.
