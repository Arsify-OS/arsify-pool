# VPS Capacity Planning for Multiple Hermes Agents

Session: 2026-05-04 (3 independent agents + 5 shared systemd services)

## Resource Baseline (8GB RAM, 4 CPU, 96GB Disk VPS)

### Memory Usage Pattern
- **Total RAM**: 7.8 GB
- **Used with 8 agents**: 2.2 GB (28%)
- **Available**: 5.5 GB (70%)
- **Swap**: 4.0 GB (< 1 MB used - healthy)

### Per-Agent Memory Footprint
**Independent Docker Agents** (isolated containers):
- hermes-gamedev: 106 MB
- hermes-agent-loyx: 68 MB
- Average: ~90 MB per independent agent

**Shared Systemd Services** (using same /usr/local/bin/hermes binary):
- hermes-builder (CTO): ~64 MB
- hermes-dashboard: ~64 MB
- hermes-infra (COO): ~64 MB
- hermes-plaza (CMO): ~64 MB
- hermes-upshalternal (CEO): ~64 MB
- Average: ~64 MB per shared agent

**Supporting Processes**:
- hermes-cli (PM2 TUI session): ~90 MB
- Gateway processes: ~165 MB each
- Node.js TUI: ~131 MB

**Total Hermes Memory**: 1.24 GB for 8 agents (17 processes)

### CPU Usage
- Load average: 0.17 (very low on 4-core system)
- CPU idle: 90%+
- No bottlenecks observed

### Disk Usage
- Total: 96 GB
- Used: 45 GB (47%)
- Available: 52 GB (53%)
- Each agent data directory: ~11 MB

## Capacity Estimates

### Conservative (Safe for Production)
- **Independent agents**: 3-4 more (total 6-7)
- **Shared agents**: 10+ more (total 15+)
- **Mixed deployment**: Current 3 independent + 5 shared is only 16% memory usage

### Aggressive (Maximum Theoretical)
- **Independent agents only**: ~60 agents (60 × 90 MB = 5.4 GB)
- **Shared agents only**: ~100 agents (100 × 64 MB = 6.4 GB)
- Not recommended: leaves no headroom for spikes

### Recommended Limits
- **Memory threshold**: Stop adding agents when usage > 6 GB (75%)
- **Disk threshold**: Alert when < 20 GB available
- **CPU threshold**: Load average > 3.0 sustained

## Architecture Patterns

### Independent Agents (Docker Containers)
**Use when**:
- Need complete isolation (separate API keys, models, configs)
- Different project contexts (e.g., gamedev, orchestrator, personal)
- Want easy backup/migration (just copy /docker/{name}/ directory)

**Resource cost**: ~90 MB RAM + 11 MB disk per agent

**Example**: Loyx (orchestrator), GameDev (game development), CEO (executive tasks)

### Shared Agents (Systemd Services)
**Use when**:
- Same API keys and base config acceptable
- Role-based separation sufficient (CTO, COO, CMO, etc.)
- Want to minimize resource usage

**Resource cost**: ~64 MB RAM + 11 MB disk per agent

**Example**: C-suite setup (CEO, CTO, COO, CMO on same binary)

### Hybrid Approach (Current Setup)
- 3 independent agents for distinct contexts
- 5 shared agents for role-based tasks
- Total: 1.24 GB RAM (16% of available)
- **Status**: Very healthy, room for 3-4x growth

## Monitoring Commands

```bash
# Quick health check
free -h
df -h /
uptime

# Detailed agent inventory
docker stats --no-stream
ps aux | grep hermes | grep -v grep
systemctl list-units --type=service | grep hermes

# Memory breakdown
ps aux | grep hermes | awk '{sum+=$6} END {printf "Total: %.2f MB\n", sum/1024}'

# Disk usage per agent
du -sh /docker/hermes-*/data /opt/hermes-*/data 2>/dev/null
```

## Scaling Recommendations

### When to Add More Agents
✅ Memory usage < 6 GB
✅ CPU load average < 2.0
✅ Disk available > 30 GB
✅ No swap usage (< 100 MB)

### When to Stop Adding
❌ Memory usage > 6.5 GB
❌ Sustained CPU load > 3.0
❌ Disk < 20 GB
❌ Swap usage > 500 MB

### Optimization Tips
1. **Use shared agents** for similar tasks (saves ~30% RAM per agent)
2. **Disable unused agents**: Check `systemctl list-units | grep hermes` for restart loops
3. **Clean Docker images**: `docker system prune -a` frees 10-25 GB
4. **Monitor swap**: If swap usage grows, reduce agent count
5. **Port allocation**: Use sequential ports (8643, 8644, 8645...) for easy tracking

## Real-World Example (2026-05-04)

**Setup**:
- 3 independent agents (Loyx, GameDev, hermes-cli)
- 5 shared agents (CEO, CTO, COO, CMO, Dashboard)
- 1 Hermes Workspace (frontend)

**Resources**:
- Memory: 2.2 GB / 7.8 GB (28%)
- CPU: 0.17 load average (4 cores)
- Disk: 45 GB / 96 GB (47%)

**Verdict**: 🟢 VERY HEALTHY - Can add 3-4 more independent agents or 10+ shared agents

**User feedback**: "apakah masih layak" → "SANGAT LAYAK!"
