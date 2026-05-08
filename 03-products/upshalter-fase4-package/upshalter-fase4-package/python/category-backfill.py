#!/usr/bin/env python3
"""
category-backfill.py — Upshalter SKP Category Enrichment
Versi: 1.0 — Mei 2026

Masalah yang diselesaikan:
  334/414 (80.7%) entries dikategorikan "general"
  Target: < 30% general setelah backfill

Cara kerja:
  1. Baca semua entries dengan category = 'general'
  2. Classify berdasarkan key pattern + keyword matching
  3. Update category dan tags di database

Tidak butuh ML library — pakai rule-based matching yang akurat.
"""

import sqlite3
import json
import os
import re
from datetime import datetime

# ── Konfigurasi ──────────────────────────────────────────────────────────
DB_PATH = os.getenv("SKP_DB_PATH", "/data/arsify.db")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
NOW = datetime.utcnow().isoformat()

# ── Aturan Klasifikasi ─────────────────────────────────────────────────
# Format: (kategori, priority, [keywords_in_key_or_value])
CATEGORY_RULES = [

    # === DOMAIN SENATOR ===
    ("akademisi", 8, [
        # Dari key pattern
        "akademisi/", "senator-akademisi",
        # Keywords konten
        "universitas", "perguruan tinggi", "riset", "penelitian", "publikasi",
        "jurnal", "scopus", "skripsi", "tesis", "disertasi", "akademis",
        "dosen", "mahasiswa", "kampus", "pendidikan tinggi", "inovasi iptek",
        "dikti", "kemdikbud", "brin", "lembaga riset", "paper", "citation"
    ]),

    ("bisnis", 7, [
        "bisnis/", "senator-bisnis",
        "startup", "funding", "investasi", "venture capital", "vc", "unicorn",
        "umkm", "usaha kecil", "e-commerce", "marketplace", "tokopedia",
        "shopee", "gojek", "grab", "traveloka", "fintech", "revenue",
        "profit", "market", "pasar", "ekonomi digital", "gdp", "pertumbuhan",
        "ekspor", "impor", "bisnis digital", "saham", "bursa", "idx",
        "perdagangan", "penjualan", "omzet", "rupiah", "dolar"
    ]),

    ("komunitas", 6, [
        "komunitas/", "senator-komunitas",
        "developer", "programmer", "komunitas tech", "github", "open source",
        "hackathon", "meetup", "conference", "forum", "discord", "slack",
        "twitter tech", "linkedin tech", "sentiment", "opini", "feedback",
        "review", "komentar komunitas", "tech indonesia", "indo dev",
        "coding", "bootcamp", "belajar coding", "workshop"
    ]),

    ("pemerintah", 9, [
        "pemerintah/", "senator-pemerintah",
        "regulasi", "peraturan", "kebijakan", "undang-undang", "uu ",
        "permenkominfo", "kominfo", "kemenkominfo", "kemenkeu", "kemenperin",
        "bpssn", "ojk", "bi ", "bank indonesia", "pdpa", "perlindungan data",
        "tender", "pengadaan", "apbn", "perpres", "pp ", "permen",
        "pemerintah pusat", "kementerian", "lkpp", "bpkp", "bpk",
        "presiden", "menteri", "dirjen", "eselon", "pns", "asn",
        "transformasi digital pemerintah", "spbe", "e-government"
    ]),

    ("media", 5, [
        "media/", "senator-media",
        "berita", "headline", "narasi", "framing", "kompas", "tempo",
        "detik", "cnbc indonesia", "katadata", "techcrunch", "media nasional",
        "wartawan", "jurnalis", "liputan", "pemberitaan", "konten",
        "media sosial", "viral", "trending", "click-through", "media online"
    ]),

    # === KNOWLEDGE DOMAIN ===
    ("upshalter", 10, [
        "upshalter/", "arsify", "pentahelix", "senator", "kurator",
        "arsiparis", "hermes", "skp", "shared_knowledge", "deploy",
        "vps", "production", "infra/", "prd/", "rules/", "automation/"
    ]),

    ("laporan", 7, [
        "laporan/", "brief", "report", "konsolidasi", "ringkasan",
        "summary", "daily-summary", "weekly", "monthly"
    ]),

    ("ai-ml", 6, [
        "machine learning", "deep learning", "neural network", "llm",
        "large language model", "gpt", "claude", "gemini", "mistral",
        "llama", "ai ", "artificial intelligence", "generative ai",
        "prompt engineering", "fine-tuning", "rag ", "vector", "embedding",
        "nlp", "computer vision", "transformers"
    ]),

    ("keamanan", 8, [
        "keamanan", "security", "cve", "vulnerability", "exploit",
        "bug bounty", "penetration test", "pentest", "hacker", "siber",
        "bpssn", "cyber", "enkripsi", "ssl", "certificate", "firewall",
        "zero day", "patch", "security update"
    ]),
]

# ── Tag Rules (bisa multiple tags per entry) ───────────────────────────
TAG_RULES = {
    "ai-relevan":     ["ai", "machine learning", "llm", "generative", "artificial intelligence"],
    "regulasi":       ["regulasi", "peraturan", "kebijakan", "undang-undang", "kominfo", "pdpa"],
    "bisnis-peluang": ["startup", "funding", "investasi", "umkm", "revenue", "market opportunity"],
    "riset":          ["riset", "penelitian", "paper", "jurnal", "publikasi", "akademis"],
    "urgent":         ["alert", "kritis", "segera", "darurat", "regulasi baru", "deadline"],
    "indonesia":      ["indonesia", "jakarta", "bandung", "surabaya", "nusantara", "wib"],
    "teknologi":      ["teknologi", "digital", "software", "platform", "aplikasi", "tech"],
}

