---
name: skp-external-knowledge-ingestion
description: Example workflow for ingesting Romi Satria Wahono thesis list into Shared Knowledge Pool
---

# External Knowledge Ingestion Example: Romi Wahono Thesis Dataset

## Context
83 thesis entries from Romi Satria Wahono's research, structured into SKP for all Hermes agents to access. Used in 2026-05-07 session.

## Raw Data Fields
| Field | Description |
|-------|-------------|
| No | Entry ID (1-83) |
| Kategori | Main category (Software Engineering, Data Mining, Intelligent Systems) |
| Judul | Thesis title |
| Penulis | Author |
| Pembimbing | Supervisor |
| Gelar | Degree (Magister/Doctor) |
| Prodi | Program |
| Universitas | University |
| Tahun | Year |

## Step 1: Create Structured Storage
```bash
mkdir -p /root/.hermes/knowledge/
```

## Step 2: Parse to Structured Formats
```python
import json, csv, sqlite3

# Parsed raw data (83 entries)
theses = [
    {"No": 1, "Kategori": "Software Engineering", "Judul": "Pengembangan Sistem Informasi Koperasi ...", ...},
    # ... 82 more entries
]

structured = []
for t in theses:
    structured.append({
        "id": t["No"],
        "main_category": t["Kategori"],
        "sub_category": "",
        "title": t["Judul"],
        "author": t["Penulis"],
        "supervisor": t["Pembimbing"],
        "degree": t["Gelar"],
        "program": t["Prodi"],
        "university": t["Universitas"],
        "year": int(t["Tahun"]),
        "keywords": [],
        "source": "Romi Satria Wahono Thesis Dataset"
    })

# Write JSON
with open("/root/.hermes/knowledge/romi-wahono-theses.json", "w") as f:
    json.dump(structured, f, indent=2, ensure_ascii=False)

# Write CSV
with open("/root/.hermes/knowledge/romi-wahono-theses.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=structured[0].keys())
    writer.writeheader()
    writer.writerows(structured)
```

## Step 3: Insert into SKP DB
```bash
# Create table
sqlite3 /root/.hermes/shared_knowledge_pool.db << 'SQL'
CREATE TABLE IF NOT EXISTS romi_theses (
    id INTEGER PRIMARY KEY,
    main_category TEXT,
    sub_category TEXT,
    title TEXT NOT NULL,
    author TEXT,
    supervisor TEXT,
    degree TEXT,
    program TEXT,
    university TEXT,
    year INTEGER,
    keywords TEXT,  # JSON array stored as text
    source TEXT
);
SQL

# Insert data (via Python script above)
# Use INSERT OR IGNORE to avoid duplicates on re-run
```

## Step 4: Update Memory
```python
# Use memory tool to add entry:
# action=add, target=memory, content="Romi Satria Wahono Thesis Dataset: 83 entries (Software Engineering/Data Mining/Intelligent Systems), structured JSON/CSV in /root/.hermes/knowledge/, table romi_theses in SKP DB"
```

## Verification
```bash
# Check files
ls -la /root/.hermes/knowledge/romi-wahono-theses.*

# Check DB
sqlite3 /root/.hermes/shared_knowledge_pool.db "SELECT COUNT(*) FROM romi_theses;"
sqlite3 /root/.hermes/shared_knowledge_pool.db "SELECT id, title, year FROM romi_theses LIMIT 3;"
```

## Pitfalls
1. **Directory creation**: Always `mkdir -p /root/.hermes/knowledge/` before writing files
2. **Duplicate inserts**: Use `INSERT OR IGNORE` for idempotent runs
3. **JSON storage**: Store keywords as JSON string in SQLite text field for easy parsing
4. **Encoding**: Use `ensure_ascii=False` when writing JSON to preserve Indonesian characters
