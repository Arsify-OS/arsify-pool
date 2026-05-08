# PRD-001: Foundation Fix — Sistem Harus Berjalan Dulu
## Status: URGENT · Dikerjakan HARI INI
## Assignee: Hermes Agent (profil: infra atau upshalternal)
## Deadline: 24 jam dari sekarang

---

## KONTEKS UNTUK HERMES

Berdasarkan Weekly Report 1-7 Mei 2026, sistem memiliki 5 bug kritis yang menyebabkan:
- 775 cycle Senator berjalan tanpa menghasilkan SATU PUN knowledge entry ke SKP
- hermes-upshalternal restart 19.052 kali dalam 7 hari (membuang resource)
- Semua cron automation tidak berjalan (0 eksekusi dari semua script)
- Database SKP ada tapi di path yang salah (tidak bisa ditulis)
- Telegram notifikasi gagal karena format chat_id salah

SEMUA masalah ini harus diperbaiki sebelum produk apapun bisa dijual.
Ini adalah prerequisite untuk PRD-002, PRD-003, PRD-004, dan PRD-005.

---

## TUJUAN

Membuat semua komponen sistem berjalan dengan benar sehingga:
1. Senator Pentahelix menghasilkan knowledge entries ke SKP setiap 6 jam
2. hermes-upshalternal berjalan stabil tanpa restart loop
3. Semua cron jobs terjadwal dan berjalan sesuai jadwal
4. SKP database dapat dibaca dan ditulis dengan benar
5. Telegram notifikasi terkirim ke chat yang benar

---

## SUCCESS METRICS (Acceptance Criteria)

Hermes dinyatakan berhasil jika semua ini terpenuhi:

```
✅ sqlite3 /data/arsify.db "SELECT COUNT(*) FROM memory_notes" → angka > 0 dan bertambah
✅ systemctl is-active hermes-upshalternal → "active"
✅ journalctl -u hermes-upshalternal -n 20 | grep -c "restart" → < 3 dalam 1 jam
✅ crontab -l | grep senator-cycle → ada entry
✅ /root/upshalter-logs/senator.log → ada log dari hari ini
✅ Telegram menerima pesan test
✅ curl -sf http://localhost:11434/api/tags → OK (Ollama berjalan)
```

---

## TASK BREAKDOWN UNTUK HERMES

### Task 1.1: Investigasi dan Fix hermes-upshalternal (PRIORITAS P0)

```bash
# Step 1: Stop service yang looping
sudo systemctl stop hermes-upshalternal

# Step 2: Baca log crash terakhir
journalctl -u hermes-upshalternal --since "2026-05-03" -n 100 --no-pager \
  | grep -E "(Error|Failed|exit|Cannot|not found|Exception)" | head -20

# Step 3: Cek apakah config file ada
ls -la /root/.hermes/config.yaml
cat /root/.hermes/config.yaml | head -50

# Step 4: Cek apakah dependency service ada (ollama, redis)
systemctl is-active ollama redis

# Step 5: Tambah restart delay agar tidak loop terlalu cepat
# Edit /etc/systemd/system/hermes-upshalternal.service
# Tambahkan di [Service]:
#   RestartSec=30
#   StartLimitIntervalSec=300
#   StartLimitBurst=5

sudo systemctl daemon-reload
sudo systemctl start hermes-upshalternal
sleep 60  # tunggu 1 menit
systemctl status hermes-upshalternal
```

**Hermes WAJIB lapor:** root cause dari restart loop sebelum lanjut ke task berikutnya.
Format laporan: "[FIX 1.1] Root cause: {penyebab}. Status: {fixed/partial/blocked}"

---

### Task 1.2: Fix LLM Provider untuk Senator (PRIORITAS P0)

Masalah: Senator gagal karena OpenRouter kredit habis (HTTP 402).
Solusi prioritas: Aktifkan Ollama sebagai fallback TERLEBIH DAHULU.

