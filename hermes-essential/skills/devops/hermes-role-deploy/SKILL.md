---
name: hermes-role-deploy
description: "Deploy Hermes agents using proven role-based models discovered from VPSO production analysis. Includes 7 role models, templates, decision criteria, one-click scripts, and nginx pitfalls from FASE 3 execution."
---

# Hermes Role-Based Agent Deployment

Deploy agent Hermes baru dengan memilih **role model** yang sudah teruji di VPSO production (Mei 2026).

## 7 Role Models Tersedia

### 0. ROLE: VPSO Upshalter (TUI Mode) ⭐ ONE-CLICK
**Contoh:** hermes-upshalter.service (port 9120)

**Kapan pakai:**
- Butuh **interactive TUI** access ke Hermes
- Butuh **central management** untuk VPSO units
- Quick deploy dengan one-click script

**Arsitektur:**
```
hermes-upshalter.service (systemd)
  ├── WorkingDirectory: /opt/hermes-upshalter
  ├── HERMES_HOME: /opt/hermes-upshalter/data
  ├── TUI mode: --tui --host 0.0.0.0 --port 9120
  └── Auto-restart enabled
```

**One-Click Deploy:**
```bash
bash /root/.hermes/skills/devops/hermes-role-deploy/scripts/deploy-upshalter.sh [port] [install_dir]
# Default: port 9120, install_dir /opt/hermes-upshalter
```

---

### 1. ROLE: VPSO Unit (Systemd + Hermes CLI)
**Contoh:** hermes-api (9125), hermes-archivist (9124), hermes-backend (9126), hermes-flowforce (9128), hermes-frontend (9125), hermes-workstation (9127)

**Pola:**
- ExecStart: `/usr/local/bin/hermes dashboard --host 0.0.0.0 --port <port> --no-open --insecure`
- Environment: `HERMES_ALLOWED_ORIGINS=*`
- Restart: always, RestartSec: 10
- Port range: 9120-9137

**Kapan pakai:** Unit spesifik dengan port dedicated, bagian dari VPSO ecosystem

---

### 2. ROLE: VPSO Manager (Main Manager + TUI)
**Contoh:** hermes-upshalternal (Main Manager, port 8645), hermes-upshalter (TUI mode, port 9120)

**Pola:**
- Main Manager: Dashboard mode di port 8645 (default Hermes)
- TUI mode: `--tui --host 0.0.0.0 --port 9120` + `WorkingDirectory` + `HERMES_HOME`
- Central coordination point

**Kapan pakai:** Central manager & interactive TUI access

---

### 3. ROLE: Internal Worker Pool (Monolith)
**Contoh:** hermes-internet.service (16 workers dalam 1 daemon)

**Kapan pakai:**
- Tugas **berurutan** (pipeline: A→B→C→D)
- Perlu **shared state** (database, cache, file bersama)
- Agent **ringan** (polling, scraping, transform data)
- **Satu tujuan** terintegrasi

**Arsitektur:**
```
daemon.py (1 proses Python)
  ├── Worker 1: Gap Detection
  ├── Worker 2-5: Collection (sources)
  ├── Worker 6-10: Processing
  ├── Worker 11-14: Distribution
  └── Worker 15-16: Feedback
  
Komunikasi: Queue internal / shared memory
Deploy: systemd service
```

**Template:** `references/worker-pool-daemon.py`

---

### 4. ROLE: Swarm Agent (Docker Container)
**Contoh:** hermes-gamedev, hermes-loyx

**Pola:**
- Image: `nousresearch/hermes-agent:latest`
- Volume: `/root/.hermes:/opt/data:rw` + `user: root`
- Environment: `OPENROUTER_API_KEY`, `HOST=0.0.0.0`, `TRUST_PROXY=1`
- extra_hosts: `host.docker.internal:host-gateway` (akses Ollama)

**Kapan pakai:** Agent mandiri, isolasi, scalable

**Template:** `references/swarm-docker-compose.yml`

---

### 5. ROLE: Workspace Instance (Docker Compose Stack)
**Contoh:** hermes-kanban, hermes-workspace-fresh

