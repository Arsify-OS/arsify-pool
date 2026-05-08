# 9Router Supported Models (as of 2026-05-04)
9Router runs at `http://76.13.194.136:20128` (VPS). Check available models via:
```bash
curl -s -H "Authorization: Bearer S" http://76.13.194.136:20128/v1/models | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin).get('data',[])]"
```

## Available Claude/Sonnet Models
- `kr/claude-sonnet-4.5` ✅ Available
- `kr/claude-haiku-4.5` ✅ Available

## Unavailable Models
- `gpt5.5` / `gpt-5` ❌ Not available on this 9Router instance
- `google/gemini-2.0-flash-001` ❌ Not routed via this 9Router

## Using 9Router Models in Hermes Agent
1. Add 9Router as custom provider in `~/.hermes/config.yaml`:
```yaml
custom_providers:
- name: 9router
  base_url: http://76.13.194.136:20128
  api_key: S
```
2. Set model: `hermes config set model.default kr/claude-sonnet-4.5`
3. Set provider: `hermes config set model.provider "custom:9router"`
```