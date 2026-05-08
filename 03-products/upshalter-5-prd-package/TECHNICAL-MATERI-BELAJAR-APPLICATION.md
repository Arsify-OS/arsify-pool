# 📚 TEKNIS MATERI BELAJAR KNOWLEDGE UNTUK SELURUH GELOMBANG

## Berdasarkan:
- `/root/Materi Belajar Knowledge/` (3 PDFs)
- `/root/.hermes/knowledge/romi-wahono-theses.json` (83 entries)
- Memory: AI/ML, KM, UML/SE materials

---

## 🎯 RINGKASAN TEKNIS YANG BISA DITERAPKAN

### 1. CRISP-DM (CRoss-Industry Standard Process for Data Mining)
**Sumber:** AI/ML Materials + Romi Wahono Thesis (SE category)

**5 Fase CRISP-DM Mapping ke Upshalter:**

| Fase CRISP-DM | Aplikasi di Upshalter | Gelombang |
|---------------|----------------------|----------|
| **1. Business Understanding** | Senator dapat brief domain (akademisi/bisnis/media) | G1, G3 |
| **2. Data Understanding** | Senator crawl & baca sumber (web, arxiv, news) | G1, G3 |
| **3. Data Preparation** | Bersihkan, strukturkan jadi SKP entries | G1, G3 |
| **4. Modeling** | Kurator analisa pola lintas domain | G3 |
| **5. Evaluation** | Kurator review & deliver ke subscriber | G3, G4 |

**Penerapan Praktis:**
```python
# Setiap Senator cycle mengikuti CRISP-DM:
# File: /root/upshalter-scripts/senator-crispdm-cycle.sh

1. Business Understanding: Baca prompt domain dari SKP key "senator/{nama}/prompt"
2. Data Understanding: Fetch URLs (arxiv, news, github topics)
3. Data Preparation: Extract key insights → simpan ke SKP "akademisi/temuan/{tanggal}"
4. Modeling: (Kurator) Analisa 50 entries → deteksi pola
5. Evaluation: Kurator kirim laporan, subscriber kasih feedback
```

**✅ Cocok untuk:** G1 (fix Senator), G3 (Pentahelix Intel), G5 (Brand Brain analysis)

---

### 2. NONAKA SECI SPIRAL (Knowledge Management)
**Sumber:** romi-km-1hour-may2020.pdf + KM Materials

**4 Fase SECI + Mapping ke Upshalter:**

```
[SOCIALIZATION] Senators gather raw data → Tacit knowledge
      ↓
[EXTERNALIZATION] Senators write ke SKP → Explicit knowledge 
      ↓
[COMBINATION] Kurator compile laporan → New explicit knowledge
      ↓
[INTERNALIZATION] Subscribers baca laporan → New tacit knowledge (decisions)
      ↓
   (Loop kembali ke Socialization dengan konteks baru)
```

**Penerapan Praktis:**
```bash
# SKP Schema mengikuti SECI phases:

# 1. Socialization (Tacit) → simpan sebagai draft/raw
SKP key: "senator/{nama}/raw/{timestamp}"

# 2. Externalization (Explicit) → SKP entries formal
SKP key: "akademisi/temuan/{tanggal}"
Fields: source, insight, confidence, tags, senator_name

# 3. Combination (Explicit+) → Kurator reports
SKP key: "laporan/daily/{tanggal}"
Fields: executive_summary, themes, cross_domain, recommendations

# 4. Internalization (Tacit) → Subscriber feedback
SKP key: "subscriber/{id}/feedback/{tanggal}"
Fields: rating, action_taken, new_questions
```

**✅ Cocok untuk:** Semua Gelombang (G1-G5) karena ini adalah core flow Upshalter

---

### 3. ISO 30401 (Knowledge Management Systems Standard)
**Sumber:** KM Materials

**Klausul Kunci untuk Upshalter:**

| Klausul ISO 30401 | Implementasi di Upshalter | Status |
|-------------------|--------------------------|--------|
| **4. Context** | SKP menyimpan konteks bisnis klien (Brand Brain) | G5 |
| **5. Leadership** | Kurator sebagai "knowledge owner" untuk setiap domain | G3 |
| **6. Planning** | PRD-001 s/d PRD-005 sesuai risk-based planning | G1-G5 |
| **7. Support** | OpenSwarm dashboard untuk monitoring | G3 |
| **8. Operation** | Senator cycle tiap 6 jam, Kurator tiap 8 jam | G3 |
| **9. Performance** | Metrics: entries/cycle, latency, subscriber satisfaction | G3-G5 |
| **10. Improvement** | Feedback loop dari subscriber → perbaiki Senator prompts | G3-G5 |

