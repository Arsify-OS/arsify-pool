# Senator Cycle v3 — OpenRouter Direct Pattern

**Created**: 8 Mei 2026
**Context**: Fase 4 fix — Ollama CPU-only too slow, Hermes API portsocket is async-only

## Architecture Decision

```
BEFORE (v1/v2):
  Senator → Hermes API :8100 /chat → Ollama lokal → 39s load + >60s inference → TIMEOUT
  
AFTER (v3):
  Senator → OpenRouter API langsung → GPU inference → <30s response ✅
              ↓ (fallback only)
            Ollama lokal → 30s timeout, num_predict=512
```

## OpenRouter API Call Pattern

```python
import httpx, json

OPENROUTER_API = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = "sk-or-v1-..."  # From env or config
OPENROUTER_MODEL = "openrouter/owl-alpha"

r = httpx.post(
    OPENROUTER_API + "/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": research_prompt}
        ],
        "max_tokens": 1500
    },
    timeout=75.0
)
content = r.json()["choices"][0]["message"]["content"]
```

## Tested Results (8 Mei 2026)

All 5 senators succeeded via OpenRouter direct:

| Senator | Status | Response Time |
|---------|--------|---------------|
| senator-akademisi | ✅ SUCCESS | ~30s |
| senator-bisnis | ✅ SUCCESS | ~30s |
| senator-komunitas | ✅ SUCCESS | ~30s |
| senator-pemerintah | ✅ SUCCESS | ~30s |
| senator-media | ✅ SUCCESS | ~30s |

Total SKP: 414 → 419 entries (5 new senator outputs)

## Key OpenRouter Details

- **Auth header**: `Authorization: Bearer <key>` (NOT `X-API-Key`)
- **Working models**: `openrouter/owl-alpha` (default for this project)
- **API URL**: `https://openrouter.ai/api/v1/chat/completions`
- **Verified**: Response in <30s even for JSON-structured analysis prompts

## What Doesn't Work

1. **Hermes API /chat** → Routes to Ollama lokal = same slowness
2. **Hermes API /v1/portsocket** → Async only (returns task_id, requires Celery polling)
3. **Ollama lokal** → 39s model load + >60s inference on 2-core CPU
4. **httpx without httpcore** → `ModuleNotFoundError` even when httpx installed

## Hermes API Portsocket Auth Details

```
POST /v1/portsocket
Headers: X-API-Key: hermes-secret-change-me-in-production
         X-Agent-ID: senator-akademisi
Body: {"input": "string", "mode": "auto"}

Response: {"task_id": "xxx", "status": "queued", ...} — ASYNC
Poll: GET /v1/result/{task_id}
```

Celery may not process external tasks → stuck at PENDING. Not suitable for sync inference.

## Prompt Fixes Applied (v3)

### Senator Pemerintah
Added: *"Sebutkan nomor pasal spesifik, lembaga penyelenggara, dan deadline compliance yang relevan untuk bisnis digital dan startup Indonesia."*

### Senator Media
Added: *"Output hanya SATU JSON block, tidak ada teks di luar JSON."*

## Kurator v2 Rewrite

kurator-v2.sh rewritten as `kurator-v2.py` (standalone Python) because:
1. Inline Python heredoc `__file__` resolves incorrectly from bash
2. `sqlite3.Raw` doesn't exist — should be `sqlite3.Row`
3. Easier to maintain Python logic in .py file

Kurator v2 also uses **OpenRouter as primary** (not Ollama):
- Before: confidence 0.3 (Ollama timeout → fallback)
- After: confidence 0.9 (OpenRouter full analysis)
