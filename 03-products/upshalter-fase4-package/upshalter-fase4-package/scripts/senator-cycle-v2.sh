#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  SENATOR CYCLE v2 — Upshalter Pentahelix Research System
#  Versi: 2.0 — Mei 2026
#  Perubahan dari v1: Bypass Kanban/Gateway, langsung call Hermes API
#  atau Ollama. Tidak ada dependency pada hermes gateway (port 8643).
# ═══════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Konfigurasi ──────────────────────────────────────────────────────
HERMES_API="http://localhost:8100"
OLLAMA_API="http://localhost:11434"
SKP_DB="${SKP_DB_PATH:-/data/arsify.db}"
LOG_DIR="/root/upshalter-logs"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
DATE_KEY=$(date +%Y%m%d-%H)
LOG="$LOG_DIR/senator-$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

echo "" >> "$LOG"
echo "════════════════════════════════════════" >> "$LOG"
echo "SENATOR CYCLE v2 START: $TIMESTAMP" >> "$LOG"
echo "════════════════════════════════════════" >> "$LOG"

# ── Fungsi: Deteksi model Ollama yang tersedia ─────────────────────────
get_ollama_model() {
    local models
    models=$(curl -sf "$OLLAMA_API/api/tags" 2>/dev/null | \
        python3 -c "import sys,json; ms=[m['name'] for m in json.load(sys.stdin).get('models',[])]; print(ms[0] if ms else '')" 2>/dev/null || echo "")
    # Preferensi model berdasarkan kualitas
    for prefer in "qwen2.5:7b" "llama3.1:8b" "llama3.2:3b" "qwen2.5:1.5b" "phi3:mini"; do
        if echo "$models" | grep -q "^$prefer$" 2>/dev/null; then
            echo "$prefer"; return
        fi
    done
    # Fallback ke model apapun yang ada
    echo "$models" | head -1
}

# ── Fungsi: Call Ollama langsung ───────────────────────────────────────
call_ollama() {
    local model="$1" prompt="$2" system="$3" timeout="${4:-120}"
    python3 - << PYEOF
import httpx, json, sys

model = "$model"
timeout = $timeout

payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": """$system"""},
        {"role": "user", "content": """$prompt"""}
    ],
    "stream": False,
    "options": {
        "temperature": 0.3,
        "num_predict": 2048,
        "top_p": 0.9
    }
}

try:
    with httpx.Client(timeout=timeout) as c:
        r = c.post("$OLLAMA_API/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        print(data["message"]["content"])
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
}

# ── Fungsi: Call Hermes API (dengan tool access) ───────────────────────
call_hermes_api() {
    local agent_id="$1" prompt="$2" timeout="${3:-90}"
    python3 - << PYEOF
import httpx, json, sys

payload = {
    "agent_id": "$agent_id",
    "message": """$prompt""",
    "stream": False
}

try:
    with httpx.Client(timeout=$timeout) as c:
        # Coba endpoint v1/portsocket (Hermes native)
        try:
            r = c.post("$HERMES_API/v1/portsocket", json=payload)
            if r.status_code == 200:
                data = r.json()
                print(data.get("response", data.get("content", str(data))))
                sys.exit(0)
        except:
            pass
        # Coba endpoint /task
        try:
            r = c.post("$HERMES_API/task", json={"agent": "$agent_id", "prompt": """$prompt"""})
            if r.status_code == 200:
                data = r.json()
                print(data.get("result", data.get("response", str(data))))
                sys.exit(0)
        except:
            pass
        # Coba OpenAI-compatible
        r = c.post("$HERMES_API/v1/chat/completions", json={
            "model": "$agent_id",
            "messages": [{"role": "user", "content": """$prompt"""}]
        })
        r.raise_for_status()
        data = r.json()
        print(data["choices"][0]["message"]["content"])
except Exception as e:
    print(f"HERMES_API_ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
}

# ── Fungsi: Simpan ke SKP ─────────────────────────────────────────────
save_to_skp() {
    local key="$1" value="$2" agent="$3"
    python3 - << PYEOF
import sqlite3, os, sys
from datetime import datetime

db_path = "$SKP_DB"
key = """$key"""
value = """$value"""[:4000]
agent = "$agent"
now = datetime.utcnow().isoformat()

try:
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            scope TEXT DEFAULT 'global',
            source_agent_name TEXT,
            category TEXT DEFAULT 'general',
            tags TEXT DEFAULT '[]',
            priority INTEGER DEFAULT 5,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        INSERT OR REPLACE INTO memory_notes
            (key, value, scope, source_agent_name, category, updated_at)
        VALUES (?, ?, 'global', ?, ?, ?)
    """, (key, value, agent, key.split('/')[0], now))
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM memory_notes").fetchone()[0]
    conn.close()
    print(f"OK: Saved to SKP. Total entries: {total}")
