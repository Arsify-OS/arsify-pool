---
name: arsify-core-maintenance
description: Repeatable maintenance workflow for Arsify Core repo (Arsify Workforce OS intelligence engine). Covers adding missing standard files, fixing hardcoded paths, adding deployment configs, rebranding to remove creator traces, and repo hygiene.
---

# Arsify Core Maintenance

Standard workflow for maintaining the [Arsify Core](https://github.com/Arsify-OS/Arsify-core) repository.

## Trigger Conditions
- User asks to "polish", "fix hardcoded paths", or "add missing files" to Arsify Core repo
- Repo lacks standard files (requirements.txt, .env.example)
- Scripts contain hardcoded `/root/` paths instead of dynamic detection
- Deployment configs (systemd, logrotate) need to be added/updated

## Workflow Steps

### 1. Check Repo Structure
```bash
cd /path/to/arsify-core-publish
ls -a
# Look for: requirements.txt, .env.example, deploy/ directory
```

### 1.5 Handle Divergent Git Histories
If the local repo has unrelated history compared to remote (e.g., adding new components to an existing remote repo with prior commits):
```bash
cd /path/to/arsify-core
git pull origin main --allow-unrelated-histories
# Resolve merge conflicts if any, then commit merge
git push -u origin main  # First push after merge to set upstream
```

### 2. Add Missing Standard Files
- **requirements.txt**: Only dependency is `httpx>=0.27.0`
- **.env.example**: Template for all env vars (OPENROUTER_API_KEY, OPENROUTER_MODEL, SKP_DB_PATH, SCRIPT_DIR, HERMES_API, HERMES_API_KEY)

### 3. Fix Hardcoded Paths
#### Shell Scripts (e.g., senator-cycle-v5.sh)
Replace static paths with dynamic detection:
```bash
# Before
SCRIPT_DIR="${SCRIPT_DIR:-/root/upshalter-scripts}"
LOG_DIR="/root/upshalter-logs"

# After
SCRIPT_DIR="${SCRIPT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
LOG_DIR="${LOG_DIR:-/var/log/arsify}"
```

#### Python Scripts (e.g., senator-execution.py)
Replace static paths with dynamic detection:
```python
# Before
SDIR = os.getenv("SCRIPT_DIR", "/root/upshalter-scripts")

# After
SDIR = os.getenv("SCRIPT_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### 4. Add Deploy Configs
Create `deploy/` directory with:
- `deploy/systemd/arsify-senator.service` (systemd service unit)
- `deploy/systemd/arsify-senator.timer` (6-hour cycle timer)
- `deploy/logrotate/arsify` (log rotation config)

### 5. Rebranding & Security (Remove Creator Traces)
If the repo was originally built by a specific AI agent (e.g., Hermes Agent), remove all traces to avoid exposing system origin:
1. **Replace creator-specific references**:
   - Env vars: `HERMES_*` → `UPSHALTER_*` (or your chosen rebranded name)
   - Paths: `/root/.hermes` → `/root/.upshalter`, `/opt/hermes-cognitive` → `/opt/upshalter-cognitive`
   - Key prefixes in DB: `hermes/senator/` → `upshalter/senator/`
   - Default secrets: `hermes-secret-change-me-in-production` → `upshalter-secret-change-me-in-production`
2. **Full case-insensitive scan**:
   ```bash
   cd /path/to/arsify-core
   grep -rin "hermes" --include="*.py" --include="*.sh" --include="*.md" --include="*.example" . 2>/dev/null | grep -v "upshalter" | grep -v ".git/"
   ```
   Replace all remaining references (comments, docs, variable names).
3. **Sensitive data check**:
   - Scan for real API keys/tokens: `grep -r "sk-or-v1-\|AAEFPs2G\|TELEGRAM_BOT_TOKEN" --include="*.py" --include="*.sh" --include="*.md"`
   - Check git history for leaked credentials: `git log --all -p -S "secret-string"`
   - Ensure no real `.env` files are committed (`.gitignore` should include `.env`, `.env.local`)

4. **Git History Sanitization** (permanently remove all traces from commit history):
   - **Backup first**: `cp -r arsify-core-publish arsify-core-publish-backup-$(date +%Y%m%d-%H%M%S)`
   - Install `git-filter-repo`: `apt-get install -y git-filter-repo` (Ubuntu/Debian)
   - Replace all case-sensitive/insensitive references in history:
     ```bash
     cd /path/to/arsify-core-publish
     git filter-repo --replace-text <(echo -e "oldname\nOldName\nOLDNAME") --force
     ```
   - Force push cleaned history:
     ```bash
     git remote set-url origin git@github.com:Arsify-OS/Arsify-core.git
     git push -f origin main
     ```
   - **Pitfall**: Force pushing rewrites remote history; notify collaborators first or ensure you're the only maintainer.

### 6. Update Notifications
Replace hardcoded CLI calls (e.g., `hermes` CLI) with curl-based Telegram notifications:
```bash
# In shell scripts
[ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ] && \
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        --data-urlencode "chat_id=$TELEGRAM_CHAT_ID" \
        --data-urlencode "text=$MSG" > /dev/null 2>&1 || true
```

### 7. Commit & Push
Use descriptive commit messages:
```bash
git add -A
git commit -m "Polish: Add requirements.txt, .env.example, fix hardcoded paths, add deploy configs

- Add requirements.txt with httpx dependency
- Add .env.example template for environment variables
- Fix hardcoded /root/upshalter-scripts paths in shell script and Python
- Change default LOG_DIR to /var/log/arsify
- Add deploy/ directory with systemd service/timer and logrotate config
- SCRIPT_DIR now auto-detects from script location instead of hardcoded path"
git push origin main
```

For rebranding commits:
```bash
git commit -m "Rebrand: Replace all Hermes references with Upshalter

- Rename HERMES_API to UPSHALTER_API, HERMES_API_KEY to UPSHALTER_API_KEY
- Replace all references to Hermes Cognitive Engine with Upshalter Cognitive Engine
- Replace paths: /root/.hermes -> /root/.upshalter, /opt/hermes-cognitive -> /opt/upshalter-cognitive
- Replace key prefixes: hermes/senator/ -> upshalter/senator/
- Update .env.example with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
- Replace hermes CLI call with curl-based Telegram notification
- Clean all case-insensitive 'hermes' references from source code and docs"
git push origin main
```

### 8. Arsify MoE Integration (Active Production Setup)
Upgrade Arsify-core to use local Arsify MoE Router to eliminate OpenRouter 402 errors and leverage local Ollama models (now the active production setup):
1. **Source**: Use `/root/arsify-final-package_v0.1.1/` as the base for MoE components.
2. **Directory Structure**: Create `moe/` directory in Arsify-core root:
   ```bash
   mkdir -p /root/Arsify-OS/Arsify-core/moe
   ```
3. **Copy Core MoE Files**: Copy `router.py`, `memory.py`, `config.py`, `main.py` from `arsify-final-package/arsify-os-prototype-final/arsify-app/app/` to `moe/`.
4. **Update `router.py`**: Add 5 Senator domains + Kurator with keyword-based routing:
   - `senator_akademisi`: Keywords = riset, publikasi, jurnal, akademik; model = `llama3.2:3b` (Ollama)
   - `senator_bisnis`: Keywords = startup, UMKM, investasi, bisnis; model = `qwen2.5-coder:3b` (Ollama)
   - `senator_pemerintah`: Keywords = regulasi, kebijakan, pemerintah, birokrasi; model = `llama3.2:3b` (Ollama)
   - `senator_komunitas`: Keywords = komunitas, developer, warga, sosial; model = `llama3.2:3b` (Ollama)
   - `senator_media`: Keywords = narasi, framing, media, jurnalis; model = `llama3.2:3b` (Ollama)
   - `kurator`: Keywords = konsolidasi, laporan, rekap; model = `meta/llama-3.1-8b-instruct:free` (OpenRouter fallback)
5. **Update `config.py`**: Add new OpenRouter key `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`, set MoE Router port to 8000, Ollama URL to `http://localhost:11434`.
6. **Create `senator-execution-moe.py`**: New Senator execution script that calls MoE Router at `http://localhost:8000/v1/chat/completions` instead of OpenRouter directly. Copy to `python/` and `/root/upshalter-scripts/python/`.
7. **Create `moe-router-start.sh`**: Startup script for MoE Router (FastAPI on port 8000). Copy to `scripts/` and `/root/upshalter-scripts/`.
8. **Update Senator Cycle**: Create `senator-cycle-v6-moe.sh` (auto-starts MoE Router, runs all 5 Senators via MoE). Symlink as `senator-cycle.sh` (active cycle script).
9. **Test MoE Router**:
   ```bash
   bash /root/upshalter-scripts/moe-router-start.sh
   curl http://localhost:8000/v1/models
   ```
10. **Test Senator Execution**:
    ```bash
    python3 /root/upshalter-scripts/python/senator-execution-moe.py --domain akademisi --dry-run
    ```

For full Q&A analysis of Arsify MoE, see `references/arsify-moe-qa.md`.

## 9. Per-Senator OpenRouter API Keys & Ollama Detection (v5)

**Per-Senator Keys**: Update `moe/config.py` to include separate `SENATOR_KEYS` dict with each Senator's OpenRouter key. This allows each domain to use its own quota and avoid 402 errors.

```python
# In moe/config.py
SENATOR_KEYS: dict = field(default_factory=lambda: {
    "akademisi": os.getenv("SENATOR_AKADEMISI_KEY", "sk-or-v1-..."),
    "bisnis": os.getenv("SENATOR_BISNIS_KEY", "sk-or-v1-..."),
    "pemerintah": os.getenv("SENATOR_PEMERINTAH_KEY", "sk-or-v1-..."),
    "komunitas": os.getenv("SENATOR_KOMUNITAS_KEY", "sk-or-v1-..."),
    "media": os.getenv("SENATOR_MEDIA_KEY", "sk-or-v1-..."),
    "kurator": os.getenv("KURATOR_KEY", "sk-or-v1-...")
})
```

**Ollama Detection (Arsify Detection)**: Add automatic discovery of available Ollama models on VPS via Ollama HTTP API (preferred over subprocess). In `moe/router.py`, implement as an async method:

```python
import httpx  # Add to imports

async def detect_ollama_models(self) -> list[str]:
    """Arsify Detection: Detect available Ollama models on VPS via HTTP API."""
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

Add helper to get best available Ollama model:

```python
def get_best_ollama_model(self, preferred_list: list[str]) -> Optional[str]:
    """Dapatkan model Ollama terbaik yang tersedia dari daftar preferensi."""
    for model in preferred_list:
        if model in self._available_ollama_models:
            return model
    # Fallback: ambil model pertama yang tersedia
    if self._available_ollama_models:
        return self._available_ollama_models[0]
    return None
```

**Startup Auto-Detection**: Add FastAPI startup event in `moe/main.py` to scan Ollama models on MoE Router start:

```python
@app.on_event("startup")
async def startup_event():
    """Arsify Detection: Detect Ollama models on startup."""
    print("[Arsify Detection] Scanning Ollama models...")
    models = await router.detect_ollama_models()
    print(f"[Arsify Detection] Found {len(models)} models: {models}")
```

**Dynamic Routing**: Modify `route()` and `route_stream()` in `moe/router.py` to use dynamic provider selection: prefer Ollama if model available, else fallback to OpenRouter with Senator-specific key.

```python
# In route() method
provider = cfg.get("provider", "auto")
actual_provider = provider
model = None

if provider == "auto":
    if self._ollama_available:
        model = self.get_best_ollama_model(cfg["preferred_ollama_models"])
        if model:
            actual_provider = "ollama"
    if not model:
        model = cfg["openrouter_model"]
        actual_provider = "openrouter"
```

**Endpoint**: Add `/arsify-detection` in `moe/main.py` to expose Ollama status, available models, and Senator domain mapping (requires auth):

```python
@app.get("/arsify-detection")
async def arsify_detection(key_data: dict = Depends(require_auth)):
    """Arsify Detection: Scan Ollama models dan show Senator domain mapping."""
    available = await router.detect_ollama_models()
    
    domain_mapping = {}
    for category, cfg in ROUTING_RULES.items():
        preferred = cfg.get("preferred_ollama_models", [])
        available_for_domain = [m for m in preferred if m in available]
        best_model = router.get_best_ollama_model(preferred) if available else None
        
        domain_mapping[category] = {
            "preferred_models": preferred,
            "available_models": available_for_domain,
            "best_available": best_model,
            "openrouter_fallback": cfg.get("openrouter_model", "N/A"),
            "provider_mode": cfg.get("provider", "auto"),
        }
    
    return {
        "ollama_status": "connected" if router._ollama_available else "disconnected",
        "available_ollama_models": available,
        "total_models": len(available),
        "senator_domain_mapping": domain_mapping,
        "routing_strategy": "Per-Senator OpenRouter keys + Ollama auto-detection",
    }
```

**Pitfall**: Ensure `import uuid` is included in `moe/router.py`; missing import causes `NameError: name 'uuid' is not defined` when generating conversation IDs.

## 10. MoE Router Standalone Deployment (from `/root/arsify-moe-router/`)

When deploying MoE Router as a standalone service (not integrated into Arsify-core repo):

### Prerequisites Check
```bash
# Check Ollama service
systemctl status ollama
ollama list  # Should show: phi3:mini, llama3.2:3b, qwen2.5-coder:3b

# If Ollama not running
systemctl start ollama
systemctl enable ollama

# Pull required models (~6GB total, ~10-15 min on CPU)
ollama pull phi3:mini
ollama pull llama3.2:3b
ollama pull qwen2.5-coder:3b
```

### Deploy to `/opt/arsify/`
```bash
# 1. Create service user
id arsify 2>/dev/null || useradd -r -s /bin/false -m -d /home/arsify arsify

# 2. Copy files
mkdir -p /opt/arsify
cp -r /root/arsify-moe-router/arsify/app /opt/arsify/
cp -r /root/arsify-moe-router/arsify/static /opt/arsify/
cp /root/arsify-moe-router/arsify/requirements.txt /opt/arsify/

# 3. Setup Python venv
cd /opt/arsify
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

# 4. Set permissions
chown -R arsify:arsify /opt/arsify
chown -R arsify:arsify /home/arsify
```

### Systemd Service Setup
```bash
# Copy service file
cp /root/arsify-moe-router/arsify/scripts/arsify.service /etc/systemd/system/arsify.service

# Edit port if 8000/8001 occupied (check: ss -tlnp | grep -E "8000|8001")
# Edit /etc/systemd/system/arsify.service:
#   Environment="ARSIFY_PORT=8002"
#   ExecStart=... --port 8002

sed -i 's/ARSIFY_PORT=8000/ARSIFY_PORT=8002/' /etc/systemd/system/arsify.service
sed -i 's/--port 8000/--port 8002/' /etc/systemd/system/arsify.service

# Enable and start
systemctl daemon-reload
systemctl enable arsify
systemctl start arsify
sleep 3
systemctl status arsify --no-pager | head -15
```

### Verification
```bash
# Health check
curl -s http://localhost:8002/health
# Expected: {"status":"online","ollama":"connected","models":["phi3:mini",...]}

# List models
curl -s http://localhost:8002/models | jq .

# Test chat (may take 30-60s on CPU)
# NOTE: MoE Router uses /chat endpoint (POST), NOT OpenAI /v1/chat/completions
timeout 60 curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Halo, siapa kamu?", "model": "phi3:mini", "max_tokens": 50}'
```

### Nginx Reverse Proxy for chat.upshalter.com
```bash
# Update Nginx to proxy to MoE Router port 8002
sudo sed -i 's/127.0.0.1:8000/127.0.0.1:8002/g' /etc/nginx/sites-available/chat.upshalter.com

# Verify config
sudo nginx -t && sudo systemctl reload nginx

# Test public endpoint
curl -sk https://chat.upshalter.com/health
# Expected: same as localhost:8002/health
```

### Updated Pitfalls (2026-05-08)
- **Ollama CPU Timeout**: CPU-only VPS causes 30-60s+ inference delays, swap pressure (3.8/4G used). Use smaller models (phi3:mini) or switch to OpenRouter API.
- **Endpoint Mismatch**: MoE Router does NOT support OpenAI `/v1/chat/completions` — use `/chat` instead.
- **Nginx Port Sync**: Ensure `chat.upshalter.com` Nginx config matches MoE Router port (8002, not 8000/8001).

### Debugging Service Failures
```bash
# Check logs
journalctl -u arsify -n 50 --no-pager

# Check port conflicts
ss -tlnp | grep -E "8000|8001|8002"

# Test Ollama directly
curl -s http://localhost:11434/api/tags | jq .
timeout 30 ollama run phi3:mini "hello"

# Check service user can run app
runuser -u arsify -- /opt/arsify/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8002
```

## Pitfalls
- Always use `git status` before committing to stage only intended changes
- Verify path fixes by grepping for old hardcoded strings post-change
- Ensure systemd service uses correct `SCRIPT_DIR` and `OPENROUTER_API_KEY` values
- **Rebranding**: After replacing creator references, do a full case-insensitive grep for remaining "hermes" (or original creator name) references
- **Sensitive data**: Never commit real `.env` files; verify `.gitignore` includes `.env`, `.env.local`, and any secret files
- **Notifications**: When replacing CLI calls with curl Telegram notifications, ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in env or .env file
- **Git History Cleanup**: Always backup the repo before running git filter-repo or force pushing. These operations are irreversible.
- **MoE Integration**: Always test MoE Router startup (`bash /root/upshalter-scripts/moe-router-start.sh`) before running Senator cycles; verify Ollama models are installed (`ollama list`).
- **MoE Router Import**: Ensure `import uuid` is included in `moe/router.py`; missing import causes `NameError: name 'uuid' is not defined` when generating conversation IDs.
- **OpenRouter 402 Errors**: Use Ollama as primary model source for Senators; only use OpenRouter for Kurator fallback. New OpenRouter key is stored in `moe/config.py`.
- **Git Push After Merge**: After merging unrelated histories with `--allow-unrelated-histories`, use `git push -u origin main` to set upstream for the first push.
- **MoE Router Port Conflict**: Check if port 8000 is already in use before starting MoE Router (`ss -tlnp | grep 8000`); verify FastAPI and uvicorn are installed (`pip3 install fastapi uvicorn`).
- **Port Conflict Resolution**: If 8000 occupied (common: Hermes orchestrator), try 8001, then 8002. Always `ss -tlnp | grep PORT` before selecting. Update both `Environment="ARSIFY_PORT=XXXX"` and `ExecStart=... --port XXXX` in service file.
- **Ollama on CPU**: Inference is slow (~30-60s for 3B models). Use `/chat/stream` endpoint for better UX. Consider smaller model (qwen2.5:1.5b) for faster responses.
- **Service User**: Ensure `arsify` user exists and owns `/opt/arsify/`. Service fails with "permission denied" if wrong user.
- **Ollama Service**: Must be running BEFORE starting arsify service. Use `After=ollama.service` and `Wants=ollama.service` in systemd unit (already in template).

## References
- `templates/.env.example`: Reusable .env template with all optional/required vars (includes UPSHALTER_* and Telegram vars)
- `templates/arsify-senator.service`: Systemd service unit template
- `templates/arsify-senator.timer`: Systemd timer template for 6-hour cycles
- `templates/logrotate-arsify`: Logrotate config template for Arsify logs
- `scripts/clean-git-history.sh`: Automated git history sanitization using git-filter-repo
- See `references/` for Arsify Core architecture docs (ARCHITECTURE.md, DEPLOYMENT.md)
- `references/arsify-moe-v5-workflow.md`: Detailed workflow for MoE v5 with per-Senator keys and Arsify Detection (auto Ollama scan)
