# Upshalter Fase 4 FINAL — Semua Mismatch Fixed

## Deploy (satu command):
chmod +x deploy-fase4.sh && bash deploy-fase4.sh

## Yang dilakukan:
1. Deteksi sistem (table: knowledge vs memory_notes, DB path, key format)
2. Install dependencies (httpx, scikit-learn)
3. Deploy senator-cycle-v2.sh (bypass gateway, direct API call)
4. Deploy kurator-v2.sh (120s timeout, confidence scoring)
5. Jalankan category-backfill HANYA untuk entries 'general' (preserve curated, backend, dll)
6. Update crontab
7. Kirim laporan ke Telegram

## Fixes yang sudah diverifikasi:
✓ Table: auto-detect knowledge vs memory_notes
✓ DB path: auto-detect 4 kandidat path
✓ Key format: auto-detect senator-X/execution/Y vs X/temuan/Y
✓ Backfill: HANYA update category='general', preserve yang sudah benar
✓ moe-router-patch: DILEWATI (router tidak ada di container)

## Test yang sudah dijalankan:
✓ SKP adapter: tabel 'knowledge' terdeteksi, read/write berhasil
✓ Backfill: 'curated' dan 'backend' tetap utuh, 'general' terklasifikasi
✓ Semua bash scripts: syntax OK
✓ Semua Python files: compile OK
