#!/bin/bash
# Final log verification pattern - checks all Hermes containers for errors
# Usage: bash scripts/final-log-check.sh

echo "=== SENATOR LOGS (no active_model_map/errors?) ==="
for container in senator-akademisi senator-bisnis senator-komunitas senator-pemerintah senator-media; do
  echo "--- $container ---"
  docker logs $container --since "2026-05-07T14:30:00" 2>&1 | grep -E "(active_model|❌|ERROR)" | head -3
done

echo ""
echo "=== WORKER LOGS (no errors?) ==="
docker logs hermes-worker --since "2026-05-07T14:30:00" 2>&1 | grep -E "(active_model|raised|ERROR)" | head -5

echo ""
echo "=== API LOGS (200 OK, no 500?) ==="
docker logs hermes-api --since "2026-05-07T14:30:00" 2>&1 | grep -E "(500|ERROR|Traceback)" | head -5

echo ""
echo "✅ VERIFICATION COMPLETE"
