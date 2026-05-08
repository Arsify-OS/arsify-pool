# Systemd Service Troubleshooting

## Common Restart Loop Patterns

### Pattern 1: Missing File/Script
**Symptoms:**
- Service in `activating (auto-restart)` state
- High restart counter (1000+)
- Exit code 127 in logs
- Error: "No such file or directory"

**Diagnosis:**
```bash
systemctl status <service> --no-pager -l
journalctl -u <service> -n 20 --no-pager
```

**Resolution:**
- If file truly missing and service not needed: `systemctl stop <service> && systemctl disable <service>`
- If file should exist: recreate the script/binary, then `systemctl restart <service>`

**Example from session:**
```
hermes-telegram-bridge.service
Error: /opt/hermes-telegram-bridge.sh: No such file or directory
Restart counter: 4513+
Solution: Stopped and disabled (file not recoverable)
```

### Pattern 2: Port Already in Use
**Symptoms:**
- Service in `activating (auto-restart)` state
- Exit code 1 in logs
- Error: "address already in use" or "Errno 98"

**Diagnosis:**
```bash
systemctl status <service> --no-pager -l
journalctl -u <service> -n 30 --no-pager
lsof -i :<port> | grep LISTEN
```

**Resolution:**
1. Identify process using the port: `lsof -i :<port>`
2. Check if it's a duplicate/zombie process: `ps aux | grep <process_name>`
3. Options:
   - Kill the conflicting process: `kill <PID>`
   - Change service port in config
   - If it's a proxy (socat, nginx), check if it's needed

**Example from session:**
```
hermes-upshalternal.service (Port 9120)
Error: [Errno 98] error while attempting to bind on address ('0.0.0.0', 9120)
Conflicting process: socat PID 757 (TCP-LISTEN:9120,fork,reuseaddr TCP:127.0.0.1:9120)
Solution: Killed socat process, service started successfully
```

### Pattern 3: Permission/Dependency Issues
**Symptoms:**
- Service fails immediately after start
- Exit code varies (1, 126, etc.)
- Errors about missing dependencies, permissions, or config files

**Diagnosis:**
```bash
systemctl status <service> --no-pager -l
journalctl -u <service> -n 50 --no-pager
# Check service file
cat /etc/systemd/system/<service>.service
# Test command manually
sudo -u <service_user> <ExecStart_command>
```

## Investigation Workflow

1. **Check service status**
   ```bash
   systemctl list-units --type=service --all | grep <pattern>
   ```

2. **For each problematic service:**
   ```bash
   systemctl status <service> --no-pager -l
   journalctl -u <service> -n 30 --no-pager
   ```

3. **Identify root cause** (exit code + error message)
   - 127: File not found
   - 1: General failure (check logs for specifics)
   - 126: Permission denied

4. **Check dependencies** (ports, files, other services)
   ```bash
   # Port conflicts
   lsof -i :<port>
   
   # File existence
   ls -la <file_path>
   
   # Process conflicts
   ps aux | grep <process_name>
   ```

5. **Apply fix** (stop/disable, kill conflict, fix config)

6. **Verify resolution**
   ```bash
   systemctl status <service> --no-pager -l
   # Should show: Active: active (running)
   ```

## Pitfalls

- Don't immediately restart a failing service without diagnosing the root cause
- High restart counters (1000+) indicate the problem has persisted for hours/days
- Exit code 127 almost always means missing file/binary
- Port conflicts may be caused by proxy processes (socat, nginx) that are intentional
- Always check if a service is actually needed before stopping/disabling it
- Use `--no-pager -l` flags with systemctl/journalctl for full output in scripts
