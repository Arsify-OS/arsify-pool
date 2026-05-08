# Hermes Multi-Instance Audit Pattern

## Context
When user asks "how many Hermes Agent instances are running", they want a complete inventory across all deployment methods (Docker, systemd, PM2, raw processes).

## Investigation Sequence
Execute in parallel or rapid sequence, then synthesize:

1. **Docker containers**
   ```bash
   docker ps --filter "name=hermes" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
   ```

2. **PM2 processes**
   ```bash
   pm2 list | grep -E "hermes|9router"
   ```

3. **Systemd services**
   ```bash
   systemctl list-units --type=service --all | grep hermes
   ```

4. **Raw processes** (catch-all for non-containerized instances)
   ```bash
   ps aux | grep -i "hermes\|claude" | grep -v grep | awk '{print $2, $11, $12, $13, $14, $15}'
   ```

5. **Service details** (for systemd services found above)
   ```bash
   cat /etc/systemd/system/hermes-*.service 2>/dev/null | grep -E "ExecStart|Description"
   ```

## Output Format
Deliver a single consolidated summary, not incremental findings. User prefers:
- Categorized by status (running vs problematic)
- Role/purpose identified (CTO, CEO, Orchestrator, etc.)
- Port numbers included
- Total count with breakdown

Example structure:
```
AKTIF & BERJALAN:
  1. Loyx (Docker) - Port 8643 - Orchestrator
  2. hermes-builder (systemd) - Port 9122 - CTO
  ...

BERMASALAH:
  7. hermes-telegram-bridge (systemd) - auto-restart loop

TOTAL: 8 instance
  - 6 berjalan normal
  - 2 bermasalah
```

## Pitfall: Incremental Delivery
**WRONG**: Running each check command, showing output, then running next check.
**RIGHT**: Run all checks, synthesize findings, deliver one consolidated answer.

User frustration signal: repeated "continue" responses indicate you're drip-feeding information instead of completing the investigation and delivering the full answer.

## Session Reference
- 2026-05-04: User asked "ada berapa agent ai hermes di vps ini"
- Investigation took 7+ tool calls with user saying "continue" each time
- Final answer: 8 instances (6 running, 2 in restart loop)
