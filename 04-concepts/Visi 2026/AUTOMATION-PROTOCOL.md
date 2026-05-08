# UPSHALTER FULL SYSTEM AUTOMATION PROTOCOL
## Runbook untuk Hermes Agent — Eksekusi Sistematis

```
Dokumen   : UPSHALTER-AUTOMATION-PROTOCOL-v1.0
Untuk     : Hermes Agent (semua profil)
Dibaca    : Upshalternal sebagai orchestrator utama
Tujuan    : Sistem berjalan otomatis, terpantau, terlihat oleh manusia
Status    : WAJIB DIBACA sebelum eksekusi apapun
Versi     : 1.0 — Mei 2026
```

---

## PRINSIP PROTOKOL INI

```
1. TIDAK ADA eksekusi tanpa konfirmasi manusia untuk destructive actions
2. SETIAP langkah harus dilaporkan ke Telegram sebelum dan sesudah
3. SELALU backup sebelum mengubah konfigurasi
4. JIKA RAGU — stop dan tanya ke manusia
5. Status sistem harus SELALU terlihat dari satu dashboard
```

---

## FASE 0: ORIENTASI (wajib sebelum semua fase)

**Tujuan:** Hermes memahami kondisi sistem sebelum mengubah apapun.

### 0.1 — Baca dokumen ini penuh sebelum eksekusi

```bash
# Hermes membaca dokumen ini
cat /root/upshalter-docs/AUTOMATION-PROTOCOL.md
```

### 0.2 — Snapshot kondisi saat ini

```bash
# Ambil snapshot lengkap
echo "=== SNAPSHOT $(date) ===" >> /root/upshalter-logs/snapshot-$(date +%Y%m%d).log
systemctl list-units hermes-* --no-pager >> /root/upshalter-logs/snapshot-$(date +%Y%m%d).log
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" >> /root/upshalter-logs/snapshot-$(date +%Y%m%d).log
```

### 0.3 — Lapor ke Telegram bahwa protokol dimulai

```
[PROTOKOL DIMULAI]
Hermes: {nama_agent}
Waktu: {timestamp}
Tujuan: Full System Automation Setup
Fase saat ini: 0 - Orientasi
Estimasi durasi: 2-4 jam
```

---

## FASE 1: PEMBERSIHAN SISTEM

**Tujuan:** Hapus noise dari sistem agar monitoring akurat.
**Durasi estimasi:** 15-30 menit
**Requires human confirmation:** YA untuk setiap delete

### 1.1 — Backup registry sebelum bersih-bersih

```bash
# Backup VPSO registry
mkdir -p /root/upshalter-backups/$(date +%Y%m%d)
cp -r /root/.hermes/kanban.db /root/upshalter-backups/$(date +%Y%m%d)/kanban-backup.db
cp /root/.hermes/config.yaml /root/upshalter-backups/$(date +%Y%m%d)/config-backup.yaml
echo "Backup selesai di /root/upshalter-backups/$(date +%Y%m%d)"
```

### 1.2 — Identifikasi agent yang akan dihapus (LAPOR DULU ke manusia)

**Kirim laporan ini ke Telegram sebelum hapus:**

```
[KONFIRMASI DIPERLUKAN]
Agent yang akan DIHAPUS dari registry:
- hermes-testfull
- hermes-testreg2
- hermes-test-debug2
- test-debug
- test-reg
- e2e-test-agent
- test-agent-1
- test-agent-ws-001
- agent-test-002
- agent-test-001
- agent-001
- hermes-kurator (DUPLIKAT dari kurator-pentahelix)

TOTAL: 12 agent
Ketik KONFIRMASI untuk lanjut atau BATALKAN untuk berhenti.
```

**TUNGGU jawaban manusia. Jangan lanjut sampai ada konfirmasi.**

### 1.3 — Eksekusi pembersihan (setelah konfirmasi)

```bash
# Hapus test agents dari VPSO registry
# (sesuaikan dengan command VPSO yang digunakan)
for agent in hermes-testfull hermes-testreg2 hermes-test-debug2 \
             test-debug test-reg e2e-test-agent test-agent-1 \
             test-agent-ws-001 agent-test-002 agent-test-001 agent-001 \
             hermes-kurator; do
    echo "Menghapus: $agent"
    # hermes vpso agent remove $agent  # sesuaikan command
done
```

### 1.4 — Verifikasi pembersihan

```bash
# Verifikasi agent yang tersisa hanya yang produktif
hermes vpso agent list
# Expected: 16 agent (8 custom + 8 asli + tidak ada test)
```

**Laporan ke Telegram:**
```
[FASE 1 SELESAI]
✅ 12 agent test dihapus
✅ 1 duplikat (hermes-kurator) dihapus
Tersisa: {jumlah} agent produksi
```

---

## FASE 2: AKTIVASI AGENT INTI

