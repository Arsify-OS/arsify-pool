# 🔄 URUTAN PENGERJAAN SEJALAN (ALUR KERJA UPSHALTER)
## Prinsip: Output Tahap Sebelumnya = Input Tahap Berikutnya
## Berdasarkan PRD-001 s/d 005 + Materi Belajar Knowledge

---

## 📍 FASE 0: PERSIAPAN TEKNIS (H-0 Sampai H-1)
**Tujuan: Pastikan semua "tools" dan "standards" siap pakai**

| Step | Kegiatan | Teknis Materi Belajar | Output |
|------|-----------|-----------------------|--------|
| 0.1 | Setup SKP DB Sesuai ISO 30401 | ISO 30401 Clause 7-8 | `memory_notes` table + `seci_phase` column |
| 0.2 | Buat Prompt Library (Senator & Kurator) | Prompt Engineering (Few-Shot, Chain-of-Thought) | `/root/.hermes/prompts/*.json` |
| 0.3 | Definisikan CRISP-DM Checklist | CRISP-DM Fase 1-5 | Checklist di `senator-crispdm-cycle.sh` |
| 0.4 | Siapkan OpenSwarm Sebagai Dashboard | OpenSwarm Spatial Dashboard | `http://localhost:3000` (monitoring) |

```bash
# Cek apakah semua tools ada:
command -v ollama && echo "✅ Ollama" || echo "❌ Ollama"
test -f /root/.hermes/knowledge/romi-wahono-theses.json && echo "✅ Dataset" || echo "❌ Dataset"
curl -sf http://localhost:11434/api/tags && echo "✅ Ollama API" || echo "❌ Ollama API"
```

---

## 🚀 FASE 1: CORE FIX (PRD-001) — H-1 s/d H-3
**Alur: Senator → SKP Entry (Externalization)**

| Step | Kegiatan | Input | Output | Teknis |
|------|-----------|-------|--------|--------|
| 1.1 | Fix Senator Rate Limit | OpenRouter 402/429 | Ollama Fallback Aktif | Emergency-fix.sh Fix #2 |
| 1.2 | Terapkan Prompt Engineering | Prompt Library (0.2) | Senator Output JSON Valid | Role + Constrained Output |
| 1.3 | Jalankan Senator Cycle (CRISP-DM) | URLs (Arxiv, News) | Raw Insights (Tacit) | CRISP-DM Fase 1-3 |
| 1.4 | Simpan ke SKP (Externalization) | Raw Insights | `akademisi/temuan/*` | SECI: Externalization |
| 1.5 | Verifikasi SKP Write | `sqlite3 /data/arsify.db` | COUNT(*) > 10 | ISO 30401 Clause 8 |

**Success Criteria Fase 1:**
```
✅ sqlite3 /data/arsify.db "SELECT COUNT(*) FROM memory_notes" → > 10
✅ Senator logs: "Task selesai" (bukan error 402/429)
✅ SKP entries punya field: source, insight, confidence, tags
```

---

## 🎨 FASE 2: DEMO-READY (PRD-004) — H-2 s/d H-4 (Paralel dg Fase 1)
**Alur: API → UI Chat → Subscriber (Boundary Layer)**

| Step | Kegiatan | Input | Output | Teknis |
|------|-----------|-------|--------|--------|
| 2.1 | Fix chat.upshalter.com | Hermes API (:8000) | Chat UI Bisa Dipakai | BCE: Boundary |
| 2.2 | Fix workspace.upshalter.com | Env Vars (ENHANCED_CHAT) | Fitur Chat Aktif | UML Deployment Diagram |
| 2.3 | Fix status.upshalter.com | Real-time Polling Script | Status Dots Hijau | Nginx + no-cache |
| 2.4 | Test Demo Flow Lengkap | Browser/Screenshot | 15 Menit Demo Lancar | UML Use Case |

