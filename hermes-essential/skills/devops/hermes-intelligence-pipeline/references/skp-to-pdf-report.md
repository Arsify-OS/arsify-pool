# SKP-to-PDF Report Generation

**Created**: 8 Mei 2026  
**Context**: Generate formatted PDF intelligence briefs from SKP senator output

## Workflow

```
SKP Database → Query Best Entry → Extract JSON → fpdf2 → PDF Report
```

## Step 1: Query SKP for Best Senator Output

```bash
# List komunitas entries, newest first
sqlite3 /data/arsify.db "SELECT id, key, category, source_agent_name, created_at, LENGTH(value) as val_len FROM knowledge WHERE category='komunitas' ORDER BY created_at DESC LIMIT 15"

# Pick the entry with largest content (highest val_len) and most recent created_at
# Best entry pattern: senator-komunitas/isu/YYYYMMDD-HH (largest, most recent)

# Extract full content
sqlite3 /data/arsify.db "SELECT value FROM knowledge WHERE key='senator-komunitas/isu/20260508-06'"
```

**Selection criteria**: Largest `LENGTH(value)` with `category='komunitas'`, ordered by `created_at DESC`. The `isu/` prefix entries are the richest (2000+ chars vs 300-500 for `planning/` or `analysis/`).

## Step 2: Generate PDF with fpdf2

### Installation

```bash
pip3 install fpdf2 --break-system-packages
```

### Font Setup (CRITICAL)

DejaVu fonts at `/usr/share/fonts/truetype/dejavu/`:

```python
FONT_PATH = "/usr/share/fonts/truetype/dejavu/"

pdf.add_font("DejaVu", "", FONT_PATH + "DejaVuSans.ttf")
pdf.add_font("DejaVu", "B", FONT_PATH + "DejaVuSans-Bold.ttf")
pdf.add_font("DejaVu", "I", FONT_PATH + "DejaVuSans.ttf")       # NO DejaVuSans-Oblique.ttf!
pdf.add_font("DejaVu", "BI", FONT_PATH + "DejaVuSans-Bold.ttf")  # NO DejaVuSans-BoldOblique.ttf!
```

**PITFALL**: `DejaVuSans-Oblique.ttf` and `DejaVuSans-BoldOblique.ttf` do NOT exist on this system. Using them causes `FileNotFoundError`. Map italic to regular and bold-oblique to bold as fallback.

Verify available fonts:
```bash
ls /usr/share/fonts/truetype/dejavu/DejaVuSans*
```

### PDF Layout Pattern (Single Page A4)

```python
from fpdf import FPDF, XPos, YPos

class BriefPDF(FPDF):
    def footer(self):
        self.set_y(-10)
        self.set_font("DejaVu", "I", 6)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, f"Pentahelix Editorial Pipeline | Senator-Komunitas v3 | SKP Knowledge Pool | Page {self.page_no()}/1", align="C")

pdf = BriefPDF()
pdf.set_auto_page_break(auto=False, margin=12)  # auto=False for single-page control
pdf.add_page()
pdf.add_font("DejaVu", "", FONT_PATH + "DejaVuSans.ttf")
pdf.add_font("DejaVu", "B", FONT_PATH + "DejaVuSans-Bold.ttf")
pdf.add_font("DejaVu", "I", FONT_PATH + "DejaVuSans.ttf")
pdf.add_font("DejaVu", "BI", FONT_PATH + "DejaVuSans-Bold.ttf")

# Header banner (dark)
pdf.set_fill_color(15, 23, 42)
pdf.rect(0, 0, 210, 33, "F")
pdf.set_fill_color(59, 130, 246)
pdf.rect(0, 33, 210, 1.5, "F")  # blue accent line

# Sentiment bar (colored rectangles)
# Issues with colored left border
# Footer disclaimer
```

### Color Scheme

| Element | RGB | Usage |
|---------|-----|-------|
| Header bg | (15, 23, 42) | Dark navy banner |
| Accent | (59, 130, 246) | Blue accent line |
| Negatif | (220, 38, 38) | Red dot/badge |
| Positif | (22, 163, 74) | Green dot/badge |
| Netral | (234, 179, 8) | Yellow dot/badge |
| Text primary | (15, 23, 42) | Dark text |
| Text secondary | (51, 65, 85) | Body text |
| Text muted | (100, 116, 139) | Captions |
| Divider | (226, 232, 240) | Separator lines |

### Space Budget (Single A4 Page)

| Section | Y Start | Height |
|---------|---------|--------|
| Header banner | 0 | 34.5mm |
| Sentiment overview | 39 | 5mm |
| Sentiment bar | 46 | 5mm |
| Divider | 53 | 1mm |
| Issues (x5) | 57 | ~43mm each |
| Footer disclaimer | ~270 | 5mm |

**Total**: 297mm (A4 height) - 12mm margin = 285mm usable. Budget ~43mm per issue for 5 issues + header + footer.

### HTML Entity Decoding

SKP values may contain HTML entities (`&lt;`, `&gt;`, `&amp;`). Always decode:

```python
import html
isu["deskripsi"] = html.unescape(isu["deskripsi"])
```

## Step 3: Verify Output

```bash
file /root/upshalter-reports/sample-brief-DEMO.pdf
# Should show: PDF document, version 1.3, 1 page(s)

ls -la /root/upshalter-reports/sample-brief-DEMO.pdf
# Check file size (expect ~40-50KB)
```

**PITFALL**: `execute_code` sandbox Python is DIFFERENT from system `python3`. Packages installed via system pip (fpdf2, pymupdf) may not be visible in sandbox. Always use `terminal` command to run Python scripts that need system packages.

```bash
# CORRECT: Run via terminal
python3 /tmp/gen_brief_v3.py

# WRONG: execute_code may not see system-installed packages
```

## Output Path Convention

```
/root/upshalter-reports/sample-brief-DEMO.pdf   # Demo/sample briefs
/root/upshalter-reports/pentahelix-brief-*.md   # Production markdown briefs
```

## SKP Data Structure (Senator Komunitas Output)

```json
{
  "sentiment_overall": "negatif",
  "tanggal": "2026-05-08",
  "isu": [
    {
      "judul": "...",
      "sentiment": "negatif|positif|netral",
      "deskripsi": "...",
      "tokoh_kunci": ["Name (role)", "Name (role)"]
    }
  ]
}
```

## Complete Generator Script

See `/tmp/gen_brief_v3.py` for the full working template. Key features:
- Dark header with blue accent line
- Sentiment overview with colored bar
- 5 issues with colored left border, title, description, key figures, sentiment badge
- Footer disclaimer
- Single page A4 output
