---
name: hermes-infra-verification
description: Verifikasi otomatis infrastruktur Upshalter/Hermes - cek bukan hanya "running" tapi fungsional
trigger: User minta verifikasi infrastruktur, cek status layanan, validasi deployment
---

# SKILL: hermes-infra-verification
# Version: 1.0
# Deskripsi: Verifikasi otomatis infrastruktur Upshalter/Hermes - cek bukan hanya "running" tapi fungsional

## Kapan Gunakan Skill Ini
Jalankan skill ini setiap kali ingin memverifikasi status infrastruktur secara menyeluruh.
Tidak hanya cek apakah service "running" — tapi apakah benar-benar fungsional.
Khususnya setelah deployment besar atau sebelum laporan status ke user.

**User Preference**: Deploy fixes "satu per satu" (one by one), verifikasi tiap langkah sebelum lanjut ke langkah berikutnya. Saat melaporkan hasil verifikasi ke user (terutama via terminal), gunakan:
- Struktur dengan box-drawing characters (┌ ─ ┐ │ └ ┘)
- Emoji status: ✅ (OK), ⏳ (proses), ❌ (gagal)
- Bahasa Indonesia untuk komunikasi lisan, tapi kode/perintah tetap dalam English
- Brief status updates, hindari penjelasan panjang di inline; detail ke laporan akhir

## Apa yang Dicek

### Level 1: Process Check (cepat, 10 detik)
```bash
# Cek zombie processes
ZOMBIE_COUNT=$(ps aux | awk '$8 == "Z"' | wc -l)
[ "$ZOMBIE_COUNT" -eq 0 ] && echo "✅ Zombie: 0" || echo "❌ Zombie: $ZOMBIE_COUNT"

# Cek systemd services
systemctl is-active hermes-orchestrator hermes-upshalternal hermes-archivist \
  hermes-backend hermes-frontend hermes-workstation hermes-flowforce hermes-api

# Cek Docker containers (detail dengan health status)
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(senator|hermes-|redis|nginx)"

# Cek cron jobs Senator
crontab -l 2>/dev/null | grep -i senator && echo "✅ Senator cron: terdaftar" || echo "❌ Senator cron: tidak ada"
```

### Level 1.5: Quick Functional Checks (15 detik)
```bash
# Redis connectivity
redis-cli ping 2>/dev/null | grep -q PONG && echo "✅ Redis: PONG" || echo "❌ Redis: tidak merespons"

# Ollama LLM models (CPU-only: expect slowness)
OLLAMA_MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c "import sys,json; ms=json.load(sys.stdin).get('models',[]); print(len(ms))" 2>/dev/null || echo "0")
[ "$OLLAMA_MODELS" -gt 0 ] && echo "✅ Ollama: $OLLAMA_MODELS model tersedia" || echo "❌ Ollama: tidak ada model"

# SKP DB entries — try multiple paths, table is 'knowledge' (NOT 'memory_notes' or 'romi_theses')
SKP_COUNT=$(sqlite3 /data/arsify.db "SELECT COUNT(*) FROM knowledge;" 2>/dev/null || \
  sqlite3 /root/.hermes/shared_knowledge_pool.db "SELECT COUNT(*) FROM knowledge;" 2>/dev/null || \
  sqlite3 /data/shared_knowledge_pool.db "SELECT COUNT(*) FROM knowledge;" 2>/dev/null || echo "0")
echo "✅ SKP DB: $SKP_COUNT entries (knowledge table)"

# Cek Celery worker status (jalankan dari container worker)
docker exec hermes-worker celery -A celery_app status 2>&1 | grep -q "OK" && echo "✅ Celery worker: online" || echo "❌ Celery worker: tidak merespons"

# FASE 4+: OpenRouter direct check (primary LLM backend)
OR_TEST=$(curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OPENROUTER_API_KEY:-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}" \
  -d '{"model":"openrouter/owl-alpha","messages":[{"role":"user","content":"OK"}],"max_tokens":5}' \
  --max-time 30 2>&1)
echo "$OR_TEST" | python3 -c "
import sys
raw = sys.stdin.read()
if 'choices' in raw: print('✅ OpenRouter: reachable (<30s)')
elif raw.strip(): print('⚠️  OpenRouter: error —', raw[:80])
else: print('❌ OpenRouter: unreachable')
" 2>/dev/null || echo "❌ OpenRouter: timeout"

# FASE 5: Health endpoint check (cognitive engine)
curl -sf http://localhost:8100/health 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'✅ Health: {d[\"status\"]} | SKP: {d[\"skp\"][\"total_entries\"]} | Queue: {d[\"queue\"][\"queue_length\"]} pending')
" 2>/dev/null || echo "⚠️  Health endpoint: tidak merespons (recreate api container jika perlu)"
```

