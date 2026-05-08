# Multi-Agent Game Development Pattern

**Pattern**: Orchestrator + Specialist + Monitoring for autonomous game development projects.

**Use case**: Long-running creative/development projects where a specialist agent works autonomously while an orchestrator monitors progress and sends updates to the user.

## Architecture

```
User (receives notifications)
  ↑
Loyx (Orchestrator) - monitors progress, sends updates
  ↓
GameDev (Specialist) - autonomous development work
  ↓
Project Workspace - shared filesystem for collaboration
```

## Implementation (Docker Compose)

### 1. Specialist Agent Container

Create a dedicated Docker Compose project for the specialist:

```yaml
# /root/project-name/docker-compose.yml
version: '3.8'

services:
  specialist-agent:
    image: nousresearch/hermes-agent:latest
    container_name: hermes-specialist
    restart: unless-stopped
    ports:
      - "8644:8642"  # Unique port per agent
    volumes:
      - /root/project-name:/workspace
      - ./agent-config:/root/.hermes
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - WORKSPACE_PATH=/workspace
    extra_hosts:
      - "host.docker.internal:host-gateway"
    working_dir: /workspace
    command: ["hermes", "gateway", "run"]
```

**Key points**:
- Use `hermes gateway run` (not `start`) for container mode
- Mount project workspace to `/workspace`
- Separate config directory per agent
- `extra_hosts` required for accessing host services (Ollama, custom proxies)

### 2. Agent Configuration

Create minimal config for specialist (`agent-config/config.yaml`):

```yaml
model:
  default: "openai/gpt-4o-mini"
  provider: "openrouter"
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

### 3. Project Structure

```
/root/project-name/
├── docker-compose.yml           # Specialist container config
├── .env                         # API keys (copy from main agent)
├── agent-config/
│   └── config.yaml             # Specialist agent config
├── PROJECT_BRIEF.md            # Vision & requirements
├── TASK_001_XXX.md             # Task definitions
├── progress_log.md             # Auto-updated by specialist
├── notifications.log           # Auto-updated by monitoring
└── (project files)
```

### 4. Automated Monitoring (Cron Job)

Set up a cron job on the main/orchestrator agent to monitor progress:

```bash
hermes cron create "every 30m" \
  --prompt "Check /root/project-name/progress_log.md for updates. If there are new entries (compare with last check), summarize the latest progress and append to /root/project-name/notifications.log with timestamp. Keep summaries concise (2-3 sentences)." \
  --toolsets file,terminal \
  --workdir /root/project-name \
  --name monitor-specialist-progress
```

**Alternative**: Manual monitoring script:

```bash
#!/bin/bash
# monitor_specialist.sh
WORKSPACE="/root/project-name"
LOG_FILE="$WORKSPACE/progress_log.md"
LAST_CHECK="$WORKSPACE/.last_check"

if [ -f "$LOG_FILE" ]; then
    if [ -f "$LAST_CHECK" ]; then
        CHANGES=$(find "$WORKSPACE" -newer "$LAST_CHECK" -type f | wc -l)
        if [ $CHANGES -gt 0 ]; then
            LATEST=$(tail -5 "$LOG_FILE")
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Update: $CHANGES file(s) changed" >> "$WORKSPACE/notifications.log"
            echo "$LATEST" >> "$WORKSPACE/notifications.log"
            echo "---" >> "$WORKSPACE/notifications.log"
        fi
    fi
fi

touch "$LAST_CHECK"
```

## Communication Patterns

### File-Based (Current Implementation)

**Specialist → Orchestrator**:
- Specialist writes to `progress_log.md`
- Orchestrator reads via cron job every N minutes
- Updates appended to `notifications.log`

**Orchestrator → User**:
- File-based: User reads `notifications.log`
- Future: WhatsApp/Telegram bot integration

**User → Specialist**:
- Direct: `docker exec -it hermes-specialist hermes`
- Via files: Write to `instructions.md`, specialist monitors

### Gateway API (Future Enhancement)

Use gateway HTTP API for real-time communication:

```bash
# Send message to specialist
curl -X POST http://localhost:8644/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Add unit tests for the authentication module"}'