except Exception as e:
    print(f"SKP_ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
}

# ── Fungsi: Jalankan satu Senator ─────────────────────────────────────
run_senator() {
    local senator="$1" domain="$2" skp_prefix="$3"
    local system_prompt="$4" research_prompt="$5"
    local skp_key="${skp_prefix}/${DATE_KEY}"

    echo "[$(date +%H:%M:%S)] Starting $senator..." >> "$LOG"

    local result=""
    local success=false

    # Step 1: Coba Hermes API (punya web_search)
    if curl -sf "$HERMES_API/health" -m 3 >/dev/null 2>&1 || \
       curl -sf "$HERMES_API/" -m 3 >/dev/null 2>&1; then
        echo "  → Using Hermes API at $HERMES_API" >> "$LOG"
        result=$(call_hermes_api "$senator" "$research_prompt" 90 2>>"$LOG") && success=true || true
    fi

    # Step 2: Fallback ke Ollama langsung
    if [ "$success" = false ] || [ -z "$result" ]; then
        local model
        model=$(get_ollama_model)
        if [ -z "$model" ]; then
            echo "  ✗ FAIL: No Ollama model available" >> "$LOG"
            return 1
        fi
        echo "  → Using Ollama ($model) direct call" >> "$LOG"
        result=$(call_ollama "$model" "$research_prompt" "$system_prompt" 120 2>>"$LOG") && success=true || true
    fi

    if [ "$success" = false ] || [ -z "$result" ]; then
        echo "  ✗ FAIL: Both Hermes API and Ollama failed" >> "$LOG"
        return 1
    fi

    # Simpan ke SKP
    local save_output
    save_output=$(save_to_skp "$skp_key" "$result" "$senator" 2>>"$LOG")
    echo "  ✓ $senator: $save_output" >> "$LOG"
    echo "  Key: $skp_key" >> "$LOG"
    return 0
}

# ── Deteksi model ─────────────────────────────────────────────────────
OLLAMA_MODEL=$(get_ollama_model)
echo "Available Ollama model: ${OLLAMA_MODEL:-NONE}" >> "$LOG"

# ── Senator 1: Akademisi ──────────────────────────────────────────────
FAILED=0

run_senator \
    "senator-akademisi" \
    "akademisi" \
    "akademisi/temuan" \
    "Kamu adalah Senator Akademisi dari Upshalter Pentahelix. Spesialisasimu: riset AI, teknologi, dan pendidikan Indonesia. Tulis analisa terstruktur dalam Bahasa Indonesia. Format output: JSON dengan field temuan (array), sumber (array), relevansi_bisnis (string), timestamp." \
    "Lakukan riset tentang perkembangan terbaru AI, teknologi, dan pendidikan tinggi di Indonesia hari ini ($TIMESTAMP). Fokus: (1) Publikasi/riset baru dari universitas Indonesia, (2) Program AI pemerintah untuk pendidikan, (3) Startup edtech Indonesia terbaru. Identifikasi 3-5 temuan paling signifikan. Output dalam JSON." \
|| ((FAILED++)) || true

# ── Senator 2: Bisnis ─────────────────────────────────────────────────
run_senator \
    "senator-bisnis" \
    "bisnis" \
    "bisnis/peluang" \
    "Kamu adalah Senator Bisnis dari Upshalter Pentahelix. Spesialisasimu: market intelligence, startup Indonesia, ekonomi digital. Analisa bisnis yang tajam dan actionable dalam Bahasa Indonesia. Format output: JSON dengan field peluang (array), risiko (array), rekomendasi (string), timestamp." \
    "Lakukan riset market intelligence Indonesia untuk tanggal $TIMESTAMP. Fokus: (1) Funding/investasi startup Indonesia terbaru, (2) Pergerakan pasar digital/e-commerce, (3) Tren UMKM dan digitalisasi bisnis, (4) Ekonomi makro yang mempengaruhi bisnis digital. Identifikasi 3-5 peluang bisnis paling menarik. Output dalam JSON." \
