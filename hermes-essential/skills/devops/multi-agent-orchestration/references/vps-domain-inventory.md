# VPS Domain & Port Inventory (2026-05-06)

## Domain/Subdomain Status

### Fully Automated (Root + Proxy + SSL + Port Open)
1. **upshalter.com** — ROOT: /var/www/upshalter.com, SSL: 81 days
2. **arsify.upshalter.com** — ROOT: /var/www/arsify.upshalter.com, PROXY: :8000, SSL: 78 days
3. **data.upshalter.com** — ROOT: /var/www/data.upshalter.com, PROXY: :3001, SSL: 85 days
4. **flowise.upshalter.com** — PROXY: :3000, SSL: 83 days
5. **terminal.upshalter.com** — ROOT: /var/www/terminal.upshalter.com, PROXY: :3001, SSL: 85 days
6. **regrow.upshalter.com** — ROOT: /var/www/regrow-upshalter, SSL: 87 days
7. **workstation.upshalter.com** — PROXY: :3000/:3001/:8000/:9120/:9124-9128/:8645, SSL: 87 days

### Partial (SSL but incomplete)
8. **api.upshalter.com** — PROXY: :8000, NO SSL (Tailscale only)
9. **arsify-api.upshalter.com** — PROXY: :8000, NO SSL (Tailscale only)
10. **hermes-agents** (localhost) — 9 port closed (9121-9123, 9129-9134)
11. **n8n.upshalter.com** — SSL: 83 days, PROXY: :5678 CLOSED

### SSL Only (No root/proxy — not configured)
12. **flowtask.upshalter.com** — SSL: 84 days, no root/proxy
13. **chat.upshalter.com** — SSL: 75 days, no root/proxy
14. **game.upshalter.com** — SSL: 74 days, no root/proxy
15. **hermes.upshalter.com** — SSL: 83 days, no root/proxy
16. **play.upshalter.com** — SSL: 72 days, no root/proxy
17. **workspace.upshalter.com** — SSL: 87 days, no root/proxy

### Internal
18. **hermes-tailscale** — :9118 → :9119 (CLOSED)
19. **local-workspaces** — :8080 → :3000 ✅, :8082 → :3002 CLOSED
20. **remote-forward** — :20129 → 76.13.194.136:20128 ✅

## Port Services

| Port | Service | Status |
|------|---------|--------|
| 22 | SSH | ✅ |
| 53 | DNS | ✅ |
| 80 | HTTP (nginx) | ✅ |
| 443 | HTTPS (nginx) | ✅ |
| 3000 | Workspace (Docker) | ✅ |
| 3001 | Data/Kanban (Docker) | ✅ |
| 4860 | ttyd | ✅ |
| 5678 | n8n | ❌ CLOSED |
| 6379 | Redis | ✅ |
| 8000 | VPSO Orchestrator | ✅ |
| 8080 | Nginx → :3000 | ✅ |
| 8120-8137 | Hermes Agents proxy | Partial |
| 8642 | Hermes Gateway | ✅ |
| 8645 | Upshalternal | ✅ |
| 9118-9137 | VPSO dashboards | Partial |
| 20128 | Next.js app | ✅ |
| 20129 | Remote forward | ✅ |

## Root Directories (/var/www/)
- upshalter.com/ — Main website
- arsify.upshalter.com/ — Arsify app
- data.upshalter.com/ — Data portal
- terminal.upshalter.com/ — Terminal web
- regrow-upshalter/ — Regrow app
- hermes-dashboard/ — Hermes dashboard
- workstation/ — Workstation
- ai/, api/, app/, auth/, eljaranika/, flow/, landing/, msai/, regrow/ — Other roots

## SSL Certificates (all valid)
- api.upshalter.com + data.upshalter.com — Jul 30 2026
- arsify.upshalter.com — Jul 23 2026
- chat.upshalter.com — Jul 20 2026
- flowise.upshalter.com — Jul 28 2026
- flowtask.upshalter.com — Jul 30 2026
- game.upshalter.com — Jul 20 2026
- hermes.upshalter.com — Jul 28 2026
- n8n.upshalter.com — Jul 29 2026
- play.upshalter.com — Jul 17 2026
- terminal.upshalter.com — Jul 30 2026
- upshalter.com + www + multi-domain — Jul 27 / Aug 3 2026
- workspace.upshalter.com — Aug 1 2026
- workstation.upshalter.com + regrow.upshalter.com — Aug 1 2026

## DNS/Hosts
- 127.0.1.1 → ubuntu-docker.localhost, srv1589470.hstgr.cloud
- Tailscale: 100.109.101.58
- VPS Host: srv1589470 (Hostinger)

## Recommendations
- 6 SSL-only domains need root/proxy config or cert deletion
- n8n service needs to be started (port 5678)
- hermes-agents ports 9121-9123, 9129-9134 need services
- api.upshalter.com and arsify-api.upshalter.com need SSL certs for Tailscale IP
