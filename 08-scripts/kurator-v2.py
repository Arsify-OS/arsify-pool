#!/usr/bin/env python3
"""
kurator-v2.py — Pentahelix Kurator Intelligence Brief Generator
Mei 2026

Reads Senator outputs from SKP, consolidates via Open Router API,
generates intelligence brief, saves to report directory + SKP.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKP_DB = "/data/arsify.db"
SKP_TABLE = "knowledge"
REPORT_DIR = "/root/upshalter-reports"
LOG_DIR = "/root/upshalter-logs"

OPENROUTER_API = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = "INSERT_OPENROUTER_KEY_HERE"
OPENROUTER_MODEL = "openrouter/owl-alpha"

OLLAMA_API = "http://localhost:11434"

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

DATE = datetime.now().strftime("%Y%m%d")
HOUR = datetime.now().strftime("%H")
TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
LOG = f"{LOG_DIR}/kurator-{DATE}.log"
REPORT_FILE = f"{REPORT_DIR}/pentahelix-brief-{DATE}-{HOUR}.md"


def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")


# ── Step 1: Read Senator data from SKP ──────────────────────────────────
log("=== KURATOR v2.1 START ===")
log(f"SKP: {SKP_DB} | Table: {SKP_TABLE}")

conn = sqlite3.connect(SKP_DB)
conn.row_factory = sqlite3.Row

# Read senator entries (both curated and raw, last 12 hours)
rows = conn.execute(f"""
    SELECT key, value, source_agent_name, created_at
    FROM {SKP_TABLE}
    ORDER BY created_at DESC
    LIMIT 20
""").fetchall()

# Filter: only senator entries (not system/curated kurator)
senator_entries = []
for r in rows:
    key = r[0]
    if key.startswith("senator-") and not key.startswith("senator-") is False:
        senator_entries.append({"key": key, "value": r[1][:800], "agent": r[2] or "unknown", "created_at": r[3] or ""})
    elif "temuan" in key or "peluang" in key or "isu" in key or "regulasi" in key or "narasi" in key:
        senator_entries.append({"key": key, "value": r[1][:800], "agent": r[2] or "unknown", "created_at": r[3] or ""})

# Deduplicate by key
seen = set()
unique_entries = []
for e in senator_entries:
    if e["key"] not in seen:
        seen.add(e["key"])
        unique_entries.append(e)

senator_entries = unique_entries[:15]
entry_count = len(senator_entries)
log(f"Found {entry_count} senator entries for consolidation")

# ── Step 2: Calculate confidence ─────────────────────────────────────────
if entry_count == 0:
    confidence = 0.10
elif entry_count < 3:
    confidence = round(entry_count / 10 * 0.5, 2)
elif entry_count < 8:
    confidence = round(entry_count / 10 * 0.8, 2)
else:
    confidence = round(min(entry_count / 10, 1.0) * 0.9, 2)

log(f"Confidence: {confidence} (based on {entry_count} entries)")

# ── Step 3: Build context ───────────────────────────────────────────────
lines = []
for entry in senator_entries[:12]:
    domain = entry.get("key", "").split("/")[0]
    value = entry.get("value", "")[:400]
    lines.append(f"[{domain.upper()}] {value}")

skp_context = "\n---\n".join(lines) if lines else "Belum ada data Senator."

# ── Step 4: Generate report via OpenRouter ───────────────────────────────
log("Generating report...")

SYSTEM = """Kamu adalah Kurator Pentahelix Upshalter. Buat intelligence brief yang tajam, 
faktual, dan actionable dalam Bahasa Indonesia untuk eksekutif bisnis."""

PROMPT = f"""Buat Pentahelix Intelligence Brief berdasarkan data Senator berikut:

=== DATA SENATOR ===
{skp_context}
=== END DATA ===

Tanggal: {TIMESTAMP}
Confidence tersedia: {confidence} (berdasarkan {entry_count} entries)

Format laporan (gunakan PERSIS):

# PENTAHELIX INTELLIGENCE BRIEF
**Tanggal:** {TIMESTAMP}
**Confidence:** {confidence}

## RINGKASAN EKSEKUTIF
[2-3 kalimat paling penting dari seluruh data]

## TEMUAN PER DOMAIN
### AKADEMISI
[2-3 poin spesifik dengan fakta/angka]
### BISNIS
[2-3 poin spesifik]
### KOMUNITAS
[2-3 poin spesifik]
### PEMERINTAH
[2-3 poin spesifik, terutama regulasi]
### MEDIA
[2-3 poin spesifik]

## TEMA LINTAS DOMAIN
[2-3 tema yang muncul di 2+ domain]

## IMPLIKASI UNTUK UPSHALTER
[1-2 poin actionable]

## ALERT
[Kosong jika tidak ada yang kritis]

Jika data minimal/kosong: tulis dengan note confidence rendah tapi tetap buat brief 
menggunakan pengetahuan kontekstual Indonesia terkini."""

try:
    import httpx

    r = httpx.post(
        OPENROUTER_API + "/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": PROMPT},
            ],
            "max_tokens": 3000,
        },
        timeout=90.0,
    )
    r.raise_for_status()
    report_content = r.json()["choices"][0]["message"]["content"]
    log("Report generated via OpenRouter")
except Exception as e:
    log(f"OpenRouter error: {e}")
    report_content = f"""# PENTAHELIX INTELLIGENCE BRIEF
**Tanggal:** {TIMESTAMP}
**Confidence:** 0.05

## ALERT
Kurator gagal generate: {e}

## CATATAN TEKNIS
Model: {OPENROUTER_MODEL} | Entries: {entry_count} | Error: {type(e).__name__}
"""

# ── Step 5: Save report ─────────────────────────────────────────────────
FINAL = f"""<!-- Generated: {TIMESTAMP} | Model: {OPENROUTER_MODEL} | Entries: {entry_count} | Confidence: {confidence} -->
{report_content}
---
*Hermes Kurator Pentahelix v2.1 | {TIMESTAMP} | confidence {confidence}*
"""

with open(REPORT_FILE, "w") as f:
    f.write(FINAL)
log(f"Report saved: {REPORT_FILE}")

# ── Step 6: Save to SKP ─────────────────────────────────────────────────
try:
    conn.execute(
        f"INSERT OR REPLACE INTO {SKP_TABLE} (key, value, source_agent_name, category) VALUES (?,?,?,?)",
        (f"laporan/konsolidasi/{DATE}-{HOUR}", report_content[:4000], "kurator-v2", "laporan"),
    )
    conn.commit()
    log(f"SKP written: laporan/konsolidasi/{DATE}-{HOUR}")
except Exception as e:
    log(f"SKP write error: {e}")

conn.close()

# ── Summary ─────────────────────────────────────────────────────────────
print()
print("=" * 50)
print(f"  KURATOR v2.1 — DONE")
print(f"  Entries: {entry_count} | Confidence: {confidence}")
print(f"  Report: {REPORT_FILE}")
print("=" * 50)
print()
print(report_content[:500])
