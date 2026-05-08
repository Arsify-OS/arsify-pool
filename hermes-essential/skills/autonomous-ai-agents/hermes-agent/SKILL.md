---
name: hermes-agent
description: "Configure, extend, or contribute to Hermes Agent."
version: 2.0.0
author: Hermes Agent + Teknium
license: MIT
metadata:
  hermes:
    tags: [hermes, setup, configuration, multi-agent, spawning, cli, gateway, development]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---

# Hermes Agent

Hermes Agent is an open-source AI agent framework by Nous Research that runs in your terminal, messaging platforms, and IDEs. It belongs to the same category as Claude Code (Anthropic), Codex (OpenAI), and OpenClaw — autonomous coding and task-execution agents that use tool calling to interact with your system. Hermes works with any LLM provider (OpenRouter, Anthropic, OpenAI, DeepSeek, local models, and 15+ others) and runs on Linux, macOS, and WSL.

What makes Hermes different:

- **Self-improving through skills** — Hermes learns from experience by saving reusable procedures as skills. When it solves a complex problem, discovers a workflow, or gets corrected, it can persist that knowledge as a skill document that loads into future sessions. Skills accumulate over time, making the agent better at your specific tasks and environment.
- **Persistent memory across sessions** — remembers who you are, your preferences, environment details, and lessons learned. Pluggable memory backends (built-in, Honcho, Mem0, and more) let you choose how memory works.
- **Multi-platform gateway** — the same agent runs on Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, and 10+ other platforms with full tool access, not just chat.
- **Provider-agnostic** — swap models and providers mid-workflow without changing anything else. Credential pools rotate across multiple API keys automatically.
- **Profiles** — run multiple independent Hermes instances with isolated configs, sessions, skills, and memory.
- **Extensible** — plugins, MCP servers, custom tools, webhook triggers, cron scheduling, and the full Python ecosystem.

People use Hermes for software development, research, system administration, data analysis, content creation, home automation, and anything else that benefits from an AI agent with persistent context and full system access.

**This skill helps you work with Hermes Agent effectively** — setting it up, configuring features, spawning additional agent instances, troubleshooting issues, finding the right commands and settings, and understanding how the system works when you need to extend or contribute to it.

**Docs:** https://hermes-agent.nousresearch.com/docs/

## Quick Start

```bash
# Install
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Interactive chat (default)
hermes

# Single query
hermes chat -q "What is the capital of France?"

# Setup wizard
hermes setup

# Change model/provider
hermes model

# Check health
hermes doctor
```

---

## CLI Reference

### Global Flags

```
hermes [flags] [command]

  --version, -V             Show version
  --resume, -r SESSION      Resume session by ID or title
  --continue, -c [NAME]     Resume by name, or most recent session
  --worktree, -w            Isolated git worktree mode (parallel agents)
  --skills, -s SKILL        Preload skills (comma-separate or repeat)
  --profile, -p NAME        Use a named profile
  --yolo                    Skip dangerous command approval
  --pass-session-id         Include session ID in system prompt
```

No subcommand defaults to `chat`.

### Chat

```
hermes chat [flags]
  -q, --query TEXT          Single query, non-interactive
  -m, --model MODEL         Model (e.g. anthropic/claude-sonnet-4)
  -t, --toolsets LIST       Comma-separated toolsets
  --provider PROVIDER       Force provider (openrouter, anthropic, nous, etc.)
  -v, --verbose             Verbose output
  -Q, --quiet               Suppress banner, spinner, tool previews
  --checkpoints             Enable filesystem checkpoints (/rollback)
  --source TAG              Session source tag (default: cli)
```

### Configuration

```
hermes setup [section]      Interactive wizard (model|terminal|gateway|tools|agent)
hermes model                Interactive model/provider picker
hermes config               View current config
hermes config edit          Open config.yaml in $EDITOR
hermes config set KEY VAL   Set a config value
hermes config path          Print config.yaml path
hermes config env-path      Print .env path
hermes config check         Check for missing/outdated config
hermes config migrate       Update config with new options
hermes login [--provider P] OAuth login (nous, openai-codex)
hermes logout               Clear stored auth
hermes doctor [--fix]       Check dependencies and config
hermes status [--all]       Show component status
```

### Tools & Skills

```
hermes tools                Interactive tool enable/disable (curses UI)
hermes tools list           Show all tools and status
hermes tools enable NAME    Enable a toolset
hermes tools disable NAME   Disable a toolset

hermes skills list          List installed skills
hermes skills search QUERY  Search the skills hub
hermes skills install ID    Install a skill (ID can be a hub identifier OR a direct https://…/SKILL.md URL; pass --name to override when frontmatter has no name)
hermes skills inspect ID    Preview without installing
hermes skills config        Enable/disable skills per platform
hermes skills check         Check for updates
hermes skills update        Update outdated skills
hermes skills uninstall N   Remove a hub skill
hermes skills publish PATH  Publish to registry
hermes skills browse        Browse all available skills
hermes skills tap add REPO  Add a GitHub repo as skill source
```

### MCP Servers

