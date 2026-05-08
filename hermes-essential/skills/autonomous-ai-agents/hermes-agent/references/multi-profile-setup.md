# Multi-Profile Hermes Setup for Specialized Workloads

Steps to create isolated Hermes profiles for different use cases (e.g., server management, domain management, AI team orchestration):

## 1. Create Profiles
Clone from default profile to inherit base config:
```bash
hermes profile create server --clone-from default
hermes profile create domain --clone-from default
hermes profile create progamer-team --clone-from default
```

Each profile gets its own directory at `~/.hermes/profiles/<name>/` with isolated config, sessions, skills, and memory.

## 2. Configure Profile-Specific Toolsets
Enable toolsets relevant to the profile's use case (NOT skills — toolsets are `terminal`, `web`, `cronjob`, etc.):
```bash
# For server management profile
server tools enable terminal file cronjob skills session_search

# For domain management profile
domain tools enable terminal file web cronjob skills

# For AI team profile (add after installing autonomous-ai-agents skills)
progamer-team tools enable terminal file delegation autonomous-ai-agents skills
```

## 3. Add Default Skills to Profiles
Edit the profile's `config.yaml` to load skills automatically on startup:
```yaml
# ~/.hermes/profiles/server/config.yaml
skills:
  default: [vps-system-inspection]

# ~/.hermes/profiles/progamer-team/config.yaml
skills:
  default: [claude-code, codex, workspace-dispatch]
```

**Pitfall**: Do NOT try to enable skills via `hermes tools enable` — skills are not toolsets and this will fail with "Unknown toolset".

## 4. Verify Profiles
List all profiles and check their configuration:
```bash
hermes profile list
cat ~/.hermes/profiles/server/config.yaml
```

## 5. Use Profiles
Start a chat session with a specific profile:
```bash
server chat
domain chat
progamer-team chat
```

Or run as a background gateway service:
```bash
server gateway start
```
