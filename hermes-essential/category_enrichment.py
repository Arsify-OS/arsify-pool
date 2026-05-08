"""
core/category_enrichment.py
────────────────────────────────────────────────────────────────────────────────
SKP Category Enrichment — Auto-categorization engine untuk knowledge entries.

Masalah yang dipecahkan:
  - 124/164 entries = "general" (75.6%) — terlalu dominan
  - Hanya 5/164 entries punya tags — hampir tidak terpakai
  - Tidak ada domain-specific categorization

Solusi:
  - Keyword-based classification dengan domain mapping per agent
  - Content analysis untuk entries yang tidak match keyword
  - Backfill existing "general" entries dengan category yang lebih spesifik
  - Auto-tag generation berdasarkan content

Fase: 4 — Enhancement & Optimization
"""

import json
import logging
import os
import re
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("SKP_DB_PATH", "/data/shared_knowledge_pool.db")

# ── Domain Category Mapping ────────────────────────────────────────────────────
# Setiap agent punya domain keywords yang map ke category spesifik

AGENT_DOMAIN_CATEGORIES = {
    "senator-akademisi": {
        "primary": "research",
        "keywords": {
            "research": [
                "penelitian", "riset", "jurnal", "publikasi", "paper",
                "study", "research", "journal", "publication", "thesis",
                "dissertation", "skripsi", "akademik", "academic", "ilmiah",
                "scientific", "literature review", "metodologi", "methodology",
                "hypothesis", "hipotesis", "experiment", "eksperimen",
                "data analysis", "analisis data", "survey", "questionnaire",
                "kuesioner", "interview", "wawancara", "observation",
                "observasi", "case study", "studi kasus", "qualitative",
                "kuantitatif", "quantitative", "mixed method",
            ],
            "education": [
                "pendidikan", "education", "universitas", "university",
                "fakultas", "faculty", "dosen", "lecturer", "mahasiswa",
                "student", "curriculum", "kurikulum", "pengajaran", "teaching",
                "pembelajaran", "learning", "e-learning", "mooc",
                "academic", "akademik", "scholarship", "beasiswa",
                "campus", "kampus", "sekolah", "school",
            ],
            "ai-ml": [
                "artificial intelligence", "kecerdasan buatan", "machine learning",
                "deep learning", "neural network", "transformer", "llm",
                "large language model", "nlp", "natural language processing",
                "computer vision", "reinforcement learning", "supervised",
                "unsupervised", "classification", "klasifikasi", "clustering",
                "regression", "regresi", "algorithm", "algoritma",
                "model training", "fine-tuning", "embedding", "vector",
                "dataset", "training data", "inference", "deployment",
            ],
        },
    },
    "senator-bisnis": {
        "primary": "business",
        "keywords": {
            "business": [
                "bisnis", "business", "usaha", "company", "perusahaan",
                "startup", "enterprise", "corporate", "korporasi",
                "revenue", "pendapatan", "profit", "laba", "roi",
                "investment", "investasi", "funding", "pendanaan",
                "market", "pasar", "market share", "pangsa pasar",
                "growth", "pertumbuhan", "scaling", "scale-up",
                "strategy", "strategi", "business model", "model bisnis",
                "competition", "kompetisi", "competitive advantage",
                "customer", "pelanggan", "client", "klien",
                "sales", "penjualan", "marketing", "pemasaran",
            ],
            "finance": [
                "finance", "keuangan", "financial", "keuangan",
                "accounting", "akuntansi", "budget", "anggaran",
                "cash flow", "arus kas", "balance sheet", "neraca",
                "income statement", "laba rugi", "tax", "pajak",
                "audit", "auditing", "compliance", "kepatuhan",
                "banking", "perbankan", "fintech", "insurtech",
                "cryptocurrency", "crypto", "blockchain",
                "stock", "saham", "bond", "obligasi", "mutual fund",
            ],
            "entrepreneurship": [
                "entrepreneur", "wirausaha", "entrepreneurship", "kewirausahaan",
                "founder", "co-founder", "ceo", "cto", "coo",
                "pitch deck", "elevator pitch", "business plan",
                "lean startup", "minimum viable product", "mvp",
                "product-market fit", "pmf", "go-to-market", "gtm",
                "venture capital", "vc", "angel investor", "seed funding",
                "series a", "series b", "ipo", "exit strategy",
                "bootstrapping", "accelerator", "incubator",
            ],
        },
    },
    "senator-pemerintah": {
        "primary": "policy",
        "keywords": {
            "policy": [
                "kebijakan", "policy", "regulation", "regulasi",
                "undang-undang", "law", "uu", "peraturan", "perpres",
                "presidential regulation", "pp", "permen", "ministerial",
                "government", "pemerintah", "public policy", "kebijakan publik",
                "governance", "tata kelola", "bureaucracy", "birokrasi",
                "reform", "reformasi", "public service", "pelayanan publik",
                "civil service", "pegawai negeri", "asn",
                "decentralization", "desentralisasi", "otonomi daerah",
                "local government", "pemda", "provinsi", "kabupaten", "kota",
            ],
            "compliance": [
                "compliance", "kepatuhan", "regulatory", "regulasi",
                "pdpa", "personal data protection", "perlindungan data",
                "gdpr", "data privacy", "privasi data", "cybersecurity",
                "keamanan siber", "iso", "certification", "sertifikasi",
                "standard", "standar", "audit", "inspection", "pemeriksaan",
                "enforcement", "penegakan", "sanction", "sanksi",
                "license", "izin", "permit", "perizinan",
                "nib", "oss", "online single submission",
            ],
            "digital-gov": [
                "e-government", "e-gov", "digital government",
                "smart city", "kota cerdas", "digital transformation",
                "transformasi digital", "digitalisasi", "digitization",
                "open data", "data terbuka", "open government",
                "egov", "spbe", "sistem pemerintahan berbasis elektronik",
                "national data center", "pusat data nasional",
                "cloud computing", "komputasi awan", "data center",
                "interoperability", "interoperabilitas", "integration",
                "integrasi", "one data", "satu data",
            ],
        },
    },
    "senator-komunitas": {
        "primary": "community",
        "keywords": {
            "community": [
                "komunitas", "community", "developer community",
                "komunitas developer", "user group", "kelompok pengguna",
                "forum", "discussion", "diskusi", "collaboration",
                "kolaborasi", "open source", "open-source", "oss",
                "contributor", "kontributor", "maintainer",
                "hackathon", "hackfest", "meetup", "gathering",
                "workshop", "seminar", "webinar", "conference", "konferensi",
                "networking", "jaringan", "ecosystem", "ekosistem",
                "grassroots", "akar rumput", "volunteer", "sukarelawan",
            ],
            "sentiment": [
                "sentiment", "sentimen", "opinion", "pendapat",
                "perception", "persepsi", "feedback", "umpan balik",
                "review", "ulasan", "rating", "penilaian",
                "satisfaction", "kepuasan", "trust", "kepercayaan",
                "engagement", "keterlibatan", "participation", "partisipasi",
                "adoption", "adopsi", "awareness", "kesadaran",
                "trending", "viral", "buzz", "hype", "controversy",
                "kontroversi", "debate", "debat", "polarization",
            ],
            "social-impact": [
                "social impact", "dampak sosial", "social responsibility",
                "csr", "corporate social responsibility", "sustainability",
                "kelestarian", "environment", "lingkungan", "climate change",
                "perubahan iklim", "renewable energy", "energi terbarukan",
                "social enterprise", "usaha sosial", "ngo", "non-profit",
                "nonprofit", "charity", "amal", "donation", "donasi",
                "education", "pendidikan", "digital literacy", "literasi digital",
            ],
        },
    },
    "senator-media": {
        "primary": "media",
        "keywords": {
            "media": [
                "media", "pers", "press", "journalism", "jurnalisme",
                "news", "berita", "article", "artikel", "report", "laporan",
                "broadcast", "siaran", "televisi", "television", "radio",
                "podcast", "youtube", "social media", "media sosial",
                "twitter", "instagram", "tiktok", "facebook", "linkedin",
                "content", "konten", "content creation", "pembuatan konten",
                "editorial", "redaksi", "opinion", "opini", "column", "kolom",
            ],
            "narrative": [
                "narrative", "narasi", "framing", "pembingkaian",
                "storytelling", "penceritaan", "story", "cerita",
                "message", "pesan", "messaging", "pesan kunci",
                "key message", "talkpoint", "soundbite", "headline",
                "judul berita", "clickbait", "viral", "trending",
                "agenda setting", "priming", "gatekeeping",
                "media bias", "bias media", "propaganda", "hoax",
                "misinformation", "disinformation", "fake news",
            ],
            "pr-communication": [
                "public relations", "pr", "hubungan masyarakat",
                "communications", "komunikasi", "corporate communication",
                "crisis communication", "komunikasi krisis",
                "reputation", "reputasi", "brand", "merek", "branding",
                "campaign", "kampanye", "advertising", "iklan",
                "press release", "siaran pers", "media kit",
                "influencer", "key opinion leader", "kol",
                "media relations", "hubungan media", "spokesperson",
                "juru bicara", "public speaking", "pidato",
            ],
        },
    },
    "kurator": {
        "primary": "curated",
        "keywords": {
            "curated": [
                "kurasi", "curated", "curation", "kurator",
                "analysis", "analisis", "synthesis", "sintesis",
                "summary", "ringkasan", "insight", "wawasan",
                "trend", "tren", "pattern", "pola",
                "recommendation", "rekomendasi", "actionable",
                "conclusion", "kesimpulan", "finding", "temuan",
            ],
        },
    },
    "system": {
        "primary": "system",
        "keywords": {
            "system": [
                "system", "sistem", "infrastructure", "infrastruktur",
                "configuration", "konfigurasi", "deployment", "deploy",
                "monitoring", "monitoring", "logging", "log",
                "performance", "kinerja", "optimization", "optimasi",
            ],
        },
    },
}