```bash
# Cek Ollama
sudo systemctl start ollama
sleep 5
curl -sf http://localhost:11434/api/tags | python3 -c \
  "import sys,json; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]"

# Jika ada model (llama3.2:3b atau yang lain), update senator config
# Cari file konfigurasi senator
find /root /opt -name "senator*.py" -o -name "senator*.yaml" 2>/dev/null | head -10
find /root -path "*/senator*" -name "*.env" 2>/dev/null | head -5
```

Setelah menemukan config Senator, update agar:
- Jika HTTP 402 dari OpenRouter → fallback ke Ollama lokal
- Model Ollama: gunakan model yang tersedia (cek dari api/tags)
- Jika Ollama tidak ada model → pull model: `ollama pull llama3.2:3b`

```bash
# Pull model jika belum ada
ollama list | grep -q "llama3" || ollama pull llama3.2:3b
```

---

### Task 1.3: Fix SKP Database Path (PRIORITAS P1)

```bash
# Verifikasi lokasi database yang sebenarnya
find /root -name "*.db" -size +1k 2>/dev/null
ls -la /root/.hermes/*.db 2>/dev/null

# Buat symlink agar semua script bisa akses via path standar
mkdir -p /data
DB_ACTUAL="/root/.hermes/shared_knowledge_pool.db"
DB_EXPECTED="/data/arsify.db"

if [ -f "$DB_ACTUAL" ]; then
    ln -sfn "$DB_ACTUAL" "$DB_EXPECTED"
    echo "Symlink created: $DB_EXPECTED -> $DB_ACTUAL"
else
    echo "Database tidak ditemukan di $DB_ACTUAL"
    # Cek alternatif path
    find / -name "*.db" -path "*/hermes/*" 2>/dev/null | head -5
fi

# Pastikan tabel memory_notes ada
sqlite3 "$DB_EXPECTED" << 'SQL'
CREATE TABLE IF NOT EXISTS memory_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    scope TEXT DEFAULT 'global',
    source_agent_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_key ON memory_notes(key);
CREATE INDEX IF NOT EXISTS idx_scope ON memory_notes(scope);
SQL

# Test write
sqlite3 "$DB_EXPECTED" "INSERT OR IGNORE INTO memory_notes (key,value,scope) VALUES ('test/fix-001','PRD-001 fix applied','global')"
sqlite3 "$DB_EXPECTED" "SELECT COUNT(*) FROM memory_notes"
```

---

### Task 1.4: Setup Cron Jobs (PRIORITAS P1)

```bash
# Buat semua script yang dibutuhkan
mkdir -p /root/upshalter-scripts /root/upshalter-logs

# Cek script mana yang sudah ada
ls -la /root/upshalter-scripts/

# Daftarkan cron jobs
crontab - << 'CRON'
# Upshalter Automation — setup by PRD-001
*/5 * * * * /root/upshalter-scripts/health-check.sh >> /root/upshalter-logs/health.log 2>&1
*/5 * * * * /root/upshalter-scripts/generate-status-page.sh >> /root/upshalter-logs/status.log 2>&1
0 */2 * * * /root/upshalter-scripts/telegram-status.sh >> /root/upshalter-logs/telegram.log 2>&1
0 */6 * * * /root/upshalter-scripts/senator-cycle.sh >> /root/upshalter-logs/senator.log 2>&1
0 1,7,13,19 * * * /root/upshalter-scripts/kurator-review.sh >> /root/upshalter-logs/kurator.log 2>&1
0 0 * * * /root/upshalter-scripts/daily-summary.sh >> /root/upshalter-logs/daily.log 2>&1
0 1 * * * /root/upshalter-scripts/ssl-check.sh >> /root/upshalter-logs/ssl.log 2>&1
0 20 * * * /root/upshalter-scripts/backup-skp.sh >> /root/upshalter-logs/backup.log 2>&1
CRON

crontab -l  # verifikasi
```

---

