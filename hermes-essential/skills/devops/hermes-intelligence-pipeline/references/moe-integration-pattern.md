# Arsify MoE + Hermes API Integration Pattern

**Created:** 8 Mei 2026  
**Context:** Fase 4 Enhancement — integrating Arsify MoE router from arsify-final-package with existing Hermes Cognitive Engine

---

## Key Insight: INTEGRATE, Don't Replace

```
❌ WRONG: Replace Hermes API with Arsify MoE
  Senator → Arsify MoE → Ollama
  (Loses L1-L4 pipeline, SKP write-back, Kurator)

✅ RIGHT: Inject MoE capabilities INTO Hermes API
   Senator → Hermes API (with MoE classifier + memory inject) → Ollama
                       ↓
                  SKP Write-Back
                       ↓
                  Kurator Pipeline
```

## What Arsify MoE Provides

From `/root/arsify-final-package_v0.1.1/arsify-final-package/arsify-os-prototype-final/arsify-app/`:

| Component | File | Capability |
|-----------|------|------------|
| `ArsifyRouter.classify()` | `router.py` | Keyword-based domain classification |
| `ArsifyRouter.route()` | `router.py` | Route to correct Ollama model |
| `_build_messages()` | `router.py` | Inject memory context into system prompt |
| `build_memory_context()` | `memory.py` | Build context string from memory_notes |
| `save_message()` | `memory.py` | Persistent conversation history |
| 120s timeout | `config.py` | More generous than Hermes' 60s |

## What Hermes API Provides (Keep)

| Layer | Capability |
|-------|------------|
| L1 Perception | complexity scoring, risk assessment |
| L2 Cognition | SKP knowledge injection, planning |
| L3 Execution | Multi-model execution with fallback |
| L4 Reflection | Quality scoring, write-back trigger |
| SKP Write-Back | Automatic knowledge persistence |
| Kurator Pipeline | Periodic curation (Celery beat) |
| /v1/portsocket | Async task submission with polling |

## Integration Plan

### Step 1: Extend MoE Routing Rules

Add senator-specific domains to ROUTING_RULES:

```python
ROUTING_RULES = {
    # Existing
    "code": {"model": "qwen2.5-coder:3b", "priority": 3, "keywords": [...]},
    "system": {"model": "phi3:mini", "priority": 2, "keywords": [...]},
    "general": {"model": "llama3.2:3b", "priority": 0, "keywords": []},
    
    # NEW: Senator domains
    "senator_akademisi": {
        "model": "qwen2.5:1.5b",  # good for research synthesis
        "priority": 2,
        "keywords": ["riset", "penelitian", "jurnal", "publikasi", "akademik", 
                     "pendidikan", "universitas", "ilmiah", "study", "research"],
        "role": "Kamu adalah Senator Akademisi..."
    },
    "senator_bisnis": {
        "model": "qwen2.5:1.5b",
        "priority": 2,
        "keywords": ["bisnis", "startup", "UMKM", "pasar", "investasi", "ekonomi",
                     "market", "business", "revenue", "pertumbuhan"],
        "role": "Kamu adalah Senator Bisnis..."
    },
    "senator_pemerintah": {
        "model": "qwen2.5:1.5b",
        "priority": 2,
        "keywords": ["regulasi", "kebijakan", "pemerintah", "UU", "peraturan",
                     "legal", "hukum", "compliance", "PDPA"],
        "role": "Kamu adalah Senator Pemerintah..."
    },
    "senator_komunitas": {
        "model": "qwen2.5:1.5b",
        "priority": 2,
        "keywords": ["komunitas", "developer", "sentimen", "diskusi", "forum",
                     "community", "social", "opini"],
        "role": "Kamu adalah Senator Komunitas..."
    },
    "senator_media": {
        "model": "qwen2.5:1.5b",
        "priority": 2,
        "keywords": ["media", "berita", "narasi", "framing", "pers", "press",
                     "journalism", "coverage", "headline"],
        "role": "Kamu adalah Senator Media..."
    },
    "kurator": {
        "model": "qwen2.5:1.5b",  # or nemotron via OpenRouter for complex
        "priority": 3,
        "keywords": ["konsolidasi", "ringkasan", "laporan", "analisis lintas"],
        "role": "Kamu adalah Kurator..."
    },
}
```

### Step 2: Add Memory Context Injection

In `router.py` L3 execution, after L2 planning, inject conversation history:

```python
# Pseudocode for integrated L3
def execute_with_moe(prompt, agent_id, memory_context=""):
    category = classify(prompt)
    model = ROUTING_RULES[category]["model"]
    
    # Build messages with memory
    system_prompt = ROUTING_RULES[category]["role"]
    if memory_context:
        system_prompt += f"\n\n{memory_context}"
    
    # Call Ollama with 120s timeout (for kuratur)
    timeout = 120 if category == "kurator" else 90
    response = call_ollama(model, system_prompt, prompt, timeout=timeout)
    return response
```

### Step 3: Increase Kurator Timeout

Kurator needs more time for JSON generation:
- Hermes API: `LLM_TIMEOUT_READ=90` → change to `120` for kuratur
- Or use MoE route directly: `timeout=120.0` (from arsify config)

### Step 4: Category Enrichment via MoE

Use `classify()` to backfill "general" entries:

```python
for entry in skp_entries_where_category_general:
    category = classify(entry["value"])  # MoE keyword classification
    if category != "general":
        update_entry_category(entry["key"], category)
```

## Verification

```bash
# Test MoE classify
python3 -c "
from router import ArsifyRouter
r = ArsifyRouter()
print(r.classify('Riset AI terbaru di Indonesia'))  # → senator_akademisi
print(r.classify('Startup funding series A'))        # → senator_bisnis
print(r.classify('Kebijakan regulasi AI pemerintah')) # → senator_pemerintah
"
```

## Ollama Models Available

As of 8 Mei 2026: `qwen2.5:1.5b`, `phi3:miini`
Note: `llama3.2:3b` (used in arsify general rule) is NOT available — either pull it or change general rule to `qwen2.5:1.5b`.
