#!/bin/bash
# Backup SKP dan konfigurasi penting
BACKUP_DIR="/root/upshalter-backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup Arsify database
sqlite3 /root/.hermes/shared_knowledge_pool.db ".backup $BACKUP_DIR/arsify-$(date +%H%M).db" 2>/dev/null || echo "SKP backup failed"

# Backup Hermes configs
cp -r /root/.hermes/config.yaml $BACKUP_DIR/ 2>/dev/null || true
cp -r /root/.hermes/kanban.db $BACKUP_DIR/ 2>/dev/null || true

# Compress backup lebih dari 7 hari
find /root/upshalter-backups -name "*.db" -mtime +7 -exec gzip {} \; 2>/dev/null || true

# Hapus backup lebih dari 30 hari
find /root/upshalter-backups -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

echo "Backup selesai: $BACKUP_DIR"
