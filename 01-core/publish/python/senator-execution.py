#!/usr/bin/env python3
"""
senator-execution.py — Arsify Workforce OS
THE MISSING LAYER: Menjalankan satu Senator dan menulis INSIGHT NYATA ke SKP.

Ini adalah kode yang hilang. Senator lama menyimpan prompt-nya sendiri ke SKP.
Script ini memastikan yang tersimpan adalah hasil analisis, bukan prompt.

Alur yang benar:
  1. Build prompt (+ memory context dari cycle sebelumnya)
  2. Call LLM (Upshalter :8100 atau OpenRouter)
  3. Parse response → extract structured insights
  4. Validate insight (bukan prompt junk)
  5. Write ke SKP dengan format yang benar
  6. Return count of insights written

Usage:
  python3 senator-execution.py --domain akademisi
  python3 senator-execution.py --domain bisnis --dry-run
  python3 senator-execution.py --domain pemerintah --test-mode
"""

import sys, os, json, re, argparse, sqlite3, hashlib
from datetime import datetime, timezone
from typing import Optional

# ── Auto-detect SKP ───────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from skp_adapter import SKP, find_db, find_table
    USE_ADAPTER = True
except ImportError:
    USE_ADAPTER = False

# ── Config ────────────────────────────────────────────────────────────
UPSHALTER_API     = os.getenv("UPSHALTER_API", "http://localhost:8100")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
MODEL          = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
SDIR           = os.getenv("SCRIPT_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIMESTAMP      = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
DATE_KEY       = datetime.now(timezone.utc).strftime("%Y%m%d-%H")

# ── Domain Configuration ──────────────────────────────────────────────
DOMAIN_CONFIG = {
    "akademisi": {
        "system": (
            "Kamu adalah Senator Akademisi dari Arsify Workforce OS. "
            "Kamu adalah intelligence analyst permanen untuk domain riset, "
            "teknologi, dan pendidikan tinggi Indonesia. "
            "Tugas: hasilkan intelligence nyata — fakta, angka, nama institusi, "
            "dan implikasi bisnis. BUKAN deskripsi tugasmu."
        ),
        "prompt": (
            f"Lakukan intelligence scan domain akademisi Indonesia untuk {TIMESTAMP}.\n\n"
            "Temukan dan laporkan:\n"
            "- Publikasi/riset AI terbaru dari universitas Indonesia (nama institusi + topik)\n"
            "- Update program pemerintah untuk AI di pendidikan (Kemdikbud, BRIN)\n"
            "- Startup/spinoff edtech Indonesia yang baru aktif\n"
            "- Hibah atau funding riset AI yang sedang dibuka\n"
            "- Talent pipeline: ada peningkatan/penurunan program AI di kampus?\n\n"
            "Format output HANYA JSON berikut (tidak ada teks lain):\n"
            '{"temuan":[{"judul":"...","detail":"...","sumber":"...","dampak_bisnis":"...","urgensi":"tinggi|sedang|rendah"}],'
            '"peluang_baru":["..."],'
            '"sinyal_lemah":["..."],'
            f'"confidence":0.0,"timestamp":"{TIMESTAMP}"}}'
        ),
        "insight_fields": ["temuan", "peluang_baru", "sinyal_lemah"],
        "key_prefix": "senator-akademisi/insight",
    },
    "bisnis": {
        "system": (
            "Kamu adalah Senator Bisnis dari Arsify Workforce OS. "
            "Intelligence analyst untuk market, startup, ekonomi digital Indonesia. "
            "Hasilkan market intelligence yang actionable — data spesifik, bukan opini umum."
        ),
        "prompt": (
            f"Market intelligence scan Indonesia untuk {TIMESTAMP}.\n\n"
            "Temukan dan laporkan:\n"
            "- Funding/akuisisi startup Indonesia terbaru (nominal + investor)\n"
            "- Tren e-commerce: platform, kategori, shift konsumen\n"
            "- Regulasi OJK/BI yang baru memengaruhi bisnis digital\n"
            "- Gap pasar yang belum diisi kompetitor besar\n"
            "- Indikator makro: rupiah, BI rate, dampak ke startup\n\n"
            "Format output HANYA JSON:\n"
            '{"peluang":[{"nama":"...","detail":"...","estimasi_nilai":"...","urgensi":"tinggi|sedang|rendah"}],'
            '"risiko":[{"nama":"...","dampak":"...","probabilitas":"tinggi|sedang|rendah"}],'
            '"funding_tracker":[{"startup":"...","amount":"...","stage":"...","investor":"..."}],'
            '"rekomendasi":"...",'
            f'"confidence":0.0,"timestamp":"{TIMESTAMP}"}}'
        ),
        "insight_fields": ["peluang", "risiko", "funding_tracker"],
        "key_prefix": "senator-bisnis/insight",
    },
    "komunitas": {
        "system": (
            "Kamu adalah Senator Komunitas dari Arsify Workforce OS. "
            "Intelligence analyst untuk komunitas tech dan developer Indonesia. "
            "Hasilkan sentiment analysis yang nuanced dengan data konkret."
        ),
        "prompt": (
            f"Komunitas tech Indonesia sentiment scan untuk {TIMESTAMP}.\n\n"
            "Temukan dan laporkan:\n"
            "- Topik yang paling ramai dibahas di komunitas developer Indonesia\n"
            "- Opini komunitas tentang AI, tools, regulasi\n"
            "- Tokoh tech Indonesia yang sedang banyak dikutip\n"
            "- Isu burnout, hiring freeze, atau perubahan kultur kerja\n"
            "- Project open-source Indonesia yang mendapat traksi\n\n"
            "Format output HANYA JSON:\n"
            '{"isu":[{"topik":"...","sentiment":"positif|negatif|netral","intensitas":"tinggi|sedang|rendah","detail":"...","platform":"..."}],'
            '"tokoh_kunci":[{"nama":"...","handle":"...","konteks":"..."}],'
            '"tools_trending":["..."],'
            '"sentiment_overall":"positif|negatif|netral|campuran",'
            f'"confidence":0.0,"timestamp":"{TIMESTAMP}"}}'
        ),
        "insight_fields": ["isu", "tokoh_kunci", "tools_trending"],
        "key_prefix": "senator-komunitas/insight",
    },
    "pemerintah": {
        "system": (
            "Kamu adalah Senator Pemerintah dari Arsify Workforce OS. "
            "Intelligence analyst untuk kebijakan digital dan regulasi Indonesia. "
            "Hasilkan compliance intelligence dengan nomor pasal dan deadline spesifik."
        ),
        "prompt": (
            f"Regulatory intelligence scan Indonesia untuk {TIMESTAMP}.\n\n"
            "Temukan dan laporkan:\n"
            "- Regulasi atau kebijakan digital baru dari Kominfo/OJK/BI\n"
            "- Update implementasi UU PDP (nomor pasal, deadline compliance)\n"
            "- Program AI pemerintah yang sedang berjalan atau dibuka\n"
            "- Tender IT pemerintah yang relevan untuk bisnis digital\n"
            "- Risiko compliance yang perlu diwaspadai startup\n\n"
            "Format output HANYA JSON:\n"
            '{"regulasi":[{"nama":"...","nomor":"...","lembaga":"...","tanggal_efektif":"...","deadline_compliance":"...","dampak_bisnis":"...","urgensi":"kritis|tinggi|sedang|rendah"}],'
            '"program_pemerintah":[{"nama":"...","anggaran":"...","cara_akses":"...","deadline":"..."}],'
            '"alert_compliance":["..."],'
            f'"confidence":0.0,"timestamp":"{TIMESTAMP}"}}'
        ),
        "insight_fields": ["regulasi", "program_pemerintah", "alert_compliance"],
        "key_prefix": "senator-pemerintah/insight",
    },
    "media": {
        "system": (
            "Kamu adalah Senator Media dari Arsify Workforce OS. "
            "Intelligence analyst untuk narasi dan framing media Indonesia. "
            "Hasilkan media framing analysis yang spesifik per media outlet."
        ),
        "prompt": (
            f"Media narrative intelligence scan Indonesia untuk {TIMESTAMP}.\n\n"
            "Temukan dan laporkan:\n"
            "- Bagaimana Kompas, Tempo, Detik, CNBC Indonesia memframing AI\n"
            "- Topik tech yang sedang trending di media Indonesia\n"
            "- Tokoh atau perusahaan yang paling sering disebut terkait AI\n"
            "- Pergeseran sentiment publik tentang AI (estimasi %)\n"
            "- Narasi yang berbeda antara media tech-savvy vs media mainstream\n\n"
            "Format output HANYA satu JSON block:\n"
            '{"narasi_dominan":[{"topik":"...","framing":"...","sentiment":"positif|negatif|netral","media_utama":["..."]}],'
            '"frekuensi_ai":{"per_minggu":0,"trend":"naik|turun|stabil"},'
            '"sentiment_publik":"positif|negatif|netral|campuran",'
            '"tokoh_tersebut":[{"nama":"...","konteks":"..."}],'
            f'"confidence":0.0,"timestamp":"{TIMESTAMP}"}}'
        ),
        "insight_fields": ["narasi_dominan", "tokoh_tersebut"],
        "key_prefix": "senator-media/insight",
    },
}

# ── Junk Detection ────────────────────────────────────────────────────
JUNK_PATTERNS = [
    "step: analyze and understand",
    "anda adalah senator",
    "kamu adalah senator",
    "anda adalah intelligence analyst",
    "kamu adalah intelligence analyst",
    "## misi inti",
    "soul.md",
    "[step ",
    "executing step",
    "workflow_step",
]

def is_junk_response(text: str) -> bool:
    """Return True jika response adalah prompt/junk, bukan insight."""
    text_lower = text.lower().strip()
    if len(text_lower) < 100:
        return True
    return any(p in text_lower for p in JUNK_PATTERNS)

# ── Memory Context ────────────────────────────────────────────────────
def get_memory_context(domain: str, limit: int = 2) -> str:
    """Ambil insight terbaru dari domain ini untuk context injection."""
    try:
        if USE_ADAPTER:
            skp = SKP()
            entries = skp.read_recent(domain, hours=24, limit=limit)
            if not entries:
                return ""
            lines = [f"INSIGHT DARI CYCLE SEBELUMNYA ({len(entries)} terakhir):"]
            for e in entries:
                val = e.get("value", "")[:200]
                if not is_junk_response(val):
                    lines.append(f"- {val}")
            return "\n".join(lines) if len(lines) > 1 else ""
    except Exception:
        pass
    return ""

# ── LLM Call ─────────────────────────────────────────────────────────
def call_upshalter(system: str, prompt: str, timeout: int = 120) -> Optional[str]:
    """Call Upshalter Cognitive Engine :8100 /v1/portsocket (cognitive path).
    
    Uses X-API-Key auth header, 'input' field (not 'messages'),
    and polls async result from /v1/result/{task_id}.
    """
    UPSHALTER_KEY = os.getenv("UPSHALTER_API_KEY", "upshalter-secret-change-me-in-production")
    full_input = f"{system}\n\n{prompt}"
    try:
        import httpx
        # Submit task to cognitive path
        r = httpx.post(f"{UPSHALTER_API}/v1/portsocket",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": UPSHALTER_KEY,
                "X-Agent-ID": "senator-execution",
            },
            json={"input": full_input[:30000], "mode": "auto"},
            timeout=30)
        if r.status_code != 200:
            print(f"  Upshalter submit failed: {r.status_code} {r.text[:200]}", file=sys.stderr)
            return None
        task_data = r.json()
        task_id = task_data.get("task_id")
        if not task_id:
            print(f"  Upshalter: no task_id in response", file=sys.stderr)
            return None
        print(f"  Upshalter task: {task_id} (polling...)")
        # Poll for result
        for attempt in range(int(timeout / 3)):
            import time
            time.sleep(3)
            pr = httpx.get(f"{UPSHALTER_API}/v1/result/{task_id}",
                headers={"X-API-Key": UPSHALTER_KEY},
                timeout=15)
            if pr.status_code != 200:
                continue
            result_data = pr.json()
            status = result_data.get("status", "")
            if status == "SUCCESS":
                result_obj = result_data.get("result", {})
                # Try to get actual LLM response
                if isinstance(result_obj, dict):
                    # Check results array
                    results = result_obj.get("results", [])
                    if results:
                        return str(results[0]) if results else None
                    # Check plan
                    plan = result_obj.get("plan")
                    if plan:
                        return str(plan)
                    # Fallback: return whole result as string
                    return json.dumps(result_obj, ensure_ascii=False)
                return str(result_obj)
            elif status == "FAILURE":
                err = result_data.get("error", "unknown")
                print(f"  Upshalter task failed: {err}", file=sys.stderr)
                return None
            # else: still PENDING/STARTED, keep polling
        print(f"  Upshalter task timed out after {timeout}s", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Upshalter error: {e}", file=sys.stderr)
        return None


def call_openrouter(system: str, prompt: str, timeout: int = 120) -> Optional[str]:
    """Call OpenRouter API."""
    if not OPENROUTER_KEY:
        return None
    try:
        import httpx
        r = httpx.post(f"{OPENROUTER_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://upshalter.com",
                "X-Title": "Arsify Workforce OS",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 2000,
                "temperature": 0.3,
            },
            timeout=timeout)
        r.raise_for_status()
        result = r.json()["choices"][0]["message"]["content"]
        if result and not is_junk_response(result):
            return result
        return None
    except Exception as e:
        print(f"  OpenRouter error: {e}", file=sys.stderr)
        return None


