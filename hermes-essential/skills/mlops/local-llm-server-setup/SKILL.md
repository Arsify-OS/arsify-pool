---
name: local-llm-server-setup
description: Set up local LLM servers (Ollama, llama.cpp) on headless VPS/servers, configure for CPU-only mode, handle OOM with swap, and integrate with Hermes Agent or other tools.
trigger:
  - "install ollama"
  - "local LLM server"
  - "LM Studio replacement"
  - "run LLM on headless server"
  - "CPU-only LLM"
  - "ollama docker container access"
---

# Local LLM Server Setup

This skill covers setting up local LLM inference servers on headless VPS or servers without GPU, focusing on Ollama as the primary tool.

## When to Use Ollama vs Alternatives

| Tool | Best For | CPU Performance | Setup Complexity |
|------|----------|-----------------|-----------------|
| **Ollama** | Quick setup, API-compatible with OpenAI, good model library | Moderate (Q4 quantization) | Low |
| **llama.cpp** | Maximum control, custom builds, research | High (with optimization) | High |
| **vLLM** | High-throughput serving, multi-GPU | N/A (GPU required) | Medium |

For headless VPS with CPU-only: **Use Ollama**.

## Prerequisites Check

```bash
# Check CPU, RAM, disk
lscpu | grep -E "Model name|CPU\(s\)|Thread"
free -h
df -h /
```

Minimum for small models (3-7B Q4):
- 2+ CPU cores
- 6GB+ RAM (with swap)
- 5GB+ disk space

## Installing Ollama on Headless VPS

### Step 1: Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Fix Permission Issues

Ollama may fail to start due to permission errors on `/usr/share/ollama`:

```bash
mkdir -p /usr/share/ollama
chown -R ollama:ollama /usr/share/ollama
chmod 755 /usr/share/ollama
systemctl restart ollama
```

### Step 3: Configure for Network Access

By default, Ollama binds to `127.0.0.1`. For container/host access:

```bash
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
systemctl daemon-reload
systemctl restart ollama
```

Verify: `systemctl status ollama` should show `Listening on [::]:11434` or `0.0.0.0:11434`.

## Preventing OOM Kills on Low-Memory VPS

Ollama loading 2-3GB models can trigger OOM killer on 8GB RAM VPS. Fix by adding swap:

### Create Swap File (4GB example)

```bash
dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

### Make Swap Permanent

```bash
echo '/swapfile none swap sw 0 0' >> /etc/fstab
mount -a  # test fstab
swapon --show  # verify
```

## Pulling Models

For CPU-only VPS, use quantized models:

```bash
ollama pull phi3:mini    # 3.8B Q4, ~2.2GB (good for 8GB RAM)
ollama pull llama3.2:1b  # 1B Q4, ~1.3GB (lightweight)
```

Test: `ollama run phi3:mini "Hello"`

## Docker Container Accessing Host Ollama

### Method: host.docker.internal (Recommended)

When running Docker container, add `--add-host`:

```bash
docker run -d \
  --name hermes-agent \
  --add-host=host.docker.internal:host-gateway \
  -p 32776:4860 \
  ghcr.io/hostinger/hvps-hermes-agent:latest
```

### Configure Container to Use Host Ollama

In the container's `~/.hermes/config.yaml`:

```yaml
model:
  default: phi3:mini
  provider: ollama
  base_url: http://host.docker.internal:11434/v1
  api_mode: chat_completions
```

The `host.docker.internal` resolves to the host's Docker bridge IP (usually `172.17.0.1`).

### Verify Connectivity from Container

```bash
docker exec <container-name> curl -s http://host.docker.internal:11434/api/tags
```

## Pitfalls

1. **OOM Kills on 7.8GB VPS**: Ollama phi3:mini uses ~3.6GB RAM. On a 7.8GB VPS with multiple containers, this causes swapping and timeouts. **Fix**: Stop unnecessary containers first (`docker stop hermes-gamedev hermes-loyx ...`), then restart Ollama. Verify with `free -h` — need at least 2.5GB available. If still tight, increase swap to 8-16GB.

2. **Ollama Timeout on CPU**: phi3:mini on CPU takes ~20s for short prompts, 60s+ for long Senator prompts. Default `LLM_TIMEOUT_READ=50` is too low. **Fix**: Set `LLM_TIMEOUT_READ=300` in BOTH `/opt/hermes-cognitive/.env` AND the worker service environment block in `docker-compose.yml` (env file vars don't propagate to worker). Verify: `docker exec hermes-worker python3 -c "from src.models.openrouter_client import TIMEOUT; print(TIMEOUT.read)"` → should show `300.0`.

3. **Ollama Model Name Mismatch**: When `OPENROUTER_URL` points to Ollama (port 11434), `MODEL_MAP` and `FREE_MODEL_MAP` in `openrouter_client.py` MUST use Ollama model names (`phi3:mini`), not OpenRouter IDs. Use auto-detection: `_is_ollama = "11434" in _llm_url`. **Critical**: Define `_is_ollama` BEFORE `MODEL_MAP` to avoid `NameError`.

4. **Permission Denied**: Ollama service runs as `ollama` user. Fix `/usr/share/ollama` ownership.

5. **IPv6 Only**: If `netstat` shows `tcp6 :::11434` but no `tcp 0.0.0.0:11434`, it's still accessible via IPv4 on Linux (dual-stack). Test with `curl http://<IP>:11434`.

6. **Container DNS**: `host.docker.internal` needs `--add-host=host.docker.internal:host-gateway` on `docker run`. Without it, the container can't resolve the hostname.

7. **Model Not Found**: Ensure model is pulled on host before configuring container. Run `ollama list` to verify.

8. **LM Studio NOT Suitable for Headless VPS**: LM Studio (lmstudio.ai) is a GUI application. The `lms` CLI ships with the desktop app and has no standalone Linux server binary. The GitHub repo `lmstudio-ai/lms` is private. **Do not recommend LM Studio for headless VPS.** Use Ollama or llama.cpp instead.

## Verification Steps

```bash
# 1. Ollama service running
systemctl is-active ollama

# 2. API accessible
curl -s http://<host-ip>:11434/api/tags | jq -r '.models[].name'

# 3. Model generates text
echo "Say hello" | ollama run phi3:mini

# 4. Container can access (from inside container)
curl -s http://host.docker.internal:11434/api/tags

# 5. Swap active
swapon --show
```

10. **Ollama on 2-Core CPU-Only VPS Is Not Viable for Production Inference** — Even small models (qwen2.5:1.5b @ 1GB, phi3:mini @ 2GB) take 39s to load + >60s to generate text on a 2-core AMD EPYC CPU with 7.8GB RAM. This exceeds ALL reasonable client timeouts (20s, 60s, 90s). The Ollama runner process hits 100-172% CPU during inference. **Do NOT rely on Ollama as primary LLM endpoint on CPU-only VPS.** Use cloud-backed APIs (OpenRouter via Hermes API :8100) as primary, Ollama only as offline last resort. Verified 8 Mei 2026 on production VPS.

9. **Ollama JSON Output Requires Strict Prompts**: qwen2.5:1.5b on Ollama frequently wraps JSON in markdown code fences. Use this pattern for reliable JSON: `"Output ONLY valid JSON — no markdown, no code fences, no explanation. Schema: {...}\nOutput ONLY the JSON:"`. Verified 100% success rate with this pattern.

## References

- Ollama official install: https://ollama.com/download/linux
- Model library: https://ollama.com/library
- Hermes Agent config: `~/.hermes/config.yaml`
- Session log with exact commands: `references/vps-ollama-setup-log.md`
