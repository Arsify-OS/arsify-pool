# Senator Pentahelix Debugging Reference

## Quick Diagnosis Commands

```bash
# Check all senator containers
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}" | grep senator

# Check logs for a specific senator
docker logs --tail 50 senator-pemerintah 2>&1

# Check restart count
docker inspect senator-pemerintah --format '{{.RestartCount}}'

# Check OpenRouter credit
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $(cat /root/.hermes/.openrouter_key)" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Free tier: {d[\"data\"][\"is_free_tier\"]}, Usage: {d[\"data\"][\"usage\"]}')"
```

## Common Failure Patterns

### Pattern 1: Restart Loop (Container Never Healthy)
**Symptoms**: "Up X seconds (health: starting)" forever
**Root causes**:
1. Healthcheck typo: `$HEALTHBEAT` vs `$HEARTBEAT`
2. Pipeline `sys.exit(1)` on LLM failure
3. Heartbeat file not created

### Pattern 2: LLM 402 Errors
**Root causes**:
- Out of credit (check via API)
- Invalid model name (e.g., `openrouter/owl-alpha` doesn't exist)
- Free tier rate limits

**Free models** (verified 2026-05-07):
- `meta-llama/llama-3.3-70b-instruct:free` (64K ctx) — recommended
- `meta-llama/llama-3.2-3b-instruct:free` (128K ctx)
- `nousresearch/hermes-3-llama-3.1-405b:free` (131K ctx)

### Pattern 3: Container Read-Only Volume
Cannot `docker exec cp` into `:ro` mounted volumes. Must rebuild image.

### Pattern 4: Scraping Works but Draft Missing
Pipeline crashed at LLM step. Replace `sys.exit(1)` with fallback draft.

## Rebuild Procedure

```bash
cd /root/senator-pentahelix
docker compose build --no-cache
docker compose down
docker compose up -d
```

## File Locations

| File | Path |
|------|------|
| Docker Compose | `/root/senator-pentahelix/docker-compose.yml` |
| Healthcheck | `/root/senator-pentahelix/healthcheck.sh` |
| Factory Pipeline | `/root/.hermes/skills/devops/hermes-editorial/scripts/senator-factory-pipeline.py` |
| OpenRouter key | `/root/.hermes/.openrouter_key` |
