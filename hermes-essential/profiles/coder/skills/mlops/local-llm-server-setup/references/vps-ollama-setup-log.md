# VPS Ollama Setup - Session Reference

## Environment (this session)
- VPS: AMD EPYC 9355P (2 vCPU), 7.8GB RAM, No GPU, Ubuntu 24.04.4 LTS
- Disk: 96GB (79GB free)
- Docker: Docker bridge IP 172.17.0.1, container `agent-hermes-ceo`

## Commands Used

### Ollama Install & Fix
```bash
curl -fsSL https://ollama.com/install.sh | sh
mkdir -p /usr/share/ollama
chown -R ollama:ollama /usr/share/ollama
chmod 755 /usr/share/ollama
systemctl restart ollama
```

### Swap Creation (4GB)
```bash
dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### Ollama Network Config
```bash
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
systemctl daemon-reload && systemctl restart ollama
```

### Docker Container with Host Access
```bash
docker run -d \
  --name agent-hermes-ceo \
  --add-host=host.docker.internal:host-gateway \
  -p 32776:4860 \
  ghcr.io/hostinger/hvps-hermes-agent:latest
```

### Container Config (config.yaml)
```yaml
model:
  default: phi3:mini
  provider: ollama
  base_url: http://host.docker.internal:11434/v1
  api_mode: chat_completions
```

## Pitfalls Encountered

1. **OOM Killer**: Ollama killed when loading 2.2GB model on 8GB RAM → Fixed with 4GB swap
2. **Permission Denied**: Ollama couldn't create `/usr/share/ollama` → Fixed ownership
3. **Container can't reach host**: Needed `--add-host=host.docker.internal:host-gateway`
4. **Symlink mismatch**: Hermes Workspace build output in `dist/server/` but start script expects `.output/server/index.mjs`

## Verification
```bash
# Ollama running
systemctl is-active ollama
curl -s http://172.17.0.1:11434/api/tags

# Swap active
swapon --show

# Container access
docker exec agent-hermes-ceo curl -s http://host.docker.internal:11434/api/tags
```
