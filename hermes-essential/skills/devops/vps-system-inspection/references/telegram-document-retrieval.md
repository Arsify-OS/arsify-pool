# Telegram Document Retrieval Pattern

## Context
When user mentions sending a document via Telegram bot, the document is cached locally by Hermes Agent's Telegram integration.

## Cache Location
Documents sent via Telegram are stored in:
```
/root/.hermes/cache/documents/
```

File naming pattern: `doc_<hash>_<original_filename>`

Example:
```
doc_a78e8879c2f2_seedmemory.txt
```

## Retrieval Workflow

1. **Check cache directory**
   ```bash
   ls -lah /root/.hermes/cache/documents/
   ```

2. **Identify recent documents**
   - Sort by modification time (most recent first)
   - Match filename pattern if user mentioned the filename

3. **Read document**
   ```bash
   # For text files
   cat /root/.hermes/cache/documents/doc_<hash>_<filename>
   
   # For large files, use read_file tool with offset/limit
   ```

4. **Handle large documents**
   - Files >50KB may be truncated on first read
   - Use `offset` parameter to continue reading
   - Example: `read_file(path="...", offset=501, limit=500)` to read next 500 lines

## Common Document Types from Telegram
- `.txt` - Plain text (analysis, plans, logs)
- `.md` - Markdown documents
- `.json` - Configuration or data files
- `.log` - Log files
- `.yaml` / `.yml` - Configuration files

## Pitfalls
- Don't assume document location without checking cache first
- Large documents (>50KB) require multiple read operations with offset
- Cache directory may not exist if Telegram integration hasn't received files yet
- Document hash in filename is unique per upload, same file uploaded twice gets different hash

## User Communication Pattern
When user says "saya sudah mengirimkannya" (I already sent it) or "saya sudah mengirimkan dokumen" (I already sent the document), check the cache directory immediately rather than asking for clarification.

## Session Example (2026-05-04)
User sent `seedmemory.txt` (90KB) via Telegram containing:
- Multi-agent orchestration planning documents
- Impact analysis
- Ecosystem audit (12 domains)
- Priority scoring matrix
- Full pipeline analysis

Retrieved successfully from `/root/.hermes/cache/documents/doc_a78e8879c2f2_seedmemory.txt` using multiple read operations with offset.
