# 🌊 STRATEGI GELOMBANG PERBAIKAN UPSHALTER
## Berdasarkan PRD-001 s/d PRD-005 + OpenSwarm + NotebookLM
## Dibuat: 7 Mei 2026 | Eksekusi: Mei-Juli 2026

---

## 📊 STATUS SAAT INI (Baseline)

| PRD | Progress | Status | Blokir |
|-----|----------|--------|--------|
| PRD-001 Foundation Fix | 80% | 🟡 In Progress | Senator belum hasilkan SKP entries |
| PRD-002 Pentahelix Intel | 20% | 🔴 Not Started | Tunggu PRD-001 selesai |
| PRD-003 Implementation Svc | 0% | 🔴 Not Started | Bisa paralel dengan PRD-001 |
| PRD-004 Managed Workspace | 0% | 🔴 Not Started | Tunggu PRD-001 (Ollama) |
| PRD-005 Arsify Vox MVP | 0% | 🔴 Not Started | Tunggu PRD-001 + PRD-002 stabil |

**Arsitektur Saat Ini:**
- Hermes Cognitive Engine (port 8100) ✅
- 3 Senator containers (bisnis, akademisi, media) ⚠️ Rate limit
- Celery Worker (concurrency=2, free models) ⚠️ Sering 429
- SKP DB: `/root/.hermes/shared_knowledge_pool.db` ✅
- Telegram: `5807834405` ✅

---

## 🌊 GELOMBANG 1: SELESAIKAN PRD-001 (H-7 Mei)
**Target: Senator menghasilkan SKP entries > 0**

### Task 1.1: Fix Senator Rate Limit (P0 - 4 jam)
```bash
# 1. Tambah Ollama sebagai fallback cadangan (sesuai PRD-001 Task 1.2)
systemctl start ollama
ollama list | grep -q "llama3" || ollama pull llama3.2:3b

# 2. Update senator_cognitive_client.py untuk fallback Ollama jika OpenRouter 402/429
# File: /root/.hermes/senator_cognitive_client.py
# Logic: Jika free models gagal → coba Ollama lokal

# 3. Testing
docker restart senator-bisnis senator-akademisi senator-media
sleep 120
sqlite3 /data/arsify.db "SELECT COUNT(*) FROM memory_notes"
```

### Task 1.2: Verifikasi SKP Write (P0 - 1 jam)
```bash
# Pastikan Senator bisa tulis ke SKP
sqlite3 /data/arsify.db "INSERT OR IGNORE INTO memory_notes (key,value,scope) 
VALUES ('test/senator-fix','Test dari PRD-001 Task 1.3','global')"
sqlite3 /data/arsify.db "SELECT * FROM memory_notes WHERE key LIKE 'test/%'"
```

### Task 1.3: Update Telegram Chat ID (P1 - 30 menit)
```bash
# Sudah numeric: 5807834405 (di memory)
# Test kirimNotifikasi
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
  -d "chat_id=5807834405&text=[PRD-001] Senator test notification"
```

### Task 1.4: Delivery Report PRD-001 (P1 - 30 menit)
```bash
# File: /root/upshalter-logs/prd-001-result.log
# Status: ⚠️ Partial (Senator belum hasilkan entries)
# Laporan ke Telegram
```

**✅ SUCCESS CRITERIA GELOMBANG 1:**
```
✅ sqlite3 /data/arsify.db "SELECT COUNT(*) FROM memory_notes" → angka > 10
✅ Senator logs menunjukkan "SUCCESS" atau "Task selesai"
✅ Telegram menerima notifikasi test
✅ Ollama berjalan sebagai cadangan (curl -sf http://localhost:11434/api/tags)
```

---

## 🌊 GELOMBANG 2: FIX DEMO-READY (H-8 s/d H-10 Mei)
**Target: chat.upshalter.com, workspace.upshalter.com, status.upshalter.com bisa didemo**

