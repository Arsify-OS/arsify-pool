#!/usr/bin/env python3
"""
moe-router-senator-patch.py — Tambah Senator routing rules ke Arsify router.py
Versi: 1.0 — Mei 2026

Jalankan: python3 moe-router-senator-patch.py [path_to_router.py]
Default path: /opt/arsify/arsify-os-prototype-final/arsify-app/app/router.py

Apa yang dilakukan:
  1. Baca router.py yang ada
  2. Tambahkan ROUTING_RULES untuk 5 domain Senator + Kurator
  3. Tulis ulang file dengan rules baru
  4. Backup file lama dengan .backup.YYYYMMDD
"""

import os
import sys
import shutil
from datetime import datetime

# ── Cari router.py ─────────────────────────────────────────────────────
POSSIBLE_PATHS = [
    "/opt/arsify/arsify-os-prototype-final/arsify-app/app/router.py",
    "/root/arsify-os-prototype-final/arsify-app/app/router.py",
    "/home/ubuntu/arsify-os-prototype-final/arsify-app/app/router.py",
    "/opt/hermes-cognitive/src/router.py",
]

if len(sys.argv) > 1:
    POSSIBLE_PATHS.insert(0, sys.argv[1])

router_path = None
for p in POSSIBLE_PATHS:
    if os.path.exists(p):
        router_path = p
        break

# ── Senator ROUTING_RULES yang akan ditambahkan ───────────────────────
SENATOR_RULES = '''
    # ══════════════════════════════════════════════════════════════════
    #  SENATOR PENTAHELIX ROUTING RULES
    #  Ditambahkan oleh moe-router-senator-patch.py — Mei 2026
    # ══════════════════════════════════════════════════════════════════

    "senator_akademisi": {
        "model": "qwen2.5:1.5b",  # Model tersedia di production
        "priority": 6,
        "keywords": [
            "akademisi", "riset", "penelitian", "publikasi", "jurnal", "universitas",
            "kampus", "dosen", "mahasiswa", "scopus", "paper", "citation", "dikti",
            "kemdikbud", "brin", "pendidikan tinggi", "inovasi iptek", "lembaga riset",
            "skripsi", "tesis", "disertasi", "vokasi", "politeknik",
        ],
        "role": (
            "Kamu adalah Senator Akademisi dari Upshalter Pentahelix Indonesia. "
            "Spesialisasimu: monitoring riset, publikasi ilmiah, dan inovasi teknologi Indonesia. "
            "Analisa terstruktur, faktual, dengan referensi ke sumber akademis. "
            "Output dalam Bahasa Indonesia, format JSON jika diminta."
        ),
    },

    "senator_bisnis": {
        "model": "qwen2.5:1.5b",
        "priority": 7,
        "keywords": [
            "startup", "funding", "investasi", "venture capital", "unicorn", "umkm",
            "e-commerce", "marketplace", "fintech", "revenue", "profit", "market",
            "ekonomi digital", "gdp", "pertumbuhan bisnis", "ekspor", "saham",
            "bursa", "idx", "perdagangan", "penjualan", "omzet", "bisnis digital",
            "gojek", "tokopedia", "shopee", "traveloka", "bukalapak",
        ],
        "role": (
            "Kamu adalah Senator Bisnis dari Upshalter Pentahelix Indonesia. "
            "Spesialisasimu: market intelligence, startup ecosystem, dan ekonomi digital Indonesia. "
            "Analisa bisnis yang tajam dan actionable untuk eksekutif. "
            "Output dalam Bahasa Indonesia, format JSON jika diminta."
        ),
    },

    "senator_komunitas": {
        "model": "phi3:mini",
        "priority": 5,
        "keywords": [
            "komunitas tech", "developer", "programmer", "github", "open source",
            "hackathon", "meetup", "conference tech", "forum developer", "discord",
            "sentiment komunitas", "opini developer", "indo dev", "coding bootcamp",
            "belajar coding", "workshop tech", "tech indonesia", "komunitas digital",
        ],
        "role": (
            "Kamu adalah Senator Komunitas dari Upshalter Pentahelix Indonesia. "
            "Spesialisasimu: sentiment komunitas tech dan developer Indonesia. "
            "Analisa nuanced tentang opini dan dinamika komunitas. "
            "Output dalam Bahasa Indonesia, format JSON jika diminta."
        ),
    },

    "senator_pemerintah": {
        "model": "qwen2.5:1.5b",
        "priority": 9,  # Highest priority — regulasi paling time-sensitive
        "keywords": [
            "regulasi", "peraturan pemerintah", "kebijakan", "undang-undang",
            "kominfo", "kemenkominfo", "bpssn", "ojk", "bank indonesia",
            "pdpa", "perlindungan data", "tender pemerintah", "pengadaan",
            "apbn", "perpres", "permenkominfo", "kementerian digital",
            "transformasi digital pemerintah", "spbe", "e-government",
            "presiden", "menteri", "dirjen", "kebijakan ai", "regulasi ai",
        ],
        "role": (
            "Kamu adalah Senator Pemerintah dari Upshalter Pentahelix Indonesia. "
            "Spesialisasimu: kebijakan digital, regulasi AI, dan program pemerintah Indonesia. "
            "Analisa regulasi yang presisi dengan implikasi bisnis yang jelas. "
            "Output dalam Bahasa Indonesia, format JSON jika diminta."
        ),
    },

    "senator_media": {
        "model": "phi3:mini",
        "priority": 5,
        "keywords": [
            "narasi media", "framing berita", "kompas", "tempo", "detik",
            "cnbc indonesia", "katadata", "media nasional", "pemberitaan",
            "wartawan", "jurnalis", "liputan media", "viral", "trending news",
            "media sosial", "twitter", "instagram", "tiktok indonesia",
            "opini publik", "sentiment media",
        ],
        "role": (
            "Kamu adalah Senator Media dari Upshalter Pentahelix Indonesia. "
            "Spesialisasimu: analisa narasi dan framing media Indonesia tentang AI dan teknologi. "
            "Analisa media yang kritis dan objektif. "
            "Output dalam Bahasa Indonesia, format JSON jika diminta."
        ),
    },

    "kurator": {
        "model": "qwen2.5:1.5b",
        "priority": 8,
        "keywords": [
            "konsolidasi", "ringkasan semua senator", "kurator", "pentahelix brief",
            "intelligence report", "laporan harian", "daily brief", "weekly brief",
            "analisa lintas domain", "tema bersama", "cross-domain",
        ],
        "role": (
            "Kamu adalah Kurator Pentahelix dari Upshalter Indonesia. "
            "Tugasmu: konsolidasi temuan 5 Senator menjadi intelligence brief yang actionable. "
            "Identifikasi tema lintas domain dan implikasi strategis untuk bisnis Indonesia. "
            "Output dalam Bahasa Indonesia dengan format markdown terstruktur."
        ),
    },
'''

