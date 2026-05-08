# VPS Disk Cleanup Workflow (Hermes Agent Host)

## Context
This workflow was used to clean a VPS from 36GB → 7.1GB (28.9GB freed) when only Hermes Agent and base Linux were needed.

## Steps (Ordered by Space Recovered)
1. **Docker Cleanup (~24GB)**
   ```bash
   docker system prune -a --volumes -f
   ```
   - Removes unused images, containers, volumes
   - Check results: `docker system df`

2. **User Cache Cleanup (~2.9GB)**
   ```bash
   rm -rf /root/.cache/*
   ```
   - Clears pip, npm, and other tool caches

3. **Temp Directory Cleanup (~1.4GB)**
   ```bash
   rm -rf /tmp/*
   ```

4. **Systemd Journal Cleanup (~600MB)**
   ```bash
   journalctl --vacuum-size=50M
   ```
   - Limits journal logs to 50MB

5. **APT Cache Cleanup**
   ```bash
   apt clean && apt autoremove -y
   ```

6. **Documentation/Include Cleanup**
   ```bash
   rm -rf /usr/share/doc/*
   rm -rf /usr/src/*
   rm -rf /usr/include/*
   ```

7. **NPM Cache Cleanup**
   ```bash
   npm cache clean --force
   ```

## Post-Cleanup Verification
```bash
df -h /                # Check root disk usage
du -sh /* 2>/dev/null | sort -rh | head -10  # Check top-level directories
```

## Notes
- Always verify no critical data is in `/tmp` or caches before cleaning
- Docker cleanup will remove all unused images/containers/volumes
- Journal vacuum size can be adjusted (default 50MB is safe for minimal setups)