```
hermes mcp serve            Run Hermes as an MCP server
hermes mcp add NAME         Add an MCP server (--url or --command)
hermes mcp remove NAME      Remove an MCP server
hermes mcp list             List configured servers
hermes mcp test NAME        Test connection
hermes mcp configure NAME   Toggle tool selection
```

### Gateway (Messaging Platforms)

```
hermes gateway run          Start gateway foreground
hermes gateway install      Install as background service
hermes gateway start/stop   Control the service
hermes gateway restart      Restart the service
hermes gateway status       Check status
hermes gateway setup        Configure platforms
```

Supported platforms: Telegram, Discord, Slack, WhatsApp, Signal, Email, SMS, Matrix, Mattermost, Home Assistant, DingTalk, Feishu, WeCom, BlueBubbles (iMessage), Weixin (WeChat), API Server, Webhooks. Open WebUI connects via the API Server adapter.

Platform docs: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/

#### Gateway Host Binding

**Default behavior:** Gateway binds to `127.0.0.1:8642` (localhost only).

**To expose gateway API externally** (for Hermes Workspace, Open WebUI, or LAN access):

1. **Via environment variables** (recommended for Docker):
   ```bash
   export API_SERVER_ENABLED=true
   export API_SERVER_HOST=0.0.0.0
   export API_SERVER_PORT=8642
   hermes gateway run
   ```

2. **Via config.yaml** (not currently supported - environment variables only):
   ```yaml
   # This does NOT work - gateway ignores config.yaml host/port
   gateway:
     host: 0.0.0.0
     port: 8642
   ```

**Docker Compose pattern:**
```yaml
hermes-agent:
  image: nousresearch/hermes-agent:latest
  command: ["hermes", "gateway", "run"]  # Use "run" not "start" for containers
  environment:
    API_SERVER_ENABLED: 'true'
    API_SERVER_HOST: ${API_SERVER_HOST:-127.0.0.1}
    API_SERVER_PORT: ${API_SERVER_PORT:-8642}
    API_SERVER_KEY: ${API_SERVER_KEY:-}  # Set for authentication
  extra_hosts:
    - "host.docker.internal:host-gateway"  # Required for accessing host services
```

**Pitfall**: Using `hermes gateway start` in containers causes restart loops. The `start` command is for systemd services on the host. Containers must use `hermes gateway run` as the main process.

**Security note:** When exposing gateway on 0.0.0.0, always set `API_SERVER_KEY` for authentication.

**Custom proxy/router setup:** For routing containerized Hermes through a custom proxy (9router, LiteLLM, etc.) running on the host, see `references/docker-custom-proxy.md` for complete configuration including:
- Correct config file paths (`/opt/data/config.yaml`, not `/root/.hermes/config.yaml`)
- Provider "custom" (not "openai") with base_url
- Context window minimum (128K, not 32K)
- Host networking via `extra_hosts`
- Dummy API key requirement

**Gateway port architecture:**
- Port 8642 (default) binds to **127.0.0.1 only** — this is intentional. It's an internal webhook/cron coordinator, not a public API endpoint.
- Messaging platforms connect **outbound** from the gateway to their services (Telegram, Discord, etc.), not inbound to port 8642.
- The **API Server** platform (when enabled via `API_SERVER_ENABLED=true`) provides HTTP access and can be configured with `API_SERVER_HOST` and `API_SERVER_PORT` environment variables.
- `hermes gateway run` does NOT accept `--host` or `--port` flags. Configuration is via environment variables or config.yaml only.

### Sessions

```
hermes sessions list        List recent sessions
hermes sessions browse      Interactive picker
hermes sessions export OUT  Export to JSONL
hermes sessions rename ID T Rename a session
hermes sessions delete ID   Delete a session
hermes sessions prune       Clean up old sessions (--older-than N days)
hermes sessions stats       Session store statistics
```

### Cron Jobs

```
hermes cron list            List jobs (--all for disabled)
hermes cron create SCHED    Create: '30m', 'every 2h', '0 9 * * *'
hermes cron edit ID         Edit schedule, prompt, delivery
hermes cron pause/resume ID Control job state
hermes cron run ID          Trigger on next tick
hermes cron remove ID       Delete a job
hermes cron status          Scheduler status
```

### Webhooks

```
hermes webhook subscribe N  Create route at /webhooks/<name>
hermes webhook list         List subscriptions
hermes webhook remove NAME  Remove a subscription
hermes webhook test NAME    Send a test POST
```

### Profiles

```
hermes profile list         List all profiles
hermes profile create NAME  Create (--clone, --clone-all, --clone-from)
hermes profile use NAME     Set sticky default
hermes profile delete NAME  Delete a profile
hermes profile show NAME    Show details
hermes profile alias NAME   Manage wrapper scripts
hermes profile rename A B   Rename a profile
hermes profile export NAME  Export to tar.gz
hermes profile import FILE  Import from archive
hermes profile import FILE  Import from archive

### Profile-Specific Skill Configuration
To load skills automatically for a profile, edit `~/.hermes/profiles/<name>/config.yaml` and add:
```yaml
skills:
  default: [skill-name-1, skill-name-2]
