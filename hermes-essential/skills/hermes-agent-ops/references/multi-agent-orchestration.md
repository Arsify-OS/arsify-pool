# Multi-Agent Orchestration System

Planning and impact analysis for connecting isolated Hermes Agent instances into a coordinated multi-agent system.

## Context

When running multiple Hermes Agent instances (Docker containers, systemd services, PM2 processes), they operate independently by default with no inter-agent communication or workflow automation. This reference documents the architecture, benefits, risks, and implementation approach for building an orchestration layer.

## Current State (Isolated Agents)

### Typical Multi-Instance Setup
- **Independent agents**: Loyx (Docker 8643), GameDev (Docker 8644), 5 systemd services (ports 9119-9123)
- **No communication**: Each agent has isolated database, config, and execution context
- **Manual coordination**: User must manually trigger tasks across agents
- **Shared binary pattern**: Systemd services share `/usr/local/bin/hermes` but have separate data directories

### Connection Status
**Connected:**
- CLI session → Gateway → Telegram (messaging)
- CLI session → Docker agents (via wrapper scripts)
- Browser → Systemd services (web UI only)

**Not Connected:**
- Agent ↔ Agent (no inter-agent communication)
- Automation workflows (no task distribution)
- Centralized monitoring (no unified dashboard)

## Proposed Architecture

### Orchestrator Hub (Central Coordination)
```
┌─────────────────────────────────────────────┐
│         ORCHESTRATOR HUB (Port 9000)        │
│  - Message Queue (Redis)                    │
│  - Task Dispatcher                          │
│  - Agent Registry                           │
│  - Workflow Engine                          │
│  - Monitoring Dashboard                     │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ↓                     ↓
┌───────────────┐    ┌───────────────┐
│  API Gateway  │    │  Event Bus    │
│  (REST/WS)    │    │  (Pub/Sub)    │
└───────┬───────┘    └───────┬───────┘
        │                    │
        └────────┬───────────┘
                 │
    ┌────────────┼────────────┬────────────┐
    │            │            │            │
    ↓            ↓            ↓            ↓
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ Loyx   │  │GameDev │  │Builder │  │ Infra  │
│ 8643   │  │ 8644   │  │ 9122   │  │ 9121   │
└────────┘  └────────┘  └────────┘  └────────┘
```

### Components

1. **Orchestrator Hub** (Python FastAPI, port 9000)
   - Central coordination service
   - Task queue management (Redis Queue)
   - Agent health monitoring
   - Workflow automation engine

2. **Agent Adapters**
   - REST API wrapper for each agent
   - Standardized communication protocol
   - Health check endpoints
   - Task execution interface

3. **Message Queue** (Redis)
   - Pub/sub messaging between agents
   - Task queue for async jobs
   - Event broadcasting
   - Agent-to-agent messaging

4. **Workflow Engine**
   - YAML-based workflow definitions
   - Automatic task distribution
   - Dependency management
   - Error handling & retry logic

5. **Monitoring Dashboard**
   - Real-time agent status
   - Task execution tracking
   - Performance metrics
   - Log aggregation

## Example Workflow

```yaml
# workflow: game-development-pipeline
name: "Regrow Up World Development"
trigger: "file_change:/root/regrow-up-world-dev/**"

steps:
  - name: "Analyze Changes"
    agent: "gamedev"
    action: "analyze_code"
    input: "${changed_files}"
    
  - name: "Review Code"
    agent: "builder"
    action: "code_review"
    input: "${step.1.output}"
    depends_on: ["Analyze Changes"]
    
  - name: "Build & Test"
    agent: "infra"
    action: "build_deploy"
    input: "${step.2.approved_changes}"
    depends_on: ["Review Code"]
    condition: "${step.2.status == 'approved'}"
    
  - name: "Notify Telegram"
    agent: "gateway"
    action: "send_message"
    input: "Build completed: ${step.3.result}"
    depends_on: ["Build & Test"]
```

## Impact Analysis

### Benefits (8/10)

**Efficiency & Productivity:**
- Automated workflow end-to-end (file change → analyze → review → deploy)
- Parallel processing for independent tasks
- Load balancing across agents
- Time saved: 2-3 hours/day (manual coordination eliminated)

**Monitoring & Visibility:**
- Centralized dashboard for all agents
- Real-time task execution tracking
- Error detection & alerting
- Log aggregation from all agents

**Scalability:**
- Easy to add new agents (register to Hub)
- Flexible workflows (YAML config)
- Better resource utilization
- A/B testing different workflows

**Reliability:**
- Automatic retry for failed tasks
- Fallback to other agents if one is down
- Task queue persistence (survives restarts)
- Health monitoring with Telegram alerts

### Risks & Costs (4/10)

**Complexity:**
- More moving parts (distributed system)
- Debugging more difficult
- Learning curve for maintenance
- Single point of failure (Orchestrator Hub)

**Resource Overhead:**
- Memory: +500-700 MB
  - Redis: ~100-200 MB
  - Orchestrator Hub: ~200-300 MB
  - Agent adapters: ~50 MB per agent
- Disk: +150-250 MB (Redis persistence, logs, code)
- CPU: +5-10% (message queue, health checks, workflow engine)

**Maintenance Burden:**
- Redis monitoring, backup, restart
- Orchestrator Hub updates & config
- Agent adapter compatibility
- Workflow definition versioning
- Estimated: +1-2 hours/week

**Performance:**
- Latency overhead: Direct call ~10ms → Via Hub ~50-100ms
- Message queue bottleneck at high task volume
- Queue backlog if agents are slow

**Security:**
- Orchestrator Hub exposed (port 9000)
- Agent API endpoints exposed
- Redis port (6379) needs protection
- JWT token management
- Task data flowing through Hub

