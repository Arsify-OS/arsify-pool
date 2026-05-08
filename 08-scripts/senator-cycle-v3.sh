#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  SENATOR CYCLE v3.0 — OpenRouter API primary, Ollama last resort
#  Mei 2026
# ═══════════════════════════════════════════════════════════════════════
#
#  Root cause fix: Ollama CPU-only terlalu lambat (39s load + >60s inference)
#  Hermes API /chat → fast path unavailable (routes to Ollama lokal)
#  Hermes API /v1/portsocket → async, Celery worker tidak memproses
#  Solution: OpenRouter API langsung (bypass Hermes & Ollama total)
#            Ollama hanya last resort dengan timeout ketat
#
#  Changelog dari v2:
#    - Primary: OpenRouter API (https://openrouter.ai/api/v1)
#    - Fallback: Ollama lokal (timeout 30s, num_predict 512)
#    - Auth: X-API-Key header
#    - Model: openrouter/owl-alpha (default)
#
# ═══════════════════════════════════════════════════════════════════════

set -uo pipefail

OPENROUTER_API="https://openrouter.ai/api/v1"
OPENROUTER_API_KEY="INSERT_OPENROUTER_KEY_HERE"
OPENROUTER_MODEL="openrouter/owl-alpha"

OLLAMA_API="http://localhost:11434"
LOG_DIR="/root/upshalter-logs"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
DATE_KEY=$(date +%Y%m%d-%H)
LOG="$LOG_DIR/senator-$(date +%Y%m%d).log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$LOG_DIR"
echo "" >> "$LOG"
echo "═══ SENATOR CYCLE v3.0 START: $TIMESTAMP ═══" >> "$LOG"

# ── SKP Detection via Python ──────────────────────────────────────────
SKP_INFO=$(python3 - << 'PYEOF'
import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python'))
try:
    from skp_adapter import SKP
    skp = SKP()
    info = skp.get_info()
    print(json.dumps(info))
except Exception as e:
    candidates = ["/data/arsify.db", "/data/shared_knowledge_pool.db", "/root/.hermes/shared_knowledge_pool.db"]
    db = next((p for p in candidates if os.path.exists(p)), "/data/arsify.db")
    print(json.dumps({"db_path": db, "table": "memory_notes", "total_entries": 0, "router_path": None}))
PYEOF
)

SKP_DB=$(echo "$SKP_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['db_path'])" 2>/dev/null || echo "/data/arsify.db")
SKP_TABLE=$(echo "$SKP_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['table'])" 2>/dev/null || echo "memory_notes")

echo "SKP: $SKP_DB | Table: $SKP_TABLE" >> "$LOG"

# ── Detect Ollama model (fallback only) ───────────────────────────────
get_ollama_model() {
    curl -sf "$OLLAMA_API/api/tags" 2>/dev/null | python3 -c "
import sys,json
try:
    ms = [m['name'] for m in json.load(sys.stdin).get('models',[])]
    prefer = ['qwen2.5:0.5b','phi3:mini','qwen2.5:1.5b','tinyllama']
    for p in prefer:
        if any(p in m for m in ms): print(p); exit()
    print(ms[0] if ms else '')
except: print('')
" 2>/dev/null || echo ""
}
OLLAMA_MODEL=$(get_ollama_model)
echo "Ollama model (fallback): ${OLLAMA_MODEL:-NONE}" >> "$LOG"

# ── Save to SKP (adaptive) ────────────────────────────────────────────
save_skp() {
    local domain="$1" content="$2" agent="$3"
    python3 - << PYEOF
import sys, json, os
sys.path.insert(0, os.path.join('$SCRIPT_DIR', 'python'))
try:
    from skp_adapter import SKP
    skp = SKP()
    key = skp.write_senator("$domain", """$content""", "$agent")
    total = skp.get_info()['total_entries']
    print(f"✓ Saved: {key} | Total SKP: {total}")
except Exception as e:
    import sqlite3
    from datetime import datetime, timezone
    db = "$SKP_DB"
    table = "$SKP_TABLE"
    key = "${domain}/temuan/${DATE_KEY}"
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(db)
    try:
        conn.execute(f"INSERT OR REPLACE INTO {table} (key, value, source_agent_name) VALUES (?,?,?)",
            (key, """$content"""[:3000], "$agent"))
        conn.commit()
        total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"✓ Fallback saved: {key} | Total: {total}")
    except Exception as e2:
        print(f"✗ Save failed: {e2}", file=sys.stderr)
    finally:
        conn.close()
PYEOF
}