### Level 1.75: Cognitive Engine Config Checks (10 detik)
```bash
# Cek apakah worker pakai concurrency=2 (free model safe)
docker exec hermes-worker ps aux | grep -oP 'celery.*-c\s*\K\d+' 2>/dev/null | head -1 | \
  xargs -I{} bash -c '[ "{}" -le 2 ] && echo "✅ Worker concurrency: {} (safe for free models)" || echo "⚠️  Worker concurrency: {} (terlalu tinggi untuk free models)"'

# Cek USE_FREE_MODELS di api & worker
docker exec hermes-api env | grep -q "USE_FREE_MODELS=true" && echo "✅ API: USE_FREE_MODELS=true" || echo "⚠️  API: USE_FREE_MODELS not set"
docker exec hermes-worker env | grep -q "USE_FREE_MODELS=true" && echo "✅ Worker: USE_FREE_MODELS=true" || echo "⚠️  Worker: USE_FREE_MODELS not set"

# Cek rate limit setting
RATE=$(docker exec hermes-api env | grep RATE_LIMIT_REQUESTS | cut -d= -f2)
[ "$RATE" -ge 500 ] 2>/dev/null && echo "✅ Rate limit: $RATE req/60s (good)" || echo "⚠️  Rate limit: ${RATE:-default} (naikkan ke 500)"

# Cek Celery backend configured
docker exec hermes-worker celery -A celery_app inspect stats 2>&1 | grep -q '"backend":' && \
  echo "✅ Celery backend: configured" || echo "❌ Celery backend: missing (AsyncResult akan error)"
```

### Level 2: Functional Check (sedang, 30 detik)
```bash
# Cek endpoint yang benar-benar respond dengan konten yang tepat
curl -sf https://upshalter.com | grep -q "Upshalter" && echo "✅ upshalter.com: OK" || echo "❌ upshalter.com: FAIL"

# Cek status page real-time (bukan static)
curl -sf https://status.upshalter.com | grep -q "checkAll\|fetch\|poll" && \
  echo "✅ status: real-time" || echo "⚠️  status: STATIC (perlu fix)"

# Cek chat UI (bukan hanya API)
curl -sf https://chat.upshalter.com | grep -q "sendMessage\|chat-input\|msg-bubble" && \
  echo "✅ chat: UI ada" || echo "⚠️  chat: API only (perlu UI)"

# Cek workspace features
curl -sf https://workspace.upshalter.com | grep -q "enhancedChat\|chat" && \
  echo "✅ workspace: chat aktif" || echo "⚠️  workspace: missing features"
```