def call_ollama(system: str, prompt: str, timeout: int = 300) -> Optional[str]:
    """Ollama fallback."""
    try:
        import httpx
        tags = httpx.get("http://localhost:11434/api/tags", timeout=5).json()
        models = [m["name"] for m in tags.get("models", [])]
        if not models:
            return None
        model = next((m for p in ["qwen2.5:1.5b","phi3:mini","llama3.2:3b"] for m in models if p in m), models[0])
        r = httpx.post("http://localhost:11434/api/chat", json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 1500},
        }, timeout=timeout)
        r.raise_for_status()
        result = r.json()["message"]["content"]
        if result and not is_junk_response(result):
            return result
        return None
    except Exception:
        return None


# ── Response Parser ────────────────────────────────────────────────────
def parse_response(response: str, domain: str) -> list[dict]:
    """
    Parse LLM response menjadi list of insight objects.
    Handles: JSON response, markdown-wrapped JSON, free text.
    """
    insights = []

    # Step 1: Cari JSON block
    json_candidates = []

    # JSON dalam code block
    code_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    json_candidates.extend(code_blocks)

    # JSON langsung
    json_candidates.append(response.strip())

    # Cari { ... } terbesar
    bracket_match = re.search(r'\{[\s\S]*\}', response, re.DOTALL)
    if bracket_match:
        json_candidates.append(bracket_match.group())

    # Step 2: Parse JSON
    config = DOMAIN_CONFIG.get(domain, {})
    insight_fields = config.get("insight_fields", [])

    for candidate in json_candidates:
        try:
            data = json.loads(candidate)
            confidence = float(data.get("confidence", 0.5))

            for field in insight_fields:
                if field not in data:
                    continue
                items = data[field]
                if not isinstance(items, list):
                    continue

                for item in items:
                    if isinstance(item, dict):
                        # Buat summary string dari dict
                        summary_parts = []
                        for k in ["judul", "nama", "topik", "detail", "dampak_bisnis",
                                  "estimasi_nilai", "urgensi", "nomor", "lembaga"]:
                            if k in item and item[k]:
                                summary_parts.append(f"{k}: {item[k]}")
                        insight_text = " | ".join(summary_parts) if summary_parts else str(item)
                    elif isinstance(item, str):
                        insight_text = item
                    else:
                        continue

                    if insight_text and len(insight_text) > 20:
                        insights.append({
                            "text": insight_text[:500],
                            "raw": json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else insight_text,
                            "field": field,
                            "confidence": confidence,
                        })

            if insights:
                return insights

        except (json.JSONDecodeError, Exception):
            continue

    # Step 3: Fallback — parse free text
    if not insights and len(response) > 100 and not is_junk_response(response):
        # Split ke paragraf/bullet
        lines = [l.strip() for l in re.split(r'\n+|•|-\s', response) if len(l.strip()) > 30]
        for line in lines[:5]:
            if not is_junk_response(line):
                insights.append({
                    "text": line[:300],
                    "raw": line,
                    "field": "general",
                    "confidence": 0.3,
                })

    return insights