**Penerapan Praktis:**
```sql
-- SKP tables mengikuti ISO 30401 structure
CREATE TABLE knowledge_assets (
    id INTEGER PRIMARY KEY,
    asset_type TEXT, -- 'raw', 'processed', 'report', 'feedback'
    scope TEXT, -- 'akademisi', 'bisnis', 'internal', 'brand'
    created_by TEXT, -- 'senator-bisnis', 'kurator', 'subscriber'
    iso_clause TEXT, -- '8.1', '8.2', etc.
    content TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

-- Index untuk performance evaluation (Klausul 9)
CREATE INDEX idx_performance ON knowledge_assets(created_at, asset_type);
```

**✅ Cocok untuk:** G3 (standardize SKP), G4 (client onboarding), G5 (Brand Brain)

---

### 4. PROMPT ENGINEERING (AI/ML Materials)
**Sumber:** AI/ML Materials + Transformer/LLM

**5 Tekik Prompt Engineering untuk Senator & Kurator:**

| Teknik | Penerapan | Impact |
|--------|-----------|--------|
| **Few-Shot Prompting** | Beri contoh 3 SKP entries bagus → Senator generate serupa | G1: Improve SKP quality |
| **Chain-of-Thought** | "Analisa langkah demi langkah: 1) Baca sumber 2) Extract insight..." | G3: Kurator better reports |
| **Role Prompting** | "Kamu adalah Senator Akademisi expert di AI Indonesia..." | G1: Better domain focus |
| **Constrained Output** | "Output HARUS JSON dengan field: source, insight, confidence" | G1: Structured SKP entries |
| **Context Stuffing** | Inject Brand Brain (PRD-005) ke system prompt | G5: Brand-consistent content |

**Penerapan Praktis:**
```python
# File: /root/.hermes/senator_prompts.py

SENATOR_PROMPTS = {
    "akademisi": """
You are Senator Akademisi, expert in Indonesian AI/tech research.
Your task follows CRISP-DM methodology.

Few-shot examples:
1. Source: "arxiv.org/abs/2401.12345" → Insight: "New LoRA technique improves..."
2. Source: "journal.ugm.ac.id/ai" → Insight: "Indonesian universities focusing on..."

Process:
1. Read the URL provided
2. Extract 3 key insights (Chain-of-Thought)
3. Output JSON: {"source": "...", "insight": "...", "confidence": 0.9, "tags": [...]}
""",
    
    "kurator": """
You are Kurator Pentahelix. Your task:
1. Read last 50 SKP entries (akademisi/*, bisnis/*, media/*, komunitas/*, pemerintah/*)
2. Identify cross-domain themes (Nonaka Combination phase)
3. Generate report following ISO 30401 Clause 8.2
4. Output structured markdown with: Executive Summary, Themes, Recommendations
"""
}
```

**✅ Cocok untuk:** G1 (fix Senator output), G3 (Kurator reports), G5 (Brand Brain content)

---

### 5. UML DIAGRAMS (Software Engineering)
**Sumber:** romi-se-uml-apr2020.pdf

**4 Diagram Untuk Dokumentasi Upshalter:**

#### 5.1 Use Case Diagram
```
Actors: Senator, Kurator, Subscriber, Admin
Use Cases:
- Senator: Research → Write SKP → Trigger Kurator
- Kurator: Read SKP → Generate Report → Deliver to Subscriber
- Subscriber: Receive Report → Give Feedback → Update Preferences
- Admin: Monitor (OpenSwarm Dashboard) → Fix Issues
```

#### 5.2 Sequence Diagram (Senator → SKP → Kurator Flow)
```
Senator -> Cognitive Engine: POST /research {prompt, urls}
Cognitive Engine -> Senator Container: Execute research
Senator Container -> SKP DB: INSERT INTO memory_notes
SKP DB -> Kurator: Trigger (90 min later)
Kurator -> SKP DB: SELECT * FROM memory_notes WHERE created_at > NOW()-8h
Kurator -> Telegram: POST /sendMessage (report)
```