# ── Global keyword-to-category mapping (agent-agnostic) ────────────────────────
# Digunakan sebagai fallback ketika agent tidak dikenal

GLOBAL_KEYWORDS = {
    "ai-ml": [
        "artificial intelligence", "machine learning", "deep learning",
        "neural network", "transformer", "llm", "gpt", "bert",
        "kecerdasan buatan", "pembelajaran mesin", "jaringan saraf",
    ],
    "research": [
        "penelitian", "riset", "jurnal", "publikasi", "paper",
        "research", "study", "journal", "publication",
    ],
    "business": [
        "bisnis", "business", "startup", "usaha", "perusahaan",
        "market", "pasar", "revenue", "pendapatan", "investasi",
    ],
    "policy": [
        "kebijakan", "policy", "regulation", "regulasi", "undang-undang",
        "pemerintah", "government", "compliance", "kepatuhan",
    ],
    "community": [
        "komunitas", "community", "developer", "open source",
        "collaboration", "kolaborasi", "sentiment", "sentimen",
    ],
    "media": [
        "media", "berita", "news", "jurnalisme", "journalism",
        "narrative", "narasi", "framing", "pr", "public relations",
    ],
    "devops": [
        "docker", "kubernetes", "k8s", "ci/cd", "deployment",
        "container", "orchestration", "pipeline", "infrastructure",
        "nginx", "redis", "celery", "monitoring", "logging",
    ],
    "backend": [
        "api", "rest", "graphql", "database", "sql", "sqlite",
        "server", "backend", "endpoint", "microservice",
        "fastapi", "flask", "django", "express",
    ],
    "frontend": [
        "frontend", "ui", "ux", "user interface", "user experience",
        "react", "vue", "angular", "html", "css", "javascript",
        "dashboard", "visualization", "chart",
    ],
    "security": [
        "security", "keamanan", "authentication", "authorization",
        "encryption", "vulnerability", "exploit", "firewall",
        "cybersecurity", "keamanan siber", "privacy", "privasi",
    ],
}


