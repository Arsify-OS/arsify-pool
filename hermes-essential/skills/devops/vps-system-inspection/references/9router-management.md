# 9Router Management
## Update Workflow
1. **Check current version**:
   ```bash
   npm list -g 9router
   ```

2. **Update to target version**:
   ```bash
   sudo npm i -g 9router@<version>
   ```

3. **Stop running processes**:
   ```bash
   sudo pkill -f "node /usr/bin/9router"
   sudo pkill -f "next-server"
   ```

4. **Restart 9Router**:
   Avoid `nohup` (blocked by terminal security). Use terminal with `background=true`:
   ```bash
   # Terminal call parameters:
   background: true
   command: 9router -p <port> --skip-update
   pty: true
   ```

5. **Verify**:
   ```bash
   9router --version
   ps aux | grep -E "9router|next-server"
   ```

## Port Conflicts
- Default port 20128 is often used by `next-server` (Hermes Workspace). Use alternative ports (e.g., 20129) if conflict occurs.

## Diagnosing Monthly Limits
- 9Router itself does not enforce monthly limits; limits come from AI providers (OpenRouter, Kiro, etc.)
- Check provider status in 9Router web interface: `http://localhost:<port>/settings`
- View usage data: `~/.9router/usage.json`
- Most common limit source: OpenRouter free tier ($5-10/month credit limit)