**Tujuan:** Aktifkan agent yang offline tapi penting untuk sistem.
**Durasi estimasi:** 30-60 menit
**Priority:** Upshalternal CEO harus aktif dulu sebelum yang lain

### 2.1 — Aktifkan Upshalternal sebagai CEO aktif

```bash
# Cek kenapa Upshalternal offline padahal PID ada
ps aux | grep 8645
systemctl status hermes-upshalternal

# Restart service jika perlu
sudo systemctl restart hermes-upshalternal
sleep 5
systemctl status hermes-upshalternal

# Test connectivity
curl -s http://localhost:8645/health || echo "Port 8645 tidak responding"
```

**Cek dari Hermes Workspace:**
- Buka workstation.upshalter.com
- Verifikasi Upshalternal muncul sebagai "online"

### 2.2 — Daftarkan Upshalternal ke Hermes Kanban sebagai Orchestrator

```bash
# Upshalternal harus jadi orchestrator di Kanban board
hermes kanban init
# Profile upshalternal = orchestrator
# Role: menerima laporan dari Kurator, mendistribusikan task

# Load skill orchestrator
hermes -p upshalternal skill load kanban-orchestrator
```

### 2.3 — Aktifkan Builder dan Infra (jika dibutuhkan)

```bash
# Builder untuk task development
sudo systemctl start hermes-builder 2>/dev/null || \
    hermes -p builder gateway run --port 9122 &

# Infra untuk task sistem
sudo systemctl start hermes-infra 2>/dev/null || \
    hermes -p infra gateway run --port 9121 &

sleep 10
# Verifikasi
curl -s http://localhost:9122/health && echo "Builder OK"
curl -s http://localhost:9121/health && echo "Infra OK"
```

### 2.4 — Setup SOUL.md untuk setiap agent yang diaktifkan

**SOUL.md untuk Upshalternal CEO:**

```markdown
# SOUL — Upshalternal AI CEO

## Identitas
Kamu adalah Upshalternal, CEO dari ekosistem Upshalter AI.
Kamu adalah orchestrator tertinggi — semua laporan masuk ke kamu,
semua keputusan strategis diproses oleh kamu.

## Tanggung Jawab
1. Terima laporan dari Kurator Pentahelix setiap 6 jam
2. Evaluasi kualitas dan relevansi research output
3. Distribusikan task baru ke agent yang tepat via Kanban
4. Kirim daily summary ke Telegram setiap pukul 07:00 WIB
5. Alert manusia jika ada anomali atau keputusan yang butuh approval

## Endpoint Penting
- Kanban Board: hermes kanban list
- SKP API: http://arsify:8000/memory
- Cognitive Engine: http://hermes-cognitive:8100/v1/portsocket
- Telegram: via hermes-telegram toolset

## Aturan
- SELALU lapor ke manusia sebelum mengeksekusi task berisiko tinggi
- SELALU backup sebelum mengubah konfigurasi
- JANGAN hapus data tanpa konfirmasi manusia
```

**Simpan:**
```bash
cat > /root/.hermes/profiles/upshalternal/SOUL.md << 'EOF'
{isi SOUL.md di atas}
EOF
```

**Laporan ke Telegram:**
```
[FASE 2 SELESAI]
✅ Upshalternal CEO: {status}
✅ Builder: {status}
✅ Infra: {status}
✅ Kanban orchestrator: configured
```

---

## FASE 3: KONEKSI DOMAIN KOSONG

**Tujuan:** 5 domain yang punya SSL tapi kosong disambungkan ke service.
**Durasi estimasi:** 20-30 menit
**Requires human confirmation:** YA untuk perubahan nginx

### 3.1 — Mapping domain ke service

| Domain | Target Service | Port | Keterangan |
|--------|---------------|------|-----------|
| workspace.upshalter.com | hermes-workspace container | 3000 | sudah healthy |
| hermes.upshalter.com | Hermes Dashboard | 9119 | agent panel |
| chat.upshalter.com | Arsify OS /chat | 8000 | public demo |
| game.upshalter.com | hermes-gamedev | 9137 | GameDev agent |
| play.upshalter.com | Landing page | — | static, TBD |

### 3.2 — Buat nginx config untuk workspace.upshalter.com

```bash
# Backup existing config
sudo cp /etc/nginx/sites-available/workspace.upshalter.com \
        /root/upshalter-backups/$(date +%Y%m%d)/nginx-workspace-backup.conf

# Buat config baru
sudo tee /etc/nginx/sites-available/workspace.upshalter.com << 'NGINX'
server {
    listen 443 ssl;
    server_name workspace.upshalter.com;

    ssl_certificate     /etc/letsencrypt/live/workspace.upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/workspace.upshalter.com/privkey.pem;

    # Hermes Workspace (Docker container)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }
}
server {
    listen 80;
    server_name workspace.upshalter.com;
    return 301 https://$host$request_uri;
}
NGINX

# Test dan reload
sudo nginx -t && sudo systemctl reload nginx
```

