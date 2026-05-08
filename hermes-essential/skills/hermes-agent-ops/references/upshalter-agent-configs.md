# Upshalter Multi-Agent Configuration Reference

## Port Assignment
```
┌─────────────────────────────────────────────┐
│ Agent            │ Port  │ Type    │ Status │
├─────────────────────────────────────────────┤
│ Orchestrator     │ :8000 │ Core    │ ✅     │
│ hermes-cli       │ -     │ PM2     │ ✅     │
│ Loyx             │ :8643 │ Docker  │ ✅     │
│ GameDev          │ :8644 │ Docker  │ ✅     │
│ Dashboard        │ :9119 │ Systemd │ ✅     │
│ Upshalternal     │ :9120 │ Systemd │ ✅     │
│ Infra            │ :9121 │ Systemd │ ✅     │
│ Builder          │ :9122 │ Systemd │ ✅     │
│ Plaza            │ :9123 │ Systemd │ ✅     │
│ Workspace        │ :3000 │ Docker  │ ✅     │
└─────────────────────────────────────────────┘
```

## 1. PM2 Configuration (hermes-cli)

**Status:** Running (id: 0)
**Command:** `hermes` CLI agent
**Ecosystem:** `~/.pm2/ecosystem.config.js`

```javascript
// ~/.pm2/ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'hermes-cli',
      script: '/usr/local/bin/hermes',
      args: 'agent',  // or whatever command hermes-cli uses
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};
```

**Management:**
```bash
pm2 list                    # Check status
pm2 logs hermes-cli         # View logs
pm2 restart hermes-cli      # Restart
pm2 save                    # Save process list
pm2 startup                 # Generate startup script
```

---

## 2. Docker Configuration (Loyx & GameDev)

### Loyx (:8643)
**Image:** `nousresearch/hermes-agent:latest`
**Mounts:** 
- `/root/.hermes:/opt/data:rw` (shared memory)
- `/root/loyx-project:/workspace:rw` (project files)

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  hermes-agent:
    image: nousresearch/hermes-agent:latest
    container_name: hermes-loyx
    restart: unless-stopped
    ports:
      - "8643:8642"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - /root/.hermes:/opt/data:rw
      - /root/loyx-project:/workspace:rw
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - ORCHESTRATOR_API_KEY=${ORCHESTRATOR_API_KEY}
      - ORCHESTRATOR_URL=http://host.docker.internal:8000
    user: root
```

### GameDev (:8644)
**Image:** `nousresearch/hermes-agent:latest`
**Mounts:**
- `/root/.hermes:/opt/data:rw`
- `/root/regrow-up-world-dev:/workspace:rw`

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  hermes-gamedev:
    image: nousresearch/hermes-agent:latest
    container_name: hermes-gamedev
    restart: unless-stopped
    ports:
      - "8644:8642"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - /root/.hermes:/opt/data:rw
      - /root/regrow-up-world-dev:/workspace:rw
    environment:
      - ORCHESTRATOR_API_KEY=${ORCHESTRATOR_API_KEY}
      - ORCHESTRATOR_URL=http://host.docker.internal:8000
    user: root
```

**Management:**
```bash
cd /root/hermes-agent-loyx && docker-compose up -d
cd /root/regrow-up-world-dev && docker-compose -f docker-compose-gamedev.yml up -d

docker logs hermes-loyx
docker logs hermes-gamedev
docker restart hermes-loyx hermes-gamedev
```

---

## 3. Systemd Configuration

### Dashboard (:9119)
**File:** `/etc/systemd/system/hermes-dashboard.service`
```ini
[Unit]
Description=Hermes Agent Dashboard
After=network.target

[Service]
Environment="HERMES_ALLOWED_ORIGINS=*"
Type=simple
User=root
ExecStart=/usr/local/bin/hermes dashboard --tui --host 0.0.0.0 --port 9119 --no-open --insecure
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Bridge:** `/etc/systemd/system/hermes-dashboard-bridge.service`
- Agent ID: `dashboard`
- Port: `9119`
- API Key: `hma_iYtXKsJ76m5jntjJWZqiZAYy8VCP_noHSUzXjNC0L9U`

### Upshalternal (:9120)
**File:** `/etc/systemd/system/hermes-upshalternal.service`
```ini
[Unit]
Description=Upshalternal Hermes Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hermes-upshalternal
Environment="HERMES_HOME=/opt/hermes-upshalternal/data"
ExecStart=/usr/local/bin/hermes dashboard --tui --host 0.0.0.0 --port 9120 --no-open --insecure
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Bridge:** `/etc/systemd/system/hermes-upshalternal-bridge.service`
- Agent ID: `upshalternal`
- Port: `9120`
- API Key: `hma_4XRGfT-xVDckggQAkGlujpF7Fyhnlxvruh_GMaJ6U50`

