# Arsify Core Rebranding & Security Workflow (2026-05-08)

## Purpose
Remove traces linking the Arsify Core system to its original creator (Hermes Agent) to improve security and anonymity.

## Step-by-Step Workflow

### 1. Prepare Rebrand Mapping
Create a mapping of old → new terms:
| Old (Hermes) | New (Upshalter) |
|---------------|-----------------|
| `HERMES_API` | `UPSHALTER_API` |
| `HERMES_API_KEY` | `UPSHALTER_API_KEY` |
| `hermes-secret-change-me-in-production` | `upshalter-secret-change-me-in-production` |
| `/root/.hermes` | `/root/.upshalter` |
| `/opt/hermes-cognitive` | `/opt/upshalter-cognitive` |
| `hermes/senator/` | `upshalter/senator/` |
| Any case-insensitive "hermes" in comments/docs | "upshalter" |

### 2. Update Source Code
- Python scripts: Replace all env vars, paths, and comments
- Shell scripts: Replace CLI calls (e.g., `hermes` CLI → curl Telegram)
- Use dynamic path detection (already covered in hardcoded path fix)

### 3. Update Documentation
- `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `DEPLOYMENT.md`
- Replace all references to "Hermes Cognitive Engine" → "Upshalter Cognitive Engine"
- Update code examples to use new env var names

### 4. Update Config Templates
- `.env.example`: Replace `HERMES_*` with `UPSHALTER_*`, add Telegram vars
- Deploy configs: Update systemd service to use `UPSHALTER_*` if applicable

### 5. Full Scan
```bash
cd /path/to/arsify-core
# Case-insensitive scan for remaining old references
grep -rin "hermes" --include="*.py" --include="*.sh" --include="*.md" --include="*.example" . 2>/dev/null | grep -v "upshalter" | grep -v ".git/"
# Should return no matches
```

### 6. Commit & Push
Use a clear rebranding commit message (see SKILL.md step 7 for example).

## Verification
- `git log --all -p -S "hermes"` returns no results (no old references in git history)
- All new commits use updated terminology
- Telegram notifications work with new curl-based setup
