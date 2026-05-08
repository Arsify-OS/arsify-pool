#!/usr/bin/env python3
"""
category-backfill v2.1 — Fixed: auto-detect table (knowledge vs memory_notes)
Mei 2026
"""

import sqlite3, os, json, re, sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '.'))
try:
    from skp_adapter import SKP, find_db, find_table
    USE_ADAPTER = True
except ImportError:
    USE_ADAPTER = False

DB_PATH = find_db() if USE_ADAPTER else os.getenv("SKP_DB_PATH", "/data/arsify.db")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
NOW = datetime.now(timezone.utc).isoformat()

CATEGORY_RULES = [
    ("upshalter",   10, ["upshalter/","arsify","pentahelix","senator","kurator","arsiparis","hermes","skp","prd/","rules/","automation/"]),
    ("pemerintah",   9, ["pemerintah/","senator-pemerintah","regulasi","peraturan pemerintah","kebijakan","undang-undang","kominfo","kemenkominfo","bpssn","ojk","pdpa","perlindungan data","tender","apbn","perpres","spbe","e-government"]),
    ("keamanan",     8, ["keamanan","security","cve","vulnerability","exploit","bug bounty","pentest","siber","enkripsi","zero day","patch"]),
    ("akademisi",    8, ["akademisi/","senator-akademisi","riset","penelitian","publikasi","jurnal","universitas","kampus","dosen","mahasiswa","scopus","dikti","brin","pendidikan tinggi","paper"]),
    ("laporan",      7, ["laporan/","brief","report","konsolidasi","ringkasan","summary","daily","weekly"]),
    ("bisnis",       7, ["bisnis/","senator-bisnis","startup","funding","investasi","umkm","e-commerce","marketplace","fintech","revenue","profit","market","ekonomi digital","saham","bursa"]),
    ("ai-ml",        6, ["machine learning","deep learning","neural network","llm","large language model","gpt","claude","gemini","mistral","llama","artificial intelligence","generative ai","rag ","embedding","nlp","transformer"]),
    ("komunitas",    6, ["komunitas/","senator-komunitas","developer","programmer","github","open source","hackathon","meetup","forum developer","sentiment komunitas","indo dev","bootcamp"]),
    ("media",        5, ["media/","senator-media","narasi","framing","kompas","tempo","detik","cnbc indonesia","katadata","pemberitaan","wartawan","media sosial","viral","trending"]),
]

TAG_RULES = {
    "ai-relevan":     ["ai","machine learning","llm","generative","artificial intelligence","transformer"],
    "regulasi":       ["regulasi","peraturan","kebijakan","undang-undang","kominfo","pdpa","ojk"],
    "bisnis-peluang": ["startup","funding","investasi","umkm","revenue","market opportunity"],
    "riset":          ["riset","penelitian","paper","jurnal","publikasi","scopus"],
    "urgent":         ["alert","kritis","segera","darurat","regulasi baru"],
    "indonesia":      ["indonesia","jakarta","bandung","nusantara","wib"],
    "teknologi":      ["teknologi","digital","software","platform","aplikasi"],
}

PRIORITY_MAP = {"upshalter":10,"keamanan":8,"pemerintah":8,"laporan":7,"bisnis":6,"ai-ml":6,"akademisi":5,"komunitas":3,"media":4,"general":2}


def classify(key: str, value: str):
    combined = (key + " " + value).lower()
    best_cat, best_score = "general", 0
    for cat, weight, kws in CATEGORY_RULES:
        score = sum((3 if kw in key.lower() else 1) for kw in kws if kw in combined) * weight
        if score > best_score:
            best_score, best_cat = score, cat
    tags = [tag for tag, kws in TAG_RULES.items() if any(kw in combined for kw in kws)][:5]
    return best_cat, list(set(tags)), PRIORITY_MAP.get(best_cat, 5)


def get_cols(conn, table):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def add_cols(conn, table):
    cols = get_cols(conn, table)
    for col, defval in [("category","'general'"),("tags","'[]'"),("priority","5")]:
        if col not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT DEFAULT {defval}")
    conn.commit()


def main():
    print(f"=== SKP CATEGORY BACKFILL v2.1 ===")

    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found: {DB_PATH}"); return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Auto-detect table
    table = find_table(conn) if USE_ADAPTER else "memory_notes"
    print(f"DB: {DB_PATH}")
    print(f"Table: {table}")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE UPDATE'}")
    print()

    add_cols(conn, table)
    cols = get_cols(conn, table)

    total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    before_gen = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE category='general' OR category IS NULL").fetchone()[0]
    print(f"Before: {before_gen}/{total} = {before_gen/max(total,1)*100:.1f}% general")
    print()

    # PENTING: hanya proses entries yang masih 'general' atau NULL
    # Jangan timpa entries yang sudah punya kategori benar (curated, backend, dll)
    rows = conn.execute(f"""
        SELECT id, key, value FROM {table}
        WHERE category IS NULL OR category = 'general' OR category = ''
    """).fetchall()
    updates, stats = [], {}
    for row in rows:
        cat, tags, pri = classify(row["key"], row["value"])
        stats[cat] = stats.get(cat, 0) + 1
        updates.append((cat, json.dumps(tags), pri, NOW, row["id"]))

    if not DRY_RUN:
        if "priority" in cols and "tags" in cols:
            conn.executemany(f"UPDATE {table} SET category=?, tags=?, priority=?, updated_at=? WHERE id=?", updates)
        else:
            conn.executemany(f"UPDATE {table} SET category=? WHERE id=?", [(u[0],u[4]) for u in updates])
        conn.commit()

    print("Category distribution (after):")
    for cat, count in sorted(stats.items(), key=lambda x: -x[1]):
        pct = count / max(total, 1) * 100
        bar = "█" * int(pct / 5)
        print(f"  {cat:<20} {count:4d} ({pct:5.1f}%) {bar}")

    if not DRY_RUN:
        after_gen = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE category='general' OR category IS NULL").fetchone()[0]
        print(f"\nAfter:  {after_gen}/{total} = {after_gen/max(total,1)*100:.1f}% general")
        print(f"Improvement: -{before_gen-after_gen} general entries")

    conn.close()
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
