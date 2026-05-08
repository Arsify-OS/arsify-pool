# Arsify Core — SKP Database Schema

## Table: knowledge

```sql
CREATE TABLE knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    tags TEXT DEFAULT '[]',
    priority INTEGER DEFAULT 5,
    source_agent_name TEXT DEFAULT 'system',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Columns

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | INTEGER | AUTO | Primary key |
| `key` | TEXT | — | Unique identifier, e.g. `senator-akademisi/insight/20260508-11-00` |
| `value` | TEXT | — | Content (JSON insight data or text) |
| `category` | TEXT | `general` | Domain: `akademisi`, `bisnis`, `komunitas`, `pemerintah`, `media` |
| `tags` | TEXT | `[]` | JSON array of tags |
| `priority` | INTEGER | `5` | Priority 1-10 |
| `source_agent_name` | TEXT | `system` | Source agent, e.g. `senator-akademisi` |
| `created_at` | DATETIME | CURRENT_TIMESTAMP | Creation time |
| `updated_at` | DATETIME | CURRENT_TIMESTAMP | Last update time |

## Indexes

```sql
CREATE INDEX idx_knowledge_key ON knowledge(key);
CREATE INDEX idx_knowledge_category ON knowledge(category);
CREATE INDEX idx_knowledge_created ON knowledge(created_at);
```

## Key Format

### New Format (v5)
```
senator-{domain}/insight/{YYYYMMDD-HH}-{counter}
```
Example: `senator-akademisi/insight/20260508-11-00`

### Legacy Format (v3/v4)
```
curated:senator-{domain}/analysis/{task_id}
senator-{domain}/execution/{task_id}
senator-{domain}/analysis/{task_id}
```

The `skp_adapter.py` auto-detects the key format used in your database.

## Data Retention

- No automatic retention policy
- Use `skp-cleaner.py` to remove junk entries periodically
- Consider archiving entries older than 90 days in production

## Migration Notes

If migrating from `memory_notes` table:
- `memory_notes` has `scope` column — `knowledge` does not
- `skp_adapter.py` handles both schemas automatically
- Recommended: keep using `knowledge` table for new deployments
