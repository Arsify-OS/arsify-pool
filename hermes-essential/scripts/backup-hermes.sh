#!/bin/bash
# HERMES BACKUP & RECOVERY SCRIPT
# FASE 7: Automated backup for Hermes Infrastructure
# Created: 2026-05-06

set -euo pipefail

# Configuration
BACKUP_ROOT="/var/backups/hermes"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
LOG_FILE="$BACKUP_ROOT/backup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN:${NC} $1" | tee -a "$LOG_FILE"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "🔄 Starting Hermes Infrastructure Backup"
log "📁 Backup destination: $BACKUP_DIR"

# 1. Backup /root/.hermes (configs, history, skills)
log "📦 Backing up Hermes config..."
tar -czf "$BACKUP_DIR/hermes-config.tar.gz" \
    -C /root/.hermes \
    --exclude='cache/*' \
    --exclude='checkpoints/*' \
    --exclude='audio_cache/*' \
    --exclude='.npm/*' \
    --exclude='.local/*' \
    config.yaml auth.json channel_directory.json SOUL.md .env 2>/dev/null || warn "Some config files missing"

# 2. Backup systemd services
log "⚙️  Backing up systemd services..."
mkdir -p "$BACKUP_DIR/systemd"
for service in /etc/systemd/system/hermes-*.service; do
    if [ -f "$service" ]; then
        cp "$service" "$BACKUP_DIR/systemd/" 2>/dev/null
    fi
done
tar -czf "$BACKUP_DIR/systemd-services.tar.gz" -C "$BACKUP_DIR" systemd && rm -rf "$BACKUP_DIR/systemd"

# 3. Backup Nginx configs
log "🌐 Backing up Nginx configurations..."
tar -czf "$BACKUP_DIR/nginx-configs.tar.gz" \
    -C /etc/nginx \
    sites-available sites-enabled 2>/dev/null || warn "Nginx config backup incomplete"

# 4. Backup SSL certificates
log "🔒 Backing up SSL certificates..."
if [ -d /etc/letsencrypt ]; then
    tar -czf "$BACKUP_DIR/ssl-certs.tar.gz" \
        -C /etc \
        letsencrypt 2>/dev/null || warn "SSL cert backup failed"
fi

# 5. Backup Docker volumes (Senator Pentahelix data) - metadata only, not full export
log "🐳 Backing up Docker container metadata..."
mkdir -p "$BACKUP_DIR/docker"
docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Mounts}}' > "$BACKUP_DIR/docker/containers-metadata.txt" 2>/dev/null || warn "Docker metadata backup failed"
# Backup volume data separately if needed
for volume in $(docker volume ls -q 2>/dev/null | grep -E 'senator|hermes' || true); do
    docker volume inspect "$volume" > "$BACKUP_DIR/docker/volume-${volume}.json" 2>/dev/null || true
done
tar -czf "$BACKUP_DIR/docker-metadata.tar.gz" -C "$BACKUP_DIR" docker && rm -rf "$BACKUP_DIR/docker"

# 6. Backup Hermes Workspace (if exists)
if [ -d /root/hermes-workspace-personal ]; then
    log "🏢 Backing up Hermes Workspace..."
    tar -czf "$BACKUP_DIR/hermes-workspace.tar.gz" \
        -C /root \
        --exclude='hermes-workspace-personal/.git' \
        --exclude='hermes-workspace-personal/node_modules' \
        hermes-workspace-personal 2>/dev/null || warn "Workspace backup incomplete"
fi

# 7. Create backup manifest
log "📋 Creating backup manifest..."
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
Hermes Infrastructure Backup
===========================
Timestamp: $TIMESTAMP
Hostname: $(hostname)
Kernel: $(uname -r)

Components Backed Up:
- Hermes Config (/root/.hermes)
- Systemd Services
- Nginx Configurations
- SSL Certificates
- Docker Containers (Senator Pentahelix)
- Hermes Workspace

Systemd Services Active:
$(systemctl list-units --type=service --all | grep hermes | grep loaded | awk '{print $1, $3, $4}')

Docker Containers:
$(docker ps -a --format '{{.Names}} {{.Status}}' 2>/dev/null | head -20)

Restore Instructions:
1. Extract component: tar -xzf <component>.tar.gz -C /
2. Reload systemd: systemctl daemon-reload
3. Restart services: systemctl restart hermes-*
4. Restart docker: docker start <container>
EOF

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "✅ Backup complete! Size: $BACKUP_SIZE"

# Cleanup old backups
log "🧹 Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_ROOT" -maxdepth 1 -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true

# List current backups
log "📊 Current backups:"
ls -lh "$BACKUP_ROOT" | tail -n +2

log "✅ Backup process completed successfully!"