```
This ensures the skill is loaded every time the profile is used, without needing `-s` flags or in-session `/skill` commands.

For common multi-agent use cases, create dedicated profiles (e.g., `server` for VPS management, `domain` for DNS/SSL, `ai-team` for coding agents) with isolated tools, skills, and memory.

### Credential Pools

```
hermes auth add             Interactive credential wizard
hermes auth list [PROVIDER] List pooled credentials
hermes auth remove P INDEX  Remove by provider + index
hermes auth reset PROVIDER  Clear exhaustion status
```

### Other

```
hermes insights [--days N]  Usage analytics
hermes update               Update to latest version (if blocked, use manual steps below) (if blocked, see Troubleshooting > Update Fails)
hermes pairing list/approve/revoke  DM authorization
hermes plugins list/install/remove  Plugin management
hermes honcho setup/status  Honcho memory integration (requires honcho plugin)
hermes memory setup/status/off  Memory provider config
hermes completion bash|zsh  Shell completions
hermes acp                  ACP server (IDE integration)
hermes claw migrate         Migrate from OpenClaw
hermes uninstall            Uninstall Hermes
```

---

## Slash Commands (In-Session)

Type these during an interactive chat session.

### Session Control
```
/new (/reset)        Fresh session
/clear               Clear screen + new session (CLI)
/retry               Resend last message
/undo                Remove last exchange
/title [name]        Name the session
/compress            Manually compress context
/stop                Kill background processes
/rollback [N]        Restore filesystem checkpoint
/background <prompt> Run prompt in background
/queue <prompt>      Queue for next turn
/resume [name]       Resume a named session
```

### Configuration
```
/config              Show config (CLI)
/model [name]        Show or change model
/personality [name]  Set personality
/reasoning [level]   Set reasoning (none|minimal|low|medium|high|xhigh|show|hide)
/verbose             Cycle: off → new → all → verbose
/voice [on|off|tts]  Voice mode
/yolo                Toggle approval bypass
/skin [name]         Change theme (CLI)
/statusbar           Toggle status bar (CLI)
```

### Tools & Skills
```
/tools               Manage tools (CLI)
/toolsets            List toolsets (CLI)
/skills              Search/install skills (CLI)
/skill <name>        Load a skill into session
/cron                Manage cron jobs (CLI)
/reload-mcp          Reload MCP servers
/plugins             List plugins (CLI)
```

### Gateway
```
/approve             Approve a pending command (gateway)
/deny                Deny a pending command (gateway)
/restart             Restart gateway (gateway)
/sethome             Set current chat as home channel (gateway)
/update              Update Hermes to latest (gateway)
/platforms (/gateway) Show platform connection status (gateway)
```

### Utility
```
/branch (/fork)      Branch the current session
/fast                Toggle priority/fast processing
/browser             Open CDP browser connection
/history             Show conversation history (CLI)
/save                Save conversation to file (CLI)
/paste               Attach clipboard image (CLI)
/image               Attach local image file (CLI)
```

### Info
```
/help                Show commands
/commands [page]     Browse all commands (gateway)
/usage               Token usage
/insights [days]     Usage analytics
/status              Session info (gateway)
/profile             Active profile info
```

### Exit
```
/quit (/exit, /q)    Exit CLI
```

---

## Key Paths & Config

```
~/.hermes/config.yaml       Main configuration
~/.hermes/.env              API keys and secrets
$HERMES_HOME/skills/        Installed skills
~/.hermes/sessions/         Session transcripts
~/.hermes/logs/             Gateway and error logs
~/.hermes/auth.json         OAuth tokens and credential pools
~/.hermes/hermes-agent/     Source code (if git-installed)
```

Profiles use `~/.hermes/profiles/<name>/` with the same layout.

### Config Sections

Edit with `hermes config edit` or `hermes config set section.key value`.

| Section | Key options |
|---------|-------------|
| `model` | `default`, `provider`, `base_url`, `api_key`, `context_length` |
| `agent` | `max_turns` (90), `tool_use_enforcement` |
| `terminal` | `backend` (local/docker/ssh/modal), `cwd`, `timeout` (180) |
| `compression` | `enabled`, `threshold` (0.50), `target_ratio` (0.20) |
| `display` | `skin`, `tool_progress`, `show_reasoning`, `show_cost` |
| `stt` | `enabled`, `provider` (local/groq/openai/mistral) |
| `tts` | `provider` (edge/elevenlabs/openai/minimax/mistral/neutts) |
| `memory` | `memory_enabled`, `user_profile_enabled`, `provider` |
| `security` | `tirith_enabled`, `website_blocklist` |
| `delegation` | `model`, `provider`, `base_url`, `api_key`, `max_iterations` (50), `reasoning_effort` |
| `checkpoints` | `enabled`, `max_snapshots` (50) |

Full config reference: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

### Providers

20+ providers supported. Set via `hermes model` or `hermes setup`.

| Provider | Auth | Key env var |
|----------|------|-------------|
| OpenRouter | API key | `OPENROUTER_API_KEY` |
| Anthropic | API key | `ANTHROPIC_API_KEY` |
| Nous Portal | OAuth | `hermes auth` |
| OpenAI Codex | OAuth | `hermes auth` |
| GitHub Copilot | Token | `COPILOT_GITHUB_TOKEN` |
| Google Gemini | API key | `GOOGLE_API_KEY` or `GEMINI_API_KEY` |
| DeepSeek | API key | `DEEPSEEK_API_KEY` |
| xAI / Grok | API key | `XAI_API_KEY` |
| Hugging Face | Token | `HF_TOKEN` |
| Z.AI / GLM | API key | `GLM_API_KEY` |
| MiniMax | API key | `MINIMAX_API_KEY` |
| MiniMax CN | API key | `MINIMAX_CN_API_KEY` |
| Kimi / Moonshot | API key | `KIMI_API_KEY` |
| Alibaba / DashScope | API key | `DASHSCOPE_API_KEY` |
| Xiaomi MiMo | API key | `XIAOMI_API_KEY` |
| Kilo Code | API key | `KILOCODE_API_KEY` |
| AI Gateway (Vercel) | API key | `AI_GATEWAY_API_KEY` |
| OpenCode Zen | API key | `OPENCODE_ZEN_API_KEY` |
| OpenCode Go | API key | `OPENCODE_GO_API_KEY` |
| Qwen OAuth | OAuth | `hermes login --provider qwen-oauth` |
| Custom endpoint | Config | `model.base_url` + `model.api_key` in config.yaml | For 9Router setup, see `references/9router-custom-provider.md` |
| GitHub Copilot ACP | External | `COPILOT_CLI_PATH` or Copilot CLI |

Full provider docs: https://hermes-agent.nousresearch.com/docs/integrations/providers

### Toolsets

Enable/disable via `hermes tools` (interactive) or `hermes tools enable/disable NAME`.

| Toolset | What it provides |
|---------|-----------------|
| `web` | Web search and content extraction |
| `browser` | Browser automation (Browserbase, Camofox, or local Chromium) |
| `terminal` | Shell commands and process management |
| `file` | File read/write/search/patch |
| `code_execution` | Sandboxed Python execution |
| `vision` | Image analysis |
| `image_gen` | AI image generation |
| `tts` | Text-to-speech |
| `skills` | Skill browsing and management |
| `memory` | Persistent cross-session memory |
| `session_search` | Search past conversations |
| `delegation` | Subagent task delegation |
| `cronjob` | Scheduled task management |
| `clarify` | Ask user clarifying questions |
| `messaging` | Cross-platform message sending |
| `search` | Web search only (subset of `web`) |
| `todo` | In-session task planning and tracking |
| `rl` | Reinforcement learning tools (off by default) |
| `moa` | Mixture of Agents (off by default) |
| `homeassistant` | Smart home control (off by default) |

Tool changes take effect on `/reset` (new session). They do NOT apply mid-conversation to preserve prompt caching.

---

## Security & Privacy Toggles

Common "why is Hermes doing X to my output / tool calls / commands?" toggles — and the exact commands to change them. Most of these need a fresh session (`/reset` in chat, or start a new `hermes` invocation) because they're read once at startup.

### Secret redaction in tool output

Secret redaction is **off by default** — tool output (terminal stdout, `read_file`, web content, subagent summaries, etc.) passes through unmodified. If the user wants Hermes to auto-mask strings that look like API keys, tokens, and secrets before they enter the conversation context and logs:

```bash
hermes config set security.redact_secrets true       # enable globally
```

**Restart required.** `security.redact_secrets` is snapshotted at import time — toggling it mid-session (e.g. via `export HERMES_REDACT_SECRETS=true` from a tool call) will NOT take effect for the running process. Tell the user to run `hermes config set security.redact_secrets true` in a terminal, then start a new session. This is deliberate — it prevents an LLM from flipping the toggle on itself mid-task.

Disable again with:
```bash
hermes config set security.redact_secrets false
```

### PII redaction in gateway messages

Separate from secret redaction. When enabled, the gateway hashes user IDs and strips phone numbers from the session context before it reaches the model:

```bash
hermes config set privacy.redact_pii true    # enable
hermes config set privacy.redact_pii false   # disable (default)
```

### Command approval prompts

By default (`approvals.mode: manual`), Hermes prompts the user before running shell commands flagged as destructive (`rm -rf`, `git reset --hard`, etc.). The modes are:

- `manual` — always prompt (default)
- `smart` — use an auxiliary LLM to auto-approve low-risk commands, prompt on high-risk
- `off` — skip all approval prompts (equivalent to `--yolo`)

```bash
hermes config set approvals.mode smart       # recommended middle ground
hermes config set approvals.mode off         # bypass everything (not recommended)
```

Per-invocation bypass without changing config:
- `hermes --yolo …`
- `export HERMES_YOLO_MODE=1`

Note: YOLO / `approvals.mode: off` does NOT turn off secret redaction. They are independent.

### Shell hooks allowlist

Some shell-hook integrations require explicit allowlisting before they fire. Managed via `~/.hermes/shell-hooks-allowlist.json` — prompted interactively the first time a hook wants to run.

### Disabling the web/browser/image-gen tools

To keep the model away from network or media tools entirely, open `hermes tools` and toggle per-platform. Takes effect on next session (`/reset`). See the Tools & Skills section above.

---

## Voice & Transcription

### STT (Voice → Text)

Voice messages from messaging platforms are auto-transcribed.

Provider priority (auto-detected):
1. **Local faster-whisper** — free, no API key: `pip install faster-whisper`
2. **Groq Whisper** — free tier: set `GROQ_API_KEY`
3. **OpenAI Whisper** — paid: set `VOICE_TOOLS_OPENAI_KEY`
4. **Mistral Voxtral** — set `MISTRAL_API_KEY`

Config:
```yaml
stt:
  enabled: true
  provider: local        # local, groq, openai, mistral
  local:
    model: base          # tiny, base, small, medium, large-v3
