#!/bin/bash
# validate-blueprint.sh - Validasi otomatis 8 FASE AUTOMATION-PROTOCOL.md
# Run: bash /root/.hermes/skills/devops/hermes-role-deploy/scripts/validate-blue-print.sh

echo "╔════════════════════════════════════════════╗"
echo "║  VALIDASI BLUEPRINT INFRASTRUKTUR       ║"
echo "╚════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0

check() {
    local name=$1
    local cmd=$2
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✅ $name"
        ((PASS++))
    else
        echo "❌ $name — GAGAL"
        ((FAIL++))
    fi
}

# FASE 0: ORIENTASI
echo "=== FASE 0: ORIENTASI ==="
check "Dokumen AUTOMATION-PROTOCOL.md ada" "test -f /root/Visi 2026/AUTOMATION-PROTOCOL.md"
check "Backup directory ada" "test -d /root/upshalter-backups"
echo ""

# FASE 1: PEMBERSIHAN SISTEM
echo "=== FASE 1: PEMBERSIHAN ==="
check "Tidak ada test agent di systemd" "systemctl list-unit-files | grep -i 'hermes-test\\|test-agent' | grep -v 'not-found' | wc -l | grep -q '^0$'"
echo ""

# FASE 2: AKTIVASI AGENT INTI
echo "=== FASE 2: AKTIVASI AGENT ==="
for svc in hermes-upshalternal hermes-orchestrator hermes-api hermes-archivist; do
    check "$svc active" "systemctl is-active $svc 2>/dev/null | grep -q active"
done
echo ""

# FASE 3: KONEKSI DOMAIN
echo "=== FASE 3: KONEKSI DOMAIN ==="
for domain in workspace.upshalter.com hermes.upshalter.com chat.upshalter.com; do
    code=$(curl -s https://$domain --max-time 5 -o /dev/null -w "%{http_code}" 2>/dev/null)
    if [ "$code" = "200" ]; then
        echo "✅ $domain → HTTP $code"
        ((PASS++))
    else
        echo "❌ $domain → HTTP ${code:-ERROR}"
        ((FAIL++))
    fi
done
echo ""

# FASE 4: MONITORING & OBSERVABILITY
echo "=== FASE 4: MONITORING ==="
check "health-check.sh ada" "test -f /root/upshalter-scripts/health-check.sh"
check "daily-summary.sh ada" "test -f /root/upshalter-scripts/daily-summary.sh"
check "ssl-check.sh ada" "test -f /root/upshalter-scripts/ssl-check.sh"
check "backup-skp.sh ada" "test -f /root/upshalter-scripts/backup-skp.sh"
check "Cron jobs FASE 4 terpasang" "crontab -l 2>/dev/null | grep -q 'health-check.sh'"
echo ""

# FASE 5: KANBAN WORKFLOW
echo "=== FASE 5: KANBAN WORKFLOW ==="
check "senator-cycle cron" "crontab -l 2>/dev/null | grep -q 'senator-cycle'"
check "kurator-review cron" "crontab -l 2>/dev/null | grep -q 'kurator-review'"
echo ""

# FASE 6: DASHBOARD
echo "=== FASE 6: DASHBOARD ==="
check "Status page ada" "test -f /var/www/upshalter.com/status/index.html"
echo ""

# FASE 7: BACKUP
echo "=== FASE 7: BACKUP ==="
check "Backup cron terpasang" "crontab -l 2>/dev/null | grep -q 'backup-skp'"
echo ""

# FASE 8: VERIFIKASI
echo "=== FASE 8: VERIFIKASI ==="
check "verify-all.sh ada" "test -f /root/upshalter-scripts/verify-all.sh"
echo ""

# SUMMARY
echo "════════════════════════════════════════════"
echo "RINGKASAN: $PASS PASS / $FAIL FAIL"
echo "════════════════════════════════════════════"

if [ $FAIL -eq 0 ]; then
    echo "🎉 SEMUA FASE BERHASIL!"
else
    echo "⚠️  Ada $FAIL item yang perlu diperbaiki"
fi