# Check specialist status
curl http://localhost:8644/health
```

## Notification Integration

### WhatsApp (Pending Setup)

Requires WhatsApp Business API:
1. Get API credentials
2. Update monitoring script to POST to WhatsApp API
3. Format messages for mobile readability

### Telegram (Pending Setup)

1. Create bot via @BotFather
2. Get bot token
3. Configure in orchestrator agent:
   ```bash
   hermes gateway setup  # Select Telegram
   ```
4. Update monitoring to send via Telegram:
   ```python
   import requests
   
   def send_telegram(message):
       bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
       chat_id = os.getenv("TELEGRAM_CHAT_ID")
       url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
       requests.post(url, json={"chat_id": chat_id, "text": message})
   ```

## Pitfalls & Solutions

### Container Restart Loop

**Problem**: Container keeps restarting with "Input is not a terminal" error.

**Cause**: Using `hermes` command without arguments in non-interactive mode.

**Solution**: Use `hermes gateway run` as the container command (not `hermes gateway start`).

### Gateway Binds to Localhost Only

**Problem**: Can't access gateway from outside container.

**Cause**: Default gateway binding is `127.0.0.1:8642`.

**Solution**: Gateway ignores `config.yaml` host settings. Use environment variables:
```yaml
environment:
  - API_SERVER_ENABLED=true
  - API_SERVER_HOST=0.0.0.0
  - API_SERVER_PORT=8642
```

### Monitoring Cron Not Triggering

**Problem**: Cron job created but never runs.

**Cause**: Gateway not running on orchestrator agent.

**Solution**: Cron jobs require gateway to be running:
```bash
hermes gateway run  # Keep running in background
```

### Specialist Can't Access Host Services

**Problem**: Specialist agent can't reach Ollama/services on host.

**Cause**: Docker network isolation.

**Solution**: Add `extra_hosts` to docker-compose.yml:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Then use `host.docker.internal` in URLs instead of `localhost`.

### Progress Log Not Updating

**Problem**: Specialist works but doesn't update progress_log.md.

**Cause**: Specialist not instructed to maintain log.

**Solution**: Include in task definition:
```markdown
## Deliverables
1. Feature implementation
2. **Update progress_log.md after each major step**
3. Document decisions in DECISIONS.md
```

## Best Practices

### Task Definition

Create clear, structured task files:

```markdown
# TASK_001: Analyze Existing Codebase

## Objective
Understand current architecture and identify integration points.

## Deliverables
1. architecture.md - Current system structure
2. integration_points.md - Where to add new features
3. **Update progress_log.md after each deliverable**

## Success Criteria
- Complete understanding of codebase
- Clear integration plan documented

## Timeline
Target: 2-3 hours
```

### Progress Logging Convention

Specialist should follow this format in `progress_log.md`:

```markdown
## YYYY-MM-DD HH:MM - Task Name

### Completed
- ✅ Item 1
- ✅ Item 2

### In Progress
- 🔄 Item 3 (50% complete)

### Next Steps
- [ ] Item 4
- [ ] Item 5

### Blockers
- None / Issue description

---
```

### Monitoring Frequency

- **Active development**: Every 15-30 minutes
- **Long-running tasks**: Every 1-2 hours
- **Overnight jobs**: Every 4-6 hours

### Resource Management

Monitor container resource usage:

```bash
# Check all Hermes containers
docker stats --no-stream | grep hermes

# Expected per container: 100-300MB RAM, <5% CPU when idle
```

### Cleanup

When project completes:

```bash
# Stop specialist
cd /root/project-name && docker compose down

# Archive project
tar -czf project-name-$(date +%Y%m%d).tar.gz /root/project-name

# Remove if no longer needed
rm -rf /root/project-name
```

## Example: Game Development Project

See the session that created this pattern (2026-05-03):

**Goal**: Transform existing match-3 game into educational circular economy game.

**Setup**:
- Loyx (existing orchestrator on port 8643)
- GameDev (new specialist on port 8644)
- Main Hermes (coordinator)

**Workflow**:
1. User defines vision in PROJECT_BRIEF.md
2. User creates TASK_001_ANALYSIS.md
3. GameDev agent analyzes existing game code
4. GameDev updates progress_log.md after each step
5. Cron job checks every 30 minutes
6. Updates appended to notifications.log
7. User reviews progress periodically

**Result**: Autonomous development with periodic human oversight.

## Related Patterns

- **Parallel Specialists**: Multiple specialists (frontend, backend, testing) coordinated by orchestrator
- **Hierarchical**: Orchestrator → Team Leads → Specialists
- **Peer-to-Peer**: Specialists communicate directly via shared workspace files

## References

- Main skill: `hermes-agent` SKILL.md
- Docker networking: https://docs.docker.com/network/
- Gateway API: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/