**Pola:**
- Image: `ghcr.io/outsourc-e/hermes-workspace:latest`
- Multi-service stack (workspace + agent dalam 1 compose)
- Healthcheck: `(healthy)` status
- Nginx reverse proxy integration
- Path: /root/hermes-workspace (personal instance)

**Kapan pakai:** Collaborative workspace dengan multiple users

---

### 6. ROLE: Orchestrator (Multi-Agent Coordinator)
**Contoh:** hermes-orchestrator.service

**Pola:**
- Deskripsi: "Hermes Multi-Agent Orchestrator"
- Mengkoordinasi agent lain (Swarm Mode)
- Systemd service yang manage Docker containers

**Kapan pakai:** Central coordination point untuk distributed agents

---

### 7. ROLE: Sidecar Agent (In-Stack)
**Contoh:** hermes-workspace-fresh-hermes-agent-1

**Pola:**
- Hermes Agent sebagai part of Docker Compose stack
- Image: `nousresearch/hermes-agent:latest`
- Berjalan bersama services lain dalam 1 stack

**Kapan pakai:** Agent yang terintegrasi dalam aplikasi stack

---

### 8. ROLE: Senator Pentahelix (News Scraping Stack)

**Contoh:** senator-akademisi, senator-bisnis, senator-komunitas, senator-pemerintah, senator-media

**Pola:**
- Docker Compose stack with 5 senator services (akademisi, bisnis, komunitas, pemerintah, media)
- Image: `senator-pentahelix:latest` (built from Dockerfile in `/root/senator-pentahelix/`)
- Network mode: `host` (access localhost:8000 orchestractor directly)
- Volumes: `senator-data:/app/data`, `/root/.hermes:/opt/data:ro`
- Environment variables (important!):
  - `SECTOR=<sector>`
  - `SENATOR_NAME=Senator <Sector>`
  - `CYCLE_INTERVAL_SECONDS=1800` (30 minutes for real-time news)
  - `ORCHESTRATOR_URL=http://127.0.0.1:8000`
  - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- Script: `/app/scripts/senator_research.py` (runs news scraping cycle)
- News source: Google News RSS (no CAPTCHA) + fallback Bing search
- Cycle: every 30 minutes, fetches fresh news, stores to SKP, sends Telegram report

**Kapan pakai:** 
- Butuh 24/7 news scraping dengan 5 sektor berbeda
- Ingin real-time news updates (bukan cuma Wikipedia/static sources)
- Membutuhkan isolasi per sektor tapi satu stack (Docker Compose)

**Reference:** `references/senator-news-scraping.md` (detailed setup, script, pitfalls)

---

## Quick Decision Tree

```
Agent baru mau dibuat?
  │
  ├─ Tugasnya berurutan & terintegrasi?
  │   └─ YA → Role: Internal Worker Pool (3)
  │
  ├─ Perlu isolasi / beda environment?
  │   └─ YA → Role: Swarm Agent (4) atau Sidecar (7)
  │
  ├─ Ada shared database/cache ketat?
  │   └─ YA → Role: Internal Worker Pool (3)
  │
  ├─ Agent mandiri & bisa scale independen?
  │   └─ YA → Role: Swarm Agent (4)
  │
  ├─ Butuh TUI interactive?
  │   └─ YA → Role: VPSO Upshalter (0)
  │
  ├─ Part of VPSO ecosystem (port 912x)?
  │   └─ YA → Role: VPSO Unit (1) atau Manager (2)
  │
  └─ Collaborative workspace?
      └─ YA → Role: Workspace Instance (5) atau Sidecar (7)
```

---

## Deployment Commands

### Deploy Internal Worker Pool
```bash
# Copy template
cp /root/.hermes/skills/devops/hermes-role-deploy/references/worker-pool-daemon.py /root/hermes-<nama>/daemon.py

# Edit konfigurasi AGENT_NAME, SOURCES, OUTPUT_TARGET
vim /root/hermes-<nama>/daemon.py

# Create systemd service
cat > /etc/systemd/system/hermes-<nama>.service <<EOF
[Unit]
Description=Hermes <Nama> Agent - Worker Pool
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/hermes-<nama>
ExecStart=/usr/bin/python3 /root/hermes-<nama>/daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable & start
systemctl daemon-reload
systemctl enable hermes-<nama>
systemctl start hermes-<nama>
```

