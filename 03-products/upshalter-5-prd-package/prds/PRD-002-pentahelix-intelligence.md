# PRD-002: Pentahelix Intelligence Platform
## Status: Ready after PRD-001 · Target Launch: 5 hari dari sekarang
## Assignee: Hermes Agent (profil: builder + arsiparis)
## Dependencies: PRD-001 Task 1.2 dan 1.3 harus selesai

---

## KONTEKS UNTUK HERMES

Senator Pentahelix adalah 5 research agents yang memantau:
- senator-akademisi: tren riset, publikasi, inovasi akademis
- senator-bisnis: market movement, startup, UMKM, e-commerce
- senator-komunitas: sentiment komunitas tech, isu sosial
- senator-pemerintah: regulasi baru, kebijakan, tender pemerintah
- senator-media: narasi media, framing AI, sentiment publik

Data yang dihasilkan Senator memiliki nilai komersial tinggi untuk:
institusi yang butuh market intelligence, think tank, konsultan, legal firm, agensi PR.

TUGAS Hermes dalam PRD ini:
Membangun sistem delivery otomatis yang mengubah output Senator menjadi
produk intelligence report yang bisa dijual kepada subscriber.

---

## TUJUAN

1. Senator cycle berjalan reliabel setiap 6 jam dan menghasilkan SKP entries
2. Kurator mengkonsolidasi dan membuat laporan lintas domain
3. Laporan terformat otomatis (Markdown/PDF) dan terkirim ke subscriber
4. Dashboard sederhana di data.upshalter.com menampilkan insights terbaru
5. Sistem billing/subscriber management sederhana

---

## SUCCESS METRICS

```
✅ Senator menghasilkan minimal 10 entries per cycle (total 50/cycle dari 5 Senator)
✅ Kurator report dibuat dalam 90 menit setelah senator cycle selesai
✅ Laporan terkirim ke subscriber setiap pagi jam 07:00 WIB via Telegram
✅ data.upshalter.com menampilkan 10 insights terbaru dari SKP
✅ Minimal 3 pilot subscriber dalam 7 hari setelah launch
✅ Zero delivery failure dalam 7 hari pertama
```

---

## FITUR YANG HARUS DIBANGUN

### Fitur 2.1: Senator Cycle Script yang Robust

File: `/root/upshalter-scripts/senator-cycle.sh`

Senator cycle harus:
- Membuat Kanban task untuk setiap Senator
- Setiap Senator: browse news → LLM analisa → tulis ke SKP
- Jika satu Senator gagal → yang lain tetap jalan (tidak block)
- Catat hasil setiap Senator ke log terpisah
- Kirim notifikasi ke Telegram jika ada Senator yang gagal

```bash
#!/bin/bash
# senator-cycle.sh — dipanggil cron setiap 6 jam

TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
LOG="/root/upshalter-logs/senator-$(date +%Y%m%d).log"
echo "=== SENATOR CYCLE START: $TIMESTAMP ===" >> $LOG

SENATORS=(
    "senator-akademisi:Riset topik AI, pendidikan, dan inovasi teknologi di Indonesia terbaru"
    "senator-bisnis:Perkembangan bisnis, startup, UMKM, dan ekonomi digital Indonesia terkini"
    "senator-komunitas:Isu komunitas tech, developer Indonesia, sentiment terhadap AI"
    "senator-pemerintah:Regulasi AI, kebijakan digital, pengumuman pemerintah Indonesia terbaru"
    "senator-media:Narasi media tentang AI dan teknologi di Indonesia, framing dan sentiment"
)

for entry in "${SENATORS[@]}"; do
    name="${entry%%:*}"
    topic="${entry#*:}"
    
    echo "[$(date +%H:%M)] Starting $name..." >> $LOG
    
    # Buat Kanban task (jika Kanban tersedia)
    hermes kanban create "$name research — $TIMESTAMP" \
        --assignee "$name" \
        --board research \
        --body "Riset: $topic
        
Instruksi:
1. Gunakan web_search untuk cari berita dan perkembangan terbaru (5-10 sumber)
2. Analisa dan identifikasi 3-5 temuan penting
3. Simpan ke SKP: write_to_skp('${name#senator-}/temuan/$(date +%Y%m%d-%H)', summary)
4. Format: {temuan: [...], sumber: [...], relevansi_upshalter: ..., timestamp: ...}
5. Kirim ringkasan ke Telegram channel riset" 2>/dev/null &
    
    echo "[$(date +%H:%M)] Task created for $name" >> $LOG
done

echo "=== SENATOR CYCLE DISPATCHED: $TIMESTAMP ===" >> $LOG
echo "5 research tasks created. Results expected in 30-60 minutes."
```

---

### Fitur 2.2: Kurator Review Script yang Menghasilkan Laporan

File: `/root/upshalter-scripts/kurator-review.sh`

Kurator harus:
- Baca semua SKP entries dari cycle terakhir (2-6 jam lalu)
- Identifikasi tema lintas domain
- Buat laporan terkonsolidasi dalam format markdown
- Simpan laporan ke file dan ke SKP
- Trigger delivery ke subscriber