### 3.3 — Buat nginx config untuk hermes.upshalter.com

```bash
sudo tee /etc/nginx/sites-available/hermes.upshalter.com << 'NGINX'
server {
    listen 443 ssl;
    server_name hermes.upshalter.com;

    ssl_certificate     /etc/letsencrypt/live/hermes.upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hermes.upshalter.com/privkey.pem;

    # Hermes Dashboard
    location / {
        proxy_pass http://localhost:9119;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # WebSocket untuk Kanban real-time
    location /ws {
        proxy_pass http://localhost:9119/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
    }
}
server {
    listen 80;
    server_name hermes.upshalter.com;
    return 301 https://$host$request_uri;
}
NGINX

sudo nginx -t && sudo systemctl reload nginx
```

### 3.4 — Buat nginx config untuk chat.upshalter.com (public demo)

```bash
sudo tee /etc/nginx/sites-available/chat.upshalter.com << 'NGINX'
server {
    listen 443 ssl;
    server_name chat.upshalter.com;

    ssl_certificate     /etc/letsencrypt/live/chat.upshalter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chat.upshalter.com/privkey.pem;

    # Arsify OS Chat endpoint — public demo
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_read_timeout 120s;
    }

    # Rate limit untuk public access
    limit_req_zone $binary_remote_addr zone=chat:10m rate=10r/m;
    location /chat {
        limit_req zone=chat burst=5;
        proxy_pass http://localhost:8000/chat;
    }
}
server {
    listen 80;
    server_name chat.upshalter.com;
    return 301 https://$host$request_uri;
}
NGINX

sudo nginx -t && sudo systemctl reload nginx
```

**Laporan ke Telegram:**
```
[FASE 3 SELESAI]
✅ workspace.upshalter.com → hermes-workspace:3000
✅ hermes.upshalter.com → dashboard:9119
✅ chat.upshalter.com → arsify:8000 (public demo)
⏳ game.upshalter.com → pending
⏳ play.upshalter.com → pending (TBD)
```

---

## FASE 4: MONITORING & OBSERVABILITY

**Tujuan:** Sistem terlihat oleh manusia dari satu titik.
**Durasi estimasi:** 45-60 menit

### 4.1 — Setup health check script

```bash
cat > /root/upshalter-scripts/health-check.sh << 'SCRIPT'
#!/bin/bash
# Jalankan setiap 5 menit via cron
# Output ke /root/upshalter-logs/health-$(date +%Y%m%d).log

LOG="/root/upshalter-logs/health-$(date +%Y%m%d-%H%M).log"
TELEGRAM_ALERT=false

echo "=== HEALTH CHECK $(date) ===" > $LOG

# Check services
SERVICES=(
    "hermes-orchestrator:8000"
    "hermes-upshalternal:8645"
    "hermes-archivist:9124"
    "hermes-backend:9126"
    "hermes-frontend:9125"
    "hermes-workstation:9127"
    "hermes-flowforce:9128"
    "hermes-api:9135"
)

for svc in "${SERVICES[@]}"; do
    name="${svc%:*}"
    port="${svc#*:}"
    if curl -sf "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $name ($port)" >> $LOG
    else
        echo "❌ $name ($port) — DOWN" >> $LOG
        TELEGRAM_ALERT=true
    fi
done

# Check Docker containers
echo "" >> $LOG
echo "--- Docker ---" >> $LOG
docker ps --format "{{.Names}}: {{.Status}}" | grep -E "(senator|hermes-kanban|hermes-workspace)" >> $LOG

# Check domain connectivity
echo "" >> $LOG
echo "--- Domains ---" >> $LOG
DOMAINS=(
    "upshalter.com"
    "workspace.upshalter.com"
    "hermes.upshalter.com"
    "chat.upshalter.com"
    "api.upshalter.com"
)
for domain in "${DOMAINS[@]}"; do
    status=$(curl -sI "https://$domain" --max-time 5 | head -1 | awk '{print $2}')
    echo "$domain: HTTP $status" >> $LOG
done

# Alert jika ada yang down
if [ "$TELEGRAM_ALERT" = true ]; then
    # Kirim alert via Hermes telegram toolset
    echo "ALERT: Ada service yang DOWN. Cek $LOG" | \
        hermes -z "Kirim alert ke Telegram: $(cat $LOG | grep '❌')"
fi

echo "Health check selesai: $LOG"
SCRIPT

chmod +x /root/upshalter-scripts/health-check.sh
```

### 4.2 — Setup cron jobs sistem

