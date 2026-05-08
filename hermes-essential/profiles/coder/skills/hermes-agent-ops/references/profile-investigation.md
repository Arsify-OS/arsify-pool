# Profile Investigation Patterns

## Identifying Unused Profiles

When you find multiple Hermes profiles and need to determine if they're actively used:

### 1. Check Profile List and Status
```bash
hermes profile list
```

Look for: Gateway status (stopped/running), last used indicators.

### 2. Check for Active Sessions
```bash
ls -la ~/.hermes/profiles/*/sessions/ 2>/dev/null
```

Empty sessions directories indicate no chat history = likely unused.

### 3. Check Logs for Activity
```bash
cat ~/.hermes/profiles/*/logs/agent.log 2>/dev/null
```

Minimal logs (only startup messages, no chat activity) = unused profile.

### 4. Compare Skill Counts
```bash
# Check default profile
hermes skills list | wc -l

# Check specific profile
hermes profile use <profile-name> && hermes skills list | wc -l && hermes profile use default
```

Note: Profiles created via `hermes profile create` may have fewer skills (92) than default (96) because not all enabled skills are copied.

### 5. Check Alias Scripts
```bash
ls -la ~/.local/bin/ | grep -E "domain|progamer|server|<profile-name>"
```

Alias scripts are created automatically but don't indicate active use.

### 6. Check Profile Creation Time
```bash
ls -la ~/.hermes/profiles/*/config.yaml
```

Recent creation + no activity = test profile safe to delete.

## Safe Profile Deletion

```bash
# Verify unused first (steps 1-6 above)
hermes profile delete <profile-name>
```

Warns: This removes all profile data permanently.

## Common Findings

- **Test profiles**: Created during experimentation, no sessions, minimal logs
- **Skill count discrepancy**: New profiles get 92 skills vs 96 in default (4 skills not copied)
- **Shared model config**: All profiles may share same default model (e.g., tencent/hy3-preview:free)
- **Space impact**: Minimal (~11MB per profile for configs, skills, logs)