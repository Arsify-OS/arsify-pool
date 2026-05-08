# Arsify Core — Senator Domain Reference

## Overview

Arsify Core menjalankan 5 AI Senator, masing-masing spesialis di satu domain intelligence. Setiap senator punya:
- System prompt yang mendefinisikan peran
- User prompt dengan instruksi + JSON schema
- Key prefix untuk SKP entries
- Field extraction rules

## Domain: Akademisi

**Focus:** Riset AI, universitas, hibah, edtech, pendidikan tinggi Indonesia

**Key Prefix:** `senator-akademisi/insight/`

**JSON Schema:**
```json
{
  "temuan": [
    {
      "judul": "Nama temuan",
      "detail": "Penjelasan detail",
      "sumber": "Sumber informasi",
      "dampak_bisnis": "Dampak ke bisnis",
      "urgensi": "tinggi|sedang|rendah"
    }
  ],
  "peluang_baru": ["Peluang 1", "Peluang 2"],
  "sinyal_lemah": ["Signal 1", "Signal 2"],
  "confidence": 0.0,
  "timestamp": "YYYY-MM-DD HH:MM UTC"
}
```

**Intelligence Targets:**
- Publikasi/riset AI terbaru dari universitas Indonesia
- Update program pemerintah untuk AI di pendidikan (Kemdikbud, BRIN)
- Startup/spinoff edtech Indonesia yang baru aktif
- Hibah atau funding riset AI yang sedang dibuka
- Talent pipeline: perubahan program AI di kampus

---

## Domain: Bisnis

**Focus:** Market, startup, ekonomi digital, regulasi bisnis Indonesia

**Key Prefix:** `senator-bisnis/insight/`

**JSON Schema:**
```json
{
  "peluang": [
    {
      "nama": "Nama peluang",
      "detail": "Penjelasan detail",
      "estimasi_nilai": "Estimasi nilai pasar",
      "urgensi": "tinggi|sedang|rendah"
    }
  ],
  "risiko": [
    {
      "nama": "Nama risiko",
      "dampak": "Deskripsi dampak",
      "probabilitas": "tinggi|sedang|rendah"
    }
  ],
  "funding_tracker": [
    {
      "startup": "Nama startup",
      "amount": "Jumlah funding",
      "stage": "Seed/Series A/dll",
      "investor": "Nama investor"
    }
  ],
  "rekomendasi": "Rekomendasi strategis",
  "confidence": 0.0,
  "timestamp": "YYYY-MM-DD HH:MM UTC"
}
```

**Intelligence Targets:**
- Funding/akuisisi startup Indonesia terbaru
- Tren e-commerce: platform, kategori, shift konsumen
- Regulasi OJK/BI yang memengaruhi bisnis digital
- Gap pasar yang belum diisi kompetitor besar
- Indikator makro: rupiah, BI rate, dampak ke startup

---

## Domain: Komunitas

**Focus:** Komunitas tech dan developer Indonesia, sentiment analysis

**Key Prefix:** `senator-komunitas/insight/`

**JSON Schema:**
```json
{
  "isu": [
    {
      "topik": "Nama topik",
      "sentiment": "positif|negatif|netral",
      "intensitas": "tinggi|sedang|rendah",
      "detail": "Penjelasan detail",
      "platform": "Twitter/Reddit/GitHub/dll"
    }
  ],
  "tokoh_kunci": [
    {
      "nama": "Nama tokoh",
      "handle": "@handle sosial media",
      "konteks": "Konteks penyebutan"
    }
  ],
  "tools_trending": ["Tool 1", "Tool 2"],
  "sentiment_overall": "positif|negatif|netral|campuran",
  "confidence": 0.0,
  "timestamp": "YYYY-MM-DD HH:MM UTC"
}
```

**Intelligence Targets:**
- Topik yang paling ramai di komunitas developer Indonesia
- Opini komunitas tentang AI, tools, regulasi
- Tokoh tech Indonesia yang sedang banyak dikutip
- Isu burnout, hiring freeze, perubahan kultur kerja
- Project open-source Indonesia yang mendapat traksi

---

## Domain: Pemerintah

**Focus:** Kebijakan digital dan regulasi Indonesia, compliance

**Key Prefix:** `senator-pemerintah/insight/`

**JSON Schema:**
```json
{
  "regulasi": [
    {
      "nama": "Nama regulasi",
      "nomor": "Nomor UU/Perppu",
      "lembaga": "Kominfo/OJK/BI/dll",
      "tanggal_efektif": "YYYY-MM-DD",
      "deadline_compliance": "YYYY-MM-DD",
      "dampak_bisnis": "Dampak ke bisnis",
      "urgensi": "kritis|tinggi|sedang|rendah"
    }
  ],
  "program_pemerintah": [
    {
      "nama": "Nama program",
      "anggaran": "Jumlah anggaran",
      "cara_akses": "Cara mengakses",
      "deadline": "YYYY-MM-DD"
    }
  ],
  "alert_compliance": ["Alert 1", "Alert 2"],
  "confidence": 0.0,
  "timestamp": "YYYY-MM-DD HH:MM UTC"
}
```

**Intelligence Targets:**
- Regulasi atau kebijakan digital baru dari Kominfo/OJK/BI
- Update implementasi UU PDP (nomor pasal, deadline compliance)
- Program AI pemerintah yang sedang berjalan atau dibuka
- Tender IT pemerintah yang relevan untuk bisnis digital
- Risiko compliance yang perlu diwaspadai startup

---

## Domain: Media

**Focus:** Narasi dan framing media Indonesia tentang AI

**Key Prefix:** `senator-media/insight/`

**JSON Schema:**
```json
{
  "narasi_dominan": [
    {
      "topik": "Topik utama",
      "framing": "Cara framing media",
      "sentiment": "positif|negatif|netral",
      "media_utama": ["Kompas", "Tempo", "Detik"]
    }
  ],
  "frekuensi_ai": {
    "per_minggu": 0,
    "trend": "naik|turun|stabil"
  },
  "sentiment_publik": "positif|negatif|netral|campuran",
  "tokoh_tersebut": [
    {
      "nama": "Nama tokoh",
      "konteks": "Konteks penyebutan"
    }
  ],
  "confidence": 0.0,
  "timestamp": "YYYY-MM-DD HH:MM UTC"
}
```

**Intelligence Targets:**
- Bagaimana Kompas, Tempo, Detik, CNBC Indonesia memframing AI
- Topik tech yang sedang trending di media Indonesia
- Tokoh atau perusahaan yang paling sering disebut terkait AI
- Pergeseran sentiment publik tentang AI (estimasi %)
- Narasi yang berbeda antara media tech-savvy vs media mainstream

---

## Extending Domains

To add a new domain, add entry to `DOMAIN_CONFIG` in `senator-execution.py`:

```python
"new_domain": {
    "system": "System prompt describing the senator role...",
    "prompt": "User prompt with JSON schema instructions...",
    "insight_fields": ["field1", "field2"],
    "key_prefix": "senator-newdomain/insight",
},
```

Then add the domain to the loop in `senator-cycle-v5.sh`:

```bash
for domain in akademisi bisnis komunitas pemerintah media new_domain; do
```
