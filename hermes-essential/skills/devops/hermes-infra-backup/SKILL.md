---
name: hermes-infra-backup
description: Set up automated backup & recovery for Hermes Infrastructure (VPSO agents, Nginx, Docker, configs, SSL certs). Includes backup script, systemd timer, recovery documentation for daily automated backups with 7-day retention.
triggers:
  - User requests backup setup for Hermes infrastructure
  - FASE 7 of Hermes Infrastructure deployment
  - Need to recover Hermes components after failure
  - Automating backup for /root/.hermes, systemd services, Nginx, SSL, Docker metadata
---

# Hermes Infrastructure Backup & Recovery

## Overview
Automated daily backups for all Hermes Infrastructure components with 7-day retention. Covers configs, systemd services, Nginx, SSL certs, Docker metadata, and includes full recovery documentation.

## Core Workflow
1. **Deploy Backup Script**
   - Use pre-built `scripts/backup-hermes.sh` (install to `/root/.hermes/scripts/`)
   - Key exclusions: `cache/*`, `checkpoints/*`, `node_modules`, `.git` to keep backups small
   - Never use `docker export` for full containers (causes timeouts) → use metadata-only backup

2. **Setup Systemd Automation**
   - Install service/timer files from `templates/` to `/etc/systemd/system/`
   - Enable daily timer: `systemctl enable --now hermes-backup.timer`
   - Verify: `systemctl list-timers | grep hermes`

3. **Verify Backup Operation**
   - Check backups: `ls -lh /var/backups/hermes/`
   - View logs: `tail -10 /var/backups/hermes/backup.log`
   - Test run: `systemctl start hermes-backup.service`

4. **Recovery Procedures**
   - Follow full steps in `references/BACKUP_RECOVERY_GUIDE.md`
   - Supports full recovery, single-component restore, and config rollback

5. **Manual Pre-Reset GitHub Pool Backup**
   - For VPS reset preparation, create a structured GitHub pool to preserve critical assets:
     - Directory structure: `scripts/`, `skills/`, `configs/`, `docs/`, `database/`, `nginx/`
     - Copy assets excluding secrets: automation scripts, custom skills, example configs (suffix `.example`), docs, SQLite DBs, nginx configs
     - Add `.gitignore` (use `templates/github-pool.gitignore`) to exclude: `.env`, `*.key`, `auth.json`, `*.db-wal`, `*.db-shm`, `*.log`, `__pycache__/`, `.git/`
     - Init git repo, commit with clear snapshot message, push to GitHub for easy restore
   - Verification: Ensure no secrets in committed files via `git show --name-only`

## Critical Pitfalls
- **Docker Timeout**: Full container exports (`docker export`) cause 60s+ timeouts. Always use metadata-only backup (container lists, volume inspects) as implemented in the script.
- **Systemd Path Protection**: Skill management tools block writes to `/etc/systemd/system/`. Use `terminal` tool with sudo/approval for system file deployments.
- **Retention Policy**: Auto-cleans backups older than 7 days. Adjust `RETENTION_DAYS` in the script if longer retention is needed.
- **Secret Exposure**: Never include `.env`, API keys, `auth.json`, or other secrets in GitHub-bound backups. Always use example configs (e.g., `config.yaml.example`) and exclude sensitive files via `.gitignore`.

## Support Files
- `scripts/backup-hermes.sh`: Executable backup script (copy to `/root/.hermes/scripts/`)
- `templates/hermes-backup.service`: Systemd service definition
- `templates/hermes-backup.timer`: Daily timer configuration
- `templates/github-pool.gitignore`: Pre-built .gitignore for manual GitHub pool backups (excludes secrets)
- `references/BACKUP_RECOVERY_GUIDE.md`: Full recovery documentation with verification checklists
