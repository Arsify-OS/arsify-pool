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
  - "clean vps disk"
  - "free vps space"
  - "remove docker ollama"
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
   - Check running Docker containers: `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"`
   - Investigate unknown containers (see references/docker-container-investigation.md):
     - Check image source: `docker inspect <container> --format '{{.Config.Image}}'`
     - Check for Hostinger images: images from `ghcr.io/hostinger/*`
     - Trace deployment: `grep -r "<container_name>" /root/.local/share/tirith/log.jsonl 2>/dev/null`
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

4. **Disk cleanup (optional, for freeing space)**
   - **Priority order: Target big items first**
     1. Docker (often 10-15GB): `docker system df` to check, then uninstall if unused
     2. Ollama models (2-8GB): `du -sh /usr/share/ollama /var/lib/ollama`
     3. Hermes Workspace node_modules: `du -sh /root/hermes-workspace/node_modules`
     4. Old logs: `journalctl --disk-usage`, `du -sh /var/log`
     5. APT cache: `apt-get clean && apt-get autoclean`
     6. Small tools last (llama.cpp, etc.)
   - Identify large directories: `du -sh /usr/* /var/* /root/* 2>/dev/null | sort -rh | head -20`
   - Clean APT package cache: `apt-get clean && apt-get autoclean`
   - Remove unused Docker resources (if Docker is installed):
     - Stop and remove unused containers: `docker stop <container_name> && docker rm <container_name>`
     - Remove unused images: `docker rmi <image_name>`
     - Full prune (removes all unused images/containers/volumes/networks): `docker system prune -a --volumes -f` (warn: irreversible)
   - Remove Ollama if unused:
     - Verify Ollama is not the active provider: `grep provider ~/.hermes/config.yaml`
     - If provider is not ollama: `systemctl stop ollama; pkill -f ollama; rm -rf /usr/share/ollama /var/lib/ollama /usr/local/bin/ollama`
   - Remove unused local tools (e.g., llama.cpp): `rm -rf /root/llama.cpp` (verify not in use first)
   - Full Docker uninstall (if requested): `apt-get remove -y docker docker.io containerd runc; apt-get purge -y docker-ce docker-ce-cli containerd.io; rm -rf /var/lib/docker /var/lib/containerd`
     - Check common access ports (SSH/SMB/RDP/WinRM):
       ```
       for port in 22 445 3389 5985; do timeout 3 bash -c "echo > /dev/tcp/<device_tailscale_ip>/$port" 2>/dev/null && echo "Port $port open" || echo "Port $port closed"; done
       ```
     - Windows SMB file access (port 445 open):
       - Install SMB tools if missing: `apt-get update -qq && apt-get install -y smbclient cifs-utils`
       - List available shares: `smbclient -L //<device_tailscale_ip> -U <windows_username>`
   - Nginx domains: `grep -r "server_name" /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null || nginx -T 2>/dev/null | grep server_name`
   - DNS/hosts: `cat /etc/hosts`, `cat /etc/resolv.conf`

## Repair broken/missing Docker CE
If Docker CLI is missing (`docker: command not found`) or Docker service fails to start due to incomplete package removal:
1. **Check current state**
   - Verify installed packages: `dpkg -l | grep -i docker` (note `rc` status = removed, `ii` = installed)
   - Check binary existence: `which docker`
2. **Reinstall from official Docker repo** (avoids outdated docker.io packages)
   - Install prerequisites: `apt-get update > /dev/null && apt-get install -y ca-certificates curl gnupg`
   - Add Docker GPG key: `install -m 0755 -d /etc/apt/keyrings && curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc && chmod a+r /etc/apt/keyrings/docker.asc`
   - Add Docker apt source: `echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null`
   - Install full Docker CE suite: `apt-get update > /dev/null && apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin`
3. **Fix docker.socket errors** (common after incomplete removal, service fails with "docker.socket failed to load properly")
   - Reload systemd config: `systemctl daemon-reload`
   - Stop broken socket: `systemctl stop docker.socket`
   - Remove stale socket file: `rm -f /var/run/docker.sock`
   - Restart services: `systemctl start docker.socket && systemctl start docker`
4. **Verify**
   - `docker --version` (should return Docker version 29.x+)
   - `systemctl status docker --no-pager` (should show Active: active (running))

## Pitfalls
- Zombies cannot be killed directly; must terminate/restart their parent process
- Never remove core system files (/usr, /boot) during VPS cleanup per user request
- Tailscale may not be installed; always check existence first with `which tailscale`
- When accessing Windows Tailscale devices, SMB (port 445) is the most common file sharing port; ensure Windows File and Printer Sharing is enabled on the remote device before attempting SMB access
- Avoid removing Ollama without first verifying Hermes Agent dependencies: run `grep provider ~/.hermes/config.yaml` to check the active LLM provider. If Ollama is the configured provider (`provider: ollama`), removing it will break Hermes Agent. If the provider has been switched (e.g., to openrouter), Ollama can be safely removed.
- When uninstalling Docker, always stop running containers first (especially critical workloads) to avoid data loss. Verify no active services depend on Docker before full removal.
- Incomplete Docker removal (docker-ce deleted, official repo missing) requires reinstalling from Docker's official apt repository, not the default Ubuntu docker.io package, to restore full functionality.
- Docker containers may be deployed via Hostinger VPS Docker Compose Catalog (images from `ghcr.io/hostinger/*`) rather than local docker-compose files; these will not appear in `docker compose ls` output and require checking image origin to confirm management source.
- Docker container names may not match docker-compose service names; use `docker inspect` to trace the actual image source and compose project
- Dynamic Docker port mappings (e.g., 32776) differ from static ports defined in docker-compose.yml (e.g., 8642); check `docker ps` output carefully
- Hostinger VPS may deploy containers via their Docker Compose Catalog using different image names (e.g., `ghcr.io/hostinger/hvps-hermes-agent`) than official images; these containers may not appear in local `docker compose ls`
- For long-lived Node.js CLI services, always use PM2 instead of raw background commands (&) or Hermes background processes to ensure auto-restart and persistence across reboots.

## Verification
- Post-cleanup: `ps aux | grep defunct | grep -v grep` returns no results
- Resource check: Disk usage <80%, available memory >1GB
- Post-disk cleanup: `df -h /` shows increased available space; `du -sh <removed_dir>` returns "No such file or directory" for cleaned directories

## CLI Output Rules (mandatory for this task)
- Use plain text only, no markdown formatting
- Do not emit MEDIA:/path tags (CLI only)
- Reference files by absolute path in plain text

## References
- See `references/docker-container-investigation.md` for detailed Docker container investigation patterns (tracing container origins, dynamic vs static ports, Hostinger VPS Catalog specifics)
- See `references/repair-docker-ce.md` for step-by-step commands to repair broken/missing Docker CE installations
- See `references/persistent-nodejs-service-setup.md` for steps to set up persistent Node.js services with PM2, UFW, and systemd.