|| ((FAILED++)) || true

# ── Senator 3: Komunitas ──────────────────────────────────────────────
run_senator \
    "senator-komunitas" \
    "komunitas" \
    "komunitas/isu" \
    "Kamu adalah Senator Komunitas dari Upshalter Pentahelix. Spesialisasimu: sentiment komunitas tech Indonesia, developer ecosystem, opini publik tentang AI. Analisa sentiment yang nuanced dalam Bahasa Indonesia. Format output: JSON dengan field isu (array), sentiment (string: positif/negatif/netral), tokoh_kunci (array), timestamp." \
    "Lakukan riset sentiment komunitas tech dan developer Indonesia untuk $TIMESTAMP. Fokus: (1) Topik yang sedang ramai di komunitas developer Indonesia, (2) Sikap komunitas terhadap AI dan otomatisasi, (3) Isu yang muncul di forum/grup tech Indonesia, (4) Opini developer tentang tools/platform baru. Identifikasi 3-5 isu paling penting. Output dalam JSON." \
|| ((FAILED++)) || true

# ── Senator 4: Pemerintah ─────────────────────────────────────────────
run_senator \
    "senator-pemerintah" \
    "pemerintah" \
    "pemerintah/regulasi" \
    "Kamu adalah Senator Pemerintah dari Upshalter Pentahelix. Spesialisasimu: kebijakan digital Indonesia, regulasi AI, program pemerintah teknologi. Analisa kebijakan yang presisi dalam Bahasa Indonesia. Format output: JSON dengan field regulasi (array), dampak_bisnis (string), compliance_notes (array), timestamp." \
    "Lakukan riset kebijakan dan regulasi pemerintah Indonesia terkait digital/AI untuk $TIMESTAMP. Fokus: (1) Regulasi atau kebijakan digital terbaru dari Kominfo/Kemenko, (2) Program pemerintah tentang AI dan transformasi digital, (3) Tender atau pengadaan IT pemerintah terbaru, (4) Update PDPA atau kebijakan data. Identifikasi 3-5 regulasi/kebijakan paling berdampak. Output dalam JSON." \
|| ((FAILED++)) || true

# ── Senator 5: Media ──────────────────────────────────────────────────
run_senator \
    "senator-media" \
    "media" \
    "media/narasi" \
    "Kamu adalah Senator Media dari Upshalter Pentahelix. Spesialisasimu: narasi media Indonesia tentang AI, framing teknologi, sentiment publik. Analisa media yang kritis dalam Bahasa Indonesia. Format output: JSON dengan field narasi_dominan (array), framing (string), sentiment_publik (string), media_utama (array), timestamp." \
    "Lakukan analisa narasi media Indonesia tentang AI dan teknologi untuk $TIMESTAMP. Fokus: (1) Bagaimana media nasional Indonesia memframing AI (positif/negatif/netral), (2) Topik AI yang sedang trending di media Indonesia, (3) Tokoh/perusahaan yang banyak disebut dalam konteks AI, (4) Kekhawatiran atau antusiasme yang paling sering muncul. Identifikasi 3-5 narasi dominan. Output dalam JSON." \
|| ((FAILED++)) || true

# ── Summary ───────────────────────────────────────────────────────────
SUCCESS=$((5 - FAILED))
echo "" >> "$LOG"
echo "════════ SENATOR CYCLE DONE: $SUCCESS/5 success, $FAILED failed ════════" >> "$LOG"
echo "SKP entries written for cycle: $DATE_KEY" >> "$LOG"

# ── Notifikasi ke Telegram ────────────────────────────────────────────
TOTAL_SKP=$(python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$SKP_DB')
    print(conn.execute('SELECT COUNT(*) FROM memory_notes').fetchone()[0])
    conn.close()
except: print('?')
" 2>/dev/null)

# Trigger kurator setelah 5 menit jika semua sukses
if [ $FAILED -eq 0 ]; then
    echo "All senators succeeded. Scheduling kurator in 5 min..." >> "$LOG"
    (sleep 300 && bash /root/upshalter-scripts/kurator-v2.sh) &
fi

echo "SENATOR CYCLE v2 SELESAI: $(date) | Success: $SUCCESS/5 | SKP total: $TOTAL_SKP" >> "$LOG"
