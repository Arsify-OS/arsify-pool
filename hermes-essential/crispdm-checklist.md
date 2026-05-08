# CRISP-DM Checklist untuk Senator Pipeline
## Versi: 1.0.0 — Mapping ke SECI Spiral & ISO 30401

---

## 📋 CHECKLIST PER CYCLE SENATOR (6 Jam Sekali)

### FASE 1: BUSINESS UNDERSTANDING (15 Menit)
**Tujuan: Pahami tujuan pengetahuan yang akan diekstrak**

- [ ] Baca instruksi dari `prompt_library/{role}.json`
- [ ] Identifikasi kategori pengetahuan (AI/ML, Public Policy, Business, dll)
- [ ] Tentukan scope: Akademik / Pemerintah / Bisnis / Komunitas / Media
- [ ] Set `seci_phase` target: `externalization` (default)

**Output:** Task context siap untuk Fase 2

---

### FASE 2: DATA UNDERSTANDING (60 Menit)
**Tujuan: Kumpulkan sumber pengetahuan (SECI: Socialization)**

- [ ] **Senator Akademisi:** Crawl Arxiv API (latest papers in AI/ML)
- [ ] **Senator Pemerintah:** Crawl government portal / regulasi terbaru
- [ ] **Senator Bisnis:** Crawl market reports / business news
- [ ] **Senator Komunitas:** Crawl Reddit/Forum diskusi terkait
- [ ] **Senator Media:** Crawl berita media (CNN, Reuters, dsb)

**Validasi Data:**
- [ ] URL/Source dapat diakses (HTTP 200)
- [ ] Konten relevan dengan role senator
- [ ] Minimal 5 sumber per cycle

**Output:** Raw data (tacit knowledge) siap diproses

---

### FASE 3: DATA PREPARATION (45 Menit)
**Tujuan: Bersihkan & strukturkan data (SECI: Externalization)**

- [ ] Extract teks dari sumber (PDF/HTML/API response)
- [ ] Bersihkan noise (ads, navigation, boilerplate)
- [ ] Chunk teks ke bagian yang relevan (abstract, conclusion, key points)
- [ ] Load prompt dari `/root/.hermes/prompts/{role}.json`
- [ ] Siapkan few-shot examples sebagai context

**Output:** Clean text + prompt template siap untuk inference

---

### FASE 4: MODELING (60 Menit)
**Tujuan: Generate insight dengan LLM (SECI: Externalization)**

- [ ] Pilih model: `llama3.2:3b-instruct-q4_K_M` (primary) atau `phi3:mini-instruct-q4_K_M` (fallback)
- [ ] Kirim prompt + clean text ke Ollama (bukan OpenRouter untuk hindari 402/429)
- [ ] Parse output JSON (HANYA JSON, tanpa markdown)
- [ ] Validasi struktur JSON sesuai `output_schema`:
  - [ ] `source` ada
  - [ ] `insight` ada (1-2 kalimat)
  - [ ] `confidence` antara 0.0-1.0
  - [ ] `category` sesuai role
  - [ ] `tags` minimal 3, maksimal 8
  - [ ] `seci_phase` = "externalization"
  - [ ] `actionable` = boolean
  - [ ] `summary` maksimal 100 karakter

**Output:** Validated JSON insights (explicit knowledge)

---

### FASE 5: EVALUATION (30 Menit)
**Tujuan: Quality check sebelum simpan ke SKP**

- [ ] Cek confidence score: Jika < 0.6, tandai untuk review manual
- [ ] Cek duplicate: Apakah insight sudah ada di SKP? (cek `key` field)
- [ ] Cek actionable: Apakah insight bisa ditindaklanjuti?
- [ ] Sample check: Baca 3 insight secara manual, apakah masuk akal?

**Jika ada error:**
- [ ] Retry dengan model fallback
- [ ] Jika masih gagal, simpan ke `failed_queue` untuk Kurator review

**Output:** High-quality insights siap disimpan

---

### FASE 6: DEPLOYMENT (30 Menit)
**Tujuan: Simpan ke SKP DB (SECI: Externalization → Combination)**

- [ ] Generate `key` unik: `{role}/{category}/{slug}` (contoh: `akademisi/ai-ml/transformer-attention`)
- [ ] Simpan ke SKP DB (`memory_notes` table):
  - [ ] `key` = unique key
  - [ ] `value` = JSON insight lengkap
  - [ ] `scope` = `{role}`
  - [ ] `source_agent_name` = `senator-{role}`
  - [ ] `seci_phase` = `externalization`
- [ ] Verifikasi: `SELECT * FROM memory_notes WHERE key = '{key}'`
- [ ] Update `updated_at` timestamp

**Output:** Insight tersimpan di SKP (Explicit Knowledge Pool)

---

## 🔄 POST-CYCLE: KURATOR REVIEW (90 Menit Setelah Cycle Selesai)

### KURATOR TASKS (SECI: Combination → Internalization)
- [ ] **Retrieve:** `SELECT * FROM memory_notes WHERE seci_phase = 'externalization' AND updated_at > (NOW() - 90 minutes)`
- [ ] **Combine:** Gabungkan insights dari 5 Senator → Laporan Terstruktur
- [ ] **Validate:** Cek konsistensi, hapus duplikat, tambah cross-references
- [ ] **Store:** Simpan laporan ke `memory_notes` dengan `seci_phase` = `combination`
- [ ] **Deliver:** Kirim ke Subscriber via Telegram Bot (`/root/hermes-workspace-personal/telegram-deliver.sh`)

---

## 📊 METRICS PER CYCLE

| Metric | Target | Actual |
|--------|--------|--------|
| Sumber dikumpulkan | 5+ | ___ |
| Insights generated | 3-5 | ___ |
| Confidence avg | > 0.75 | ___ |
| Valid JSON % | 100% | ___ |
| SKP entries created | 3-5 | ___ |
| Failed (need review) | < 10% | ___ |

---

## 🚨 ERROR HANDLING

| Error | Action |
|-------|--------|
| OpenRouter 402/429 | Switch ke Ollama (`ollama run llama3.2:3b`) |
| JSON parse error | Retry dengan `phi3:mini` |
| Confidence < 0.5 | Masukkan ke `failed_queue` |
| Duplicate key | Append `-v2`, `-v3` ke key |
| DB write error | Restart Redis + Celery worker |

---

## 📚 REFERENSI (Materi Belajar Knowledge)

- **CRISP-DM:** Fase 1-6 (Business Understanding s/d Deployment)
- **SECI Spiral:** Socialization → Externalization → Combination → Internalization
- **ISO 30401:** Clause 7 (Support), Clause 8 (Operation)
- **Prompt Engineering:** Few-Shot, Chain-of-Thought, Constrained Output

---

*File: /root/.hermes/crispdm-checklist.md*
*Gunakan checklist ini setiap Senator cycle berjalan (tiap 6 jam)*
