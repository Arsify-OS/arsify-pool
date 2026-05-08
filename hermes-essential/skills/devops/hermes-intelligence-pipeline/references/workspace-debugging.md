# workspace.upshalter.com 502 Debugging Guide

**Created:** 8 Mei 2026  
**Symptom:** https://workspace.upshalter.com returns 502 Bad Gateway

---

## Diagnosis Steps

```bash
# 1. Check if workspace container is running
docker ps | grep workspace

# 2. Check container health
docker inspect hermes-workspace --format '{{.State.Health.Status}}' 2>/dev/null

# 3. Check workspace app logs
docker logs hermes-workspace --tail 50

# 4. Check nginx config for workspace
cat /etc/nginx/sites-available/workspace.upshalter.com

# 5. Test nginx config
nginx -t

# 6. Check what port workspace app listens on
docker exec hermes-workspace cat /app/.env | grep -i port

# 7. Test direct access (bypass nginx)
curl -sf http://localhost:<WORKSPACE_PORT> 2>/dev/null | head -5
```

## Common Causes

1. **Container crashed** — check `docker ps -a | grep workspace` for `Exited` status
2. **Wrong proxy_pass port** — nginx proxies to a port the app doesn't listen on
3. **Missing env vars** — workspace needs: `ENHANCED_CHAT_ENABLED`, `HERMES_MCP_ENABLED`, `HERMES_MCP_FALLBACK_ENABLED`, `HERMES_GATEWAY_URL`, `HERMES_API_BASE`, `NEXT_PUBLIC_ENHANCED_CHAT`
4. **Workspace app not built** — Next.js app may need `npm run build` before `npm start`

## Fix

```bash
# Restart workspace container
docker restart hermes-workspace
sleep 10
curl -sf https://workspace.upshalter.com | head -5

# If still 502, recreate:
cd /opt/hermes-cognitive  # or wherever docker-compose.yml is
docker compose up -d --force-recreate hermes-workspace

# Verify env vars
docker exec hermes-workspace env | grep -E "ENHANCED_CHAT|MCP|HERMES"
```

## Prevention

- Add workspace health check to monitoring: `curl -sf -o /dev/null -w "%{http_code}" https://workspace.upshalter.com` should return 200
- Add to health-check.sh cron