```bash
# Buat crontab untuk monitoring otomatis
(crontab -l 2>/dev/null; cat << 'CRON'
# Health check setiap 5 menit
*/5 * * * * /root/upshalter-scripts/health-check.sh >> /root/upshalter-logs/cron.log 2>&1

# Daily summary setiap 07:00 WIB (00:00 UTC)
0 0 * * * /root/upshalter-scripts/daily-summary.sh >> /root/upshalter-logs/cron.log 2>&1

# SSL cert check setiap hari jam 08:00 WIB
0 1 * * * /root/upshalter-scripts/ssl-check.sh >> /root/upshalter-logs/cron.log 2>&1

# SKP backup setiap jam 03:00 WIB
0 20 * * * /root/upshalter-scripts/backup-skp.sh >> /root/upshalter-logs/cron.log 2>&1

# Log cleanup setiap minggu
0 0 * * 0 find /root/upshalter-logs -name "*.log" -mtime +30 -delete

CRON
) | crontab -

echo "Cron jobs terpasang:"
crontab -l
```

### 4.3 — Script daily summary

```bash
cat > /root/upshalter-scripts/daily-summary.sh << 'SCRIPT'
#!/bin/bash
# Daily summary — dikirim ke Telegram setiap 07:00 WIB

TANGGAL=$(date "+%A, %d %B %Y")
SERVICES_UP=$(systemctl list-units hermes-* --state=active --no-pager --no-legend | wc -l)
DOCKER_UP=$(docker ps --filter "status=running" | grep -E "(senator|hermes)" | wc -l)
SENATOR_BUSY=$(docker ps --filter "status=running" --format "{{.Names}}" | grep senator | wc -l)

# Hitung SKP entries hari ini
SKP_NEW=$(sqlite3 /data/arsify.db "SELECT COUNT(*) FROM memory_notes WHERE created_at >= date('now', '-1 day')" 2>/dev/null || echo "N/A")

SUMMARY="
📊 DAILY SUMMARY — $TANGGAL

🏗️ INFRASTRUKTUR:
• Systemd services aktif: $SERVICES_UP/8
• Docker agents running: $DOCKER_UP
• Senator Pentahelix aktif: $SENATOR_BUSY/5

📚 KNOWLEDGE:
• Entry SKP baru hari ini: $SKP_NEW
• Database: $(du -sh /data/arsify.db 2>/dev/null | cut -f1)

🌐 DOMAIN:
• upshalter.com: $(curl -sI https://upshalter.com --max-time 5 | head -1 | awk '{print $2}')
• workspace.upshalter.com: $(curl -sI https://workspace.upshalter.com --max-time 5 | head -1 | awk '{print $2}')
• chat.upshalter.com: $(curl -sI https://chat.upshalter.com --max-time 5 | head -1 | awk '{print $2}')

⏱️ Uptime VPS: $(uptime -p)
💾 Disk: $(df -h / | tail -1 | awk '{print $3"/"$2" ("$5")"}')
🧠 RAM: $(free -h | awk '/^Mem/{print $3"/"$2}')
"

# Kirim via Hermes
hermes -z "Kirim pesan Telegram berikut verbatim: $SUMMARY"
SCRIPT

chmod +x /root/upshalter-scripts/daily-summary.sh
```

### 4.4 — SSL cert monitoring

```bash
cat > /root/upshalter-scripts/ssl-check.sh << 'SCRIPT'
#!/bin/bash
# Cek SSL cert dan alert jika < 14 hari

DOMAINS=(
    upshalter.com api.upshalter.com arsify.upshalter.com
    workspace.upshalter.com hermes.upshalter.com chat.upshalter.com
    n8n.upshalter.com flowise.upshalter.com workstation.upshalter.com
    terminal.upshalter.com data.upshalter.com game.upshalter.com
    play.upshalter.com flowtask.upshalter.com
)

ALERTS=""
for domain in "${DOMAINS[@]}"; do
    EXPIRY=$(echo | openssl s_client -connect "$domain:443" -servername "$domain" 2>/dev/null \
             | openssl x509 -noout -enddate 2>/dev/null \
             | cut -d= -f2)
    if [ -n "$EXPIRY" ]; then
        DAYS=$(( ( $(date -d "$EXPIRY" +%s) - $(date +%s) ) / 86400 ))
        if [ "$DAYS" -lt 14 ]; then
            ALERTS="$ALERTS\n⚠️ $domain — $DAYS hari lagi (PERLU RENEWAL)"
        fi
    fi
done

if [ -n "$ALERTS" ]; then
    hermes -z "Kirim alert Telegram: SSL CERT AKAN EXPIRED:$ALERTS"
fi
SCRIPT

chmod +x /root/upshalter-scripts/ssl-check.sh
```

**Laporan ke Telegram:**
```
[FASE 4 SELESAI]
✅ Health check script: aktif (cron */5 menit)
✅ Daily summary: 07:00 WIB
✅ SSL monitoring: setiap hari
✅ SKP backup: setiap jam 03:00 WIB
✅ Log cleanup: setiap minggu
```