**Success Criteria Fase 2:**
```
✅ Buka chat.upshalter.com → Ketik "Halo" → Dapat Respons AI
✅ Buka workspace.upshalter.com → Login → Chat Feature Visible
✅ Buka status.upshalter.com → Auto-refresh tiap 30s
```

---

## 🧠 FASE 3: PENTAHELIX INTEL (PRD-002) — H-5 s/d H-15
**Alur: 5 Senator → Kurator → Subscriber (SECI Full Spiral)**

| Step | Kegiatan | Input | Output | Teknis |
|------|-----------|-------|--------|--------|
| 3.1 | Daftarkan 5 Senator di OpenSwarm | Prompt Library (0.2) | 5 Agent Active | OpenSwarm Agent Templates |
| 3.2 | Jalankan 5 Senator Cycle (6 jam sekali) | CRISP-DM Checklist | 50 SKP Entries/Day | CRISP-DM + SECI Socialization |
| 3.3 | Kurator Review (90m setelah cycle) | 50 SKP Entries | Laporan Terstruktur | SECI: Combination + ISO 30401 |
| 3.4 | Kurator Deliver ke Subscriber | Laporan + Telegram Bot | Notifikasi Tiap Pagi | Human-in-the-Loop (OpenSwarm) |
| 3.5 | Deploy data.upshalter.com | SKP Insights (10 terbaru) | Landing Page Intel | UML Sequence Diagram |

**Success Criteria Fase 3:**
```
✅ 5 Senator menghasilkan 50 entries/cycle
✅ Kurator report otomatis setelah cycle selesai
✅ Laporan terkirim ke subscriber jam 07:00 WIB
✅ data.upshalter.com menampilkan 10 insights terbaru
```

---

## 💼 FASE 4: IMPLEMENTATION SERVICE (PRD-003) — H-10 s/d H-20 (Paralel dg Fase 3)
**Alur: Proposal → Onboarding → Client Active (Business Flow)**

| Step | Kegiatan | Input | Output | Teknis |
|------|-----------|-------|--------|--------|
| 4.1 | Buat Proposal Template | PRD-003 Deliverable 3.1 | `/root/upshalter-materials/proposal-template.md` | Business Docs |
| 4.2 | Buat Onboarding Script | SSH + Hermes Install | `onboard-client.sh` | ISO 30401 Clause 6 (Planning) |
| 4.3 | Deploy Sales Page (upshalter.com/services) | 3 Paket Harga | Leads Form Aktif | BCE: Boundary Layer |
| 4.4 | Test Onboarding 3 Hari | VPS Klien Dummy | Client Workspace Active | UML Use Case |
| 4.5 | Launch & Dapat Klien | Sales Page | Revenue Masuk | Business Milestone |

**Success Criteria Fase 4:**
```
✅ Checklist onboarding selesai dalam 3 hari
✅ Klien bisa akses workspace & Telegram bot aktif
✅ Zero critical issues dalam 7 hari pertama
```

---

## 🧬 FASE 5: BRAND BRAIN FOUNDATION (PRD-005) — H-20 s/d H-40
**Alur: Brand Data → AI Content → Waiting List (Intelligent Systems)**

| Step | Kegiatan | Input | Output | Teknis |
|------|-----------|-------|--------|--------|
| 5.1 | Design Brand Brain Schema | ISO 30401 + Romi Dataset | `brand/{slug}/brain` SKP Key | ISO 30401 Asset Management |
| 5.2 | Inject Brand Brain ke Prompt | PRD-005 Task 5.1 | AI Tahu Tone Brand | Prompt Engineering (Context Stuffing) |
| 5.3 | Demo Content Generation | Brand Brain Upshalter | 3 Caption Instagram | CRISP-DM Modeling |
| 5.4 | Deploy Landing Page (arsify.upshalter.com/vox) | Headline + Form | Waiting List Aktif | UML Deployment Diagram |
| 5.5 | Target 50 Sign-up | Marketing Campaign | 50 Leads Terkumpul | Business Objective |

