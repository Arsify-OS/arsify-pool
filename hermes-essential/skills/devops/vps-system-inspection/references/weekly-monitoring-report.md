# Weekly Monitoring Report Protocol

## When to Use
- User asks for "laporan mingguan", "weekly report", "cek kondisi VPS lengkap"

## Execution Order
Run ALL data collection FIRST, then synthesize into ONE report. Do NOT drip-feed.

### Section 1: Infrastructure
```
systemctl list-units --type=service --state=running
for svc in hermes-orchestrator hermes-upshalternal hermes-archivist; do
  journalctl -u $svc --since "<START>" --until "<END>" | grep -c "Started\|Failed"
done
docker ps -a --format "table {{.Names}}\t{{.Status}}"
df -h / && free -h && uptime
```

### Section 2: Senator Pentahelix
```
for senator in senator-akademisi senator-bisnis senator-komunitas senator-pemerintah senator-media; do
  docker logs $senator --since "<START>T00:00:00" | grep -c "Stored to SKP"
done
# SKP DB: try /data/arsify.db first, then /root/.hermes/shared_knowledge_pool.db
```

### Sections 3-7: See full protocol at /root/Monitoring/MONITORING-PROTOCOL.md

## Key Findings from 1-7 May 2026
- Senator: 775 cycles, 0 SKP entries (OpenRouter 402)
- hermes-upshalternal: 19,052 restarts (EXTREME)
- Orchestrator: 30x 401 errors from health-check
- Cron: 0 executions logged
- n8n: Not found
- SKP DB path: /data/arsify.db does NOT exist
- Traffic: 9 requests/week (very low)
- SSL: All valid (nearest 74 days)
- Infrastructure: Stable (RAM 27%, Disk 53%)