```

### TTS (Text → Voice)

| Provider | Env var | Free? |
|----------|---------|-------|
| Edge TTS | None | Yes (default) |
| ElevenLabs | `ELEVENLABS_API_KEY` | Free tier |
| OpenAI | `VOICE_TOOLS_OPENAI_KEY` | Paid |
| MiniMax | `MINIMAX_API_KEY` | Paid |
| Mistral (Voxtral) | `MISTRAL_API_KEY` | Paid |
| NeuTTS (local) | None (`pip install neutts[all]` + `espeak-ng`) | Free |

Voice commands: `/voice on` (voice-to-voice), `/voice tts` (always voice), `/voice off`.

---

## Spawning Additional Hermes Instances

Run additional Hermes processes as fully independent subprocesses — separate sessions, tools, and environments.

### When to Use This vs delegate_task

| | `delegate_task` | Spawning `hermes` process |
|-|-----------------|--------------------------|
| Isolation | Separate conversation, shared process | Fully independent process |
| Duration | Minutes (bounded by parent loop) | Hours/days |
| Tool access | Subset of parent's tools | Full tool access |
| Interactive | No | Yes (PTY mode) |
| Use case | Quick parallel subtasks | Long autonomous missions |

### One-Shot Mode

```
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)

# Background for long tasks:
terminal(command="hermes chat -q 'Set up CI/CD for ~/myapp'", background=true)
```

### Interactive PTY Mode (via tmux)

Hermes uses prompt_toolkit, which requires a real terminal. Use tmux for interactive spawning:

```
# Start
terminal(command="tmux new-session -d -s agent1 -x 120 -y 40 'hermes'", timeout=10)