# ── SKP Writer ────────────────────────────────────────────────────────
def write_insights_to_skp(domain: str, insights: list[dict], dry_run: bool = False) -> int:
    """
    Tulis insights yang sudah diparse ke SKP.
    Returns: jumlah insight yang berhasil ditulis.
    """
    if not insights:
        return 0

    config = DOMAIN_CONFIG.get(domain, {})
    prefix = config.get("key_prefix", f"senator-{domain}/insight")

    written = 0

    if USE_ADAPTER:
        try:
            skp = SKP()
            for i, insight in enumerate(insights):
                # Key unik: prefix/date-counter
                key = f"{prefix}/{DATE_KEY}-{i:02d}"

                # Value: raw JSON jika ada, atau text
                value = insight.get("raw") or insight.get("text", "")
                if not value or is_junk_response(value):
                    continue

                if dry_run:
                    print(f"  [DRY] Would write: {key}")
                    print(f"         Value: {value[:100]}...")
                else:
                    skp.write(key, value, agent=f"senator-{domain}", category=domain)
                    print(f"  ✓ Written: {key} ({len(value)} chars)")
                written += 1

            return written
        except Exception as e:
            print(f"  Adapter error: {e}", file=sys.stderr)

    # Fallback: direct SQLite
    try:
        db = find_db() if USE_ADAPTER else next(
            (p for p in ["/data/arsify.db", "/data/shared_knowledge_pool.db"] if os.path.exists(p)), None
        )
        if not db:
            print("ERROR: No database found", file=sys.stderr)
            return 0

        conn = sqlite3.connect(db)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        table = next((t for t in ["knowledge", "memory_notes"] if t in tables), tables[0] if tables else "knowledge")
        now = datetime.now(timezone.utc).isoformat()

        for i, insight in enumerate(insights):
            key = f"{prefix}/{DATE_KEY}-{i:02d}"
            value = insight.get("raw") or insight.get("text", "")
            if not value or is_junk_response(value):
                continue

            if not dry_run:
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                if "source_agent_name" in cols and "category" in cols:
                    conn.execute(
                        f"INSERT OR REPLACE INTO {table} (key,value,source_agent_name,category,updated_at) VALUES(?,?,?,?,?)",
                        (key, value[:3000], f"senator-{domain}", domain, now)
                    )
                else:
                    conn.execute(
                        f"INSERT OR REPLACE INTO {table} (key,value) VALUES(?,?)",
                        (key, value[:3000])
                    )
                print(f"  ✓ Written: {key}")
            else:
                print(f"  [DRY] Would write: {key}")
            written += 1

        if not dry_run:
            conn.commit()
            total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  SKP total: {total} entries")
        conn.close()

    except Exception as e:
        print(f"  SQLite error: {e}", file=sys.stderr)

    return written


