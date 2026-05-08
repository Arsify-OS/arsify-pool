# Multi-Agent Orchestration System Planning

Session: 2026-05-04 (Indonesian user, Upshalter ecosystem)

## Context
User had 7+ Hermes Agent instances running (3 Docker containers, 5 systemd services) with 12 domains in ecosystem, 6 domains inactive/empty, significant backlog of work. Asked about connecting agents for automated collaboration.

## Planning Methodology

### Priority Scoring Matrix (Weighted)
Use objective scoring to rank tasks when user has multiple competing priorities:

```
Priority Score = (Impact × 0.30) + (Urgency × 0.25) + (Effort × 0.20) + (Dependencies × 0.15) + (ROI × 0.10)
```

**Criteria (1-10 scale):**
- **Impact** (30%): How critical for operations, how many users affected
- **Urgency** (25%): Blocking work now (10) vs can wait 3+ months (1-3)
- **Effort** (20%): INVERTED - Quick tasks score higher (< 2h = 10, 8+ hours = 1-3)
- **Dependencies** (15%): No blockers (10) vs many dependencies (1-3)
- **ROI** (10%): Unlocks multiple tasks (10) vs standalone (1-3)

### Resource Impact Analysis Template

When proposing infrastructure changes, provide:

1. **Current State**
   - Memory: X GB used / Y GB total (Z% used)
   - Disk: X GB used / Y GB total (Z% used)
   - CPU: Load average
   - Process count

2. **After Implementation**
   - Memory: +X MB overhead → new total
   - Disk: +X MB
   - CPU: +X% estimated
   - Still safe: Y GB available

3. **ROI Calculation**
   ```
   Time Investment: X hours setup + Y hours/month maintenance
   Time Saved: Z hours/month
   Net Benefit: (Z - Y) hours/month
   ROI: ((Z - Y) / X) × 100%
   ```

4. **Risk Assessment**
   - Complexity: Low/Medium/High
   - Reversibility: Easy/Moderate/Difficult
   - Single point of failure: Yes/No
   - Mitigation strategies

### Multi-Agent Task Distribution

When planning parallel work across agents:

**Agent Role Mapping:**
- **Orchestrator** (Loyx): Coordination, task distribution, integration testing
- **Builder/CTO**: API development, code architecture, CI/CD
- **Infra/COO**: Deployment, monitoring, server config, SSL
- **GameDev**: Game-specific development
- **Plaza/CMO**: Documentation, landing pages, content
- **CEO**: Strategy, priority decisions, resource allocation

**Timeline Visualization:**
```
Week 1: FOUNDATION
├─ Day 1-2: [████] Task A (Xh)
├─ Day 3:   [██] Task B (Yh)
└─ Day 4-5: [███] Task C (Zh)

Week 2: PARALLEL EXECUTION
├─ Agent A: [████████] Task D (Xh)
├─ Agent B: [████] Task E (Yh)
└─ Agent C: [██████] Task F (Zh)
Wall time: ~Wh (parallel)
```

### Ecosystem Audit Pattern

When user asks about backlog/status:

1. **Domain Inventory**
   - List all configured domains: `nginx -T 2>/dev/null | grep "server_name" | sort -u`
   - Check each domain status: proxy_pass, root directory, file existence
   - Categorize: Active, Proxy, Empty/Inactive

2. **Work Classification**
   - Tier 1 (Critical): Blocking, high impact
   - Tier 2 (Important): Medium impact, needed soon
   - Tier 3 (Nice-to-have): Low priority, can defer

3. **Execution Strategy Options**
   - **Sequential**: Simple, slow, single-threaded
   - **Parallel (with orchestration)**: Fast, complex, requires setup
   - **MVP**: Quick wins, validate needs, technical debt

4. **Decision Framework**
   Present GO/NO-GO criteria with current status checkmarks

## Communication Preferences (Indonesian User)

- User communicates in Indonesian
- Prefers brief status updates during implementation
- Detailed documentation goes in files/summaries, not inline
- Appreciates structured terminal output with box-drawing (╔═╗║╚╝) and emoji (✅⚠️❌)
- Wants consolidated summaries, NOT incremental "continue" prompts
- When asked "how many X", run ALL checks first, then deliver ONE summary

## Deliverables Format

When creating planning documents, structure as:

1. **Executive Summary** (Telegram-friendly)
   - Top 3 priorities with scores
   - Timeline overview
   - Resource impact
   - Decision options (A/B/C)

2. **Detailed Plan** (Markdown file)
   - Methodology explanation
   - Full scoring matrix
   - Timeline with phases
   - Agent assignments
   - Risk mitigation
   - Success metrics

3. **Supporting Analysis** (Separate files)
   - Impact analysis
   - Ecosystem audit
   - Priority scale with formulas

## Key Insights from Session

- **Orchestration ROI**: 4h setup saves 24h execution (46% faster via parallel work)
- **VPS Capacity**: 7.8 GB RAM, 2.2 GB used → can add 3-4 more Docker agents safely
- **Agent Isolation**: Docker containers (Loyx, GameDev) are truly independent; systemd services share binary but have separate data dirs
- **Backlog Reality**: 50% of domains inactive = need prioritization system
- **User Preference**: Wants optimization/prioritization before execution

## CLI Wrapper Pattern for Containerized Agents

When creating CLI access to Docker containers:

```bash
#!/bin/bash
# Wrapper script for <agent_name>

if [ -t 0 ]; then
    # Interactive mode
    docker exec -it <container_name> /opt/hermes/.venv/bin/hermes "$@"
else
    # Non-interactive mode
    docker exec -i <container_name> /opt/hermes/.venv/bin/hermes "$@"
fi
```

Save to `/usr/local/bin/<agent_name>`, chmod +x, test with `<agent_name> --version`

## Pitfalls

- Don't implement orchestration without showing impact analysis first
- Don't assume user wants to proceed - always present options with clear trade-offs
- Don't drip-feed analysis results - consolidate before presenting
- When user asks "how many agents", they want breakdown by type (Docker, systemd, PM2) with clear categorization
- Resource overhead estimates must include memory, disk, AND CPU
- ROI calculations must show both time investment and time saved
- Always provide GO/NO-GO decision criteria with current status
