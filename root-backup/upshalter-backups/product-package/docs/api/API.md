# PENTAHELIX API Documentation v1.0

> **Base URL:** `https://data.upshalter.com/api/v1`  
> **Auth:** `X-API-Key: your-api-key-here` (Pro & Enterprise tiers)  
> **Format:** JSON

---

## Authentication

All API requests require an API key in the header:

```
X-API-Key: px_your_api_key_here
```

API keys are generated from the client portal. Starter tier uses shared read-only access (no key needed for GET).

---

## Endpoints

### 1. Get Insights

```
GET /api/v1/insights
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| domain | string | No | Filter by domain: `akademisi`, `bisnis`, `komunitas`, `pemerintah`, `media` |
| from | date | No | Start date (YYYY-MM-DD) |
| to | date | No | End date (YYYY-MM-DD) |
| limit | int | No | Max results (default: 20, max: 100) |
| offset | int | No | Pagination offset |
| sentiment | string | No | Filter: `positif`, `negatif`, `netral` |

**Example Request:**
```bash
curl -s "https://data.upshalter.com/api/v1/insights?domain=bisnis&limit=5" \
  -H "X-API-Key: px_your_key"
```

**Example Response:**
```json
{
  "status": "ok",
  "meta": {
    "total": 15,
    "returned": 5,
    "timestamp": "2026-05-08T08:00:00Z",
    "confidence": 0.9
  },
  "data": [
    {
      "id": "bisnis/temuan/20260508-06",
      "domain": "bisnis",
      "summary": "Startup funding pre-seed/seed naik 22% YoY...",
      "source": "senator-bisnis",
      "timestamp": "2026-05-08T06:28:30Z",
      "sentiment": "positif",
      "data": {
        "peluang": ["..."],
        "risiko": ["..."],
        "rekomendasi": "..."
      }
    }
  ]
}
```

---

### 2. Get Latest Brief

```
GET /api/v1/brief/latest
```

Returns the latest consolidated intelligence brief.

**Example Response:**
```json
{
  "status": "ok",
  "meta": {
    "generated_at": "2026-05-08T07:00:10Z",
    "confidence": 0.9,
    "entries_used": 11,
    "model": "openrouter/owl-alpha"
  },
  "data": {
    "markdown": "# PENTAHELIX INTELLIGENCE BRIEF\n...",
    "html": "<h1>PENTAHELIX INTELLIGENCE BRIEF</h1>...",
    "ringkasan_eksekutif": "...",
    "temuan_per_domain": {
      "akademisi": ["..."],
      "bisnis": ["..."],
      "komunitas": ["..."],
      "pemerintah": ["..."],
      "media": ["..."]
    }
  }
}
```

---

### 3. Get Senator Status

```
GET /api/v1/senators
```

Returns current status of all 5 senators.

**Example Response:**
```json
{
  "status": "ok",
  "data": [
    {
      "name": "senator-akademisi",
      "domain": "akademisi",
      "active": true,
      "last_update": "2026-05-08T06:28:06Z",
      "latest_key": "akademisi/temuan/20260508-06",
      "entries_total": 57
    },
    ...
  ]
}
```

---

### 4. Get System Stats

```
GET /api/v1/stats
```

**Example Response:**
```json
{
  "status": "ok",
  "data": {
    "total_entries": 421,
    "entries_by_domain": {
      "akademisi": 57,
      "bisnis": 73,
      "komunitas": 69,
      "pemerintah": 101,
      "media": 69,
      "other": 52
    },
    "latest_senator_run": "2026-05-08T06:28:00Z",
    "latest_kurator_run": "2026-05-08T07:00:10Z",
    "uptime_hours": 168,
    "database_size_kb": 650
  }
}
```

---

### 5. Webhook Subscription (Enterprise only)

```
POST /api/v1/webhooks
```

**Body:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["new_brief", "new_insight", "system_alert"],
  "secret": "your-webhook-secret"
}
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "webhook_id": "wh_abc123",
    "url": "https://your-server.com/webhook",
    "events": ["new_brief", "new_insight", "system_alert"],
    "created_at": "2026-05-08T08:00:00Z"
  }
}
```

---

## Rate Limits

| Tier | Requests/min | Requests/day |
|------|-------------|-------------|
| Starter | 10 | 500 |
| Pro | 60 | 5,000 |
| Enterprise | 300 | 50,000 |

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 55
X-RateLimit-Reset: 1715156400
```

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Tier doesn't allow this endpoint |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

**Error Response Format:**
```json
{
  "status": "error",
  "error": {
    "code": 429,
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

---

## SDK Examples

### Python
```python
import requests

API_KEY = "px_your_key"
BASE = "https://data.upshalter.com/api/v1"

headers = {"X-API-Key": API_KEY}

# Get latest insights
r = requests.get(f"{BASE}/insights?domain=bisnis&limit=5", headers=headers)
data = r.json()

# Get latest brief
r = requests.get(f"{BASE}/brief/latest", headers=headers)
brief = r.json()
```

### JavaScript
```javascript
const API_KEY = "px_your_key";
const BASE = "https://data.upshalter.com/api/v1";

const headers = { "X-API-Key": API_KEY };

// Get latest insights
const res = await fetch(`${BASE}/insights?domain=bisnis&limit=5`, { headers });
const data = await res.json();

// Get latest brief
const brief = await fetch(`${BASE}/brief/latest`, { headers });
const briefData = await brief.json();
```

### cURL
```bash
# Get insights
curl -s "https://data.upshalter.com/api/v1/insights?limit=10" \
  -H "X-API-Key: px_your_key" | jq .

# Get brief
curl -s "https://data.upshalter.com/api/v1/brief/latest" \
  -H "X-API-Key: px_your_key" | jq .data.markdown
```

---

*API v1.0 — Last updated: 2026-05-08*
