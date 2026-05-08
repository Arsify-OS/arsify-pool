# Docker Container Investigation Patterns

## Investigating Unknown Containers

When you find a running container that doesn't appear in `docker compose ls`, use these steps to trace its origin:

### 1. Check Container Details
```bash
docker inspect <container_name> --format '{{.Name}} {{.Config.Image}} {{.Config.Labels}}'
```

Look for:
- Image name pattern (e.g., `ghcr.io/hostinger/*` indicates Hostinger VPS Catalog deployment)
- Labels that may contain `org.opencontainers.image.source` or `com.docker.compose.project`

### 2. Check Port Mapping Discrepancies
```bash
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

Compare with docker-compose.yml:
- Dynamic ports (e.g., `0.0.0.0:32776->4860/tcp`) vs static ports defined in compose files
- Container names may not match service names

### 3. Trace Deployment History
```bash
grep -r "<container_name>\|docker compose" /root/.local/share/tirith/log.jsonl 2>/dev/null | head -20
```

Look for:
- `COMPOSE_PROJECT_NAME` settings
- `docker compose up -d` commands in specific directories
- Directory paths where compose files were executed

### 4. Verify Against Local Compose Files
```bash
find /root -name "docker-compose.yml" -o -name "docker-compose.yaml" 2>/dev/null
```

Check if running containers match services defined in those files.

### 5. Hostinger VPS Specifics
Containers deployed via Hostinger panel:
- Image pattern: `ghcr.io/hostinger/hvps-*` 
- Size: Very large (8.4GB+ for Hermes Agent images)
- Management: Outside local docker compose, handled by Hostinger panel
- Won't appear in: `docker compose ls` output
- May have different internal ports (e.g., 4860 instead of standard 8642)

## Cleanup Decision Tree

1. Is container running critical workload? → Keep it
2. Is provider Ollama? → Check `grep provider ~/.hermes/config.yaml`
3. Is container from Hostinger? → User must decide (panel-managed)
4. Unused test containers? → Safe to remove
5. Space savings? → `docker system df` to check before/after