**Success Criteria Fase 5:**
```
✅ Brand Brain tersimpan di SKP dengan format ISO 30401
✅ AI generate konten sesuai brand voice ("We Own Knowledge...")
✅ 50 sign-up waiting list dalam 30 hari
✅ 1 pilot client aktif menggunakan Brand Brain
```

---

## 📊 VISUALISASI ALUR KERJA (SEJAJAR)

```
[FASE 0: PREP] ─── [FASE 1: CORE FIX] ─── [FASE 3: INTEL PLATFORM]
       │                     │                           │
       │ (Prompt Lib)       │ (Senator→SKP)           │ (5 Senator→Kurator)
       │ (CRISP-DM)        │ (10+ entries)           │ (50 entries/cycle)
       │ (OpenSwarm)       │                         │ (Delivery to Sub)
       ▼                     ▼                           ▼
[FASE 2: DEMO]         [FASE 4: SERVICE]         [FASE 5: BRAND BRAIN]
       │                     │                           │
       │ (chat/workspace)   │ (Onboarding Kit)        │ (Brand Brain Schema)
       │ (status page)      │ (Sales Page)            │ (Waiting List)
       │                     │ (Revenue)                │ (Pilot Client)
```

---

## ⚡ PRIORITAS EKSEKUSI (URUTAN YANG HARUS DIKERJAKAN SEKARANG)

### Hari 1 (H-7 Mei): FASE 1.1 s/d 1.3
```bash
# 1. Fix Senator Rate Limit (Emergency-fix.sh Fix #2)
systemctl start ollama
# Inject Ollama fallback ke senator_cognitive_client.py

# 2. Terapkan Prompt Engineering ke Senator Akademisi
# File: /root/.hermes/prompts/senator-akademisi.json
# Isi: Role prompt + Few-shot examples + Constrained JSON output

# 3. Jalankan Senator Cycle manual (test)
docker start senator-akademisi
sleep 120
sqlite3 /data/arsify.db "SELECT * FROM memory_notes ORDER BY id DESC LIMIT 5"
```

### Hari 2 (H-8 Mei): FASE 1.4 s/d 2.2
```bash
# 4. Verifikasi SKP Entries (SECI Externalization)
# 5. Fix chat.upshalter.com (BCE Boundary)
# 6. Fix workspace.upshalter.com (Enable ENHANCED_CHAT)
```

### Hari 3 (H-9 Mei): FASE 3.1 s/d 3.2
```bash
# 7. Setup OpenSwarm Dashboard
cd /root/openswarm && bash backend/run.sh &
# 8. Daftarkan 5 Senator sebagai Agent Templates
# 9. Start 5 Senator Containers (Ollama fallback aktif)
```

---

## 🎯 DEPENDENSI ANTAR FASE (JANGAN LONCAT)

| Jika Ini Belum Selesai | Jangan Kerjakan Ini |
|------------------------|---------------------|
| Fase 1 (Senator → SKP) | Fase 3 (Kurator Review) |
| Fase 1 (SKP Entries) | Fase 5 (Brand Brain injection) |
| Fase 2 (Demo Ready) | Fase 4 (Sales Page launch) |
| Fase 3 (Delivery System) | Fase 5 (Pilot Client) |

---

## 📝 CHECKLIST HARIAN (TEMPLATE)

```markdown
## Hari [Tanggal] — Fase [X.Y]

### Yang Dikerjakan:
- [ ] Step X.Y.Z: [Nama Kegiatan]
- [ ] Step X.Y.Z: [Nama Kegiatan]

### Output:
- [ ] File: [Path]
- [ ] Metric: [Angka/Kondisi]

### Blokir:
- [ ] [Masalah yang ditemukan]

### Next Step (Tomorrow):
- [ ] Step X.Y.Z: [Nama Kegiatan]
```

---

*Dokumen: /root/upshalter-5-prd-package/WORKFLOW-SEQUENCE.md*
*Alur ini memastikan setiap teknologi (CRISP-DM, SECI, Prompt Eng, ISO 30401) dipakai di tahap yang tepat.*
