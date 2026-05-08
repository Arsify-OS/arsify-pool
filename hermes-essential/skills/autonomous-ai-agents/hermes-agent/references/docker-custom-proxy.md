# Docker Container Configuration with Custom Model Proxy

## Problem

When running Hermes Agent in Docker and routing through a custom model proxy/router (e.g., 9router, LiteLLM, custom OpenAI-compatible endpoint) running on the host machine, several configuration pitfalls can block successful model access.

## Solution: Complete Configuration Checklist

### 1. Config File Path (Critical)

**Pitfall:** Hermes Agent in Docker reads config from `/opt/data/config.yaml`, NOT `/root/.hermes/config.yaml`.

```bash
# Wrong - config ignored
docker run -v /tmp/config.yaml:/root/.hermes/config.yaml ...

# Correct - config loaded
docker run -v /tmp/config.yaml:/opt/data/config.yaml:ro ...
```

Verify with:
```bash
docker exec <container> hermes config show | grep "Config:"
# Should show: Config: /opt/data/config.yaml
```

### 2. Environment File Path

Similarly, `.env` must be mounted to `/opt/data/.env`:

```bash
docker run \
  -v /tmp/gamedev-config.yaml:/opt/data/config.yaml:ro \
  -v /tmp/gamedev-env:/opt/data/.env:ro \
  ...
```

### 3. Provider Configuration

**Pitfall:** Provider "openai" with custom base_url is not recognized. Use provider "custom" instead.

```yaml
# Wrong - fails with "Unknown provider 'openai'"
model:
  default: "Hermes-Gamedev"
  provider: "openai"
  base_url: "http://host.docker.internal:20128/v1"

# Correct
model:
  default: "Hermes-Gamedev"
  provider: "custom"
  base_url: "http://host.docker.internal:20128/v1"
  context_length: 128000
```

### 4. Context Window Minimum

**Pitfall:** Hermes Agent requires minimum 64K context window. Default 32K causes initialization failure.

```yaml
model:
  context_length: 128000  # Must be >= 64000
```

Error if too low:
```
Failed to initialize agent: Model X has a context window of 32,000 tokens,
which is below the minimum 64,000 required by Hermes Agent.
```

### 5. Host Networking for Custom Proxy

**Pitfall:** Docker containers cannot reach `localhost` or `127.0.0.1` on the host by default.

```bash
# Add host gateway mapping
docker run \
  --add-host host.docker.internal:host-gateway \
  ...
```

Then use `host.docker.internal` in base_url:
```yaml
model:
  base_url: "http://host.docker.internal:20128/v1"
```

### 6. API Key Requirement

Even with custom provider, Hermes checks for an API key. Provide a dummy key:

```bash
# In /tmp/gamedev-env
OPENAI_API_KEY=sk-dummy-key-for-custom-provider
```

### 7. Gateway Command for Containers

**Pitfall:** `hermes gateway start` causes restart loops in containers (it's for systemd services).

```bash
# Wrong - restart loop
CMD ["hermes", "gateway", "start"]

# Correct - runs as main process
CMD ["hermes", "gateway", "run"]
```

## Complete Working Example

### Config File (`/tmp/gamedev-config.yaml`)

```yaml
model:
  default: "Hermes-Gamedev"
  provider: "custom"
  base_url: "http://host.docker.internal:20128/v1"
  context_length: 128000
agent:
  max_turns: 90
  gateway_timeout: 1800
terminal:
  backend: local
  cwd: /workspace
  persistent_shell: true
toolsets:
- file
- terminal
- web
gateway:
  host: 0.0.0.0
  port: 8642
memory:
  memory_enabled: true
  user_profile_enabled: true
display:
  compact: false
  streaming: false
delegation:
  max_spawn_depth: 1
  max_concurrent_children: 2
```

### Environment File (`/tmp/gamedev-env`)

```bash
OPENAI_API_KEY=sk-dummy-key-for-custom-provider
```

### Docker Run Command

```bash
docker run -d \
  --name hermes-gamedev \
  --add-host host.docker.internal:host-gateway \
  -p 8644:8642 \
  -v /root/regrow-up-world-dev:/workspace \
  -v /tmp/gamedev-config.yaml:/opt/data/config.yaml:ro \
  -v /tmp/gamedev-env:/opt/data/.env:ro \
  nousresearch/hermes-agent:latest \
  hermes gateway run
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  hermes-gamedev:
    image: nousresearch/hermes-agent:latest
    container_name: hermes-gamedev
    command: ["hermes", "gateway", "run"]
    ports:
      - "8644:8642"
    volumes:
      - /root/regrow-up-world-dev:/workspace
      - /tmp/gamedev-config.yaml:/opt/data/config.yaml:ro
      - /tmp/gamedev-env:/opt/data/.env:ro
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
```

## Verification Steps

1. **Check config path:**
   ```bash
   docker exec hermes-gamedev hermes config show | grep "Config:"
   # Should show: /opt/data/config.yaml
   ```

2. **Check model configuration:**
   ```bash
   docker exec hermes-gamedev hermes config show | grep -A 5 "Model:"
   # Should show: Hermes-Gamedev, custom provider, correct base_url
   ```

3. **Test model access:**
   ```bash
   docker exec hermes-gamedev /opt/hermes/.venv/bin/hermes chat -q "Say hello"
   # Should get response, not "No inference provider configured"
   ```

4. **Check logs:**
   ```bash
   docker logs hermes-gamedev --tail 50
   # Should NOT show "Unknown provider" or "context window" errors
   ```

## Troubleshooting

### "No inference provider configured"

- Config file not mounted to `/opt/data/config.yaml`
- `.env` file not mounted to `/opt/data/.env`
- Missing `OPENAI_API_KEY` in `.env`

### "Unknown provider 'openai'"

- Change `provider: "openai"` to `provider: "custom"` in config.yaml

### "Context window below minimum 64,000"

- Set `context_length: 128000` in config.yaml

### "Connection refused" to proxy

- Missing `--add-host host.docker.internal:host-gateway`
- Proxy not running on host
- Wrong port in `base_url`

### Container restart loop

- Using `hermes gateway start` instead of `hermes gateway run`
- Check logs: `docker logs hermes-gamedev`

## Model Combo Routing

If your custom proxy supports model combos with fallback (e.g., 9router with round-robin):

```yaml
model:
  default: "Hermes-Gamedev"  # Combo name that routes to multiple models
  provider: "custom"
  base_url: "http://host.docker.internal:20128/v1"
  context_length: 128000
```

The proxy handles fallback automatically. Hermes sees a single model name.

Example combo routing:
- `Hermes-Gamedev` → round-robin to:
  - `kr/claude-sonnet-4.5`
  - `kr/claude-haiku-4.5`
  - `kr/qwen3-coder-next`
  - +3 more models

## Session: 2026-05-04

Discovered during multi-agent game development setup. GameDev container initially failed with:
1. Config ignored (wrong path)
2. "Unknown provider 'openai'" (should be "custom")
3. Context window error (32K < 64K minimum)
4. "No inference provider configured" (missing .env mount)

Final working config achieved after ~1 hour troubleshooting. Test task succeeded:
```
Query: "SUCCESS TEST: Say hello and confirm you are working with Hermes-Gamedev model"
Response: "Hello! I'm Kiro, and I can confirm I'm working with the Hermes-Gamedev model."
Duration: 7s
```
