# OpenSwarm Integration Reference
Local clone path: `/root/openswarm` (https://github.com/openswarm-ai/openswarm)

## Key Features for Hermes Multi-Agent Setups
### 1. Spatial Dashboard
- Infinite canvas with drag-and-drop agent cards
- Real-time monitoring of all agents (5 Senators + Kurator for Pentahelix)
- Pan/zoom to view entire agent fleet status

### 2. Persistent Agent History
- Conversation history survives backend restarts
- Fixes task loss issues common with Celery-only setups
- Per-agent session cost tracking (critical for OpenRouter free tier)

### 3. Human-in-the-Loop Controls
- Approve/deny agent tool calls via dashboard
- Batch approval shortcuts (Shift+A to approve all, Shift+D to deny all)
- Configurable per-tool permissions (always allow/ask/deny)

### 4. Agent Modes & Custom Prompts
- 5 built-in modes (Agent, Ask, Plan, View Builder, Skill Builder)
- Custom mode support with configurable system prompts
- Per-Senator domain prompts (akademisi, bisnis, komunitas, pemerintah, media)

### 5. MCP & Skills Integration
- Full MCP server support (stdio, HTTP, SSE)
- Auto-discovers tools from MCP servers
- Syncs skills to `~/.claude/skills/` (aligned with Hermes skill system)

### 6. Git Worktree Isolation
- Each agent runs in isolated git worktree/branch
- Prevents conflicts between parallel Senator tasks

## Integration with Senator Pentahelix (PRD-002)
1. **Start OpenSwarm Backend**:
   ```bash
   cd /root/openswarm
   bash backend/run.sh  # Runs on port 8324
   ```

2. **Define Senator Agent Templates**:
   Create 5 Senator agents with domain-specific prompts:
   - `senator-akademisi`: Prompt for riset akademisi terbaru
   - `senator-bisnis`: Prompt for peluang bisnis
   - `senator-komunitas`: Prompt for tren komunitas
   - `senator-pemerintah`: Prompt for regulasi pemerintah
   - `senator-media`: Prompt for sentiment media

3. **Configure Kurator Agent**:
   Custom mode with prompt:
   ```
   Baca SKP entries 8 jam terakhir (key: */temuan/*), buat laporan terstruktur dengan:
   - RINGKASAN EKSEKUTIF
   - TEMUAN PER DOMAIN (2-3 poin each)
   - TEMA LINTAS DOMAIN
   - IMPLIKASI UNTUK UPSHALTER
   - ALERT (jika ada regulasi baru/ancaman)
   ```

4. **Monitor via Dashboard**:
   Access http://localhost:8324/dashboard to view all Senator cycles, task status, and API usage.

## Comparison with Existing Hermes Orchestrator
| Feature               | Hermes Orchestrator (Phase 1-2) | OpenSwarm |
|-----------------------|----------------------------------|-----------|
| Persistent History    | Requires SKP API                | Built-in  |
| Visual Dashboard      | Phase 3 Workstation             | Built-in  |
| Human-in-the-Loop     | Manual approval via API          | Dashboard UI |
| Cost Tracking         | Manual implementation           | Built-in per session |
| MCP Support           | Via skill system                 | Native support |

## Recommendation
Use OpenSwarm as the **visual orchestration layer** for Senator Pentahelix, while keeping existing Hermes Orchestrator for backend task routing and SKP integration.