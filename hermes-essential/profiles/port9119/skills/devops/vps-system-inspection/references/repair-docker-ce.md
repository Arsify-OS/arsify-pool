# Repair Broken/Missing Docker CE (Session 2026-05-03)

## Problem
Docker CLI missing (`docker: command not found`), `dpkg -l` shows docker-ce not installed, docker.io status `rc` (removed), no Docker apt repository present.

## Verified Fix Steps
1. Check state:
   ```bash
   docker --version 2>&1
   dpkg -l | grep -i docker
   apt-cache policy docker-ce
   ```

2. Install prerequisites:
   ```bash
   apt-get update > /dev/null 2>&1 && apt-get install -y ca-certificates curl gnupg
   ```

3. Add Docker official GPG key and repository:
   ```bash
   install -m 0755 -d /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   chmod a+r /etc/apt/keyrings/docker.asc
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
   ```

4. Install full Docker CE suite:
   ```bash
   apt-get update > /dev/null 2>&1 && apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```

5. Fix broken docker.socket (if service fails to start):
   ```bash
   systemctl daemon-reload
   systemctl stop docker.socket
   rm -f /var/run/docker.sock
   systemctl start docker.socket
   systemctl start docker
   ```

6. Verify:
   ```bash
   docker --version
   systemctl status docker --no-pager | head -10
   docker ps
   ```
