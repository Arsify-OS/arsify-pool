# Auxiliary Model Debug Reference

## Session: 2026-05-06

### Problem
`Auxiliary title generation failed: HTTP 401: User not found.` appeared on CLI. Compression threshold warning also appeared.

### Root Cause Analysis

1. **401 "User not found"**: Model `openai/gpt-4o-mini` configured in `auxiliary.title_generation.model` returns HTTP 401 on OpenRouter. The API key is valid (confirmed with `/api/v1/models`), but the `openai/` prefixed model has stricter access requirements on OpenRouter. The `openrouter/` prefix models work correctly.

2. **Compression threshold mismatch**: The auxiliary compression model (`openai/gpt-4o-mini`) has 128K context, but `compression.threshold: 0.48` of the main model's ~503K context = ~241K tokens, which exceeds the auxiliary model's capacity. Hermes auto-lowers to 128K with a warning.

### Debug Commands Used

```bash
# Check auxiliary task config
python3 -c "
from hermes_cli.config import load_config
config = load_config()
aux = config.get('auxiliary', {})
for task in ['title_generation', 'compression', 'session_search', 'vision']:
    print(f'{task}:', dict(aux.get(task, {})))
"

# Test OpenRouter API key validity
curl -s "https://openrouter.ai/api/v1/auth/key" -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Test specific model on OpenRouter
curl -s "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"test"}],"max_tokens":10}'

# Test openrouter/ prefix model
curl -s "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openrouter/owl-alpha","messages":[{"role":"user","content":"test"}],"max_tokens":10}'

# Check which auxiliary tasks are failing
grep "auxiliary\|title_generation\|compression.*failed" ~/.hermes/logs/errors.log | tail -20

# Check gateway process
ps aux | grep "hermes_cli.main gateway" | grep -v grep
```

### Applied Fix

Changed `~/.hermes/config.yaml`:
```yaml
# BEFORE (broken):
auxiliary:
  title_generation:
    provider: openrouter
    model: openai/gpt-4o-mini
    api_key: sk-or-v1-...  # explicit key
  compression:
    model: openai/gpt-4o-mini
  session_search:
    model: openai/gpt-4o-mini

compression:
  threshold: 0.48
  target_ratio: 0.2

# AFTER (working):
auxiliary:
  title_generation:
    provider: openrouter
    model: openrouter/owl-alpha
    api_key: ""  # empty = use OPENROUTER_API_KEY env var
  compression:
    provider: openrouter
    model: openrouter/owl-alpha
    api_key: ""
  session_search:
    provider: openrouter
    model: openrouter/owl-alpha
    api_key: ""

compression:
  threshold: 0.75
  target_ratio: 0.3
```

Then restarted gateway:
```bash
terminal(background=true, command="cd /root && /usr/local/lib/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace")
```

### Key Takeaway
- **Never use `openai/` prefixed models in auxiliary config on OpenRouter** — use `openrouter/<model>` prefix
- `api_key: ""` (empty string) makes the client use the `OPENROUTER_API_KEY` environment variable
- Gateway restart is required for auxiliary config changes to take effect
- Compression threshold should be 0.6-0.75 to avoid premature compression
