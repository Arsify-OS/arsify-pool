# VPS Inspection Session Commands (2026-05-03)

## Full System Check (original command)
```bash
echo "=== DISK USAGE ===" && df -h && echo -e "\n=== MEMORY USAGE ===" && free -h && echo -e "\n=== CPU LOAD ===" && uptime && echo -e "\n=== TOP PROCESSES (by CPU) ===" && ps aux --sort=-%cpu | head -10 && echo -e "\n=== TOP PROCESSES (by MEM) ===" && ps aux --sort=-%mem | head -10
```

## Zombie Process Check & Cleanup
```bash
# Detect zombies
ps aux | grep defunct | grep -v grep

# Find parent of zombie PID 2247411
ps -o pid,ppid,stat,cmd -p 2247411

# Kill parent (ttyd example)
kill -9 2246524

# Verify cleanup
ps aux | grep defunct | grep -v grep || echo "No zombie processes found - CLEAN!"
```

## Network & Service Audit
```bash
# Listening ports
ss -tlnp | head -30

# Tailscale check
which tailscale 2>/dev/null && tailscale status 2>/dev/null || echo "Tailscale not found/running"

# Hosts & DNS
cat /etc/hosts
cat /etc/resolv.conf

# Nginx domains (full config grep)
nginx -T 2>/dev/null | grep -E "server_name|server {"
```

## Detected Configs (this session)
- Tailscale IP: 100.109.101.58
- Domain: upshalter.com
- Subdomains: api, arsify-api, arsify, data, flowise, flowtask, hermes
- Open ports: 80, 443, 9119, 9118, 8120-8123, 8644, 22, Tailscale 50993/65284
