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
  - "vps cpu throttle"
  - "hostinger throttle"
  - "high cpu usage"
  - "cpu usage tinggi"
category: devops
---
# VPS System Inspection

## Steps
0. **CPU Throttle Triage (when VPS is throttled by Hostinger)**
   - Full diagnosis: see `references/cpu-throttle-diagnosis.md`
   - Run CPU categorization via execute_code (ps aux in terminal inflates readings by 40-80%):
     ```python
     import subprocess
     result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
     lines = result.stdout.strip().split("\n")[1:]
     totals = {"hermes":0,"ollama":0,"uvicorn":0,"celery":0,"redis":0,"container":0,"senator":0,"zombie":0,"other":0}
     total = 0
     for line in lines:
         cols = line.split()
         cpu = float(cols[2])
         cmd = " ".join(cols[10:])
         total += cpu
         if "defunct" in cmd or "runc]" in cmd: totals["zombie"] += cpu
         elif "ollama" in cmd: totals["ollama"] += cpu
         elif "uvicorn" in cmd: totals["uvicorn"] += cpu
         elif "celery" in cmd: totals["celery"] += cpu
         elif "redis" in cmd: totals["redis"] += cpu
         elif any(k in cmd for k in ["containerd","docker","tini"]): totals["container"] += cpu
         elif "senator" in cmd or "hermes_sandbox" in cmd: totals["senator"] += cpu
         elif "hermes" in cmd: totals["hermes"] += cpu
         else: totals["other"] += cpu
     for k,v in totals.items(): print(f"{k}: {v:.1f}%")
     print(f"TOTAL: {total:.1f}% ({total/2:.0f}% of 2-core)")
     ```
   - Distinguish **temporary spikes** (senator cycle, 15-30min, every 6h) from **chronic issues**
   - ps aux itself + parent shell inflate CPU readings by 40-80% — this is measurement overhead, not real load
   - Target after fixes: base CPU < 60% of 2-core (< 120% in ps aux total)
   - Key chronic issues to check: ollama (stop/disable), health-check.sh blocking on dead services (remove dead services, add --max-time 3), redundant dashboard processes, zombie [runc] processes, stale celery queue (redis-cli DEL celery)

1. **System resource check**
   - Check memory usage and top memory-consuming processes:
     ```bash
     free -h && echo "---" && ps aux --sort=-%mem | head -10
     ```
   - Check zombie processes (defunct):
     ```bash
     ps aux | grep -w Z || echo "No zombie processes found"
     ```
   - **Output Format (User Preference)**: Use ✅ ⏳ ❌ emojis, brief Indonesian updates, no markdown, structured terminal output. Communicate in Indonesian for status updates.

## Deep Cleanup & Maintenance (beyond zombie check)
- Never touch `/usr`, `/boot`, or Hermes Agent installation files during cleanup (core system files).
- Remove unused large directories:
  ```bash
  rm -rf /root/openclaw /root/openswarm /root/hermes-workspace-fresh  # example large unused dirs
  rm -rf /backup/hermes/*  # old backups already archived
  rm -rf /root/.cache/camoufox /root/.cache/ms-playwright /root/.cache/uv  # cleanup caches
  ```
- Docker cleanup (reclaim space):
  ```bash
  docker system prune -f          # remove stopped containers, unused networks
  docker image prune -a -f        # remove all unused images
  docker builder prune -a -f      # remove build cache
  docker volume prune -f          # remove unused volumes
  ```
- Stop unused services to free memory:
  ```bash
  systemctl stop ollama browser-use-api  # example unused services
  ```
- Memory/swap optimization:
  ```bash
  sync && echo 3 > /proc/sys/vm/drop_caches  # drop filesystem caches
  swapoff /swapfile && swapon /swapfile      # reset swap to clear usage
  ```
- Verify cleanup:
  ```bash
  df -h / && free -h && du -sh /* 2>/dev/null | sort -rh | head -10
  ```

## 24/7 GitHub Sync Setup (automated VPS ↔ GitHub sync)
- Create sync script `/root/sync-github.sh`:
  ```bash
  #!/bin/bash
  cd /root/arsify-archive || exit 1
  git add -A
  if ! git diff --cached --quiet; then
      git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')"
  fi
  git push origin main 2>&1
  git pull origin main 2>&1
  ```
- Make executable and test:
  ```bash
  chmod +x /root/sync-github.sh
  /root/sync-github.sh
  ```
- Add to crontab for every 5 minutes:
  ```bash
  (crontab -l 2>/dev/null; echo "*/5 * * * * /root/sync-github.sh >> /var/log/github-sync.log 2>&1") | crontab -
  ```
- Verify cron:
  ```bash
  crontab -l | grep sync-github
  tail -10 /var/log/github-sync.log
  ```