# Wait for startup, then send a message
terminal(command="sleep 8 && tmux send-keys -t agent1 'Build a FastAPI auth service' Enter", timeout=15)

# Read output
terminal(command="sleep 20 && tmux capture-pane -t agent1 -p", timeout=5)

# Send follow-up
terminal(command="tmux send-keys -t agent1 'Add rate limiting middleware' Enter", timeout=5)

# Exit
terminal(command="tmux send-keys -t agent1 '/exit' Enter && sleep 2 && tmux kill-session -t agent1", timeout=10)
```

### Multi-Agent Coordination

**Important limitation:** Hermes Agent has **no built-in agent-to-agent communication protocol**. Agents cannot directly message each other, share state, or coordinate via API calls. Multi-agent setups require external coordination mechanisms.

#### Communication Patterns

**1. File-based coordination** (recommended for async workflows):
```bash
# Orchestrator writes task file
echo "Analyze game architecture" > /workspace/TASK_001.md

# Worker agent reads task file via docker exec or shared volume
docker exec worker-agent hermes chat -q "$(cat /workspace/TASK_001.md)"

# Worker writes results
# Orchestrator polls for completion file
```

**2. Tmux relay pattern** (for interactive coordination):
```bash
# Agent A: backend
terminal(command="tmux new-session -d -s backend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t backend 'Build REST API for user management' Enter", timeout=15)

# Agent B: frontend
terminal(command="tmux new-session -d -s frontend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t frontend 'Build React dashboard for user management' Enter", timeout=15)

# Orchestrator manually relays context between agents
terminal(command="tmux capture-pane -t backend -p | tail -30", timeout=5)
terminal(command="tmux send-keys -t frontend 'Here is the API schema from the backend agent: ...' Enter", timeout=5)
```

**3. Shared message queue** (external tool):
Use Redis, RabbitMQ, or filesystem queue with agents polling for tasks.

#### Pitfalls

- **No HTTP gateway for agent-to-agent calls**: Gateway port 8642 is for webhooks/cron, not inter-agent RPC. The API Server platform (when enabled) provides HTTP access but is designed for external clients, not agent coordination.
- **Docker exec limitations**: `hermes chat -q` works for one-shot tasks but has no streaming, no interactive feedback, and no way to cancel mid-execution.
- **Context limits**: Large files (>100KB) cause context exhaustion. Use strategic sampling (read key sections) instead of full file reads.
- **Credit exhaustion**: Expensive models (claude-opus-4) can exhaust API credits quickly on large tasks. Use cheaper models (gpt-4o-mini) for worker agents or switch to local models.

### Session Resume

```bash
# Resume most recent session
terminal(command="tmux new-session -d -s resumed 'hermes --continue'", timeout=10)

