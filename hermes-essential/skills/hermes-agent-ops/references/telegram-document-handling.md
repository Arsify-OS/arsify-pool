# Telegram Document Handling

When users send documents via Telegram bot, Hermes Agent automatically downloads and caches them for processing.

## Document Cache Location

Documents sent via Telegram are stored in:
```
/root/.hermes/cache/documents/
```

## Naming Pattern

Files are named with the pattern:
```
doc_<hash>_<original-filename>.<ext>
```

Example:
```
doc_a78e8879c2f2_seedmemory.txt
```

Where:
- `doc_` - prefix indicating Telegram document
- `a78e8879c2f2` - hash/identifier for the document
- `seedmemory.txt` - original filename from user

## Workflow

1. **User sends document via Telegram**
   - User uploads file to Telegram bot (@upshalter_hermes_bot)
   - Bot receives and processes the file

2. **Agent downloads and caches**
   - Document is automatically downloaded
   - Saved to `/root/.hermes/cache/documents/`
   - Named with hash prefix for uniqueness

3. **Agent can read the document**
   - Use `ls -lah /root/.hermes/cache/documents/` to list available documents
   - Use `read_file` tool to read the content
   - Documents persist across sessions until manually cleaned

## Finding Recent Documents

List documents by modification time (newest first):
```bash
ls -lht /root/.hermes/cache/documents/ | head -10
```

Find documents by name pattern:
```bash
ls -la /root/.hermes/cache/documents/ | grep "seedmemory"
```

## Supported File Types

Common types that work well:
- `.txt` - Plain text files
- `.md` - Markdown documents
- `.pdf` - PDF documents (may need OCR for scanned PDFs)
- `.json` - JSON data files
- `.yaml` / `.yml` - YAML configuration files
- `.log` - Log files

## Pitfalls

- **Cache persistence**: Documents remain in cache indefinitely. Clean up old documents manually if disk space is a concern.
- **Large files**: Very large documents (>10MB) may take time to download and process.
- **Binary files**: Images, videos, and other binary formats are cached but may need special tools to process.
- **Filename collisions**: The hash prefix prevents collisions even if users send files with the same name.

## Example Session

```
User: "saya sudah mengirimkannya dalam bentuk .txt"

Agent checks:
1. ls -lah /root/.hermes/cache/documents/
2. Finds: doc_a78e8879c2f2_seedmemory.txt (89K, recent timestamp)
3. read_file /root/.hermes/cache/documents/doc_a78e8879c2f2_seedmemory.txt
4. Successfully reads and processes the document
```

## Integration with Other Platforms

This pattern is specific to Telegram. Other platforms (Discord, Slack) may use different cache locations:
- Discord: Check `/root/.hermes/cache/discord/`
- Slack: Check `/root/.hermes/cache/slack/`

(Verify actual paths with `find /root/.hermes/cache -type f -name "*.*" | head -20`)
