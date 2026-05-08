---
name: vps-system-inspection
description: "Inspect VPS health, audit system resources, clean zombie processes, and check network services (domains, ports, Tailscale, nginx configs) for CLI agents."
trigger:
  - "cek kondisi vps"
  - "check vps status"
  - "vps health check"
  - "clean zombie process"
  - "check domains/ports/tailscale"
  - "check nginx domains"
category: devops
---
# VPS System Inspection

## Steps
1. **System resource check**
   - Disk: `df -h`
   - Memory: `free -h`
   - CPU load: `uptime`
   - Top processes: `ps aux --sort=-%cpu | head -10`

2. **Zombie process audit & cleanup**
   - Detect: `ps aux | grep defunct | grep -v grep`
   - Find parent PID: `ps -o ppid= -p <zombie_pid>`
   - Kill parent: `kill -9 <parent_pid>`
   - Verify cleanup: re-run zombie detect command, should return nothing

3. **Network & service audit**
   - Listening ports: `ss -tlnp`
   - Tailscale check: `which tailscale && tailscale status`
   - Remote Tailscale device access (for managing files on connected devices):
     - Verify connectivity: `ping -c 3 <device_tailscale_ip>`
     - Check common access ports (SSH/SMB/RDP/WinRM):
       ```
       for port in 22 445 3389 5985; do timeout 3 bash -c "echo > /dev/tcp/<device_tailscale_ip>/$port" 2>/dev/null && echo "Port $port open" || echo "Port $port closed"; done
       ```
     - Windows SMB file access (port 445 open):
       - Install SMB tools if missing: `apt-get update -qq && apt-get install -y smbclient cifs-utils`
       - List available shares: `smbclient -L //<device_tailscale_ip> -U <windows_username>`
   - Nginx domains: `grep -r "server_name" /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null || nginx -T 2>/dev/null | grep server_name`
   - DNS/hosts: `cat /etc/hosts`, `cat /etc/resolv.conf`

## Pitfalls
- Zombies cannot be killed directly; must terminate/restart their parent process
- Never remove core system files (/usr, /boot) during VPS cleanup per user request
- Tailscale may not be installed; always check existence first with `which tailscale`
- When accessing Windows Tailscale devices, SMB (port 445) is the most common file sharing port; ensure Windows File and Printer Sharing is enabled on the remote device before attempting SMB access

## Verification
- Post-cleanup: `ps aux | grep defunct | grep -v grep` returns no results
- Resource check: Disk usage <80%, available memory >1GB

## CLI Output Rules (mandatory for this task)
- Use plain text only, no markdown formatting
- Do not emit MEDIA:/path tags (CLI only)
- Reference files by absolute path in plain text