### Deploy Swarm Mode
```bash
# Copy Docker Compose template
cp /root/.hermes/skills/devops/hermes-role-deploy/references/swarm-docker-compose.yml /root/hermes-<nama>/docker-compose.yml

# Edit konfigurasi (services, volumes, networks)
vim /root/hermes-<nama>/docker-compose.yml

# Deploy with Docker
cd /root/hermes-<nama>
docker-compose up -d

# Create systemd service (optional, for auto-start)
cat > /etc/systemd/system/hermes-<nama>.service <<EOF
[Unit]
Description=Hermes <Nama> Agent - Swarm Mode
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/root/hermes-<nama>
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable hermes-<nama>
systemctl start hermes-<nama>
```

---

## Template Variables

### Worker Pool Daemon
- `AGENT_NAME`: Nama agent (misal: "finance", "health")
- `WORKER_COUNT`: Jumlah workers (default: 16)
- `SOURCES`: Array sumber data (APIs, RSS, websites)
- `OUTPUT_TARGET`: Tujuan output (SKP DB, Telegram, file)
- `LAYER_CONFIG`: Konfigurasi tiap layer (0-4)

### Swarm Docker Compose
- `SERVICE_NAME`: Nama service (misal: "code-agent", "ml-agent")
- `CONTAINERS`: Daftar container & spesialisasinya
- `SHARED_VOLUME`: Path volume bersama (default: `/root/.hermes:/opt/data`)
- `NETWORK`: Docker network untuk inter-container comms
- `RESOURCES`: CPU/memory limits per container

---

## Verification

### Worker Pool
```bash
systemctl status hermes-<nama>
ps aux | grep daemon.py
tail -f /root/hermes-<nama>/data/*.log
```

### Swarm Mode
```bash
docker ps | grep hermes-<nama>
docker-compose logs -f
curl http://localhost:<port>/health
```

---

## Pitfalls (FASE 3 & 4 Lessons Learned)

### FASE 3 Pitfalls (Domain Connections)

1. **nginx `limit_req_zone` placement**
   - ERROR: Placing `limit_req_zone` in server block causes config test failure
   - FIX: Use `limit_req` directly in location block, or define zone in http block
   - See: chat.upshalter.com config iteration

2. **Hermes port confusion**
   - ERROR: Proxying to port 9119 (not listening) instead of 8645 (hermes-upshalternal)
   - FIX: Always verify with `ss -tlnp | grep <port>` before configuring proxy_pass
   - Hermes default dashboard port: 8645

3. **Enable sites before reload**
   - ERROR: Creating config in sites-available but forgetting symlink to sites-enabled
   - FIX: `ln -sf /etc/nginx/sites-available/<site> /etc/nginx/sites-enabled/`

4. **DNS must be setup**
   - ERROR: Config ready but domain doesn't resolve (chat.upshalter.com initially)
   - FIX: Verify with `dig +short <domain>` before nginx config
   - VALIDATED: chat.upshalter.com now resolves to 76.13.194.136 ✅

5. **Hermes rejects HEAD requests**
   - ERROR: Testing with `curl -sI` (HEAD) returns 405
   - FIX: Use `curl -s -o /dev/null -w "%{http_code}"` (GET) for testing
   - VALIDATED: All 3 domains return HTTP 200 with GET ✅

6. **Nginx restart vs reload**
   - ERROR: Config changes not taking effect with reload
   - FIX: Use `systemctl restart nginx` (not reload) when changing multiple configs

7. **Backup before overwrite**
   - GOOD: `cp /etc/nginx/sites-available/<site> $BACKUP_DIR/`
   - Always backup to /root/upshalter-backups/YYYYMMDD/
   - VALIDATED: Backup stored in /root/upshalter-backups/20260506/ ✅

