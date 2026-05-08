Telegram: bot token 8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU, chat ID 5807834405. Workspace: /root/hermes-workspace-personal, Nginx /etc/nginx/sites-available/hermes-workspace. PM2 for Node.js. Docker needs extra_hosts host.docker.internal:host-gateway.
§
Active SKP: /data/arsify.db (symlink), table=knowledge, NO scope column. Columns: id/key/value/category/tags/priority/source_agent_name/created_at/updated_at. Schema auto-detect via PRAGMA table_info. Key format: senator-{domain}/insight/{date-counter}. 353 entries after cleanup (2026-05-08).
§
Unified Knowledge Pool active: All Hermes agents (hermes-cli, hermes-debug, loyx, gamedev) share /root/.hermes via volume mounts. Loyx & GameDev Docker containers mount /root/.hermes:/opt/data with 'user: root' in docker-compose to avoid permission issues. hermes-debug CLI wrapper uses tmux session for persistence.
§
System Consolidation Pattern (2026-05-08): Consolidation = READ/INVENTORY/CLASSIFY/DESIGN/WRITE 15-doc. Split Product (user-facing) and Infrastructure (runtime). Hermes = runtime, Arsify Workforce OS = product. Skill: system-consolidation-engine.
§
Hermes Cognitive Engine :8100: auth=X-API-Key header (value: hermes-secret-change-me-in-production). /v1/portsocket=async task (input string, NOT messages). /chat=fast path to Ollama (broken CPU VPS). For sync inference call OpenRouter directly. OpenRouter keys: host .env=ACTIVE, cognitive .env=EXPIRED (check both on 402). Senator containers=standalone Hermes agents (nousresearch/hermes-agent:latest), mount /root/.hermes.
§
Arsify MoE Router (port 8002): uses /chat endpoint (not OpenAI /v1/chat/completions), health endpoint shows Ollama status, 4 models available. Ollama on CPU VPS causes inference timeout, swap near full (3.8/4G as of 2026-05-08). chat.upshalter.com Nginx config proxies to port 8002 (updated 2026-05-08).
§
GitHub sync cron active: /root/sync-github.sh runs every 5 mins, logs to /var/log/github-sync.log, syncs /root/arsify-archive with https://github.com/Arsify-OS/arsify-pool.