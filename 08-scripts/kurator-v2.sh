#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  KURATOR v2.1 — Thin wrapper, delegates to kurator-v2.py
#  Mei 2026
# ═══════════════════════════════════════════════════════════════════════
#
#  Fix: kurator logic dipindah ke Python script terpisah.
#  Shell script hanya wrapper untuk backward compatibility.
#
# ═══════════════════════════════════════════════════════════════════════

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/root/upshalter-logs"
LOG="$LOG_DIR/kurator-$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"
echo "" >> "$LOG"
echo "═══ KURATOR v2.1 (wrapper): $(date '+%Y-%m-%d %H:%M:%S') ═══" >> "$LOG"

# Check dependencies
python3 -c "import httpx" 2>/dev/null || {
    echo "✗ httpx not installed" >> "$LOG"
    exit 1
}

# Run kurator
python3 "$SCRIPT_DIR/kurator-v2.py" 2>&1 | tee -a "$LOG"