```bash
#!/bin/bash
# kurator-review.sh — berjalan 1 jam setelah senator cycle

DATE=$(date +%Y%m%d)
HOUR=$(date +%H)
REPORT_DIR="/root/upshalter-reports"
mkdir -p "$REPORT_DIR"

REPORT_FILE="$REPORT_DIR/pentahelix-brief-${DATE}-${HOUR}.md"

# Buat task Kurator di Hermes
hermes -p kurator-pentahelix << 'PROMPT'
Kamu adalah Kurator Pentahelix. Tugas hari ini:

1. Baca semua entries SKP yang dibuat Senator dalam 8 jam terakhir:
   - akademisi/temuan/*, bisnis/peluang/*, komunitas/isu/*, pemerintah/regulasi/*, media/narasi/*
   
2. Buat laporan konsolidasi dengan format berikut:

# PENTAHELIX INTELLIGENCE BRIEF
Tanggal: [hari ini]

## RINGKASAN EKSEKUTIF
[3 kalimat: apa yang paling penting terjadi hari ini dari 5 domain]

## TEMUAN PER DOMAIN
### Akademisi: [2-3 poin]
### Bisnis: [2-3 poin] 
### Komunitas: [2-3 poin]
### Pemerintah: [2-3 poin]
### Media: [2-3 poin]

## TEMA LINTAS DOMAIN
[2-3 tema yang muncul dari lebih dari 1 domain]

## IMPLIKASI UNTUK UPSHALTER
[1-2 poin yang relevan untuk strategi bisnis]

## ALERT
[Jika ada regulasi baru atau perubahan signifikan yang butuh perhatian segera]

3. Simpan laporan ke SKP: key = "laporan/daily/[tanggal]"
4. Simpan ke file: /root/upshalter-reports/pentahelix-brief-[tanggal]-[jam].md
5. Kirim ringkasan (max 300 kata) ke Telegram
PROMPT
```

---

### Fitur 2.3: Delivery ke Subscriber

File: `/root/upshalter-scripts/deliver-intelligence.sh`

Subscriber management sederhana:
- Daftar subscriber disimpan di `/root/upshalter-config/subscribers.json`
- Setiap subscriber punya: name, telegram_id, tier, topics

```json
{
  "subscribers": [
    {
      "id": "sub001",
      "name": "Nama Klien",
      "telegram_id": "NUMERIC_ID",
      "tier": "pro",
      "topics": ["bisnis", "pemerintah"],
      "active": true
    }
  ]
}
```

Script delivery:
```bash
#!/bin/bash
# deliver-intelligence.sh

LATEST_REPORT=$(ls -t /root/upshalter-reports/pentahelix-brief-*.md 2>/dev/null | head -1)
if [ -z "$LATEST_REPORT" ]; then
    echo "No report found to deliver"
    exit 1
fi

SUBSCRIBERS_FILE="/root/upshalter-config/subscribers.json"
if [ ! -f "$SUBSCRIBERS_FILE" ]; then
    echo "No subscribers configured"
    exit 0
fi

# Baca dan kirim ke setiap subscriber aktif
python3 << PYTHON
import json, subprocess

with open("$SUBSCRIBERS_FILE") as f:
    data = json.load(f)

with open("$LATEST_REPORT") as f:
    report = f.read()

for sub in data.get("subscribers", []):
    if not sub.get("active"):
        continue
    # Filter per topic jika tier starter
    # Kirim via Hermes send_message
    print(f"Delivering to {sub['name']} ({sub['telegram_id']})")
PYTHON
```

---

### Fitur 2.4: Landing Page Sederhana di data.upshalter.com

Hermes harus membuat halaman HTML yang menampilkan:
- 10 insights terbaru dari SKP
- Status Senator (aktif/terakhir update)
- Call-to-action: "Daftar untuk mendapat laporan lengkap"
- Form email sederhana

File: `/var/www/data.upshalter.com/index.html`

Isi halaman harus di-generate otomatis dari SKP setiap 30 menit:
```bash
# Tambahkan ke cron:
*/30 * * * * python3 /root/upshalter-scripts/generate-intelligence-page.py
```

---

### Fitur 2.5: Subscriber Registration

Buat endpoint sederhana atau form HTML yang:
- Menerima nama + email + telegram username calon subscriber
- Menyimpan ke `/root/upshalter-config/subscribers.json`
- Mengirim welcome message via Telegram
- Mulai deliver laporan ke subscriber baru

---

## PRICING TIER YANG HARUS DIIMPLEMENTASI

| Tier | Harga | Akses | Yang Dikirim |
|------|-------|-------|-------------|
| Starter | Rp 2jt/bln | 2 domain | Laporan mingguan, Telegram |
| Pro | Rp 5jt/bln | 5 domain | Laporan harian, Telegram + email |
| Enterprise | Rp 15jt/bln | Custom | API access + custom domain |

---

## DELIVERABLES YANG HARUS DISERAHKAN HERMES

1. `/root/upshalter-scripts/senator-cycle.sh` — script final dan berjalan
2. `/root/upshalter-scripts/kurator-review.sh` — script final dan berjalan
3. `/root/upshalter-scripts/deliver-intelligence.sh` — script delivery
4. `/var/www/data.upshalter.com/index.html` — landing page
5. `/root/upshalter-config/subscribers.json` — template dengan 1 test subscriber
6. Sample laporan: `/root/upshalter-reports/sample-brief-DEMO.md`
7. Laporan ke Telegram: "PRD-002 COMPLETE — Intelligence Platform siap"

---

## ATURAN DAN BATASAN

- Laporan harus dalam Bahasa Indonesia
- Jangan sebut nama klien atau informasi sensitif dalam laporan publik
- Pastikan delivery ke subscriber hanya jika ada laporan baru (tidak kirim duplikat)
- Log semua delivery di `/root/upshalter-logs/delivery.log`
- Jika Senator gagal menghasilkan data → laporan tetap dibuat dengan note "data tidak tersedia untuk domain ini"

---

*PRD-002 · Pentahelix Intelligence Platform · Upshalter · Mei 2026*
