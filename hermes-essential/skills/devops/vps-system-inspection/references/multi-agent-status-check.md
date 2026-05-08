# Multi-Agent Container Status Check

## Context
When managing multiple Hermes Agent containers (e.g., orchestrator + specialized agents), checking agent status requires understanding container file system isolation.

## Common Setup Pattern
- **Orchestrator**: Loyx (port 8643) - general coordination
- **Specialized agents**: GameDev (port 8644), Builder (port 9122), etc.
- **File locations**: May exist inside container at `/workspace/` AND mirrored on host at `/root/<project>-dev/`

## Correct Inspection Sequence

### 1. List All Agent Containers
```bash
docker ps --filter "name=hermes" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 2. Verify Container Working Directory
```bash
docker exec <container_name> pwd
# Example output: /opt/hermes
```

### 3. Check File Locations BEFORE Reading
```bash
# Inside container
docker exec <container_name> ls -la /workspace/

# Host mirror (if exists)
ls -la /root/<project>-dev/
```

### 4. Read Files from Correct Location
```bash
# If files are in container:
docker exec <container_name> cat /workspace/PHASE2_SUMMARY.md

# If files are mirrored on host:
cat /root/<project>-dev/PHASE2_SUMMARY.md
```

### 5. Check Container Logs
```bash
docker logs <container_name> --tail 50
```

### 6. Health Check (Optional)
```bash
# May fail if no HTTP health endpoint
curl -s http://localhost:<port>/health
```

## Example: GameDev Agent Status Check (2026-05-04)

```bash
# 1. List containers
docker ps --filter "name=hermes"
# Found: hermes-gamedev (8644), hermes-agent-loyx (8643)

# 2. Check working directory
docker exec hermes-gamedev pwd
# Output: /opt/hermes

# 3. Verify file locations
docker exec hermes-gamedev ls -la /workspace/
# Found: PHASE2_SUMMARY.md, SPRINT1_TASKS.md, etc.

ls -la /root/regrow-up-world-dev/
# Also found: Same files mirrored on host

# 4. Read status documents
docker exec hermes-gamedev cat /workspace/PHASE2_SUMMARY.md
# OR
cat /root/regrow-up-world-dev/PHASE2_SUMMARY.md

# 5. Check recent activity
docker logs hermes-gamedev --tail 50
cat /root/regrow-up-world-dev/.last_telegram_sent
```

## Anti-Pattern (What NOT to Do)

❌ **Don't assume host paths exist:**
```bash
ls -la /workspace/  # May not exist on host
cat /workspace/PHASE2_SUMMARY.md  # Fails if only in container
```

❌ **Don't try to read files before verifying location:**
```bash
# Wasted 3-4 tool calls trying /workspace/ on host
# before discovering files were in container
```

## Status Report Format (User Preference)

When presenting multi-agent status to this user, use:
- Box-drawing characters (═══, ───, │)
- Emoji indicators (✅ ⏳ ❌ 🎮 🤖 📋 📅)
- Structured sections with clear headers
- Brief, scannable format (not verbose explanations)
- Indonesian language

Example:
```
════════════════════════════════════════════════════════════════════════════════
                    📊 STATUS REGROW UP WORLD - 4 Mei 2026 05:07
════════════════════════════════════════════════════════════════════════════════

🤖 AGENT STATUS
  ✅ GameDev Agent: hermes-gamedev (port 8644) - Up 33 menit
  ✅ Loyx Orchestrator: hermes-agent-loyx (port 8643) - Up 5 jam
  ⚠️  Health check: Gagal (gateway tidak merespons HTTP health endpoint)
  ℹ️  Working directory: /workspace di dalam container
```

## Key Insight
Container file systems are isolated. Always verify paths inside the container first, then check for host mirrors. The container's working directory (`pwd`) may differ from where project files are mounted (`/workspace/`).