def _get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def classify_content(text: str, agent_id: str = "unknown") -> tuple[str, list[str], float]:
    """
    Classify content into category + tags based on keyword matching.

    Returns:
        (category, tags, confidence)
        - category: primary category string
        - tags: list of matched tag strings
        - confidence: 0.0-1.0 match confidence
    """
    if not text:
        return "general", [], 0.0

    text_lower = text.lower()
    scores: dict[str, float] = {}
    matched_tags: list[str] = []

    # 1. Try agent-specific domain categories first
    agent_config = AGENT_DOMAIN_CATEGORIES.get(agent_id)
    if agent_config:
        for category, keywords in agent_config["keywords"].items():
            cat_score = 0.0
            for kw in keywords:
                count = text_lower.count(kw.lower())
                if count > 0:
                    # Longer keywords get higher weight (more specific)
                    weight = 1.0 + (len(kw.split()) - 1) * 0.5
                    cat_score += count * weight
                    matched_tags.append(kw)
            if cat_score > 0:
                scores[category] = cat_score

    # 2. Also try global keywords as supplement
    for category, keywords in GLOBAL_KEYWORDS.items():
        cat_score = scores.get(category, 0.0)
        for kw in keywords:
            count = text_lower.count(kw.lower())
            if count > 0:
                weight = 1.0 + (len(kw.split()) - 1) * 0.5
                cat_score += count * weight * 0.5  # Global gets lower weight
                if kw not in matched_tags:
                    matched_tags.append(kw)
        if cat_score > 0:
            scores[category] = cat_score

    # 3. Determine best category
    if scores:
        best_cat = max(scores, key=scores.get)
        best_score = scores[best_cat]
        total_score = sum(scores.values())
        confidence = min(best_score / max(total_score, 1.0), 1.0)

        # If agent has primary category and it's close to best, prefer primary
        if agent_config:
            primary = agent_config.get("primary")
            if primary in scores and scores[primary] >= best_score * 0.7:
                best_cat = primary

        # Deduplicate and limit tags
        seen = set()
        unique_tags = []
        for t in matched_tags:
            tl = t.lower()
            if tl not in seen:
                seen.add(tl)
                unique_tags.append(t)
                if len(unique_tags) >= 8:
                    break

        return best_cat, unique_tags, round(confidence, 2)

    # 4. Fallback: use agent's primary category with low confidence
    if agent_config:
        return agent_config["primary"], [], 0.1

    return "general", [], 0.0


