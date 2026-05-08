# Hermes Virtual Office

Agent-Native Virtual Office untuk Hermes Agent — dashboard terpusat untuk mengelola semua AI agents, workspace, dan task management.

![Hermes Virtual Office](https://img.shields.io/badge/Hermes-AI%20Agent-purple)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![License](https://img.shields.io/badge/License-MIT-blue)

## 🏢 Tentang

Hermes Virtual Office adalah antarmuka web terpadu yang menyediakan:
- **Live Agent Status** — Monitor 5 Hermes agents secara real-time
- **Workspace Integration** — Akses langsung ke Hermes Workspace (Vite/React)
- **Kanban Board** — Task management dengan 3-column board (Running/Completed/Failed)
- **Shared Knowledge Pool** — Akses Arsify (Shared Memory)
- **Service Health** — Monitor status semua layanan (auto-refresh)

## 📁 Struktur Folder

```
hermes-virtual-office/
├── docs/           # Dokumentasi sistem (live API)
├── profile/        # Agent profiles (live API)
├── skill/          # Skills catalog
├── tool/           # Tools catalog
├── arsify/         # Shared Knowledge Pool (live API)
├── dashboard/      # Agent dashboards (5 instances)
├── lobby/          # Virtual Office Lobby (main hub)
├── status/         # Service health monitor
├── assets/         # Static assets (CSS, images)
├── scripts/        # Monitoring & utility scripts
└── README.md       # This file
```

## 🌐 Akses Paths

| Path | Deskripsi | Status |
|------|-----------|--------|
| `/hermes/lobby/` | Virtual Office Lobby (main hub) | ✅ Ready |
| `/hermes/status/` | Service health monitor | ✅ Ready |
| `/hermes/docs/` | Dokumentasi sistem | ✅ Ready |
| `/hermes/profile/` | Agent profiles | ✅ Ready |
| `/hermes/skill/` | Skills catalog | ✅ Ready |
| `/hermes/tool/` | Tools catalog | ✅ Ready |
| `/hermes/arsify/` | Shared Knowledge Pool | ✅ Ready |
| `/hermes/dashboard/` | Agent dashboards | ✅ Ready |
| `/hermes/workspace/` | Dev environment (proxy :3000) | ✅ Ready |
| `/hermes/kanban/` | Task board (proxy :3001) | ✅ Ready |
| `/hermes/api/` | Orchestrator API (proxy :8000) | ✅ Ready |
| `/hermes/ws` | WebSocket real-time | ✅ Ready |

## 🔧 Arsitektur

```
workstation.upshalter.com (Nginx Reverse Proxy)
├── /hermes/lobby/     → Static HTML (Virtual Office hub)
├── /hermes/status/    → Static HTML (Health monitor)
├── /hermes/docs/      → Static HTML (Docs)
├── /hermes/profile/   → Static HTML (Profiles)
├── /hermes/skill/     → Static HTML (Skills)
├── /hermes/tool/      → Static HTML (Tools)
├── /hermes/arsify/    → Static HTML (Arsify)
├── /hermes/dashboard/ → Static HTML (Dashboards)
├── /hermes/workspace/ → Proxy ke :3000 (Hermes Workspace)
├── /hermes/kanban/    → Proxy ke :3001 (Hermes Kanban)
├── /hermes/api/       → Proxy ke :8000 (Orchestrator API)
└── /hermes/ws         → WebSocket ke :8000
```

## 🚀 Services

| Service | Port | Deskripsi |
|---------|------|-----------|
| Hermes Workspace | 3000 | Dev environment (Vite) |
| Hermes Kanban | 3001 | Task board (3-column) |
| Orchestrator API | 8000 | Multi-agent orchestration |
| Dashboard (main) | 9119 | Main agent dashboard |
| Dashboard (upshalternal) | 9120 | Upshalternal agent |
| Dashboard (agent1) | 9121 | Agent instance 1 |
| Dashboard (agent2) | 9122 | Agent instance 2 |
| Dashboard (agent3) | 9123 | Agent instance 3 |

## 🛡️ Auto-Recovery

- **PM2**: Auto-start enabled untuk hermes-cli & 9router
- **Docker**: Containers set to `restart=always`
- **Cron**: Monitor services setiap 5 menit (`/root/check-hermes-services.sh`)

## 📊 Perbandingan: Sebelum vs Sekarang

### 🔴 Sebelum (4 Mei 2026)
```
/hermes/              → Dashboard static (saja)
/hermes/workspace/    → Proxy :3000
/hermes/kanban/      → Proxy :3001
/hermes/api/*        → Proxy :8000 + API key
/hermes/ws           → WebSocket
/hermes/workforce/   → Phase3 dashboard (direncanakan, tidak dibuat)
```

### 🟢 Sekarang (5 Mei 2026)
```
/hermes/docs/        → ✅ Dokumentasi sistem
/hermes/profile/     → ✅ Agent profiles (live API)
/hermes/skill/       → ✅ Skills catalog
/hermes/tool/        → ✅ Tools catalog
/hermes/arsify/      → ✅ Shared Knowledge Pool
/hermes/dashboard/   → ✅ Agent dashboards
/hermes/lobby/       → ✅ Virtual Office Lobby (NEW)
/hermes/status/      → ✅ Service health monitor (NEW)
/hermes/workspace/   → ✅ Dev env (proxy :3000)
/hermes/kanban/      → ✅ Task board (proxy :3001)
/hermes/api/         → ✅ Orchestrator API
/hermes/ws           → ✅ WebSocket real-time
```

**Penambahan**: +7 halaman statis baru (docs, profile, skill, tool, arsify, dashboard, lobby, status) dengan live API integration.

## 🎯 Target: Perusahaan Besar

Hermes Virtual Office adalah fondasi untuk **Agent-Native Enterprise**:

1. **Produk**: Virtual office pertama untuk AI agents kolaborasi
2. **Bisnis Model**: Open-Source (3.3k ⭐) + Enterprise SaaS ($500-$5k/bulan)
3. **Scalability**: K8s setelah 100+ enterprise users
4. **Timeline 6 Bulan**: 50+ SMB users, $10k MRR, seed funding $1M

## 🛠️ Installation

```bash
# Clone repo
git clone https://github.com/yourusername/hermes-virtual-office.git
cd hermes-virtual-office

# Copy ke web server
cp -r * /var/www/workstation/hermes/

# Setup Nginx (lihat config di /etc/nginx/sites-available/)
sudo nginx -t && sudo systemctl reload nginx
```

## 📄 License

MIT License — bebas digunakan untuk commercial maupun open-source.

## 🤝 Contributing

Pull requests welcome! Fokus pada:
- UI/UX improvements
- Additional agent integrations
- Enterprise features (SSO, RBAC, audit log)

---

**Built with ❤️ for the Hermes Agent ecosystem**