8. **SSL cert path verification**
   - Verify certs exist: `ls -la /etc/letsencrypt/live/<domain>/`
   - Certificate name in nginx config must match exact domain
   - VALIDATED: All 3 domains have valid certs (expire Jul 2026) ✅

### FASE 4 Pitfalls (Monitoring & Observability)

9. **Cron job shell escaping**
   - ERROR: Heredoc with `&` in terminal causes "Foreground command uses '&' backgrounding" error
   - FIX: Use `execute_code` with Python to write crontab:
     ```python
     from hermes_tools import terminal
     r = terminal("crontab -l 2>/dev/null || echo ''")
     current = r['output']
     # append new entries, write to /tmp/new_cron.txt
     # then: terminal("crontab /tmp/new_cron.txt")
     ```
   - VALIDATED: Cron jobs installed successfully ✅

10. **Script output parsing errors**
    - ERROR: `systemctl list-units hermes-* --state=active | wc -l` returns wrong count
    - FIX: Use `systemctl list-units --type=service --state=active | grep -c "hermes-"`
    - VALIDATED: daily-summary.sh now shows correct service count ✅

11. **Health check script must handle missing commands**
    - ERROR: `sqlite3` command missing returns "N/A" instead of count
    - FIX: Add `2>/dev/null || echo "N/A"` to all external command calls
    - VALIDATED: health-check.sh runs without errors ✅

12. **Telegram send_message format**
    - ERROR: `send_message` fails with invalid chat_id format
    - FIX: Ensure correct format: `telegram` (default) or `telegram:chat_id`
    - NOTE: Telegram integration needs manual setup for automation

### Senator Pentahelix News Scraping Pitfalls (2026-05-06)

1. **Environment variable overrides script default**
   - ERROR: Changing `CYCLE_INTERVAL_SECONDS` in script but container still uses 21600 (6 hours)
   - CAUSE: Environment variable `CYCLE_INTERVAL_SECONDS=21600` in docker-compose.yml overrides script default
   - FIX: Ensure docker-compose.yml environment section has correct value (1800 for 30min)
   - VERIFIED: After patching docker-compose.yml and recreating containers, interval shows 1800s ✅

2. **Script not auto-updated in Docker image**
   - ERROR: Editing script on host doesn't affect running container (image-based)
   - FIX: `docker cp updated_script.py container:/app/scripts/` then restart container
   - Alternatively, rebuild image: `docker compose up -d --force-recreate`
   - VERIFIED: After `docker cp` and restart, new script runs ✅

3. **Static site permission denied**
   - ERROR: Nginx returns 404 when serving from /root (owned by root)
   - FIX: Use `/var/www/<site>` as document root, ensure www-data can read
   - Command: `cp -r /root/<site> /var/www/ && chown -R www-data:www-data /var/www/<site>`
   - VERIFIED: app.upshalter.com now serves from /var/www/app.upshalter.com ✅

4. **Google News RSS parsing**
   - Use regex to parse `<item>` blocks, clean CDATA
   - No BeautifulSoup needed; curl + regex works reliably
   - URL: `https://news.google.com/rss/search?q=<query>&hl=en-US&gl=US&ceid=US:en`
   - VERIFIED: Returns 100 items, fresh 2026 news ✅

5. **SSL cert for static site**
   - Use `certbot certonly --standalone` if Nginx is running (port 80 conflict)
   - Stop Nginx, run certbot, start Nginx
   - Config: listen 443 ssl with cert paths from /etc/letsencrypt/live/<domain>/

**FASE 3 & 4 Validation Results (2026-05-06)**

**FASE 3: Domain Connections — ✅ COMPLETE**
- ✅ workspace.upshalter.com → HTTP 200 (proxy to :3000)
- ✅ hermes.upshalter.com → HTTP 200 (proxy to :8645)
- ✅ chat.upshalter.com → HTTP 200 (proxy to :8000)
- ✅ SSL certs valid for all domains
- ✅ Nginx configs in sites-enabled/
- ✅ Backup in /root/upshalter-backups/20260506/