# ── Standalone router.py jika tidak ada file asli ─────────────────────
STANDALONE_ROUTER = '''"""
Arsify MoE Router v3.1 — Senator Edition
Versi: 3.1 — Mei 2026
Standalone version dengan Senator domain routing.
"""

import httpx, uuid, json
from typing import AsyncGenerator, Optional
from collections import defaultdict

# Konfigurasi
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
TEMPERATURE = float(os.getenv("ARSIFY_TEMP", "0.3"))
MAX_TOKENS = int(os.getenv("ARSIFY_MAX_TOKENS", "2048"))
MAX_HISTORY = int(os.getenv("ARSIFY_MAX_HISTORY", "10"))

ROUTING_RULES: dict[str, dict] = {
    "code": {
        "model": "qwen2.5:1.5b", "priority": 3,
        "keywords": [
            "code", "kode", "program", "function", "fungsi", "script", "bug", "error", "debug",
            "python", "javascript", "typescript", "bash", "html", "css", "sql", "api", "database",
            "git", "compile", "syntax", "variable", "loop", "array", "class", "import", "library",
            "framework", "algorithm", "algoritma", "pip", "npm", "docker", "dockerfile", "json",
            "xml", "yaml", "regex", "async", "thread", "refactor", "unit test",
        ],
        "role": "Kamu adalah Arsify Coder dari Arsify OS. Tulis kode bersih, efisien. Sertakan contoh kode langsung bisa dijalankan.",
    },
    "system": {
        "model": "phi3:mini", "priority": 2,
        "keywords": [
            "os", "operating system", "linux", "ubuntu", "systemd", "service",
            "daemon", "process", "cpu", "memory", "ram", "disk", "storage", "network", "firewall",
            "nginx", "apache", "ssh", "server", "vps", "deploy", "terminal", "command", "shell",
            "permission", "chmod", "cron", "log", "monitor", "performance", "security", "ssl",
        ],
        "role": "Kamu adalah Arsify System dari Arsify OS. Berikan jawaban teknis akurat beserta perintah yang langsung bisa dijalankan.",
    },
    "general": {
        "model": "qwen2.5:1.5b", "priority": 0,
        "keywords": [],
        "role": "Kamu adalah Arsify, AI asisten cerdas dari Arsify OS Indonesia. Jawab dengan ramah, informatif, dan helpful dalam bahasa yang sama dengan pengguna.",
    },
    ''' + SENATOR_RULES + '''
}


class ArsifyRouter:
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.conversations: dict[str, list] = defaultdict(list)
        self.stats = {
            "total_requests": 0,
            "by_model": defaultdict(int),
            "by_category": defaultdict(int),
        }

    def classify(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        scores: dict[str, float] = {}
        for cat, cfg in ROUTING_RULES.items():
            if not cfg["keywords"]:
                continue
            hits = sum(1 for kw in cfg["keywords"] if kw in prompt_lower)
            if hits > 0:
                scores[cat] = hits * cfg["priority"]
        return max(scores, key=lambda k: scores[k]) if scores else "general"

    def _build_messages(self, prompt: str, category: str, conv_id: str, memory_context: str = "") -> list:
        role = ROUTING_RULES[category]["role"]
        system_content = role
        if memory_context:
            system_content += f"\\n\\n{memory_context}"
        history = self.conversations[conv_id][-(MAX_HISTORY * 2):]
        return [
            {"role": "system", "content": system_content},
            *history,
            {"role": "user", "content": prompt},
        ]

    async def route(self, prompt: str, conversation_id: Optional[str] = None, memory_context: str = "") -> dict:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        category = self.classify(prompt)
        model = ROUTING_RULES[category]["model"]
        messages = self._build_messages(prompt, category, conversation_id, memory_context)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self.ollama_url}/api/chat", json={
                "model": model, "messages": messages, "stream": False,
                "options": {"temperature": TEMPERATURE, "num_predict": MAX_TOKENS, "top_p": 0.9},
            })
            resp.raise_for_status()
            data = resp.json()

        response_text = data["message"]["content"]
        tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)

        self.conversations[conversation_id].append({"role": "user", "content": prompt})
        self.conversations[conversation_id].append({"role": "assistant", "content": response_text})
        self.stats["total_requests"] += 1
        self.stats["by_model"][model] += 1
        self.stats["by_category"][category] += 1

        return {
            "response": response_text, "model": model, "category": category,
            "tokens": tokens, "conversation_id": conversation_id
        }

    def get_stats(self) -> dict:
        return {
            "total_requests": self.stats["total_requests"],
            "by_model": dict(self.stats["by_model"]),
            "by_category": dict(self.stats["by_category"]),
            "active_conversations": len(self.conversations),
            "senator_rules_loaded": len([k for k in ROUTING_RULES if k.startswith("senator_")]),
        }

    async def check_ollama(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as c:
                return (await c.get(f"{self.ollama_url}/api/tags")).status_code == 200
        except Exception:
            return False
'''


