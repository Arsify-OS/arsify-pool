# Auxiliary Model Configuration — Lessons Learned

## Problem Pattern

Hermes Agent auxiliary tasks (compression, title_generation, session_search, vision, web_extract) fail with:
- HTTP 401 "User not found"
- HTTP 402 "Insufficient credits" / "Monthly request count limit"
- "No LLM provider configured for task=X provider=auto"
- Silent failures (compression drops turns without summary)

## Root Causes

### 1. `openai/` prefixed models on OpenRouter
Models like `openai/gpt-4o-mini` have stricter access requirements on OpenRouter. Even with a valid API key, they may return 401. **Always use `openrouter/<model>` prefix** for auxiliary tasks.

### 2. Custom provider rate limits
Custom providers (e.g., Kiro at `76.13.194.136:20128`) may have monthly request caps. When hit, they return HTTP 402 with `MONTHLY_REQUEST_COUNT`. These providers are suitable for main model but risky for auxiliary tasks that fire frequently.

### 3. Empty `api_key: ''` overrides env vars
Setting `api_key: ''` (empty string) in any `auxiliary.*` section prevents Hermes from falling back to `OPENROUTER_API_KEY` env var. **Remove empty api_key lines entirely.**

### 4. Compression threshold vs context window mismatch
If the auxiliary compression model has a smaller context window than the main model's threshold, Hermes auto-lowers the threshold with a warning. Fix: raise threshold to 0.75+.

## Working Configuration (as of 2026-05-07)

All auxiliary tasks use the same model as the main model for consistency:

```yaml
model:
  default: openrouter/owl-alpha
  provider: openrouter
  base_url: https://openrouter.ai/api/v1

auxiliary:
  vision:
    provider: openrouter
    model: openrouter/owl-alpha
  web_extract:
    provider: openrouter
    model: openrouter/owl-alpha
  compression:
    provider: openrouter
    model: openrouter/owl-alpha
  session_search:
    provider: openrouter
    model: openrouter/owl-alpha
  title_generation:
    provider: openrouter
    model: openrouter/owl-alpha
```

## TTS Configuration

- **Use `edge` provider** (free, no API key, default voice: `en-US-AriaNeural`)
- **Remove `gpt-4o-mini-tts`** from `tts.openai.model` — it's a paid OpenAI model
- When `tts.provider: edge`, the `tts.openai` section is inactive but can remain as fallback

## Commands to Apply

```bash
# Set all auxiliary tasks to use openrouter/owl-alpha
hermes config set auxiliary.compression.provider openrouter
hermes config set auxiliary.compression.model openrouter/owl-alpha
hermes config set auxiliary.session_search.provider openrouter
hermes config set auxiliary.session_search.model openrouter/owl-alpha
hermes config set auxiliary.title_generation.provider openrouter
hermes config set auxiliary.title_generation.model openrouter/owl-alpha
hermes config set auxiliary.vision.provider openrouter
hermes config set auxiliary.vision.model openrouter/owl-alpha
hermes config set auxiliary.web_extract.provider openrouter
hermes config set auxiliary.web_extract.model openrouter/owl-alpha

# Ensure TTS uses edge (free)
hermes config set tts.provider edge

# Remove gpt-4o-mini-tts from config.yaml tts.openai section
```

## Pitfalls

- **Never use `kill -HUP <pid>`** to reload gateway config — it kills the process. Restart fresh.
- **Config changes require gateway restart** to take effect for auxiliary tasks.
- **Removing a model entirely**: When the user asks to remove a model like `gpt-4o-mini` from the entire system, check ALL locations: auxiliary tasks, TTS config, compression, and any hardcoded references — not just the main model.
- **Docker containers** mount `/opt/data/` not `~/.hermes/`. Use `docker exec` to modify container config.
