# Arsify Core — Troubleshooting

## Common Issues

### "All LLM providers failed"

**Cause:** OpenRouter API key invalid/expired, or Ollama not running.

**Fix:**
```bash
# Verify OpenRouter key works
curl -s -X POST https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' | python3 -m json.tool
```

### "table knowledge has no column named scope"

**Cause:** `skp_adapter.py` trying to insert `scope` column that doesn't exist in the `knowledge` table.

**Fix:** This is auto-handled by the adapter (falls back to minimal INSERT). To suppress the warning, ensure you're using the latest version of `skp_adapter.py`.

### "No insights parsed from response"

**Cause:** LLM returned non-Junk text but couldn't be parsed as JSON.

**Fix:**
1. Check the response preview in the log
2. Adjust the prompt in `DOMAIN_CONFIG` to be more explicit about JSON format
3. Try a different model (some models are better at following JSON schema)

### OpenRouter 402 Payment Required

**Cause:** API key has no credits.

**Fix:** Top up at https://openrouter.ai/settings/credits or use a different key.

### JUNK entries still appearing in SKP

**Cause:** New prompt patterns not covered by existing junk detection.

**Fix:** Add new patterns to `JUNK_PATTERNS` list in `senator-execution.py`:
```python
JUNK_PATTERNS = [
    # ... existing patterns
    "your new pattern here",
]
```

### Senator cycle takes too long

**Cause:** All 5 domains running sequentially, each taking 30-60 seconds.

**Fix:** 
- Use `--all` flag for Python direct execution
- Consider async execution (see Future Roadmap)
- Use faster model (e.g. `openai/gpt-4o-mini` instead of `openai/gpt-4o`)

### Memory injection not working

**Cause:** No previous entries found for the domain.

**Fix:** This is normal for first run. Memory context builds up after 2-3 cycles.

## Debug Mode

Run with verbose output:
```bash
python3 python/senator-execution.py --domain akademisi --dry-run --test-mode
```

## Log Locations

| Log | Path |
|-----|------|
| Senator cycle | `/root/upshalter-logs/senator-{date}.log` |
| Cron | `/root/upshalter-logs/cron.log` |
| Health check | `/root/upshalter-logs/cron.log` |

## Getting Help

- Open an issue: https://github.com/Arsify-OS/arsify-core/issues
- Check existing issues: https://github.com/Arsify-OS/arsify-core/issues?q=is%3Aissue