def patch_existing_router(path: str) -> bool:
    """Patch router.py yang ada dengan Senator rules."""
    print(f"Patching existing router: {path}")

    # Backup
    backup = f"{path}.backup.{datetime.now().strftime('%Y%m%d-%H%M')}"
    shutil.copy2(path, backup)
    print(f"  Backup created: {backup}")

    with open(path) as f:
        content = f.read()

    # Cari posisi insert (sebelum "general" rule, atau sebelum penutup ROUTING_RULES)
    insert_markers = [
        '    "general": {',
        '"general":{',
        "# end of routing rules",
        "}\n\n\nclass ArsifyRouter",
    ]

    inserted = False
    for marker in insert_markers:
        if marker in content:
            content = content.replace(marker, SENATOR_RULES + "\n    " + marker.lstrip(), 1)
            inserted = True
            print(f"  Senator rules inserted before: '{marker[:40]}...'")
            break

    if not inserted:
        # Append di akhir ROUTING_RULES
        content = content.replace(
            "ROUTING_RULES: dict[str, dict] = {",
            "ROUTING_RULES: dict[str, dict] = {" + SENATOR_RULES
        )
        print("  Senator rules appended to ROUTING_RULES")

    with open(path, "w") as f:
        f.write(content)

    print(f"  router.py updated successfully")
    return True


def create_standalone_router(output_path: str) -> bool:
    """Buat standalone router-senator.py jika tidak ada router.py asli."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(STANDALONE_ROUTER)
    print(f"Standalone router created: {output_path}")
    return True


def main():
    print("=== ARSIFY MoE SENATOR ROUTING PATCH v1.0 ===")
    print()

    if router_path:
        success = patch_existing_router(router_path)
    else:
        print("Original router.py not found. Creating standalone senator router...")
        output = "/opt/arsify/router-senator.py"
        success = create_standalone_router(output)
        print(f"\nTo use: import ArsifyRouter from '{output}'")

    if success:
        print()
        print("SUCCESS. Senator routing rules are ready:")
        print("  senator_akademisi → qwen2.5:1.5b (priority 6)")
        print("  senator_bisnis    → qwen2.5:1.5b (priority 7)")
        print("  senator_komunitas → phi3:mini    (priority 5)")
        print("  senator_pemerintah→ qwen2.5:1.5b (priority 9 — highest)")
        print("  senator_media     → phi3:mini    (priority 5)")
        print("  kurator           → qwen2.5:1.5b (priority 8)")
        print()
        print("Test: python3 -c \"from router import ROUTING_RULES; print(list(ROUTING_RULES.keys()))\"")


if __name__ == "__main__":
    main()