#### 5.3 Class Diagram (SKP Data Model)
```
class KnowledgeEntry {
    +id: int
    +key: string
    +value: text
    +scope: string
    +source_agent: string
    +created_at: datetime
}

class BrandBrain {
    +brand_name: string
    +voice_tone: list
    +avoid_words: list
    +past_campaigns: list
}

KnowledgeEntry "1" -- "0..*" BrandBrain: stored_in
```

#### 5.4 Deployment Diagram (Gelombang 3-5)
```
[Internet] --> [Nginx:443]
[Nginx] --> [Chat UI:3000]
[Nginx] --> [Workspace:8643]
[Nginx] --> [OpenSwarm:8324]
[OpenSwarm] --> [Senator Containers x5]
[Senator Containers] --> [SKP DB:SQLite]
[SKP DB] --> [Kurator Container]
[Kurator] --> [Telegram Bot API]
```

**✅ Cocok untuk:** G2 (Fix workspace UI), G3 (OpenSwarm integration), G4 (Client onboarding docs)

---

### 6. BCE ARCHITECTURE (Boundary-Control-Entity)
**Sumber:** SE Materials

**Mapping ke Upshalter Components:**

| Layer BCE | Upshalter Component | Fungsi |
|-----------|---------------------|--------|
| **Boundary** | Nginx, Chat UI, Workspace UI, Telegram Bot | Interface dengan user/subscriber |
| **Control** | Hermes Cognitive Engine, Senator Logic, Kurator Logic | Business logic, research, reporting |
| **Entity** | SKP DB, Brand Brain, Subscriber DB | Data persistence |

**Penerapan di OpenSwarm Integration (Gelombang 3):**
```python
# Boundary: OpenSwarm Dashboard (port 3000)
# Control: Senator Agents (FastAPI backend:8324)
# Entity: SKP DB (SQLite with SECI structure)

# Setiap Senator adalah kombinasi BCE:
class SenatorAgent(Boundary + Control + Entity):
    def boundary(self):
        return "Accepts research prompt via OpenSwarm UI"
    
    def control(self):
        return "CRISP-DM research logic + Prompt Engineering"
    
    def entity(self):
        return "Write to SKP DB with ISO 30401 metadata"
```

**✅ Cocok untuk:** G3 (OpenSwarm setup), G5 (Brand Brain architecture)

---

### 7. ROMI WAHONO THESIS DATASET (83 Entries)
**Sumber:** `/root/.hermes/knowledge/romi-wahono-theses.json`

**3 Kategori Utama untuk Senator Prompts:**

| Kategori | Jumlah | Contoh Topik | Senator yang Cocok |
|----------|--------|--------------|-------------------|
| **Software Engineering** | 45 | Defect prediction, SDLC, Code analysis | Senator Akademisi |
| **Data Mining** | 25 | Clustering, Classification, Association | Senator Bisnis |
| **Intelligent Systems** | 13 | Expert systems, AI applications | Senator Media |

**Penerapan:**
```bash
# Inject tema dari dataset ke Senator prompts:
# Senator Akademisi: Fokus ke "Software Defect Prediction", "SDLC"
# Senator Bisnis: Fokus ke "Clustering untuk segmentasi pasar", "Classification untuk lead scoring"
# Senator Media: Fokus ke "Intelligent Systems untuk sentiment analysis"

# File: /root/.hermes/senator_themes.json
{
  "akademisi": ["software defect prediction", "SDLC", "code quality"],
  "bisnis": ["market clustering", "customer segmentation", "churn prediction"],
  "media": ["sentiment analysis", "framing detection", "narrative analysis"]
}
```

**✅ Cocok untuk:** G1 (Focus Senator research), G3 (Better domain expertise)

---

## 🚀 STRATEGI PENERAPAN PER GELOMBANG

### GELOMBANG 1 (PRD-001 Fix) — 7-10 Mei
| Teknis | Implementasi | Target |
|--------|--------------|--------|
| **Prompt Engineering** | Fix Senator prompts (Role + Few-shot + Constrained Output) | Senator hasilkan SKP entries > 0 |
| **CRISP-DM** | Senator cycle ikuti 5 fase (Data Prep → SKP write) | Structured entries |
| **SECI** | Senator writes "akademisi/temuan/*" (Externalization) | Clear knowledge flow |

### GELOMBANG 2 (PRD-004 Demo) — 8-10 Mei
| Teknis | Implementasi | Target |
|--------|--------------|--------|
| **UML Deployment Diagram** | Dokumentasi architecture chat/workspace/status | Demo jelas |
| **BCE Architecture** | Fix Boundary layer (Nginx) → Control (API) → Entity (SKP) | Workspace berfungsi |