### Task 2.1: Deploy Chat UI (PRD-004 Task 4.1 - 2 jam)
```bash
# 1. Pastikan Arsify OS / Hermes API berjalan di port 8000
curl -sf http://localhost:8000/health || systemctl start arsify-os

# 2. Deploy chat-ui.html ke chat.upshalter.com
mkdir -p /var/www/chat.upshalter.com
# Copy dari /root/upshalter-fixes/chat-ui.html (jika ada) atau generate baru

# 3. Update nginx config untuk proxy ke API
# Sesuai PRD-004 Task 4.1
nginx -t && systemctl reload nginx

# 4. Test: Buka chat.upshalter.com → ketik "halo" → dapat respons
```

### Task 2.2: Fix Workspace Missing Features (PRD-004 Task 4.2 - 2 jam)
```bash
# 1. Cek container hermes-workspace
docker ps | grep workspace

# 2. Tambah env vars (ENHANCED_CHAT, MCP, dll.)
# Sesuai PRD-004 Task 4.2

# 3. Restart & verifikasi fitur chat muncul di UI
```

### Task 2.3: Deploy Real-time Status Page (PRD-004 Task 4.3 - 1 jam)
```bash
# 1. Copy status-realtime.html
cp /root/upshalter-fixes/status-realtime.html /var/www/status/index.html

# 2. Update nginx no-cache
# 3. Test: Buka status.upshalter.com → dots berwarna hijau (update tiap 30s)
```

**✅ SUCCESS CRITERIA GELOMBANG 2:**
```
✅ chat.upshalter.com → kotak chat → ketik "halo" → respons AI
✅ workspace.upshalter.com → login → chat feature aktif
✅ status.upshalter.com → status dots real-time (bukan statis)
✅ Demo 15 menit kepada calon klien bisa dilakukan tanpa error
```

---

## 🌊 GELOMBANG 3: BUILD PENTAHELIX INTEL (H-11 s/d H-20 Mei)
**Target: Senator hasilkan 50 entries/cycle, Kurator buat laporan, Delivery ke subscriber**

### Task 3.1: Integrate OpenSwarm Sebagai Orchestrator (3 hari)
**Berdasarkan pembelajaran dari `/root/openswarm`:**

```bash
# 1. Setup OpenSwarm backend (port 8324)
cd /root/openswarm
bash backend/run.sh &
# Atau integrate dengan Hermes Cognitive Engine

# 2. Daftarkan 5 Senator sebagai Agent Templates:
# - senator-akademisi (prompt: riset AI/teknologi Indonesia)
# - senator-bisnis (prompt: startup/UMKM/ekonomi digital)
# - senator-komunitas (prompt: dev community sentiment)
# - senator-pemerintah (prompt: regulasi/kebijakan)
# - senator-media (prompt: narasi media/framing)

# 3. Manfaatkan Spatial Dashboard untuk monitoring
# Akses di http://localhost:3000 (atau deploy ke data.upshalter.com)

# 4. Setup Persistent History (agen tidak kehilangan progress saat restart)
```

### Task 3.2: Build Kurator Pentahelix (PRD-002 Fitur 2.2 - 2 hari)
```bash
# 1. Buat script /root/upshalter-scripts/kurator-review.sh
# Kurator sebagai Custom Agent Mode di OpenSwarm:
# - Baca SKP entries 8 jam terakhir (akademisi/temuan/*, bisnis/*, etc.)
# - Generate laporan terkonsolidasi (Ringkasan Eksekutif, Temuan per Domain, 
#   Tema Lintas Domain, Implikasi untuk Upshalter, Alert)
# - Format: NotebookLM-style structured output (ringkasan + Q&A + insights)

# 2. Simpan laporan ke:
# - SKP: key "laporan/daily/[tanggal]"
# - File: /root/upshalter-reports/pentahelix-brief-[date].md

# 3. Trigger: 90 menit setelah Senator cycle selesai
```

