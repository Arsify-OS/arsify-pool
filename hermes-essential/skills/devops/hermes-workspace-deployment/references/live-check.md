# Hermes Live System Check Commands
Verified commands to validate all Hermes components are live after deployment.

## Prerequisites
- Nginx config tested (`sudo nginx -t`) and reloaded
- All backend services running (ports 3000, 3001, 8000, 9119-9123)
- Domain `hermes.upshalter.com` pointed to VPS IP

## 1. DNS Resolution Check
```bash
getent hosts hermes.upshalter.com
```
Expected output: `76.13.194.136   hermes.upshalter.com`

## 2. Static Pages HTTP Status Check
```bash
for p in docs profile skill tool arsify dashboard lobby status; do
  code=$(curl -k -s -o /dev/null -w "%{http_code}" "https://hermes.upshalter.com/hermes/${p}/")
  echo "/hermes/$p/ → HTTP $code"
done
```
All should return 200.

## 3. Proxied Services Check
```bash
# Workspace (Port 3000)
curl -k -s -o /dev/null -w "Workspace: %{http_code}\n" "https://hermes.upshalter.com/hermes/workspace/"
# Kanban (Static)
curl -k -s -o /dev/null -w "Kanban: %{http_code}\n" "https://hermes.upshalter.com/hermes/kanban/"
# Orchestrator API (Port 8000)
curl -k -s -o /dev/null -w "API Health: %{http_code}\n" "https://hermes.upshalter.com/hermes/api/health"
```

## 4. Content Validation
```bash
# Verify page titles
curl -k -s "https://hermes.upshalter.com/hermes/lobby/" | grep -a -o "<title>.*</title>"
# Expected: <title>Hermes Virtual Office Lobby</title>

curl -k -s "https://hermes.upshalter.com/hermes/workspace/" | grep -a -o "<title>.*</title>"
# Expected: <title>Hermes Workspace</title>
```

## 5. Root Path Check
```bash
curl -k -s -o /dev/null -w "Root /hermes/: %{http_code}\n" "https://hermes.upshalter.com/hermes/"
```
If 403: Add `index.html` to `/var/www/workstation/hermes/` or configure Nginx redirect.

## Pitfalls
- ❌ Avoid `&` in foreground terminal commands: split into separate calls to prevent backgrounding errors.
- ✅ Use `-k` flag with curl for self-signed TLS certificates during testing.
- ✅ Always run `sudo nginx -t` and `sudo systemctl reload nginx` after Nginx config changes.
- ✅ Ensure `/var/www/workstation/hermes/` has an `index.html` to avoid 403 on root path.
