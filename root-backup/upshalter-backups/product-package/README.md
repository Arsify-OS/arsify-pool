# PENTAHELIX INTELLIGENCE PLATFORM

> AI-Powered Automated Intelligence Briefing untuk Indonesia  
> v1.0 — Mei 2026

---

## Quick Start

```bash
# Clone / copy ke VPS baru
git clone [repo] /root/pentahelix-product
cd /root/pentahelix-product

# Install
bash deploy/INSTALL.md  # Ikuti panduan step-by-step

# Verify
bash scripts/health-check.sh
```

---

## Dokumen

| Dokumen | Path | Untuk Siapa |
|---------|------|-------------|
| Product Spec | `docs/PRODUCT_SPEC.md` | Product team, investor |
| Architecture | `docs/architecture/ARCHITECTURE.md` | Developer, sysadmin |
| Operations | `docs/runbook/OPERATIONS.md` | Sysadmin, ops team |
| API Docs | `docs/api/API.md` | Developer, client |
| Install Guide | `deploy/INSTALL.md` | Sysadmin |
| Marketing | `docs/MARKETING.md` | Sales, marketing |
| Handoff | `HANDOFF.md` | Successor, new team |
| License | `legal/LICENSE.md` | Legal |

---

## Struktur Direktori

```
pentahelix-product/
├── docs/
│   ├── PRODUCT_SPEC.md          # Spesifikasi produk lengkap
│   ├── MARKETING.md             # Messaging, pricing, positioning
│   ├── architecture/
│   │   └── ARCHITECTURE.md      # Arsitektur sistem detail
│   ├── api/
│   │   └── API.md               # REST API documentation
│   └── runbook/
│       └── OPERATIONS.md        # Panduan operasi harian
├── deploy/
│   ├── INSTALL.md               # Panduan instalasi dari nol
│   └── senator-compose.yml      # Docker compose template
├── config/
│   └── subscribers.json         # Template subscriber config
├── scripts/                     # (copy dari /root/upshalter-scripts/)
│   ├── senator-cycle-v3.sh
│   ├── kurator-v2.py
│   ├── generate-intelligence-page.py
│   ├── health-check.sh
│   └── ...
├── dashboard/
│   └── index.html               # Dashboard HTML template
├── legal/
│   └── LICENSE.md               # Lisensi
└── HANDOFF.md                   # Handoff checklist & final report
```

---

## Status

| Komponen | Status |
|----------|--------|
| Pipeline (Senator + Kurator) | ✅ Production |
| Delivery (Telegram) | ✅ Production |
| Dashboard | ⚠️ Basic |
| Auth System | ❌ Not implemented |
| Billing | ❌ Not implemented |
| Content Quality | ⚠️ Needs improvement |

---

## Support

- Telegram: @upshalter_bot
- Dashboard: https://data.upshalter.com
- Dokumentasi: `/root/product-package/docs/`

---

*Built by OWL for Upshalter — 2026*