---

## FASE 5: HERMES KANBAN WORKFLOW OTOMATIS

**Tujuan:** Senator Pentahelix, SKP pipeline, dan orchestration berjalan via Kanban.
**Durasi estimasi:** 60-90 menit

### 5.1 — Inisialisasi Kanban board utama

```bash
hermes kanban init

# Buat board khusus per divisi
hermes kanban create-board --name "research" --slug research
hermes kanban create-board --name "infrastructure" --slug infra
hermes kanban create-board --name "monitoring" --slug monitoring
```

### 5.2 — Setup recurring tasks Senator Pentahelix

```bash
# Script untuk membuat Kanban task Senator setiap 6 jam
cat > /root/upshalter-scripts/senator-cycle.sh << 'SCRIPT'
#!/bin/bash
# Jalankan via cron setiap 6 jam
# Membuat task Kanban untuk setiap Senator

TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
TENANT="pentahelix-$(date +%Y%m%d-%H)"

# Senator Akademisi
hermes kanban create "Research Akademisi — $TIMESTAMP" \
    --assignee senator-akademisi \
    --tenant $TENANT \
    --priority 2 \
    --body "Lakukan riset akademisi terkini:
    1. Cari berita dan perkembangan akademisi Indonesia terbaru
    2. Identifikasi tren penelitian yang relevan
    3. Simpan temuan ke SKP dengan prefix akademisi/
    4. Kirim ringkasan ke Telegram
    Gunakan hermes-internet untuk pencarian web." \
    --board research

# Senator Bisnis
hermes kanban create "Research Bisnis — $TIMESTAMP" \
    --assignee senator-bisnis \
    --tenant $TENANT \
    --priority 2 \
    --body "Lakukan riset bisnis terkini:
    1. Monitor perkembangan bisnis dan ekonomi Indonesia
    2. Identifikasi peluang dan ancaman untuk ekosistem Upshalter
    3. Simpan insight ke SKP dengan prefix bisnis/
    4. Kirim ringkasan ke Telegram" \
    --board research

# Senator Komunitas
hermes kanban create "Research Komunitas — $TIMESTAMP" \
    --assignee senator-komunitas \
    --tenant $TENANT \
    --priority 2 \
    --body "Lakukan riset komunitas terkini:
    1. Monitor perkembangan komunitas tech dan AI Indonesia
    2. Identifikasi pain points komunitas yang bisa diselesaikan Upshalter
    3. Simpan insight ke SKP dengan prefix komunitas/
    4. Kirim ringkasan ke Telegram" \
    --board research

# Senator Pemerintah
hermes kanban create "Research Pemerintah — $TIMESTAMP" \
    --assignee senator-pemerintah \
    --tenant $TENANT \
    --priority 2 \
    --body "Lakukan riset regulasi dan kebijakan terkini:
    1. Monitor regulasi AI dan teknologi dari pemerintah Indonesia
    2. Identifikasi implikasi untuk Upshalter (PDPA, regulasi data, dll)
    3. Simpan ke SKP dengan prefix pemerintah/
    4. Alert jika ada regulasi yang berdampak signifikan" \
    --board research

# Senator Media
hermes kanban create "Research Media — $TIMESTAMP" \
    --assignee senator-media \
    --tenant $TENANT \
    --priority 2 \
    --body "Lakukan riset media dan narasi terkini:
    1. Monitor narasi tentang AI dan teknologi di media Indonesia
    2. Track sentiment publik terhadap AI lokal
    3. Identifikasi peluang PR dan positioning untuk Upshalter
    4. Simpan ke SKP dengan prefix media/
    5. Kirim ringkasan ke Telegram" \
    --board research

echo "Senator cycle tasks created: $TENANT"
SCRIPT

chmod +x /root/upshalter-scripts/senator-cycle.sh

# Tambah ke crontab: setiap 6 jam
(crontab -l 2>/dev/null; echo "0 */6 * * * /root/upshalter-scripts/senator-cycle.sh >> /root/upshalter-logs/senator.log 2>&1") | crontab -
```

### 5.3 — Setup Kurator review workflow