**Operational Risks:**
- Hub down → all automation stops
- Redis down → message queue fails
- Cascading failures (one agent error blocks workflow)
- Race conditions (multiple agents accessing same resource)

## ROI Calculation

**Investment:**
- Implementation: 3-4 hours (one-time)
- Maintenance: 8 hours/month

**Return:**
- Time saved: 60-90 hours/month (2-3 hours/day × 30 days)
- Net benefit: 52-82 hours/month
- ROI: 650-1025% (after first month)

**Benefit > Cost**: Yes, highly worth it for active multi-agent setups.

## Implementation Phases

### Phase 1: Infrastructure (30 min)
- Install Redis
- Setup Orchestrator Hub service
- Create database schema
- Setup monitoring

### Phase 2: Agent Integration (45 min)
- Create API adapters for Loyx
- Create API adapters for GameDev
- Create API adapters for 5 systemd services
- Register all agents to Hub

### Phase 3: Communication Layer (30 min)
- Implement message queue
- Setup pub/sub channels
- Create agent discovery service
- Test inter-agent messaging

### Phase 4: Workflow Engine (45 min)
- Create workflow definition format
- Implement task dispatcher
- Add dependency resolution
- Error handling & retry

### Phase 5: Automation (30 min)
- Define default workflows
- Setup cron triggers
- Event-driven automation
- Integration with Telegram

### Phase 6: Monitoring & Testing (30 min)
- Dashboard web UI
- Health checks
- Performance monitoring
- End-to-end testing

**Total Time:**
- MVP (Phases 1-3): 1-2 hours
- Full implementation: 3-4 hours

## Resource Impact on VPS

### Before Orchestration
- Memory: 2.2 GB / 7.8 GB (28% used)
- Disk: 45 GB / 96 GB (47% used)
- CPU: Load average 0.17 (very low)
- Hermes processes: 17 (1.24 GB total)

### After Orchestration (Projected)
- Memory: 2.7-2.9 GB / 7.8 GB (35-37% used)
- Disk: 45.2 GB / 96 GB (47% used)
- CPU: Load average 0.20-0.25 (still low)
- Additional processes: +3-5 (Redis, Hub, adapters)

**Verdict**: VPS can easily handle orchestration overhead. Still 63% memory available, 53% disk available.

## Risk Mitigation

### Complexity Management
- Good documentation (architecture diagrams, workflow examples)
- Monitoring & alerting (health checks every 30s, Telegram alerts)
- Dashboard for visibility

### Resource Management
- Resource limits (Redis max 500 MB, Hub max 300 MB)
- Log rotation (max 100 MB)
- Graceful degradation (agents work independently if Hub down)

### Security Hardening
- Firewall rules (only localhost access to Hub)
- JWT authentication
- Rate limiting
- Encrypt sensitive data in Redis

### High Availability
- Orchestrator auto-restart (systemd)
- Redis persistence enabled
- Task queue durability
- Circuit breakers (timeout for slow agents, retry with exponential backoff)

## Decision Matrix

| Criteria | Current | After MVP | After Full |
|----------|---------|-----------|------------|
| Automation | 20% | 60% | 90% |
| Visibility | 30% | 70% | 95% |
| Complexity | Low | Medium | High |
| Resource | 2.2GB | 2.5GB | 2.9GB |
| Maintenance | 1h/week | 1.5h/week | 2h/week |
| Productivity | Baseline | +150% | +200% |

**Sweet Spot**: MVP (60% automation, medium complexity, manageable maintenance)

## Recommendation

**Start with MVP** (Phases 1-3, 1-2 hours):
- Basic orchestration infrastructure
- Simple agent integration
- Test & validate with 2-3 workflows

**If MVP succeeds** → Full implementation (Phases 4-6)
**If not suitable** → Easy rollback (stop services, remove Redis)

## When to Implement

**Implement Now** if:
- Frequent manual coordination between agents (3+ times/day)
- Active development projects (e.g., Regrow Up World)
- Need automation for efficiency
- Have 3-4 hours for setup

**MVP First** if:
- Uncertain about all features
- Want to test before full commit
- Resource concerns (though VPS is safe)

**Skip for Now** if:
- Agents rarely used
- Manual coordination manageable
- No urgent automation needs
- Prefer simplicity over automation

## Technology Stack

```yaml
orchestrator:
  language: Python 3.11+
  framework: FastAPI
  database: SQLite (metadata)
  cache: Redis
  queue: Redis Queue (RQ)
  
agent_adapters:
  protocol: REST API + WebSocket
  auth: JWT tokens
  
monitoring:
  dashboard: React + Vite
  metrics: Prometheus (optional)
  logs: File-based aggregation
  
deployment:
  orchestrator: Docker container
  port: 9000
  restart: unless-stopped
```

## Session Context

This analysis was created during a 2026-05-04 session where:
- User had 8 Hermes instances (7 active, 1 disabled)
- Successfully created hermes-gamedev as independent agent (port 8644)
- Created CLI wrapper for gamedev access
- Fixed hermes-upshalternal (port conflict with socat)
- Disabled hermes-telegram-bridge (missing script)
- VPS resources: 7.8 GB RAM (70% free), 96 GB disk (53% free), 4 CPU cores

User requested orchestration system to enable inter-agent communication and automated workflows. Full planning documents created at:
- `/root/hermes-orchestration/PLAN.md`
- `/root/hermes-orchestration/IMPACT_ANALYSIS.md`

## Related References

- [Multi-Instance Troubleshooting](multi-instance-troubleshooting.md) - Diagnosing and fixing multi-agent deployments
- [VPS Capacity Planning](vps-capacity-planning.md) - Resource usage patterns for multi-agent setups
- Main skill: Creating independent agent containers, CLI wrappers, port allocation