### GELOMBANG 3 (PRD-002 Pentahelix) — 11-20 Mei
| Teknis | Implementasi | Target |
|--------|--------------|--------|
| **OpenSwarm + SECI** | 5 Senator (Socialization) → SKP (Externalization) → Kurator (Combination) | Full pipeline |
| **CRISP-DM Full** | Kurator lakukan Modeling + Evaluation | Laporan berkualitas |
| **ISO 30401** | Standardize SKP schema + performance metrics | Professional KM |
| **UML Sequence** | Document Senator→SKP→Kurator→Subscriber flow | Maintainable |

### GELOMBANG 4 (PRD-003 Implementation) — 15-25 Mei
| Teknis | Implementasi | Target |
|--------|--------------|--------|
| **ISO 30401 Clause 6-7** | Onboarding checklist sesuai risk-based planning | 3-day onboarding |
| **BCE Architecture** | Client workspace = Boundary, Hermes = Control, SKP = Entity | Clear separation |
| **UML Use Case** | Dokumentasi untuk client (siapa apa) | Client docs |

### GELOMBANG 5 (PRD-005 Brand Brain) — 20-40 Mei
| Teknis | Implementasi | Target |
|--------|--------------|--------|
| **Prompt Engineering** | Brand Brain injection ke system prompt | Brand-consistent content |
| **CRISP-DM** | Analisa campaign data → Brand Brain update | Continuous learning |
| **SECI + ISO 30401** | Brand Brain sebagai "knowledge asset" terkelola | Enterprise-ready |
| **Romi Dataset** | Pakai tema "Intelligent Systems" untuk client demos | Demo relevance |

---

## 📋 CHECKLIST IMPLEMENTASI TEKNIS

### Langkah 1: CRISP-DM untuk Senator (G1 - Minggu ini)
```bash
# 1. Update senator_cognitive_client.py dengan CRISP-DM stages
# 2. Simpan progress ke SKP key "senator/{nama}/crispdm-stage"
# 3. Monitor: sqlite3 /data/arsify.db "SELECT key,value FROM memory_notes WHERE key LIKE 'senator/%'"
```

### Langkah 2: SECI Spiral di SKP Schema (G1-G3 - Minggu ini)
```sql
-- Add SECI phase tracking to SKP
ALTER TABLE memory_notes ADD COLUMN seci_phase TEXT DEFAULT 'externalization';
ALTER TABLE memory_notes ADD COLUMN iso_clause TEXT;
```

### Langkah 3: Prompt Engineering Library (G1 - Segera)
```bash
# File: /root/.hermes/prompts/senator-prompts.json
# Isi dengan Few-Shot + Chain-of-Thought + Role prompts
# Test dengan: hermes -z "Gunakan prompt dari /root/.hermes/prompts/senator-akademisi.json"
```

### Langkah 4: ISO 30401 Compliance (G3 - 2 minggu)
```bash
# Buat SKP tables sesuai ISO 30401
# File: /root/upshalter-scripts/init-iso30401-skp.sql
```

### Langkah 5: UML Documentation (G2-G4 - Parallel)
```bash
# Generate UML diagrams untuk:
# - Deployment diagram (current infra)
# - Sequence diagram (Senator→Kurator flow)
# - Use Case diagram (user interactions)
```

---

## 🎯 SIMPULAN

**Yang PALING MUDAH dan COCOK untuk diimplementasi SEGERA:**

1. **Prompt Engineering** → Fix Senator (G1) dalam 1 hari
2. **CRISP-DM** → Structure Senator cycle (G1) dalam 2 hari
3. **SECI Spiral** → Clarify knowledge flow (G1-G3) dalam 1 hari

**Yang membutuhkan waktu lebih lama tapi STRATEGIS:**

4. **ISO 30401** → Standardize untuk klien enterprise (G3-G5)
5. **UML Diagrams** → Documentation untuk demo & client (G2, G4)
6. **BCE Architecture** → Clean architecture untuk scalability (G3-G5)

**Resource dari Romi Wahono Dataset:**
- 83 theses → Inspiration untuk Senator research themes
- SE + Data Mining + Intelligent Systems → Domain expertise coverage

---

*Dokumen: /root/upshalter-5-prd-package/TECHNICAL-MATERI-BELAJAR-APPLICATION.md*
*Updated: 7 Mei 2026*