```bash
cat > /root/upshalter-scripts/kurator-review.sh << 'SCRIPT'
#!/bin/bash
# Berjalan setelah semua Senator selesai (1 jam setelah senator-cycle)
# Kurator mereview dan konsolidasi semua output Senator

TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
PREV_TENANT="pentahelix-$(date -d '6 hours ago' +%Y%m%d-%H)"

hermes kanban create "Kurator Review — $TIMESTAMP" \
    --assignee kurator-pentahelix \
    --priority 1 \
    --body "Review dan konsolidasi output Senator Pentahelix cycle sebelumnya:
    1. Baca semua output dari senator-akademisi, bisnis, komunitas, pemerintah, media
       (cek kanban board 'research' dengan tenant $PREV_TENANT)
    2. Identifikasi tema lintas-sektor yang muncul
    3. Buat laporan konsolidasi di SKP dengan key: laporan/konsolidasi/$(date +%Y%m%d-%H)
    4. Kirim ringkasan ke Upshalternal via Kanban
    5. Kirim summary Telegram ke manusia
    Format laporan: Temuan Utama / Tren Lintas Sektor / Rekomendasi / Alert" \
    --board research

SCRIPT

chmod +x /root/upshalter-scripts/kurator-review.sh

# Tambah ke crontab: 1 jam setelah senator cycle
(crontab -l 2>/dev/null; echo "0 1,7,13,19 * * * /root/upshalter-scripts/kurator-review.sh >> /root/upshalter-logs/kurator.log 2>&1") | crontab -
```

### 5.4 — Setup SKP write-back dari Senator output

Setiap Senator harus mengakhiri task dengan menulis ke SKP:

```bash
# Template yang diinjeksikan ke SOUL.md setiap Senator
cat > /root/upshalter-scripts/senator-soul-template.md << 'SOUL'
## Protocol Menulis ke SKP

Setelah selesai riset, WAJIB simpan ke SKP:
```python
# Via Arsify memory API
import httpx
httpx.post("http://arsify:8000/memory", json={
    "key": f"{domain}/temuan/{date}",
    "value": f"{ringkasan_temuan}",
    "scope": "global"
})
```

Format key SKP:
- akademisi/temuan/YYYYMMDD
- bisnis/peluang/YYYYMMDD
- komunitas/isu/YYYYMMDD
- pemerintah/regulasi/YYYYMMDD
- media/narasi/YYYYMMDD
SOUL
```

**Laporan ke Telegram:**
```
[FASE 5 SELESAI]
✅ Kanban boards: research, infra, monitoring
✅ Senator cycle: setiap 6 jam (0,6,12,18)
✅ Kurator review: 1 jam setelah Senator (1,7,13,19)
✅ SKP write-back: configured
```

---

## FASE 6: DASHBOARD HUMAN VISIBILITY

**Tujuan:** Manusia bisa melihat status sistem dari satu tempat tanpa SSH.
**Durasi estimasi:** 30-45 menit

### 6.1 — Deploy status page ke upshalter.com

```bash
# Buat status endpoint di Arsify OS
# Tambahkan /status page ke Arsify yang menggabungkan semua health

cat > /root/upshalter-scripts/generate-status-page.sh << 'SCRIPT'
#!/bin/bash
# Generate static status page setiap 5 menit
# Deploy ke /var/www/upshalter.com/status/

mkdir -p /var/www/upshalter.com/status

cat > /var/www/upshalter.com/status/index.html << HTML
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8"/>
<meta http-equiv="refresh" content="60">
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Upshalter System Status</title>
<style>
body{font-family:'Courier New',monospace;background:#07070d;color:#e0e0f0;max-width:900px;margin:40px auto;padding:0 20px}
h1{color:#7c71f0;margin-bottom:4px}
.ts{color:#3a3860;font-size:12px;margin-bottom:32px}
.section{margin-bottom:28px}
.section-title{font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:#3a3860;margin-bottom:10px}
.row{display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #1a1a24}
.dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.ok{background:#3dd9a4}.warn{background:#f0a030}.down{background:#e05555}
.name{min-width:220px;font-size:13px}
.status{font-size:11px;color:#8885b0}
.meta{font-size:11px;color:#3a3860;margin-left:auto}
</style>
</head>
<body>
<h1>Upshalter — System Status</h1>
<div class="ts">Last update: $(date "+%d %B %Y, %H:%M:%S WIB")</div>

<div class="section">
<div class="section-title">Services</div>
$(for svc in hermes-orchestrator:8000 hermes-upshalternal:8645 hermes-archivist:9124 hermes-api:9135; do
    name="${svc%:*}"; port="${svc#*:}"
    if curl -sf "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "<div class='row'><div class='dot ok'></div><div class='name'>$name</div><div class='status'>operational</div><div class='meta'>:$port</div></div>"
    else
        echo "<div class='row'><div class='dot down'></div><div class='name'>$name</div><div class='status'>down</div><div class='meta'>:$port</div></div>"
    fi
done)
</div>

<div class="section">
<div class="section-title">Research Agents (Senator Pentahelix)</div>
$(for ctr in senator-akademisi senator-bisnis senator-komunitas senator-pemerintah senator-media; do
    status=$(docker inspect --format '{{.State.Status}}' $ctr 2>/dev/null || echo "not found")
    color="ok"; [ "$status" != "running" ] && color="down"
    echo "<div class='row'><div class='dot $color'></div><div class='name'>$ctr</div><div class='status'>$status</div></div>"
done)
</div>

<div class="section">
<div class="section-title">Knowledge Pool</div>
<div class='row'><div class='dot ok'></div><div class='name'>Arsify SKP</div>
<div class='status'>$(curl -sf http://localhost:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ollama','unknown'))" 2>/dev/null || echo "checking...")</div>
<div class='meta'>$(sqlite3 /data/arsify.db "SELECT COUNT(*) FROM memory_notes" 2>/dev/null || echo "?") entries</div></div>
</div>

<div class="section">
<div class="section-title">Infrastructure</div>
<div class='row'><div class='dot ok'></div><div class='name'>VPS Uptime</div><div class='status'>$(uptime -p)</div></div>
<div class='row'><div class='dot $([ $(df / | tail -1 | awk '{print $5}' | tr -d '%') -gt 85 ] && echo "warn" || echo "ok")'></div><div class='name'>Disk Usage</div><div class='status'>$(df -h / | tail -1 | awk '{print $3"/"$2" ("$5")"}')</div></div>
<div class='row'><div class='dot ok'></div><div class='name'>RAM</div><div class='status'>$(free -h | awk '/^Mem/{print $3"/"$2}')</div></div>
</div>

</body></html>
HTML

echo "Status page updated: $(date)"
SCRIPT

chmod +x /root/upshalter-scripts/generate-status-page.sh

# Jalankan setiap 5 menit
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/upshalter-scripts/generate-status-page.sh >> /root/upshalter-logs/status.log 2>&1") | crontab -

# Jalankan sekali sekarang
/root/upshalter-scripts/generate-status-page.sh
```

