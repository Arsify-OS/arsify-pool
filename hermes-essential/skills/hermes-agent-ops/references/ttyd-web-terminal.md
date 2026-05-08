# ttyd Web Terminal for Containerized Hermes Agent

When the native Hermes Agent TUI fails to start (npm install permission issues, read-only node_modules), use ttyd as a lightweight alternative to expose the CLI via web browser.

## Problem Context

The `nousresearch/hermes-agent:latest` Docker image has a hardcoded npm install step in the TUI launcher (`/opt/hermes/hermes_cli/main.py`) that:
- Runs `npm install` in `/opt/hermes/ui-tui/` on every `hermes --tui` invocation
- Fails with EACCES when node_modules is read-only (common in Docker images)
- Has no environment variable to skip the install step
- Causes container restart loops when used with `command: ["hermes", "--tui"]`

**Attempted fixes that failed:**
- Mounting writable volume for node_modules
- Running container as root
- Setting `SKIP_NPM_INSTALL=1` (not implemented in code)
- Copying node_modules to writable location

## Solution: ttyd Web Terminal

ttyd is a simple web-based terminal emulator that shares any CLI command over HTTP/WebSocket. It's perfect for exposing containerized Hermes Agent CLI to browsers.

### Installation

```bash
apt-get install -y ttyd
```

### Basic Usage

Run ttyd pointing to the Hermes CLI wrapper:
```bash
ttyd -p 4860 -W /usr/local/bin/loyx chat
```

Flags:
- `-p 4860`: Listen port
- `-W`: Enable write access (allow user input)
- Command: `loyx chat` (interactive chat session)

### Systemd Service (Persistent)

Create `/etc/systemd/system/loyx-terminal.service`:
```ini
[Unit]
Description=Loyx Web Terminal (ttyd)
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
ExecStart=/usr/bin/ttyd -p 4860 -W /usr/local/bin/loyx chat
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable loyx-terminal.service
systemctl start loyx-terminal.service
```

### Firewall Configuration

Open port for external access:
```bash
ufw allow 4860/tcp
ufw reload
```

### Access

Open in browser: `http://<vps-ip>:4860`

The terminal will load with `loyx chat` already running, ready for interactive use.

## Pitfalls

1. **Port conflicts**: If port 4860 is already in use, ttyd will fail silently. Check with `ss -tlnp | grep 4860` before starting.

2. **Background process conflicts**: If you start ttyd manually with `&` or `background=true`, then try to start the systemd service, you'll get "address already in use" errors. Kill the manual process first: `pkill -f "ttyd.*loyx"`.

3. **Docker dependency**: The systemd service has `Requires=docker.service` because the CLI wrapper (`loyx`) execs into a Docker container. If Docker is down, ttyd will start but the terminal will show connection errors.

4. **No authentication by default**: ttyd has no built-in auth. For production use, add basic auth (`-c username:password`) or put it behind Nginx with auth.

5. **Session persistence**: Each browser connection gets a new shell session. If the user closes the browser, the chat session is lost. For persistent sessions, consider tmux integration: `ttyd -p 4860 -W tmux new -A -s loyx-session /usr/local/bin/loyx chat`.

## When to Use ttyd vs Native TUI

**Use ttyd when:**
- Hermes Agent runs in Docker and native TUI fails
- You need simple browser-based access without complex setup
- The container image has read-only filesystem issues
- You want to expose CLI to non-technical users via web

**Use native TUI when:**
- Hermes Agent runs directly on host (not containerized)
- You have full control over the filesystem and dependencies
- You need the richer UI features of the Ink-based TUI
- npm/node_modules permissions are not an issue

## Alternative: Hermes Workspace

For a full-featured web UI (not just terminal), use Hermes Workspace instead. It provides chat, memory, skills, file browser, and terminal in one interface. However, it requires more setup (Node.js 22+, pnpm, build step, gateway configuration).

ttyd is the quick-and-dirty solution when you just need terminal access and don't want to debug complex web app deployments.

## Example: Complete Setup for Containerized Agent

```bash
# 1. Create CLI wrapper (if not exists)
cat > /usr/local/bin/loyx << 'EOF'
#!/bin/bash
if [ -t 0 ]; then
    docker exec -it hermes-agent-loyx-hermes-agent-1 /opt/hermes/.venv/bin/hermes "$@"
else
    docker exec -i hermes-agent-loyx-hermes-agent-1 /opt/hermes/.venv/bin/hermes "$@"
fi
EOF
chmod +x /usr/local/bin/loyx

# 2. Install ttyd
apt-get install -y ttyd

# 3. Create systemd service
cat > /etc/systemd/system/loyx-terminal.service << 'EOF'
[Unit]
Description=Loyx Web Terminal (ttyd)
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
ExecStart=/usr/bin/ttyd -p 4860 -W /usr/local/bin/loyx chat
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 4. Enable and start
systemctl daemon-reload
systemctl enable loyx-terminal.service
systemctl start loyx-terminal.service

# 5. Open firewall
ufw allow 4860/tcp
ufw reload

# 6. Verify
systemctl status loyx-terminal.service
curl -I http://localhost:4860  # Should return HTTP/1.1 200
```

Access: `http://<vps-ip>:4860`

## Cost Model Consideration

When exposing Hermes Agent via web terminal, be mindful of the model costs:
- `anthropic/claude-opus-4.6`: Very expensive (128k max_tokens), will quickly exhaust OpenRouter credits
- `anthropic/claude-sonnet-4`: Moderate cost (64k max_tokens)
- `openai/gpt-4o-mini`: Cheapest option, works well for most tasks
- `google/gemini-2.0-flash-thinking-exp`: Free tier available

If users get HTTP 402 errors ("requires more credits"), switch to a cheaper model:
```bash
loyx config set model.default "openai/gpt-4o-mini"
```

This is especially important for web-exposed terminals where multiple users might be chatting simultaneously.
