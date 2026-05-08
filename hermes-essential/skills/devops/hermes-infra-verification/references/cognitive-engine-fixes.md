# Cognitive Engine Fixes - Sesi 7 Mei 2026

## Masalah yang Ditemukan & Diperbaiki

### 1. OpenRouter Rate Limit Cascade (HTTP 429)
**Gejala**: Senator & worker kena rate limit bersamaan, task gagal beruntun.

**Fix**:
- Naikkan `RATE_LIMIT_REQUESTS` di `.env` dari 100 → 500 req/60s
- Update di `docker-compose.yml` juga agar konsisten
- File: `/opt/hermes-cognitive/.env`

### 2. Celery DisabledBackend Error
**Gejala**: `AsyncResult` gagal dengan error `DisabledBackend`.

**Fix**:
- Enable `backend` di `celery_app.py` (set sama dengan `broker`)
- Simpan file di `/root/.hermes/celery_app.py`
- Mount ke container via `docker-compose.yml`:
  ```yaml
  volumes:
    - /root/.hermes/celery_app.py:/app/celery_app.py
  ```

### 3. Free Model Fallback Tidak Iteratif
**Gejala**: `call_with_fallback` hanya coba 1 model, langsung gagal jika model itu kena rate limit.

**Fix**:
- Di `openrouter_client.py`, tambah 4 model free baru:
  - `meta-llama/llama-3.2-1b-instruct:free`
  - `microsoft/phi-3-mini-128k-instruct:free`
  - `google/gemma-2-2b-it:free`
  - `qwen/qwen-2-1.5b-instruct:free`
- Modifikasi `call_with_fallback` untuk iterasi SEMUA model di list
- Naikkan `MAX_RETRY` dari default → 10

### 4. Worker Concurrency Terlalu Tinggi
**Gejala**: 4 worker concurrency + free models = spike request → rate limit.

**Fix**:
- Set `CELERY_WORKER_CONCURRENCY=2` di `docker-compose.yml` environment

### 5. Senator Startup Spike
**Gejala**: Ketiga senator start bersamaan → burst request ke API.

**Fix**:
- Tambah `sleep 60` antar senator di `senator-cycle.sh`
- Tambah random delay (0-60s) di `senator_cognitive_client.py`:
  ```python
  import random, time
  time.sleep(random.randint(0, 60))
  ```

## File yang Dimodifikasi
- `/opt/hermes-cognitive/.env` (RATE_LIMIT_REQUESTS, USE_FREE_MODELS)
- `/opt/hermes-cognitive/docker-compose.yml` (volume mounts, concurrency, env vars)
- `/root/.hermes/celery_app.py` (backend enabled)
- `/root/.hermes/openrouter_client.py` (free models + retry logic)
- `/root/upshalter-scripts/senator-cycle.sh` (stagger delay)

## Verifikasi Setelah Fix
Jalankan `Level 1.75: Cognitive Engine Config Checks` dari SKILL.md untuk validasi.