# Resume specific session
terminal(command="tmux new-session -d -s resumed 'hermes --resume 20260225_143052_a1b2c3'", timeout=10)
```

### Managing Docker Compose Hermes Instances

When deploying Hermes via Docker Compose (e.g., Hostinger VPS image `ghcr.io/hostinger/hvps-hermes-agent:latest`), Compose automatically names containers as `{project_name}-{service_name}-{index}` (e.g., `hermes-agent-wjsc-hermes-agent-1`).

#### Renaming a Compose Project & Container
1. Stop the existing project:
   ```bash
   cd /path/to/old/project && docker compose down
   ```
2. Rename the project directory to the new project name:
   ```bash
   mv /path/to/old/project /path/to/new/project
   ```
3. Edit `docker-compose.yml` to set an explicit container name:
   ```yaml
   services:
     hermes-agent:
       container_name: desired-container-name  # e.g., agent-hermes-ceo
       image: ghcr.io/hostinger/hvps-hermes-agent:latest
       # ... rest of config
   ```
4. Add `COMPOSE_PROJECT_NAME` to the project's `.env` file:
   ```bash
   echo "COMPOSE_PROJECT_NAME=new-project-name" >> /path/to/new/project/.env
   ```
5. Start the renamed project:
   ```bash
   cd /path/to/new/project && docker compose up -d
   ```
6. Verify:
   ```bash
   docker compose ls | grep new-project-name
   docker ps --format "table {{.Names}}\t{{.Status}}"
   ```

#### Pitfall: Missing Docker Resources in Checks
When checking for existing Docker-based Hermes instances, avoid relying solely on partial name filters (e.g., `docker ps -a --filter name=partial-name`). Compose's auto-generated container names may not match partial filters. Instead:
- List all Compose projects first: `docker compose ls`
- List all containers without restrictive filters: `docker ps -a`
- Check for Hostinger VPS images specifically: `docker images | grep hvps-hermes-agent`

### Tips
When verifying if a Hermes Docker container/project already exists:
1. List all Docker Compose projects (no filter first to catch all):
   ```bash
   docker compose ls
   ```
2. Search for containers with partial name matches using glob patterns (`*`):
   ```bash
   # Correct: use * for substring match
   docker ps -a --filter name=*hermes-agent-wjsc* --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
   
   # Incorrect: without * will only match exact container names
   # docker ps -a --filter name=hermes-agent-wjsc  # MISSES containers with longer names like hermes-agent-wjsc-hermes-agent-1
   ```
3. Check common Docker Compose directories:
   ```bash
   ls -la /docker/ 2>/dev/null || echo "No /docker directory"
   ```

**Pitfall**: Docker's `--filter name=<value>` without `*` only matches exact container names, missing containers with suffixes (e.g., `-hermes-agent-1` added by Docker Compose). Always use `name=*partial-name*` for substring searches.

### Tips

- **Prefer `delegate_task` for quick subtasks** — less overhead than spawning a full process
- **Use `-w` (worktree mode)** when spawning agents that edit code — prevents git conflicts
- **Set timeouts** for one-shot mode — complex tasks can take 5-10 minutes
- **Use `hermes chat -q` for fire-and-forget** — no PTY needed
- **Use tmux for interactive sessions** — raw PTY mode has `\\\\\\\\r` vs `\\\\\\\\n` issues with prompt_toolkit
- **For scheduled tasks**, use the `cronjob` tool instead of spawning — handles delivery and retry
- **For long-running executive/C-Suite agents**, create a dedicated profile via `hermes profile create <name>` with isolated config, skills, and memory instead of spawning ephemeral processes.
- **For multi-agent orchestration patterns** (orchestrator + specialists), see `references/multi-agent-game-dev-pattern.md` for complete Docker Compose setup, file-based communication, automated monitoring via cron, and notification strategies (file-based, WhatsApp, Telegram).
- **For building orchestration infrastructure from scratch** (shared memory, task coordination, workflow automation), see `references/multi-agent-orchestration-foundation.md` for the incremental implementation pattern starting with SQLite-based shared memory as the foundation for "Hive Mind" coordination.
- **For large file analysis** (>100KB, 1000+ lines), use strategic code sampling instead of full reads to avoid context exhaustion. See `references/large-file-analysis.md` for techniques.

---

## Troubleshooting

### Voice not working
1. Check `stt.enabled: true` in config.yaml
2. Verify provider: `pip install faster-whisper` or set API key
3. In gateway: `/restart`. In CLI: exit and relaunch.

### Tool not available
1. `hermes tools` — check if toolset is enabled for your platform
2. Some tools need env vars (check `.env`)
3. `/reset` after enabling tools

### Model/provider issues
1. `hermes doctor` — check config and dependencies
2. `hermes login` — re-authenticate OAuth providers
3. Check `.env` has the right API key
4. **Copilot 403**: `gh auth login` tokens do NOT work for Copilot API. You must use the Copilot-specific OAuth device code flow via `hermes model` → GitHub Copilot.
5. **OpenRouter credit exhaustion**: Check remaining credits at https://openrouter.ai/settings/credits before large tasks. Symptoms: HTTP 402 errors, "prompt tokens limit exceeded". Solutions: top up credits, switch to cheaper model (gpt-4o-mini), or use local models via Ollama.
6. **Docker container "No inference provider configured"**: Config file must be mounted to `/opt/data/config.yaml` (not `/root/.hermes/config.yaml`). See `references/docker-custom-proxy.md` for complete Docker configuration checklist.

### Changes not taking effect
- **Tools/skills:** `/reset` starts a new session with updated toolset
- **Config changes:** In gateway: `/restart`. In CLI: exit and relaunch.
- **Code changes:** Restart the CLI or gateway process

### Skills not showing
1. `hermes skills list` — verify installed
2. `hermes skills config` — check platform enablement
3. Load explicitly: `/skill name` or `hermes -s name`

### Gateway issues
Check logs first:
```bash
grep -i "failed to send\|error" ~/.hermes/logs/gateway.log | tail -20
```

Common gateway problems:
- **Gateway dies on SSH logout**: Enable linger: `sudo loginctl enable-linger $USER`
- **Gateway dies on WSL2 close**: WSL2 requires `systemd=true` in `/etc/wsl.conf` for systemd services to work. Without it, gateway falls back to `nohup` (dies when session closes).
- **Gateway crash loop**: Reset the failed state: `systemctl --user reset-failed hermes-gateway`
- **Gateway binds to 127.0.0.1 only**: Set `API_SERVER_HOST=0.0.0.0` environment variable before running `hermes gateway run`. Config.yaml gateway section is not read by gateway command.
- **Port 8642 already in use**: Another hermes-gateway instance is running. Check with `lsof -i :8642` and kill conflicting process, or use different port with `API_SERVER_PORT=8643`.
- **Port 8642 not accessible externally**: This is expected — port 8642 is localhost-only by design (internal webhook/cron). If you need HTTP API access, enable the API Server platform with `API_SERVER_ENABLED=true`, `API_SERVER_HOST=0.0.0.0`, and `API_SERVER_PORT=<port>` in your gateway startup script or environment.

### Platform-specific issues
- **Discord bot silent**: Must enable **Message Content Intent** in Bot → Privileged Gateway Intents.
- **Slack bot only works in DMs**: Must subscribe to `message.channels` event. Without it, the bot ignores public channels.
- **Windows HTTP 400 "No models provided"**: Config file encoding issue (BOM). Ensure `config.yaml` is saved as UTF-8 without BOM.
- **PM2 environment variables not updating**: PM2 caches environment variables. After changing a startup script's `export` statements, use `pm2 delete <name>` then `pm2 start <script>` instead of `pm2 restart`. The `--update-env` flag only works for variables passed via `pm2 start --env`.

### Auxiliary models not working
Common error messages:
- `No auxiliary LLM provider configured — context compression will drop middle turns without a summary`
- `No LLM provider configured for task=<task> provider=auto`
- Silent failures for title_generation, vision, compression, session_search

Root cause: The `auto` provider can't find a backend, or explicitly set provider/model is invalid.

**Fix**: Explicitly set provider + model for each auxiliary task. Use the same model as the main model for consistency:

```bash
hermes config set auxiliary.compression.provider openrouter
hermes config set auxiliary.compression.model openrouter/owl-alpha
hermes config set auxiliary.title_generation.provider openrouter
hermes config set auxiliary.title_generation.model openrouter/owl-alpha
hermes config set auxiliary.session_search.provider openrouter
hermes config set auxiliary.session_search.model openrouter/owl-alpha
hermes config set auxiliary.vision.provider openrouter
hermes config set auxiliary.vision.model openrouter/owl-alpha
hermes config set auxiliary.web_extract.provider openrouter
hermes config set auxiliary.web_extract.model openrouter/owl-alpha
```

#### Pitfall: `openai/` prefixed models on OpenRouter
Models like `openai/gpt-4o-mini` may return HTTP 401 "User not found" on OpenRouter even with a valid key. Use `openrouter/<model>` prefix instead.

#### Pitfall: Empty `api_key: ''`
Setting `api_key: ''` in any `auxiliary.*` section overrides env var lookup. Remove empty `api_key` and `base_url` lines entirely.

#### Pitfall: Custom provider rate limits
Custom providers (e.g., Kiro/9Router) may have monthly request caps (HTTP 402 `MONTHLY_REQUEST_COUNT`). Don't use them for auxiliary tasks that fire frequently.

#### Pitfall: Compression threshold mismatch
If the auxiliary model has a smaller context window than the main model's threshold, Hermes auto-lowers it. Fix: raise `compression.threshold` to 0.75+.

For full debug transcript and test commands, see `references/auxiliary-model-config.md` in the hermes-agent-ops skill.

### Voice not working

### VPS Maintenance
See `references/vps-disk-cleanup.md` for a proven workflow to clean VPS disk space when only Hermes Agent and base Linux are required.

### Updating Hermes Agent (Manual Steps)
If `hermes update` is blocked or fails:
1. Stash local changes in the Hermes Agent repo:
   ```bash
   cd /usr/local/lib/hermes-agent && git stash
   ```
2. Pull latest commits:
   ```bash
   git pull origin main
   ```
3. If the venv (at `/usr/local/lib/hermes-agent/venv`) lacks pip:
   ```bash
   cd /usr/local/lib/hermes-agent && ./venv/bin/python -m ensurepip
   ```
4. Reinstall Hermes Agent using the venv's pip3:
   ```bash
   ./venv/bin/pip3 install -e .
   ```
5. Verify the update by checking the latest commit (ignore stale `hermes --version` "commits behind" message):
   ```bash
   cd /usr/local/lib/hermes-agent && git log --oneline -1
   ```

**Pitfall**: After manual update, `hermes --version` may still show a stale "X commits behind" message. This is a cache issue — verify the actual commit hash with `git log` in the hermes-agent directory.

**Alternative**: If git stash fails, remove the old install (as per existing procedure):
```bash
rm -rf /usr/local/lib/hermes-agent && rm -f /usr/local/bin/hermes
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Where to Find Things