### Infra (:9121)
**File:** `/etc/systemd/system/hermes-infra.service`
```ini
[Unit]
Description=Infra Hermes Agent
After=network.target

[Service]
Type=simple
User=root
Environment="HERMES_HOME=/opt/hermes-infra/data"
ExecStart=/usr/local/bin/hermes dashboard --tui --host 0.0.0.0 --port 9121 --no-open --insecure
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Bridge:** `/etc/systemd/system/hermes-infra-bridge.service`
- Agent ID: `infra`
- API Key: `hma_a9m7BSZR3-9bnrDZsQl7d6vho6teGUkDqeQBwfdLGKU`

### Builder (:9122)
**File:** `/etc/systemd/system/hermes-builder.service`
```ini
[Unit]
Description=Builder Hermes Agent
After=network.target

[Service]
Type=simple
User=root
Environment="HERMES_HOME=/opt/hermes-builder/data"
ExecStart=/usr/local/bin/hermes dashboard --tui --host 0.0.0.0 --port 9122 --no-open --insecure
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Bridge:** `/etc/systemd/system/hermes-builder-bridge.service`

### Plaza (:9123)
**File:** `/etc/systemd/system/hermes-plaza.service`
```ini
[Unit]
Description=Plaza Hermes Agent
After=network.target

[Service]
Type=simple
User=root
Environment="HERMES_HOME=/opt/hermes-plaza/data"
ExecStart=/usr/local/bin/hermes dashboard --tui --host 0.0.0.0 --port 9123 --no-open --insecure
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Bridge:** `/etc/systemd/system/hermes-plaza-bridge.service`

---

## 4. Management Commands

### Systemd Services
```bash
# Reload systemd after changes
systemctl daemon-reload

# Enable services (auto-start on boot)
systemctl enable hermes-dashboard.service
systemctl enable hermes-upshalternal.service
systemctl enable hermes-infra.service
systemctl enable hermes-builder.service
systemctl enable hermes-plaza.service

# Start services
systemctl start hermes-dashboard.service
systemctl start hermes-upshalternal.service
systemctl start hermes-infra.service
systemctl start hermes-builder.service
systemctl start hermes-plaza.service

# Check status
systemctl status hermes-dashboard.service
systemctl status hermes-upshalternal.service
# etc.

# View logs
journalctl -u hermes-dashboard.service -f
journalctl -u hermes-upshalternal.service -f
# etc.
```

### Bridge Services
```bash
# Enable bridge services
systemctl enable hermes-dashboard-bridge.service
systemctl enable hermes-upshalternal-bridge.service
systemctl enable hermes-infra-bridge.service
systemctl enable hermes-builder-bridge.service
systemctl enable hermes-plaza-bridge.service

# Start bridges
systemctl start hermes-*-bridge.service

# Check all hermes services
systemctl list-units | grep hermes
```

---

## 5. Environment Variables

**Critical:** All agents use `ORCHESTRATOR_API_KEY` (not `HERMES_ORCHESTRATOR_KEY`)

**Shared Memory:** `/root/.hermes` mounted to all Docker agents at `/opt/data`

**Docker extra_hosts:** Required for Ollama access:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

---

## 6. Verification Checklist
1. ✅ All systemd services created and enabled
2. ✅ All bridge services configured with correct `ORCHESTRATOR_API_KEY`
3. ✅ Docker agents have shared memory mount + `user: root`
4. ✅ Docker agents have `extra_hosts` for host access
5. ✅ `systemctl daemon-reload` run after service file changes
6. ✅ All agents polling Orchestrator successfully (no TaskStatus enum errors)

---

Generated: 2026-05-05
Status: All 5 agents + bridges configured and running