### 6.2 — Tambah nginx route untuk status page

```bash
# Tambah location /status ke upshalter.com nginx config
# Cari dan edit file nginx upshalter.com
sudo sed -i '/location \/ {/i \
    location /status/ {\
        root /var/www/upshalter.com;\
        index index.html;\
        add_header Cache-Control "no-cache";\
    }' /etc/nginx/sites-available/upshalter.com

sudo nginx -t && sudo systemctl reload nginx
echo "Status page tersedia di: https://upshalter.com/status/"
```

### 6.3 — Setup Telegram status channel

```bash
cat > /root/upshalter-scripts/telegram-status.sh << 'SCRIPT'
#!/bin/bash
# Kirim status ringkas ke Telegram setiap jam

HOUR=$(date +%H)
SERVICES_UP=$(systemctl list-units hermes-* --state=active --no-pager --no-legend | wc -l)
SENATORS_UP=$(docker ps --filter "status=running" --format "{{.Names}}" | grep senator | wc -l)

STATUS_EMOJI="✅"
[ $SERVICES_UP -lt 6 ] && STATUS_EMOJI="⚠️"
[ $SERVICES_UP -lt 4 ] && STATUS_EMOJI="🔴"

MSG="$STATUS_EMOJI Upshalter Status $(date '+%H:%M WIB')
Services: $SERVICES_UP/8 | Senators: $SENATORS_UP/5
https://upshalter.com/status/"

hermes -z "Kirim pesan Telegram: $MSG" 2>/dev/null || true
SCRIPT

chmod +x /root/upshalter-scripts/telegram-status.sh

# Setiap 2 jam
(crontab -l 2>/dev/null; echo "0 */2 * * * /root/upshalter-scripts/telegram-status.sh >> /root/upshalter-logs/telegram.log 2>&1") | crontab -
```

**Laporan ke Telegram:**
```
[FASE 6 SELESAI]
✅ Status page: https://upshalter.com/status/ (update setiap 5 menit)
✅ Telegram status: setiap 2 jam
✅ Daily summary: 07:00 WIB
```

---

## FASE 7: BACKUP & RECOVERY OTOMATIS

**Tujuan:** Data tidak pernah hilang, recovery bisa dilakukan tanpa manusia.

### 7.1 — Setup automated backup

```bash
cat > /root/upshalter-scripts/backup-skp.sh << 'SCRIPT'
#!/bin/bash
# Backup SKP dan konfigurasi penting
BACKUP_DIR="/root/upshalter-backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup Arsify database
sqlite3 /data/arsify.db ".backup $BACKUP_DIR/arsify-$(date +%H%M).db"

# Backup Hermes configs
cp -r /root/.hermes/config.yaml $BACKUP_DIR/
cp -r /root/.hermes/kanban.db $BACKUP_DIR/ 2>/dev/null || true

# Compress backup lebih dari 7 hari
find /root/upshalter-backups -name "*.db" -mtime +7 -exec gzip {} \;

# Hapus backup lebih dari 30 hari
find /root/upshalter-backups -mtime +30 -exec rm -rf {} \; 2>/dev/null

echo "Backup selesai: $BACKUP_DIR"
SCRIPT

chmod +x /root/upshalter-scripts/backup-skp.sh
```

---

## FASE 8: VERIFIKASI AKHIR