# ── Call LLM: OpenRouter primary → Ollama fallback ────────────────────
call_llm() {
    local system="$1" prompt="$2" timeout="${3:-60}"

    # ── PRIMARY: OpenRouter API ──
    local result
    result=$(python3 - << PYEOF 2>/dev/null
import httpx, json, sys
try:
    r = httpx.post(
        "$OPENROUTER_API/chat/completions",
        headers={
            "Authorization": "Bearer $OPENROUTER_API_KEY",
            "Content-Type": "application/json"
        },
        json={
            "model": "$OPENROUTER_MODEL",
            "messages": [
                {"role": "system", "content": """$system"""},
                {"role": "user", "content": """$prompt"""}
            ],
            "max_tokens": 2048
        },
        timeout=$timeout
    )
    if r.status_code == 200:
        d = r.json()
        content = d.get("choices", [{}])[0].get("message", {}).get("content", "")
        if content:
            print(content)
            exit(0)
    else:
        print(f"OR_ERR:{r.status_code}:{r.text[:200]}", file=sys.stderr)
except Exception as e:
    print(f"OR_ERR:{e}", file=sys.stderr)
PYEOF
    )
    if [ -n "$result" ]; then
        echo "$result"
        return 0
    fi

    # ── FALLBACK: Ollama (CPU-only, strict timeout) ──
    [ -z "$OLLAMA_MODEL" ] && return 1
    python3 - << PYEOF
import httpx, sys
try:
    r = httpx.post("$OLLAMA_API/api/chat", json={
        "model": "$OLLAMA_MODEL",
        "messages": [
            {"role":"system","content":"""$system"""},
            {"role":"user","content":"""$prompt"""}
        ],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 512}
    }, timeout=30.0)
    r.raise_for_status()
    print(r.json()["message"]["content"])
except Exception as e:
    print(f"OLLAMA_ERR:{e}", file=sys.stderr)
    sys.exit(1)
PYEOF
}

# ── Jalankan Senator ──────────────────────────────────────────────────
FAILED=0

run_senator() {
    local name="$1" domain="$2" system_prompt="$3" research_prompt="$4"
    echo "[$(date +%H:%M:%S)] $name..." >> "$LOG"
    local result
    result=$(call_llm "$system_prompt" "$research_prompt" 60 2>>"$LOG") || {
        echo "  ✗ $name: LLM call failed" >> "$LOG"
        return 1
    }
    [ -z "$result" ] && { echo "  ✗ $name: empty result" >> "$LOG"; return 1; }
    save_output=$(save_skp "$domain" "$result" "$name" 2>>"$LOG")
    echo "  $save_output" >> "$LOG"
    return 0
}

run_senator "senator-akademisi" "akademisi" \
    "Kamu Senator Akademisi Upshalter. Analisa riset AI, teknologi, pendidikan Indonesia. JSON output." \
    "Riset perkembangan AI, teknologi, pendidikan tinggi Indonesia hari ini $TIMESTAMP. Temukan 3-5 hal paling signifikan. Format: {temuan:[...], sumber:[...], relevansi_bisnis:'...', timestamp:'$TIMESTAMP'}" \
    || ((FAILED++)) || true

run_senator "senator-bisnis" "bisnis" \
    "Kamu Senator Bisnis Upshalter. Market intelligence, startup Indonesia, ekonomi digital. JSON output." \
    "Market intelligence Indonesia $TIMESTAMP: startup funding, UMKM digital, e-commerce, ekonomi makro. 3-5 peluang terpenting. Format: {peluang:[...], risiko:[...], rekomendasi:'...', timestamp:'$TIMESTAMP'}" \
    || ((FAILED++)) || true

run_senator "senator-komunitas" "komunitas" \
    "Kamu Senator Komunitas Upshalter. Sentiment komunitas tech Indonesia. JSON output." \
    "Sentiment komunitas tech developer Indonesia $TIMESTAMP: isu panas, opini AI, diskusi forum. 3-5 isu terpenting. Format: {isu:[...], sentiment:'positif/negatif/netral', tokoh_kunci:[...], timestamp:'$TIMESTAMP'}" \
    || ((FAILED++)) || true

run_senator "senator-pemerintah" "pemerintah" \
    "Kamu Senator Pemerintah Upshalter. Kebijakan digital, regulasi AI, program pemerintah Indonesia. JSON output." \
    "Regulasi dan kebijakan digital pemerintah Indonesia $TIMESTAMP: Kominfo, PDPA, tender IT, program AI. 3-5 paling berdampak ke bisnis. Format: {regulasi:[...], dampak_bisnis:'...', compliance_notes:[...], timestamp:'$TIMESTAMP'}. Sebutkan nomor pasal spesifik, lembaga penyelenggara, dan deadline compliance yang relevan untuk bisnis digital dan startup Indonesia." \
    || ((FAILED++)) || true

run_senator "senator-media" "media" \
    "Kamu Senator Media Upshalter. Narasi dan framing media Indonesia tentang AI. JSON output." \
    "Narasi media Indonesia tentang AI dan teknologi $TIMESTAMP: framing berita, sentiment publik, topik trending. 3-5 narasi dominan. Format: {narasi_dominan:[...], framing:'...', sentiment_publik:'...', media_utama:[...], timestamp:'$TIMESTAMP'}. Output hanya SATU JSON block, tidak ada teks di luar JSON." \
    || ((FAILED++)) || true

# ── Summary ───────────────────────────────────────────────────────────
SUCCESS=$((5 - FAILED))
echo "═══ DONE: $SUCCESS/5 success ═══" >> "$LOG"

[ $SUCCESS -gt 0 ] && {
    echo "Scheduling kurator-v2 in 5min..." >> "$LOG"
    ( sleep 300 && bash "$SCRIPT_DIR/kurator-v2.sh") &
}
