#!/bin/bash
# Hermes SQLite Backup Script
# Runs every hour via cron
# Backs up all SQLite databases to /backup/hermes/

BACKUP_DIR="/backup/hermes"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RETENTION_DAYS=7

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# List of databases to backup
DB_PATHS=(
    "/usr/local/lib/hermes-orchestrator/db/orchestrator.db"
    "/usr/local/lib/hermes-orchestrator/data/auth.db"
    "/root/.hermes/response_store.db"
    "/root/.hermes/kanban.db"
    "/root/.hermes/state.db"
)

echo "[$(date)] Starting Hermes database backup..."

# Backup each database
for db in "${DB_PATHS[@]}"; do
    if [ -f "$db" ]; then
        filename=$(basename "$db")
        backup_file="$BACKUP_DIR/${filename%.db}-${TIMESTAMP}.db"
        
        # Use sqlite3 to create a backup (ensures consistency)
        if command -v sqlite3 &> /dev/null; then
            sqlite3 "$db" ".backup '$backup_file'"
        else
            # Fallback to cp if sqlite3 not available
            cp "$db" "$backup_file"
        fi
        
        if [ -f "$backup_file" ]; then
            echo "  ✓ Backed up: $filename -> $backup_file"
        else
            echo "  ✗ Failed to backup: $filename"
        fi
    else
        echo "  ⚠ Not found: $db"
    fi
done

# Cleanup old backups (older than RETENTION_DAYS)
find "$BACKUP_DIR" -name "*.db" -mtime +$RETENTION_DAYS -delete 2>/dev/null
echo "[$(date)] Backup completed. Old backups cleaned (>$RETENTION_DAYS days)."

# Optional: Test recovery (verify backup integrity)
echo "Verifying backup integrity..."
for backup in "$BACKUP_DIR"/*-${TIMESTAMP}.db; do
    if [ -f "$backup" ]; then
        if sqlite3 "$backup" "PRAGMA integrity_check;" | grep -q "ok"; then
            echo "  ✓ $backup: OK"
        else
            echo "  ✗ $backup: CORRUPT!"
        fi
    fi
done

echo "[$(date)] Backup & verification completed."