### Task 3.3: Build Delivery System (PRD-002 Fitur 2.3 - 2 hari)
```bash
# 1. Buat subscriber management: /root/upshalter-config/subscribers.json
# Format sesuai PRD-002 (id, name, telegram_id, tier, topics, active)

# 2. Script delivery: /root/upshalter-scripts/deliver-intelligence.sh
# - Baca latest report
# - Filter per topic jika tier Starter
# - Kirim ke Telegram setiap pagi 07:00 WIB
# - Human-in-the-Loop: Kurator approve sebelum kirim (OpenSwarm feature)

# 3. Daftarkan cron:
# 0 7 * * * /root/upshalter-scripts/deliver-intelligence.sh
```

### Task 3.4: Deploy Landing Page (PRD-002 Fitur 2.4 - 1 hari)
```bash
# 1. Generate HTML untuk data.upshalter.com
# Adaptasi Spatial Dashboard OpenSwarm:
# - 10 insights terbaru dari SKP
# - Status Senator (aktif/terakhir update)
# - CTA: "Daftar untuk laporan lengkap"
# - Form pendaftaran subscriber

# 2. Auto-generate tiap 30 menit:
# */30 * * * * python3 /root/upshalter-scripts/generate-intelligence-page.py
```

### Task 3.5: Subscriber Registration (PRD-002 Fitur 2.5 - 1 hari)
```bash
# 1. Endpoint/form HTML: nama + email + telegram + topics
# 2. Simpan ke subscribers.json
# 3. Kirim welcome message Telegram
# 4. Mulai deliver laporan
```

**✅ SUCCESS CRITERIA GELOMBANG 3:**
```
✅ Senator 10 entries/cycle (total 50 dari 5 Senator)
✅ Kurator report dibuat < 90 menit setelah cycle
✅ Laporan terkirim ke subscriber setiap 07:00 WIB via Telegram
✅ data.upshalter.com menampilkan 10 insights terbaru
✅ Minimal 3 pilot subscriber dalam 7 hari
✅ Zero delivery failure dalam 7 hari pertama
```

---

## 🌊 GELOMBANG 4: LAUNCH IMPLEMENTATION SERVICE (H-15 s/d H-25 Mei)
**Target: Onboarding kit siap, bisa dapat klien baru dalam 3 hari**

### Task 4.1: Buat Proposal Template (PRD-003 Deliverable 3.1 - 4 jam)
```bash
# File: /root/upshalter-materials/proposal-template.md
# 3 Paket: Starter (15jt), Standard (35jt), Enterprise (75jt)
# Timeline: 3 hari (Day1: Infra, Day2: Agents, Day3: Training)
```

### Task 4.2: Onboarding Checklist Script (PRD-003 Deliverable 3.2 - 1 hari)
```bash
# File: /root/upshalter-scripts/onboard-client.sh
# Input: CLIENT_NAME, CLIENT_VPS_IP, CLIENT_TELEGRAM_ID
# Output: Log onboarding lengkap
# Hari 1: SSH + Install Hermes + Ollama
# Hari 2: Setup agents + SKP + Telegram bot
# Hari 3: Training + Handover
```

### Task 4.3: Client Documentation (PRD-003 Deliverable 3.3 - 4 jam)
```bash
# File: /root/upshalter-materials/client-docs-template.md
# Cara akses workspace, berkomunikasi dengan AI, troubleshooting, kontak support
```

### Task 4.4: Sales Page (PRD-003 Deliverable 3.4 - 1 hari)
```bash
# Deploy ke upshalter.com/services
# Penjelasan 3 paket, testimonial placeholder, tombol "Minta Demo"
# Form → simpan ke /root/upshalter-config/leads.json + notifikasi Telegram
```

**✅ SUCCESS CRITERIA GELOMBANG 4:**
```
✅ Checklist onboarding selesai dalam 3 hari
✅ Klien bisa akses workspace mereka
✅ Telegram bot klien aktif dan kirim daily brief
✅ Dokumentasi dalam Bahasa Indonesia
✅ Zero critical issues dalam 7 hari pertama
```

---

## 🌊 GELOMBANG 5: ARSIFY VOX FOUNDATION (H-20 s/d H-40 Mei)
**Target: Brand Brain schema, demo klien, waiting list 50 sign-up**