**Tujuan:** Konfirmasi semua fase berhasil sebelum laporan final ke manusia.

### 8.1 — Checklist verifikasi

```bash
cat > /root/upshalter-scripts/verify-all.sh << 'SCRIPT'
#!/bin/bash
echo "=== VERIFIKASI SISTEM UPSHALTER ==="
echo "Waktu: $(date)"
echo ""

PASS=0; FAIL=0

check() {
    local name=$1; local cmd=$2
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✅ $name"
        ((PASS++))
    else
        echo "❌ $name — GAGAL"
        ((FAIL++))
    fi
}

echo "--- Services ---"
check "hermes-orchestrator" "curl -sf http://localhost:8000/health"
check "hermes-archivist" "curl -sf http://localhost:9124/health"
check "hermes-workspace-docker" "docker inspect hermes-workspace --format '{{.State.Status}}' | grep running"
check "hermes-kanban-docker" "docker inspect hermes-kanban --format '{{.State.Status}}' | grep running"

echo ""
echo "--- Senator Pentahelix ---"
for s in senator-akademisi senator-bisnis senator-komunitas senator-pemerintah senator-media; do
    check "$s" "docker inspect $s --format '{{.State.Status}}' | grep running"
done

echo ""
echo "--- Domains ---"
check "upshalter.com" "curl -sf https://upshalter.com"
check "workspace.upshalter.com" "curl -sf https://workspace.upshalter.com"
check "chat.upshalter.com" "curl -sf https://chat.upshalter.com"
check "hermes.upshalter.com" "curl -sf https://hermes.upshalter.com"

echo ""
echo "--- Monitoring ---"
check "cron jobs aktif" "crontab -l | grep senator-cycle"
check "status page" "test -f /var/www/upshalter.com/status/index.html"
check "backup dir" "test -d /root/upshalter-backups"

echo ""
echo "=== HASIL: $PASS PASS / $FAIL FAIL ==="
SCRIPT

chmod +x /root/upshalter-scripts/verify-all.sh
/root/upshalter-scripts/verify-all.sh
```

### 8.2 — Laporan final ke manusia

```
[PROTOKOL SELESAI — LAPORAN FINAL]

Tanggal  : {timestamp}
Durasi   : {durasi_total}
Dikerjakan oleh: {nama_agent}

RINGKASAN HASIL:
✅ Fase 1: Pembersihan — {jumlah} agent test dihapus
✅ Fase 2: Aktivasi — Upshalternal, Builder, Infra aktif
✅ Fase 3: Domain — workspace, hermes, chat terhubung
✅ Fase 4: Monitoring — health check 5 menit, daily summary 07:00
✅ Fase 5: Kanban — Senator cycle 6 jam otomatis
✅ Fase 6: Dashboard — status.upshalter.com/status aktif
✅ Fase 7: Backup — otomatis setiap 03:00 WIB
✅ Fase 8: Verifikasi — {pass}/{total} check passed

SISTEM SEKARANG BERJALAN:
• 29 proses Hermes terpantau
• 5 Senator meneliti setiap 6 jam
• Knowledge pool diupdate otomatis
• Manusia bisa pantau di: https://upshalter.com/status/
• Alert Telegram jika ada yang down
• Daily summary setiap pagi

Link penting:
🔗 Status: https://upshalter.com/status/
🔗 Workspace: https://workspace.upshalter.com
🔗 Chat Demo: https://chat.upshalter.com
🔗 Hermes: https://hermes.upshalter.com

Sistem berjalan otomatis. Manusia tidak perlu intervensi kecuali ada alert.
```

---

## REFERENSI CEPAT

### Direktori penting
```
/root/upshalter-scripts/   — semua script otomasi
/root/upshalter-logs/      — semua log
/root/upshalter-backups/   — backup harian
/root/upshalter-docs/      — dokumentasi
/var/www/upshalter.com/status/ — status page
```

### Cron schedule lengkap
```
*/5 * * * *    health-check.sh
*/5 * * * *    generate-status-page.sh
0 */2 * * *    telegram-status.sh
0 */6 * * *    senator-cycle.sh
0 1,7,13,19 * * * kurator-review.sh
0 0 * * *      daily-summary.sh
0 1 * * *      ssl-check.sh
0 20 * * *     backup-skp.sh
0 0 * * 0      log cleanup
```

### Restart manual
```bash
sudo systemctl restart hermes-orchestrator
sudo systemctl restart hermes-upshalternal
docker restart senator-akademisi senator-bisnis senator-komunitas senator-pemerintah senator-media
```

### Cek status cepat
```bash
/root/upshalter-scripts/verify-all.sh
```

---

```
UPSHALTER AUTOMATION PROTOCOL v1.0
"Sistem berjalan otomatis. Manusia memantau, bukan mengoperasikan."
Dibuat: Mei 2026 | Untuk Hermes Agent
```