def enrich_entry(key: str, value: str, agent_id: str) -> dict | None:
    """
    Enrich a single SKP entry with better category and tags.

    Returns dict with enrichment result, or None if no change needed.
    """
    category, tags, confidence = classify_content(value, agent_id)

    # Only enrich if we got something better than "general" with decent confidence
    if category == "general" and confidence < 0.3:
        return None

    return {
        "key": key,
        "category": category,
        "tags": json.dumps(tags, ensure_ascii=False) if tags else "[]",
        "confidence": confidence,
    }


def backfill_general_entries(dry_run: bool = False) -> dict:
    """
    Backfill all "general" entries with better categories.

    Args:
        dry_run: If True, only report what would change without writing.

    Returns:
        Stats dict with counts of changes per category.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()

        # Get all "general" entries (excluding system/kurator/curated)
        cur.execute("""
            SELECT key, value, category, tags, source_agent_name
            FROM   knowledge
            WHERE  category = 'general'
              AND  key NOT LIKE 'system:%'
              AND  key NOT LIKE 'kurator:%'
              AND  key NOT LIKE 'curated:%'
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()

        changes: dict[str, int] = {}
        enriched = 0
        skipped = 0
        updates = []

        for row in rows:
            key = row["key"]
            value = row["value"] or ""
            agent_id = row["source_agent_name"] or "unknown"

            # Combine key + value for classification
            text = f"{key}\n{value}"
            result = enrich_entry(key, text, agent_id)

            if result and result["category"] != "general":
                new_cat = result["category"]
                changes[new_cat] = changes.get(new_cat, 0) + 1
                enriched += 1
                updates.append(result)
            else:
                skipped += 1

        # Apply updates
        if not dry_run:
            for u in updates:
                cur.execute("""
                    UPDATE knowledge
                    SET    category = ?, tags = ?, updated_at = ?
                    WHERE  key = ?
                """, (u["category"], u["tags"], datetime.utcnow().isoformat(), u["key"]))

                # Also update FTS index
                try:
                    cur.execute("""
                        UPDATE knowledge_fts
                        SET    category = ?
                        WHERE  rowid = (SELECT rowid FROM knowledge WHERE key = ?)
                    """, (u["category"], u["key"]))
                except Exception:
                    pass  # FTS update is best-effort

            conn.commit()

        conn.close()

        return {
            "status": "ok",
            "total_general": len(rows),
            "enriched": enriched,
            "skipped": skipped,
            "changes": changes,
            "dry_run": dry_run,
        }

    except Exception as exc:
        logger.error("category_enrichment: backfill failed: %s", exc)
        return {"status": "error", "error": str(exc)}


def enrich_new_entry(key: str, value: str, agent_id: str) -> tuple[str, str]:
    """
    Enrich a new entry before writing to SKP.
    Called from knowledge_injector.py write path.

    Returns (category, tags_json)
    """
    text = f"{key}\n{value}"
    category, tags, confidence = classify_content(text, agent_id)

    tags_json = json.dumps(tags, ensure_ascii=False) if tags else "[]"

    logger.debug(
        "category_enrichment: key=%s agent=%s → category=%s tags=%d conf=%.2f",
        key[:40], agent_id, category, len(tags), confidence,
    )

    return category, tags_json


def get_enrichment_stats() -> dict:
    """Get current category distribution stats."""
    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT category, COUNT(*) as cnt
            FROM   knowledge
            GROUP BY category
            ORDER BY cnt DESC
        """)
        categories = {row["category"]: row["cnt"] for row in cur.fetchall()}

        cur.execute("SELECT COUNT(*) FROM knowledge WHERE tags IS NOT NULL AND tags != '[]' AND tags != ''")
        tagged = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM knowledge")
        total = cur.fetchone()[0]

        conn.close()

        return {
            "total": total,
            "categories": categories,
            "tagged": tagged,
            "untagged": total - tagged,
        }
    except Exception as exc:
        return {"error": str(exc)}