# ── Main ──────────────────────────────────────────────────────────────
def run_senator(domain: str, dry_run: bool = False, test_mode: bool = False) -> dict:
    config = DOMAIN_CONFIG.get(domain)
    if not config:
        return {"error": f"Unknown domain: {domain}", "written": 0}

    print(f"\n{'='*60}")
    print(f"SENATOR {domain.upper()} — {TIMESTAMP}")
    print(f"{'='*60}")

    # Step 1: Memory context
    memory = get_memory_context(domain)
    full_prompt = config["prompt"]
    if memory:
        full_prompt = memory + "\n\n---\n\n" + full_prompt
        print(f"  Memory: injected ({len(memory)} chars)")
    else:
        print(f"  Memory: none (first cycle)")

    # Step 2: Call LLM — skip Upshalter (L3/L4 pipeline not returning LLM text),
    # go directly to OpenRouter which we verified works
    if test_mode:
        response = f'''{{"temuan":[{{"judul":"Test insight untuk {domain}","detail":"Data test dari {TIMESTAMP}","sumber":"test","dampak_bisnis":"Test impact","urgensi":"rendah"}}],"peluang_baru":["Test opportunity"],"sinyal_lemah":["Test signal"],"confidence":0.9,"timestamp":"{TIMESTAMP}"}}'''
        print(f"  LLM: TEST MODE (using mock response)")
    else:
        # Try OpenRouter directly (verified key works)
        print(f"  LLM: Calling OpenRouter ({MODEL})...")
        response = call_openrouter(config["system"], full_prompt)

        if not response:
            print(f"  LLM: Trying Ollama fallback...")
            response = call_ollama(config["system"], full_prompt)

        if not response:
            print(f"  ✗ All LLM providers failed")
            return {"error": "all providers failed", "written": 0, "domain": domain}

    print(f"  Response length: {len(response)} chars")
    print(f"  Response preview: {response[:100]}...")

    # Step 3: Parse response
    insights = parse_response(response, domain)
    print(f"  Insights parsed: {len(insights)}")

    if not insights:
        print(f"  ✗ No insights extracted from response")
        # Debug: show full response
        print(f"  Full response: {response[:300]}")
        return {"error": "no insights parsed", "written": 0, "domain": domain, "response": response[:300]}

    # Step 4: Write to SKP
    written = write_insights_to_skp(domain, insights, dry_run=dry_run)
    print(f"  ✓ Insights written to SKP: {written}")

    return {
        "domain": domain,
        "insights_parsed": len(insights),
        "written": written,
        "status": "success" if written > 0 else "no_data",
    }


def main():
    parser = argparse.ArgumentParser(description="Arsify Senator Execution Engine")
    parser.add_argument("--domain", choices=list(DOMAIN_CONFIG.keys()), required=True)
    parser.add_argument("--dry-run", action="store_true", help="Parse tapi tidak tulis ke SKP")
    parser.add_argument("--test-mode", action="store_true", help="Gunakan mock LLM response")
    parser.add_argument("--all", action="store_true", help="Jalankan semua 5 domain")
    args = parser.parse_args()

    if args.all:
        results = []
        for domain in DOMAIN_CONFIG.keys():
            r = run_senator(domain, dry_run=args.dry_run, test_mode=args.test_mode)
            results.append(r)
        print(f"\n{'='*60}")
        print("SUMMARY")
        for r in results:
            status = r.get("status", r.get("error", "?"))
            print(f"  {r.get('domain','?')}: {status} ({r.get('written',0)} insights)")
    else:
        result = run_senator(args.domain, dry_run=args.dry_run, test_mode=args.test_mode)
        print(f"\nResult: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
