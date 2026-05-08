## Aggressive VPS Cleanup for Hermes-Only Setups
Preserve core files: `/usr`, `/boot`, Hermes installation (`/usr/local/bin/hermes`, `/root/.hermes/`, `/usr/local/lib/hermes-agent`)

### Cleanup Steps
1. **Docker Resources**: `docker system prune -a --volumes -f`
2. **APT Caches**: `apt clean && apt autoremove -y`
3. **User Caches**: `rm -rf /root/.cache/* /root/.local/*`
4. **Temp Files**: `rm -rf /tmp/*`
5. **System Caches**: `rm -rf /var/cache/*`
6. **Old Logs**: `find /var/log -type f -name "*.log" -mtime +7 -delete`
7. **System Journal**: `journalctl --vacuum-size=50M`
8. **Unused Documentation**: `rm -rf /usr/share/doc/* /usr/src/* /usr/include/*`

### Verification
Check disk usage: `df -h`
Check preserved Hermes files: `ls -la /usr/local/bin/hermes /root/.hermes/ /usr/local/lib/hermes-agent`