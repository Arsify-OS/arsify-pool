# Upshalter Technical Frameworks Application
## Condensed from Materi Belajar Knowledge + Session Work (7 Mei 2026)

---

## 1. CRISP-DM (CRoss-Industry Standard Process for Data Mining)
**5 Fase Mapping to Upshalter:**
| Fase CRISP-DM | Upshalter Application | Gelombang |
|---------------|---------------------|----------|
| Business Understanding | Senator domain brief (akademisi/bisnis/media) | G1, G3 |
| Data Understanding | Senator crawl sources (web, arxiv, news) | G1, G3 |
| Data Preparation | Clean, structure to SKP entries | G1, G3 |
| Modeling | Kurator analyze cross-domain patterns | G3 |
| Evaluation | Kurator deliver report, subscriber feedback | G3, G4 |

**Practical Implementation:**
```bash
# Every Senator cycle follows CRISP-DM:
1. Business Understanding: Read domain prompt from SKP key "senator/{nama}/prompt"
2. Data Understanding: Fetch URLs (arxiv, news, github topics)
3. Data Preparation: Extract key insights → save to SKP "akademisi/temuan/{tanggal}"
4. Modeling: Kurator analyze 50 entries → detect patterns
5. Evaluation: Kurator send report, subscriber give feedback
```

---

## 2. Nonaka SECI Spiral (Knowledge Management)
**4 Phases + Upshalter Mapping:**
```
[Socialization] Senators gather raw data → Tacit knowledge
      ↓
[Externalization] Senators write to SKP → Explicit knowledge 
      ↓
[Combination] Kurator compile report → New explicit knowledge
      ↓
[Internalization] Subscribers read report → New tacit knowledge (decisions)
      ↓
   (Loop back to Socialization with new context)
```

**SKP Schema Mapping:**
| SECI Phase | SKP Key Pattern | Description |
|------------|-----------------|-------------|
| Socialization | `senator/{nama}/raw/{timestamp}` | Raw tacit data |
| Externalization | `akademisi/temuan/{tanggal}` | Structured explicit entries |
| Combination | `laporan/daily/{tanggal}` | Consolidated reports |
| Internalization | `subscriber/{id}/feedback/{tanggal}` | Subscriber decisions/feedback |

---

## 3. ISO 30401 (Knowledge Management Systems Standard)
**Key Clauses for Upshalter:**
| Clause | Pipeline Implementation | Status |
|--------|-------------------------|--------|
| 4. Context | SKP stores client brand context (Brand Brain) | PRD-005 |
| 5. Leadership | Kurator as knowledge owner per domain | PRD-002 |
| 6. Planning | PRD-001 to PRD-005 follow risk-based planning | G1-G5 |
| 8. Operation | Senator cycle every 6h, Kurator every 8h | PRD-002 |
| 9. Performance | Metrics: entries/cycle, latency, subscriber satisfaction | G3-G5 |
| 10. Improvement | Subscriber feedback → improve Senator prompts | G3-G5 |

**SKP Table Structure for ISO Compliance:**
```sql
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
```

---

## 4. Prompt Engineering Techniques
**5 Techniques for Senator/Kurator:**
| Technique | Application | Impact |
|-----------|--------------|--------|
| Few-Shot Prompting | Provide 3 example SKP entries → Senator generates similar | G1: Improve SKP quality |
| Chain-of-Thought | "Analyze step-by-step: 1) Read source 2) Extract insight" | G3: Better Kurator reports |
| Role Prompting | "You are Senator Akademisi expert in Indonesian AI" | G1: Better domain focus |
| Constrained Output | "Output JSON with fields: source, insight, confidence" | G1: Structured SKP entries |
| Context Stuffing | Inject Brand Brain to system prompt | G5: Brand-consistent content |

**Example Senator Prompt Template:**
```python
SENATOR_PROMPTS = {
    "akademisi": """
You are Senator Akademisi, expert in Indonesian AI/tech research.
Follow CRISP-DM methodology.

Few-shot examples:
1. Source: "arxiv.org/abs/2401.12345" → Insight: "New LoRA technique improves..."
2. Source: "journal.ugm.ac.id/ai" → Insight: "Indonesian universities focusing on..."

Process:
1. Read the provided URL
2. Extract 3 key insights (Chain-of-Thought)
3. Output JSON: {"source": "...", "insight": "...", "confidence": 0.9, "tags": [...]}
""",
    "kurator": """
You are Kurator Pentahelix. Your task:
1. Read last 50 SKP entries (akademisi/*, bisnis/*, media/*)
2. Identify cross-domain themes (SECI Combination phase)
3. Generate report following ISO 30401 Clause 8.2
4. Output structured markdown with: Executive Summary, Themes, Recommendations
"""
}
```

---

## 5. Romi Wahono Thesis Dataset (83 Entries)
**3 Main Categories for Senator Themes:**
| Category | Count | Example Topics | Matching Senator |
|----------|-------|----------------|-----------------|
| Software Engineering | 45 | Defect prediction, SDLC, Code analysis | Senator Akademisi |
| Data Mining | 25 | Clustering, Classification, Association | Senator Bisnis |
| Intelligent Systems | 13 | Expert systems, AI applications | Senator Media |

**Theme Injection for Senators:**
```json
{
  "akademisi": ["software defect prediction", "SDLC", "code quality"],
  "bisnis": ["market clustering", "customer segmentation", "churn prediction"],
  "media": ["sentiment analysis", "framing detection", "narrative analysis"]
}
```

---

## 6. Quick Implementation Checklist
### Step 1: CRISP-DM for Senators (G1 - This Week)
```bash
# Update senator_cognitive_client.py with CRISP-DM stages
# Save progress to SKP key "senator/{nama}/crispdm-stage"
# Monitor: sqlite3 /data/arsify.db "SELECT key,value FROM memory_notes WHERE key LIKE 'senator/%'"
```

### Step 2: SECI Spiral in SKP Schema (G1-G3 - This Week)
```sql
ALTER TABLE memory_notes ADD COLUMN seci_phase TEXT DEFAULT 'externalization';
ALTER TABLE memory_notes ADD COLUMN iso_clause TEXT;
```

### Step 3: Prompt Engineering Library (G1 - Immediate)
```bash
# Create /root/.hermes/prompts/senator-prompts.json
# Test with: hermes -z "Use prompt from /root/.hermes/prompts/senator-akademisi.json"
```

### Step 4: ISO 30401 Compliance (G3 - 2 Weeks)
```bash
# Create SKP tables per ISO 30401
# File: /root/upshalter-scripts/init-iso30401-skp.sql
```

---

*Source: /root/upshalter-5-prd-package/TECHNICAL-MATERI-BELAJAR-APPLICATION.md*
*Condensed for hermes-intelligence-pipeline skill reference*