| Looking for... | Location |
|----------------|----------|
| Config options | `hermes config edit` or [Configuration docs](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Available tools | `hermes tools list` or [Tools reference](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| Slash commands | `/help` in session or [Slash commands reference](https://hermes-agent.nousresearch.com/docs/reference/slash-commands) |
| Skills catalog | `hermes skills browse` or [Skills catalog](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| Provider setup | `hermes model` or [Providers guide](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| Platform setup | `hermes gateway setup` or [Messaging docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/) |
| MCP servers | `hermes mcp list` or [MCP guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) |
| Profiles | `hermes profile list` or [Profiles docs](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) |
| Cron jobs | `hermes cron list` or [Cron docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) |
| Memory | `hermes memory status` or [Memory docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| Env variables | `hermes config env-path` or [Env vars reference](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) |
| CLI commands | `hermes --help` or [CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) |
| Gateway logs | `~/.hermes/logs/gateway.log` |
| Session files | `~/.hermes/sessions/` or `hermes sessions browse` |
| Source code | `~/.hermes/hermes-agent/` |

---

## Contributor Quick Reference

For occasional contributors and PR authors. Full developer docs: https://hermes-agent.nousresearch.com/docs/developer-guide/

### Project Layout

```
hermes-agent/
├── run_agent.py          # AIAgent — core conversation loop
├── model_tools.py        # Tool discovery and dispatch
├── toolsets.py           # Toolset definitions
├── cli.py                # Interactive CLI (HermesCLI)
├── hermes_state.py       # SQLite session store
├── agent/                # Prompt builder, context compression, memory, model routing, credential pooling, skill dispatch
├── hermes_cli/           # CLI subcommands, config, setup, commands
│   ├── commands.py       # Slash command registry (CommandDef)
│   ├── config.py         # DEFAULT_CONFIG, env var definitions
│   └── main.py           # CLI entry point and argparse
├── tools/                # One file per tool
│   └── registry.py       # Central tool registry
├── gateway/              # Messaging gateway
│   └── platforms/        # Platform adapters (telegram, discord, etc.)
├── cron/                 # Job scheduler
├── tests/                # ~3000 pytest tests
└── website/              # Docusaurus docs site
```

Config: `~/.hermes/config.yaml` (settings), `~/.hermes/.env` (API keys).

### Adding a Tool (3 files)

**1. Create `tools/your_tool.py`:**
```python
import json, os
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(
        param=args.get("param", ""), task_id=kw.get("task_id")),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**2. Add to `toolsets.py`** → `_HERMES_CORE_TOOLS` list.

Auto-discovery: any `tools/*.py` file with a top-level `registry.register()` call is imported automatically — no manual list needed.

All handlers must return JSON strings. Use `get_hermes_home()` for paths, never hardcode `~/.hermes`.

### Adding a Slash Command

1. Add `CommandDef` to `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. Add handler in `cli.py` → `process_command()`
3. (Optional) Add gateway handler in `gateway/run.py`

All consumers (help text, autocomplete, Telegram menu, Slack mapping) derive from the central registry automatically.

### Agent Loop (High Level)

```
run_conversation():
  1. Build system prompt
  2. Loop while iterations < max:
     a. Call LLM (OpenAI-format messages + tool schemas)
     b. If tool_calls → dispatch each via handle_function_call() → append results → continue
     c. If text response → return
  3. Context compression triggers automatically near token limit
```

### Testing

```bash
python -m pytest tests/ -o 'addopts=' -q   # Full suite
python -m pytest tests/tools/ -q            # Specific area
```

- Tests auto-redirect `HERMES_HOME` to temp dirs — never touch real `~/.hermes/`
- Run full suite before pushing any change
- Use `-o 'addopts='` to clear any baked-in pytest flags

### Commit Conventions

```
type: concise subject line

Optional body.
```

Types: `fix:`, `feat:`, `refactor:`, `docs:`, `chore:`

### Key Rules

- **Never break prompt caching** — don't change context, tools, or system prompt mid-conversation
- **Message role alternation** — never two assistant or two user messages in a row
- Use `get_hermes_home()` from `hermes_constants` for all paths (profile-safe)
- Config values go in `config.yaml`, secrets go in `.env`
- New tools need a `check_fn` so they only appear when requirements are met