**FASE 4: Monitoring & Observability — ✅ COMPLETE**
- ✅ health-check.sh → /root/upshalter-scripts/health-check.sh
- ✅ daily-summary.sh → /root/upshalter-scripts/daily-summary.sh
- ✅ ssl-check.sh → /root/upshalter-scripts/ssl-check.sh
- ✅ backup-skp.sh → /root/upshalter-scripts/backup-skp.sh
- ✅ Cron jobs installed:
  - `*/5 * * * *` → health-check.sh
  - `0 0 * * *` → daily-summary.sh (07:00 WIB)
  - `0 1 * * *` → ssl-check.sh (08:00 WIB)
  - `0 20 * * *` → backup-skp.sh (03:00 WIB)
  - `0 0 * * 0` → log cleanup

**FASE 6: Dashboard Human Visibility — ✅ COMPLETE (2026-05-06)**
- ✅ Status page generated: /var/www/status/index.html
  - Update otomatis setiap 5 menit via cron (/etc/cron.d/status-page-update)
  - Nginx config: /etc/nginx/sites-available/status-upshalter
  - Symlink enabled: /etc/nginx/sites-enabled/status-upshalter
  - ⚠️ SSL cert pending: DNS record status.upshalter.com belum diatur (IP: 76.13.194.136 / 2a02:4780:59:7df::1)
- ✅ Telegram alerts:
  - Script: /root/upshalter-scripts/telegram-alert.sh
  - Terintegrasi dengan health-check.sh (alert jika service down)
  - Daily summary otomatis ke Telegram setiap 07:00 WIB (via daily-summary.sh)
- ✅ Cron jobs FASE 6:
  - `*/5 * * * *` → generate-status-page.sh
  - `0 0 * * *` → daily-summary.sh (sudah ada sejak FASE 4, sekarang kirim ke Telegram)

**System Status After FASE 3, 4, 5 & 6:**
- ✅ 8 systemd services active
- ✅ 11 Docker containers running (5 Senator Pentahelix healthy)
- ✅ 3 domains HTTPS active (upshalter.com, workspace.upshalter.com, hermes.upshalter.com)
- ✅ Monitoring & backup automated
- ✅ Kanban workflow automated (Senator cycle + Kurator review)
- ✅ Dashboard visibility: Status page + Telegram alerts + Daily summary

---

### FASE Scripts Reference

**validate-blueprint.sh** (scripts/validate-blueprint.sh):
- Validates all 8 FASEs of AUTOMATION-PROTOCOL.md
- Run before declaring any phase complete
- Output: ✅/⚠️/❌ for each FASE with actual validation (not just file existence)
- Usage: `bash /root/.hermes/skills/devops/hermes-role-deploy/scripts/validate-blueprint.sh`
- **Updated**: Now includes FASE 3 & 4 validation results from 2026-05-06 execution

**deploy-upshalter.sh** (scripts/deploy-upshalter.sh):
- One-click VPSO Upshalter deployment
- Usage: `bash scripts/deploy-upshalter.sh [port] [install_dir]`
- Default: port 9120, install_dir /opt/hermes-upshalter

## References

**Scripts:**
- **Validation script:** `scripts/validate-blueprint.sh` (cek FASE 0-8 otomatis)
- **One-click deploy:** `scripts/deploy-upshalter.sh` (VPSO Upshalter)

**Templates:**  
- Worker Pool: `references/worker-pool-daemon.py`  
- Swarm Docker Compose: `references/swarm-docker-compose.yml`  
- HITL template: `references/hitl-worker-template.py`  
- Senator News Scraping: `references/senator-news-scraping.md` (Google News RSS, interval config, pitfalls)  

**Production Examples:**
- Hermes Internet Agent: `/root/hermes-internet/daemon.py` (Worker Pool)
- Hermes Workspace: `/root/hermes-workspace/` (Workspace Instance)
- Automation Protocol: `/root/Visi 2026/AUTOMATION-PROTOCOL.md` (8-phase setup)
- Ecosystem Visual: `/root/Visi 2026/hermes_ecosystem_complete.html`
