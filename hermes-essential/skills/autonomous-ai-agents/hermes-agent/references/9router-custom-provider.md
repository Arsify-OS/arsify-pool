# 9Router Custom Provider Setup for Hermes Agent

9Router is a local/remote AI gateway with OpenAI-compatible REST API, supporting multiple providers (including Claude Sonnet 4.5 as `kr/claude-sonnet-4.5`). This guide covers full configuration for Hermes Agent main + auxiliary tasks.

## Prerequisites
- 9Router running and accessible (e.g., `http://76.13.194.136:20128`)
- 9Router API key (NINEROUTER_KEY, e.g., `S`)
- Hermes Agent installed

## Step 1: Verify 9Router Health
```bash
curl http://<9router-host>:20128/api/health
# Expected output: {"ok":true}
```

## Step 2: List Available Models
```bash
curl -H "Authorization: Bearer <key>" http://<9router-host>:20128/v1/models | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data']]"
# Available Claude models: kr/claude-sonnet-4.5, kr/claude-haiku-4.5
# Note: gpt5.5 is NOT available on 9Router
```

## Step 3: Configure Hermes Custom Provider
```bash
# Remove trailing /dashboard if present in base_url
hermes config set custom_providers.0.name "76.13.194.136:20128"
hermes config set custom_providers.0.base_url "http://76.13.194.136:20128"
hermes config set custom_providers.0.api_key "S"
```

## Step 4: Set Main Model
```bash
hermes config set model.default "kr/claude-sonnet-4.5"
hermes config set model.provider "custom:76.13.194.136:20128"
hermes config set model.api_key "S"
hermes config set model.base_url ""  # Clear old base_url
```

## Step 5: Configure Auxiliary Tasks (Critical!)
Auxiliary tasks (compression, title_generation, session_search) do NOT inherit main model's api_key. Set explicitly:
```bash
# Compression
hermes config set auxiliary.compression.provider "custom:76.13.194.136:20128"
hermes config set auxiliary.compression.model "kr/claude-sonnet-4.5"
hermes config set auxiliary.compression.api_key "S"

# Title Generation
hermes config set auxiliary.title_generation.provider "custom:76.13.194.136:20128"
hermes config set auxiliary.title_generation.model "kr/claude-sonnet-4.5"
hermes config set auxiliary.title_generation.api_key "S"

# Session Search
hermes config set auxiliary.session_search.provider "custom:76.13.194.136:20128"
hermes config set auxiliary.session_search.model "kr/claude-sonnet-4.5"
hermes config set auxiliary.session_search.api_key "S"
```

## Step 6: Restart Gateway
```bash
hermes gateway stop
hermes gateway run &  # For production, use PM2/systemd
```

## Step 7: Verify Setup
```bash
# Test 9Router model access
curl -s -X POST http://76.13.194.136:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer S" \
  -d '{"model":"kr/claude-sonnet-4.5","messages":[{"role":"user","content":"test"}],"max_tokens":10}'
```

## Pitfalls
1. **9Router base_url must NOT include `/dashboard`** (common mistake from Docker setups)
2. **Auxiliary tasks require explicit api_key** even if main model has it set
3. **Model IDs on 9Router use `kr/` prefix** for Claude models (e.g., `kr/claude-sonnet-4.5`)
4. **API key rate limits**: 9Router keys may have monthly request limits (wait 2m for reset if hitting 402 errors)
5. **gpt5.5 is unavailable**: Only Claude 4.5 models and other `kr/` prefixed models are available for now