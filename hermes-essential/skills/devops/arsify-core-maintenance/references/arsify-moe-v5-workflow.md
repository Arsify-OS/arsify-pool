# Arsify MoE v5 Workflow (Per-Senator Keys + Arsify Detection)

## Overview
Upgrade Arsify Core MoE Router to v5 with:
- Per-Senator OpenRouter API keys (avoid 402 errors)
- Arsify Detection: Auto-scan Ollama models on VPS
- Dynamic routing: Ollama first, fallback to OpenRouter per Senator

## Steps

### 1. Update `moe/config.py`
Add `SENATOR_KEYS` dict with per-domain OpenRouter keys:
```python
SENATOR_KEYS: dict = field(default_factory=lambda: {
    "akademisi": os.getenv("SENATOR_AKADEMISI_KEY", "sk-or-v1-..."),
    "bisnis": os.getenv("SENATOR_BISNIS_KEY", "sk-or-v1-..."),
    "pemerintah": os.getenv("SENATOR_PEMERINTAH_KEY", "sk-or-v1-..."),
    "komunitas": os.getenv("SENATOR_KOMUNITAS_KEY", "sk-or-v1-..."),
    "media": os.getenv("SENATOR_MEDIA_KEY", "sk-or-v1-..."),
    "kurator": os.getenv("KURATOR_KEY", "sk-or-v1-...")
})
```

### 2. Update `moe/router.py`
- Ensure `import uuid` is present (common pitfall if missing)
- Implement `detect_ollama_models()` async method using httpx:
  ```python
  async def detect_ollama_models(self) -> list[str]:
      try:
          async with httpx.AsyncClient(timeout=5.0) as client:
              resp = await client.get(f"{self.ollama_url}/api/tags")
              resp.raise_for_status()
              models = [m["name"] for m in resp.json().get("models", [])]
              self._available_ollama_models = models
              self._ollama_available = len(models) > 0
              return models
      except Exception as e:
          print(f"[Arsify Detection] Ollama not available: {e}")
          self._available_ollama_models = []
          self._ollama_available = False
          return []
  ```
- Add `get_best_ollama_model()` helper
- Update `route()` and `route_stream()` for dynamic provider selection (Ollama first, fallback to OpenRouter with per-Senator key)

### 3. Update `moe/main.py`
- Add FastAPI startup event to auto-detect Ollama models:
  ```python
  @app.on_event("startup")
  async def startup_event():
      print("[Arsify Detection] Scanning Ollama models...")
      models = await router.detect_ollama_models()
      print(f"[Arsify Detection] Found {len(models)} models: {models}")
  ```
- Add `/arsify-detection` endpoint to expose Ollama status, available models, and Senator domain mapping

### 4. Deploy & Test
```bash
# Start MoE Router
bash /root/upshalter-scripts/moe-router-start.sh

# Test detection endpoint (requires auth if enabled)
curl http://localhost:8000/arsify-detection

# Test chat with auto-routing
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analisa tren startup di Indonesia"}'
```

### 5. Commit & Push
```bash
cd /root/Arsify-OS/Arsify-core
git add moe/config.py moe/router.py moe/main.py
git commit -m "feat: Arsify MoE v5 - Per-Senator OpenRouter keys + Arsify Detection

- Per-Senator OpenRouter API keys in config.py
- Arsify Detection: auto-scan Ollama models via HTTP API
- Dynamic routing: Ollama first, fallback to OpenRouter per domain
- Startup event for auto-detection
- /arsify-detection endpoint for model mapping"
git push origin main
```

## Pitfalls
- Missing `import uuid` in router.py causes NameError
- Ensure httpx is installed (`pip3 install httpx`)
- Check Ollama is running before testing (`systemctl status ollama`)
- Verify per-Senator keys are valid (no 402 errors)