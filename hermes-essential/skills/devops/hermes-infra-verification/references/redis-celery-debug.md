# Redis + Celery Debug Pattern (PRD-001 Lessons)

## Problem Pattern: Cascading Celery Failures via Redis Auth

### Root Cause Identified (2026-05-07)
Redis password mismatch across multiple config files caused ALL Celery tasks to fail silently:
- `.env` had `REDIS_PASSWORD=hermes-redis-secret-2026`
- `docker-compose.yml` had password in `CELERY_BROKER_URL`
- `celery_app.py` had password in `broker_url` and `result_backend`
- But Redis was running WITHOUT password (or with different password)

This caused: `Error 111 connecting to redis...` or silent task failures.

### Debug Sequence (One-by-One Verification)

1. **Check Redis actual config**:
   ```bash
   redis-cli CONFIG GET requirepass
   redis-cli CONFIG GET bind
   ```

2. **Test Redis connectivity from container**:
   ```bash
   docker exec -it hermes-senator curl -v redis://172.17.0.1:6379 2>&1 | head -20
   ```

3. **Check all config files for password consistency**:
   ```bash
   grep -r "redis://" /opt/hermes-cognitive/ /root/hermes-*
   # Look for password in URLs
   ```

4. **Fix**: Remove passwords if Redis has no auth, or set password consistently:
   - Remove from `.env`: `REDIS_PASSWORD=`
   - Remove from `docker-compose.yml` broker URLs
   - Remove from `celery_app.py` broker/backend URLs
   - Restart everything: `docker-compose down && docker-compose up -d`

5. **Verify Celery worker sees tasks**:
   ```bash
   docker logs hermes-senator-celery-worker 2>&1 | grep -i "task\|registered"
   # Should show: "task: hermes.run"
   ```

6. **Test full flow**:
   ```bash
   curl -v -X POST http://localhost:8100/v1/portsocket \
     -H "Content-Type: application/json" \
     -H "X-API-Key: hermes-secret-change-me-in-production" \
     -H "X-Agent-ID: senator-test" \
     -d '{"input": "test simple"}'
   # Should return: {"task_id": "...", "status": "queued"}
   ```

### UFW Rules for Docker Networks
If Redis on host, containers need firewall access:
```bash
ufw allow from 172.25.0.0/16 to any port 6379
ufw allow from 172.17.0.0/16 to any port 6379
```

### Celery App Config Pattern (celery_app.py)
```python
import os
from celery import Celery

# Explicit import for task registration
import tasks  # This line is critical!

app = Celery('hermes')

app.conf.update(
    broker_url='redis://172.17.0.1:6379/0',
    result_backend='redis://172.17.0.1:6379/1',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Jakarta',
    enable_utc=True,
    # Connection pool settings
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        'visibility_timeout': 86400,
        'fanout_prefix': True,
    }
)
```

### Pitfalls
- **Password mismatch**: Most common cause of Celery failures
- **Missing `import tasks`**: Tasks won't register without explicit import
- **Docker network isolation**: Containers can't reach host Redis without UFW rules
- **No result backend**: Can't check task status without it (but can still queue)
- **Restart cascade**: After changing Celery code, must rebuild BOTH API + worker containers

### Verification Checklist
- [ ] Redis accessible without password (or with consistent password)
- [ ] Celery worker shows `task: hermes.run` registered
- [ ] `POST /v1/portsocket` returns task_id with status "queued"
- [ ] UFW allows Docker networks to access Redis port 6379
- [ ] No Redis auth errors in worker logs