### Task 5.1: Design Brand Brain Schema (PRD-005 Task 5.1 - 2 hari)
```python
# SKP key format: brand/{slug}/brain
# Contoh: brand/upshalter/brain
# Field: brand_name, tagline, voice_tone, avoid_words, target_audience, 
#        core_values, product_lines, past_campaigns, competitors, brand_colors
```

### Task 5.2: Demo Content Generation (PRD-005 Task 5.2 - 1 hari)
```bash
# 1. Simpan Brand Brain Upshalter ke SKP
# 2. Test: "Buat 3 caption Instagram untuk Senator Pentahelix" → AI tahu tone Upshalter
```

### Task 5.3: Landing Page Waiting List (PRD-005 Task 5.3 - 1 hari)
```bash
# Deploy ke arsify.upshalter.com/vox
# Headline: "AI yang mengenal merekmu lebih baik dari karyawan baru"
# Form: nama + email + nama merek + budget
# → simpan ke /root/upshalter-config/vox-waitlist.json
```

### Task 5.4: Monitor Waiting List (PRD-005 Task 5.4 - ongoing)
```bash
# Cron harian: check-waitlist.sh
# Target: 50 sign-up dalam 30 hari
```

**✅ SUCCESS CRITERIA GELOMBANG 5:**
```
✅ Brand Brain schema tersimpan di SKP
✅ Demo: AI tahu tone brand klien
✅ arsify.upshalter.com/vox → landing page aktif
✅ 50 sign-up waiting list dalam 30 hari
✅ 1 pilot client aktif menggunakan Brand Brain
```

---

## 🔗 INTEGRASI OPENSWARM & NOTEBOOKLM

| Fitur | OpenSwarm | NotebookLM | Implementasi |
|--------|-----------|------------|--------------|
| Multi-agent monitoring | ✅ Spatial Dashboard | ❌ | data.upshalter.com dashboard |
| Persistent history | ✅ Survives restart | ❌ | Fix Senator task loss |
| Human-in-the-loop | ✅ Approval workflow | ❌ | Kurator approve laporan |
| Structured output | ✅ Views & Outputs | ✅ Notebook-style | Kurator reports |
| Cost tracking | ✅ Per-session USD | ❌ | Monitor OpenRouter usage |
| Agent isolation | ✅ Git worktree | ❌ | Senator tidak saling block |

---

## 📅 TIMELINE EKSEKUSI

```
Minggu 1 (7-13 Mei): Gelombang 1 + 2
  ├─ Selesaikan PRD-001 (Senator → SKP entries)
  └─ Fix PRD-004 (Demo-ready: chat, workspace, status)

Minggu 2-3 (14-27 Mei): Gelombang 3 + 4
  ├─ Build PRD-002 (Pentahelix Intelligence Platform)
  └─ Launch PRD-003 (Implementation Service → revenue)

Minggu 4-6 (28 Mei-17 Juni): Gelombang 5
  └─ PRD-005 Foundation (Arsify Vox → waiting list)
```

---

## 🎯 PRIORITAS UTAMA (Next 48 Hours)

1. **P0**: Pastikan Senator menghasilkan SKP entries (PRD-001 Task 1.1-1.3)
2. **P0**: Fix chat.upshalter.com untuk demo (PRD-004 Task 4.1)
3. **P1**: Integrate OpenSwarm untuk monitoring Senator (Gelombang 3 prep)
4. **P1**: Setup Kurator Pentahelix (PRD-002 Fitur 2.2)

---

## 📊 MONITORING & METRICS

Setiap gelombang wajib lapor ke Telegram `5807834405`:
```
[WAVE N COMPLETE]
✅/❌ PRD-XXX: {status}
✅/❌ Success criteria: {X/Y}
⏳ Next: {Next task}
📈 Metrics: {Key numbers}
```

---

*Dokumen Strategi: /root/upshalter-5-prd-package/STRATEGY-WAVES.md*
*Update: Setiap selesai 1 task besar*