# ── Priority Rules ─────────────────────────────────────────────────────
PRIORITY_RULES = {
    "pemerintah": 8,   # Regulasi selalu high priority
    "upshalter": 10,   # System context highest
    "laporan": 7,
    "bisnis": 6,
    "akademisi": 5,
    "media": 4,
    "komunitas": 3,
    "ai-ml": 6,
    "keamanan": 8,
    "general": 2,      # Lowest priority untuk yang tidak terklasifikasi
}


def classify_entry(key: str, value: str) -> tuple[str, list[str], int]:
    """
    Klasifikasi entry berdasarkan key dan value.
    Returns: (category, tags, priority)
    """
    combined = (key + " " + value).lower()

    # Coba setiap rule berurutan (sudah diurutkan berdasarkan prioritas)
    matched_category = "general"
    max_score = 0

    for category, weight, keywords in CATEGORY_RULES:
        score = 0
        for kw in keywords:
            if kw.lower() in combined:
                # Key match lebih penting dari value match
                key_bonus = 3 if kw.lower() in key.lower() else 1
                score += key_bonus

        weighted_score = score * weight
        if weighted_score > max_score:
            max_score = weighted_score
            matched_category = category

    # Tentukan tags
    tags = []
    for tag, keywords in TAG_RULES.items():
        for kw in keywords:
            if kw.lower() in combined:
                tags.append(tag)
                break

    # Deduplicate tags
    tags = list(set(tags))[:5]

    # Priority
    priority = PRIORITY_RULES.get(matched_category, 5)

    return matched_category, tags, priority


def backfill(conn: sqlite3.Connection, dry_run: bool = False) -> dict:
    """
    Backfill categories untuk semua entries.
    Returns stats dict.
    """
    conn.row_factory = sqlite3.Row

    # Ambil semua entries (prioritaskan yang masih "general")
    all_entries = conn.execute("""
        SELECT id, key, value, category, tags
        FROM memory_notes
        ORDER BY
            CASE category WHEN 'general' THEN 0 ELSE 1 END,
            id ASC
    """).fetchall()

    stats = {
        "total": len(all_entries),
        "updated": 0,
        "skipped": 0,
        "by_category": {},
        "was_general": 0,
    }

    updates = []
    for row in all_entries:
        old_category = row["category"] or "general"

        new_category, tags, priority = classify_entry(row["key"], row["value"])

        # Track berapa yang sebelumnya "general"
        if old_category == "general":
            stats["was_general"] += 1

        # Hanya update jika ada perubahan yang meaningful
        if new_category != old_category or not row["tags"] or row["tags"] == "[]":
            updates.append((
                new_category,
                json.dumps(tags),
                priority,
                NOW,
                row["id"]
            ))
            stats["updated"] += 1
        else:
            stats["skipped"] += 1

        stats["by_category"][new_category] = stats["by_category"].get(new_category, 0) + 1

    if not dry_run and updates:
        conn.executemany("""
            UPDATE memory_notes
            SET category = ?, tags = ?, priority = ?, updated_at = ?
            WHERE id = ?
        """, updates)
        conn.commit()

    return stats


def add_missing_columns(conn: sqlite3.Connection):
    """Tambah kolom yang mungkin belum ada."""
    existing = [row[1] for row in conn.execute("PRAGMA table_info(memory_notes)").fetchall()]

    if "category" not in existing:
        conn.execute("ALTER TABLE memory_notes ADD COLUMN category TEXT DEFAULT 'general'")
        print("  Added column: category")

    if "tags" not in existing:
        conn.execute("ALTER TABLE memory_notes ADD COLUMN tags TEXT DEFAULT '[]'")
        print("  Added column: tags")

    if "priority" not in existing:
        conn.execute("ALTER TABLE memory_notes ADD COLUMN priority INTEGER DEFAULT 5")
        print("  Added column: priority")

    conn.commit()


def main():
    print(f"=== SKP CATEGORY BACKFILL v1.0 ===")
    print(f"Database: {DB_PATH}")
    print(f"Mode: {'DRY RUN (no changes)' if DRY_RUN else 'LIVE UPDATE'}")
    print()

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)

    try:
        # Ensure columns exist
        add_missing_columns(conn)

        # Before stats
        before_general = conn.execute(
            "SELECT COUNT(*) FROM memory_notes WHERE category = 'general' OR category IS NULL"
        ).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM memory_notes").fetchone()[0]

        print(f"Before: {before_general}/{total} = {before_general/max(total,1)*100:.1f}% general")
        print()

        # Run backfill
        stats = backfill(conn, dry_run=DRY_RUN)

        # After stats
        if not DRY_RUN:
            after_general = conn.execute(
                "SELECT COUNT(*) FROM memory_notes WHERE category = 'general' OR category IS NULL"
            ).fetchone()[0]
        else:
            after_general = stats["by_category"].get("general", 0)

        print(f"=== RESULTS ===")
        print(f"Total entries:    {stats['total']}")
        print(f"Updated:          {stats['updated']}")
        print(f"Skipped:          {stats['skipped']}")
        print(f"Was general:      {stats['was_general']}")
        print()
        print("Category distribution:")
        for cat, count in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
            pct = count / max(stats['total'], 1) * 100
            bar = "█" * int(pct / 5)
            print(f"  {cat:<20} {count:4d} ({pct:5.1f}%) {bar}")
        print()

        if not DRY_RUN:
            improvement = before_general - after_general
            print(f"After:  {after_general}/{total} = {after_general/max(total,1)*100:.1f}% general")
            print(f"Improvement: -{improvement} general entries ({improvement/max(before_general,1)*100:.0f}% reduction)")
        else:
            print("(DRY RUN — no changes made)")

    finally:
        conn.close()

    print()
    print("=== DONE ===")


if __name__ == "__main__":
    main()