### Task 1.5: Fix Telegram Chat ID (PRIORITAS P1)

```bash
# Masalah: @Nagara1945 bukan numeric ID
# Cara mendapatkan numeric ID:
TELEGRAM_BOT_TOKEN=$(grep -r "TELEGRAM_BOT_TOKEN\|BOT_TOKEN" /root/.hermes/ 2>/dev/null | head -1 | awk -F= '{print $2}' | tr -d ' ')

if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates" \
      | python3 -c "
import sys,json
d=json.load(sys.stdin)
for u in d.get('result',[]):
    msg=u.get('message',u.get('channel_post',{}))
    if msg:
        chat=msg.get('chat',{})
        print(f'Chat ID: {chat.get(\"id\")} | Type: {chat.get(\"type\")} | Title/Username: {chat.get(\"title\",chat.get(\"username\",chat.get(\"first_name\",\"-\")))}')
"
fi

# Setelah dapat numeric ID, update semua config yang pakai @Nagara1945
grep -rl "@Nagara1945" /root/.hermes/ /root/upshalter-scripts/ 2>/dev/null | head -10
```

**Hermes WAJIB:** Laporan numeric chat ID yang ditemukan ke manusia via pesan (tidak bisa otomatis karena perlu verifikasi user).

---

### Task 1.6: Verifikasi Akhir dan Laporan

```bash
echo "=== VERIFIKASI PRD-001 ===" > /root/upshalter-logs/prd-001-result.log
echo "Tanggal: $(date)" >> /root/upshalter-logs/prd-001-result.log

# Cek semua
check() {
    local name=$1 cmd=$2
    if eval "$cmd" >/dev/null 2>&1; then
        echo "✅ $name" >> /root/upshalter-logs/prd-001-result.log
    else
        echo "❌ $name" >> /root/upshalter-logs/prd-001-result.log
    fi
}

check "Ollama berjalan" "curl -sf http://localhost:11434/api/tags"
check "SKP database accessible" "sqlite3 /data/arsify.db 'SELECT COUNT(*) FROM memory_notes'"
check "Cron jobs registered" "crontab -l | grep senator-cycle"
check "hermes-upshalternal active" "systemctl is-active hermes-upshalternal"
check "Log directory exists" "test -d /root/upshalter-logs"

cat /root/upshalter-logs/prd-001-result.log

# Kirim ke Telegram (setelah chat_id diperbaiki)
# send_message: hasil verifikasi PRD-001
```

**Format laporan Telegram:**
```
[PRD-001 COMPLETE]
✅/❌ hermes-upshalternal: {status} ({N} restarts/jam)
✅/❌ LLM provider: {OpenRouter/Ollama}
✅/❌ SKP database: {N entries}
✅/❌ Cron jobs: {N registered}
✅/❌ Telegram: {working/needs manual chat_id}

Waktu pengerjaan: {durasi}
Next: PRD-002 Senator Pentahelix productization
```

---

## BATASAN DAN ATURAN

- JANGAN restart service tanpa investigate root cause terlebih dahulu
- JANGAN hapus database atau file konfigurasi
- JIKA ada yang tidak bisa diperbaiki otomatis → lapor ke manusia dengan detail lengkap
- SELALU backup config sebelum edit: `cp file file.backup.$(date +%Y%m%d)`
- JIKA task membutuhkan top-up OpenRouter → lapor ke manusia, jangan lanjut task lain yang bergantung padanya

---

## DEPENDENCIES

- PRD-002 tidak bisa dimulai sebelum Task 1.2 (LLM provider) dan Task 1.3 (SKP) selesai
- PRD-003 tidak bergantung pada PRD-001 (bisa paralel)
- PRD-004 tidak bergantung pada PRD-001 (bisa paralel untuk nginx config)
- PRD-005 bergantung pada PRD-001 task 1.2 dan 1.3

---

*PRD-001 · Foundation Fix · Upshalter · Mei 2026*
