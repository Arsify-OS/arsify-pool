# Nginx Config Editing — Lessons from VPSO Pipeline Session

## Problem
When adding multiple `location` blocks to an existing Nginx config (e.g., `/etc/nginx/sites-available/workstation-upshalter`), using `sed -i` or `cat >>` leads to corruption:
- Location blocks get placed **outside** the `server {}` block.
- Causes error: `"location" directive is not allowed here`.
- Duplicate blocks appear because each append adds a new copy.

## Root Cause
- `sed -i` cannot understand Nginx nested block structure.
- Appending with `cat >>` adds content after the closing `}` of the server block.

## Correct Approaches

### 1. Rewrite Entire File (Recommended)
Use a heredoc to write the complete config with all location blocks properly inside `server {}`.

```bash
# Backup first
cp /etc/nginx/sites-available/your-site /etc/nginx/sites-available/your-site.bak

# Rewrite entire file
cat > /etc/nginx/sites-available/your-site << 'NGINXEOF'
server {
    server_name example.com;
    # ... all existing directives ...

    # New location blocks go INSIDE this server block
    location /new-path {
        proxy_pass http://127.0.0.1:9999;
        # ... proxy headers ...
    }
} # ← server block closes here
NGINXEOF

# Test and reload
nginx -t && systemctl reload nginx
```

### 2. Use Python to Restructure (When Already Corrupted)
If the file is already corrupted with outside blocks, use Python to parse and restructure.

```python
from hermes_tools import terminal

result = terminal("cat /etc/nginx/sites-available/your-site")
content = result["output"]
lines = content.split('\n')

# Find server block boundaries
# Insert orphaned location blocks before the closing '}' of the first server block
# ... (see session log for exact code)
```

### 3. Verify Always
After any edit:
```bash
nginx -t 2>&1 | grep -E "syntax|successful|emerg"
```
If `emerg` appears, config is corrupt. Restore from backup and try again.

## Backup Strategy
- Before any edit: `cp /etc/nginx/sites-available/your-site /etc/nginx/sites-available/your-site.bak-$(date +%Y%m%d-%H%M%S)`
- Keep backups in a dedicated directory: `/etc/nginx/backups/`
- Remove `.bak` files from `sites-enabled/` to avoid duplicate listen warnings.

## Port Conflict Check
Before adding a new proxy, verify port is free:
```bash
ss -tlnp | grep <port> || echo "Port available"
docker ps | grep <port>  # also check Docker port mappings
```

## Session-Specific Notes (VPSO Pipeline)
- Added 8 systemd agents (ports 9119‑9126) plus Docker containers.
- Nginx config required: static pages, proxy to 5 agents, plus VPSO manager, archivist, frontend, backend.
- Final working config: all location blocks inside a single `server {}` block.
- Used Python restructuring after multiple `sed` failures.

## Related Skill Sections
- See "Creating Additional Agent Instances (Multi-Instance Pattern)" in SKILL.md for the original warning.
- See "Multiple Workspace Instances (Path-Based Routing)" for Nginx structure example.
