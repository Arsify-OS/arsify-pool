# NotebookLM Integration for Kurator Reports
Topic: https://github.com/topics/notebooklm

## What is NotebookLM?
Google's tool to transform documents/sources (berita, paper, SKP entries) into interactive notebooks with structured summaries, Q&A, and insights. Ideal for Kurator Pentahelix workflow in PRD-002.

## Workflow for Kurator Reports
### 1. Collect SKP Entries
Export last 8 hours of SKP entries (Senator findings) to a single document:
```bash
# Export from SKP DB
sqlite3 /root/.hermes/shared_knowledge_pool.db \
  "SELECT key, value, created_at FROM memory_notes \
   WHERE key LIKE '%/temuan/%' OR key LIKE '%/peluang/%' \
   AND created_at > unixepoch('now', '-8 hours') \
   ORDER BY created_at DESC" \
  > /tmp/skp-latest-entries.txt
```

### 2. Feed into NotebookLM
- Upload `/tmp/skp-latest-entries.txt` to NotebookLM
- Add context prompt: "Ini adalah temuan dari 5 Senator domain berbeda (akademisi, bisnis, komunitas, pemerintah, media). Buat laporan terstruktur untuk subscriber Upshalter."

### 3. Generate Structured Report
NotebookLM will auto-generate:
- **Ringkasan Eksekutif**: Poin penting semua domain
- **Temuan per Domain**: 2-3 poin utama each (akademisi, bisnis, etc.)
- **Tema Lintas Domain**: Pola yang muncul di multiple domain
- **Implikasi untuk Upshalter**: Peluang/ancaman bisnis
- **Alert**: Regulasi baru, tren viral, ancaman kompetisi

### 4. Export & Deliver
- Export to Markdown/PDF from NotebookLM
- Save to `/root/upshalter-reports/pentahelix-brief-*.md`
- Send to subscribers via Telegram (filtered by tier)

## Integration with Hermes Pipeline
Add to `kurator-review.sh`:
```bash
# After consolidating SKP entries
echo "📤 Uploading SKP entries to NotebookLM for structured report..."
# (Manual step: upload to NotebookLM via UI, or use NotebookLM API if available)
# After generating report in NotebookLM:
echo "✅ Report generated. Exporting to Markdown..."
# Save exported file to /root/upshalter-reports/
```

## Pitfalls
- NotebookLM requires Google account login (no direct API access yet for automated upload)
- For fully automated pipeline, fallback to manual Kurator review + template-based report generation
- Ensure SKP entries are formatted clearly before uploading to NotebookLM (use Markdown format)

## Reference
- GitHub Topic: https://github.com/topics/notebooklm
- Example Report Structure: See PRD-002 Fitur 2.2 Kurator Review