### Level 3: Deep Check (lambat, 2-3 menit)
```bash
# Cek Senator Pentahelix benar-benar menulis ke SKP
# NOTE: /data/arsify.db often does NOT exist. Try multiple paths.
SKP_COUNT=$(sqlite3 /data/arsify.db "SELECT COUNT(*) FROM memory_notes" 2>/dev/null || \
  sqlite3 /root/.hermes/shared_knowledge_pool.db "SELECT COUNT(*) FROM memory_notes" 2>/dev/null || echo "0")
echo "SKP entries: $SKP_COUNT"

# Cek Arsify API benar-benar merespons dengan content
RESPONSE=$(curl -sf -X POST https://chat.upshalter.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"ping"}' 2>/dev/null)
echo $RESPONSE | grep -q "response" && echo "✅ Arsify API: returning content" || \
  echo "❌ Arsify API: no content in response"

# Cek model yang dipilih
echo $RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ model:', d.get('model_used','unknown'))" 2>/dev/null

# Cek backup berjalan
BACKUP_AGE=$(find /var/backups/hermes -name "*.tar*" -mtime -1 -type f 2>/dev/null | wc -l)
[ "$BACKUP_AGE" -gt "0" ] && echo "✅ Backup: ada dalam 24 jam" || echo "⚠️  Backup: tidak ada backup hari ini"

# Cek SSL cert expiry
for domain in upshalter.com api.upshalter.com chat.upshalter.com; do
  DAYS=$(echo | openssl s_client -connect "$domain:443" -servername "$domain" 2>/dev/null \
    | openssl x509 -noout -enddate 2>/dev/null \
    | awk -F= '{print $2}' \
    | xargs -I{} date -d "{}" +%s \
    | xargs -I{} bash -c 'echo $(( ($1 - $(date +%s)) / 86400 ))' _ {} 2>/dev/null || echo "?")
  echo "SSL $domain: ${DAYS} hari"
done
```

## Pitfalls & Patterns

See `references/emergency-fix-patterns.md` for detailed diagnosis/fix patterns:
See `references/redis-celery-debug.md` for Redis + Celery debugging workflow:
See `references/cognitive-engine-fixes.md` for Cognitive Engine operational fixes (rate limits, Celery backend, free models):

- **Case-insensitive search**: Always use `-iname` with `find`, not `-name`
- **systemd 203/EXEC**: Binary not found — check with `which` and `ls -la`
- **systemd signal 9/KILL**: OOM killer — add `Restart=on-failure` + `StartLimitBurst`
- **sed duplicate entries**: Use `sudo tee > /dev/null << 'EOF'` to rewrite cleanly
- **OpenRouter 402**: Credit exhausted — fallback to free model or top-up
- **SKP db path**: Try `/data/arsify.db` then `/root/.hermes/shared_knowledge_pool.db` then `/data/shared_knowledge_pool.db`
- **Telegram username vs chat_id**: API needs numeric ID, not `@username`
- **Writing system files**: `write_file` refuses `/etc/` — use `sudo tee` instead
- **Redis container-to-host**: If Redis runs on host (not Docker), containers need `extra_hosts: host.docker.internal:host-gateway` + iptables rule `iptables -I INPUT -i docker0 -p tcp --dport 6379 -j ACCEPT` + Redis `bind 0.0.0.0` + password auth
- **Redis protected mode**: Returns `-DENIED` if enabled and no password. Fix: `CONFIG SET protected-mode no` + `CONFIG SET requirepass <password>`
- **Redis password mismatch (PRD-001)**: Most common Celery failure. Check `.env`, `docker-compose.yml`, `celery_app.py` for inconsistent passwords. See `references/redis-celery-debug.md` for full debug pattern
- **Celery task not registered**: Must add `import tasks` explicitly in `celery_app.py`, not just `@app.task` decorator
- **Docker UFW rules**: Containers can't reach host Redis without `ufw allow from 172.25.0.0/16 to any port 6379`
- **Celery command not found on host**: Celery binary hanya ada di container worker, jalankan via `docker exec hermes-worker celery ...`
- **Senator container health: starting**: Normal saat inisialisasi awal, tunggu beberapa menit sebelum menilai gagal
- **Senator rate limit**: Normal untuk free model OpenRouter, tunggu retry otomatis
- **OpenRouter 429 cascade**: Free models sering kena rate limit bersamaan. Mitigasi: (1) `USE_FREE_MODELS=true` di api+worker, (2) `MAX_RETRY` ≥ 10, (3) Siapkan 4+ model free cadangan di `openrouter_client.py`, (4) `call_with_fallback` harus iterasi SEMUA model, bukan berhenti di 1
- **Celery backend missing**: Worker bisa jalan tapi `AsyncResult` gagal dengan `DisabledBackend`. Pastikan `celery_app.py` set `backend` sama dengan `broker` (Redis). Cek: `docker exec hermes-worker celery -A celery_app inspect stats 2>&1 | grep backend`
- **Worker concurrency vs rate limit**: Saat pakai free models, set `CELERY_WORKER_CONCURRENCY=2` (bukan 4+) untuk hindari spike request ke OpenRouter
- **Rate limit setting**: Di `.env` set `RATE_LIMIT_REQUESTS=500` (bukan default 100) untuk izinkan burst dari multiple workers+senators
- **SKP DB path**: Gunakan `/root/.hermes/shared_knowledge_pool.db` (symlink ke `/data/arsify.db`)
- **FASE 5: Health endpoints**: `curl http://localhost:8100/health` returns full pipeline status. If missing, api container needs recreate with health.py mount.
- **FASE 5: SKP cleanup**: Runs every 6h via Celery beat. Removes old (>24h), duplicate values, caps at 200. Check: `docker exec hermes-worker python3 -c "from core.kurator import cleanup_skp; print(cleanup_skp())"`
- **FASE 5: LLM timeouts on CPU**: Ollama qwen2.5:1.5b ~30s/call. L2 planning and kurator analysis frequently timeout → fallback paths. This is NORMAL on CPU-only VPS. Mitigation: MAX_RETRY=1, LLM_TIMEOUT_READ=90.
- **FASE 5: Docker shared volumes**: Use YAML anchor `x-hermes-volumes` in docker-compose. All custom .py files must be explicitly mounted into each service (api, worker, beat).
- **9router PM2 process**: There is a "9router" process managed by PM2 (`pm2 list`). Verify its role — may be a separate Node.js API router. If it duplicates the Cognitive Engine on :8100, consolidate into one entry point during system consolidation.

## Template & Script yang Tersedia

- **templates/chat-ui.html** — UI Chat siap deploy untuk chat.upshalter.com (dark theme, connect ke /chat API)
- **templates/status-realtime.html** — Status page real-time dengan JS polling 30s (deploy ke status.upshalter.com)
- **scripts/fix-gaps.sh** — Script otomatis fix 3 gap umum (status static, chat tanpa UI, workspace missing features)
- **scripts/final-log-check.sh** — Final verification: cek log Senator/Worker/API untuk error setelah deployment (grep patterns untuk active_model_map, 500, ERROR)

Gunakan: `skill_manage(action='write_file', name='hermes-infra-verification', file_path='templates/chat-ui.html', ...)`

## Format Laporan ke Telegram

Setelah cek selesai, kirim laporan dengan format ini:

```
[INFRA VERIFICATION — {timestamp}]

SERVICES:
• {nama}: ✅/❌

DOMAINS:
• {domain}: ✅/⚠️/❌ — {keterangan}

AGENTS:
• Senator Pentahelix: ✅ bekerja ({N} entries di SKP)

BACKUP:
• Last backup: {age}

ISSUES:
• {list masalah yang ditemukan}

Score: {N}/{total} OK
```

## Kapan Alert ke Manusia

WAJIB alert jika:
- Ada service yang down > 5 menit
- SKP tidak bertambah dalam 24 jam (Senator tidak bekerja)
- Backup tidak ada dalam 48 jam
- SSL cert < 14 hari
- Disk usage > 85%

CUKUP log (tidak alert) jika:
- Satu service restart sebentar dan kembali OK
- Response time sedikit lebih lambat
- SKP bertambah normal

## Jadwal Otomatis

Tambahkan ke crontab untuk verifikasi terjadwal:
```bash
# Cek ringan setiap jam
0 * * * * hermes -p archivist -z "Jalankan Level 1 dan Level 2 infra check, laporkan hasilnya"

# Cek mendalam setiap hari jam 06:00 WIB
0 23 * * * hermes -p archivist -z "Jalankan full Level 3 infra verification, kirim laporan ke Telegram"
```

---

*Skill ini dibuat berdasarkan verifikasi manual Hermes pada 7 Mei 2026*
*Sebaiknya dijalankan setelah setiap perubahan infrastruktur besar*