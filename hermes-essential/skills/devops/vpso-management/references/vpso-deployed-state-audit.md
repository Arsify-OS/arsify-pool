# VPSO Actual Deployed State vs Documented Role Models

**Audit Date:** 8 Mei 2026  
**Auditor:** OWL (Hermes Agent)

## Discrepancy: Documented vs Actual

The VPSO Management skill documents 7 role models. The actual deployment has significantly more services.

### Documented Role Models (7)
1. VPSO Upshalter (TUI) — hermes-upshalter :9120
2. VPSO Unit (Systemd) — hermes-api, archivist, backend, flowforce, frontend, workstation
3. VPSO Manager — hermes-upshalternal :8645
4. Internal Worker Pool — hermes-internet
5. Swarm Agent (Docker) — hermes-gamedev, hermes-loyx
6. Workspace Instance — hermes-kanban, hermes-workspace-fresh
7. Orchestrator — hermes-orchestrator :8000

### Actual Deployed Services (22 systemd + 12 Docker)

#### Systemd Services NOT in Original 7 Role Models
| Service | Port | Description | Status |
|---------|------|-------------|--------|
| hermes-Infrastructure | :9121 | VPSO Unit - Infrastructure | ✅ active |
| hermes-dashboard-bridge | — | Dashboard Orchestrator Bridge | ✅ active |
| hermes-builder | :9122 | VPSO Unit - Builder | EXISTS |
| hermes-lingkungan-hidup | :9142 | VPSO Unit - Lingkungan Hidup | EXISTS |
| hermes-pariwisata | :9139 | VPSO Unit - Pariwisata | EXISTS |
| hermes-finansial | :9140 | VPSO Unit - Finansial | EXISTS |
| hermes-operation | :9134 | VPSO Unit - Operation | EXISTS |
| hermes-dashboard | :9119 | VPSO Unit - Host Agent | EXISTS |
| terminal-upshalter | — | Terminal Upshalter API Server | ⚠️ restart loop |
| tunnel-upshalternal | — | SSH Tunnel - Upshalter CEO | ✅ active |

#### Services with Issues
| Service | Issue |
|---------|-------|
| hermes-upshalter :9120 | ⚠️ activating (restart loop) |
| hermes-loyx :9136 | ❌ dead |
| hermes-dev :9137 | ❌ dead (by design?) |
| terminal-upshalter | ⚠️ activating (restart loop) |
| hermes-backup | ❌ dead (timing-based, not enabled) |

#### Docker Containers NOT in Original Role Models
| Container | Image | Status |
|-----------|-------|--------|
| hermes-api | hermes-cognitive-api | ✅ Up 13h (healthy) |
| hermes-worker | hermes-cognitive-worker | ✅ Up 12h |
| hermes-beat | hermes-cognitive-beat | ✅ Up 12h |
| senator-pemerintah | nousresearch/hermes-agent:latest | ✅ Up |
| senator-media | nousresearch/hermes-agent:latest | ✅ Up |
| senator-bisnis | nousresearch/hermes-agent:latest | ✅ Up |
| senator-komunitas | nousresearch/hermes-agent:latest | ✅ Up |
| senator-akademisi | nousresearch/hermes-agent:latest | ✅ Up |

#### Docker Containers Exited (Code 143 = SIGTERM)
| Container | Notes |
|-----------|-------|
| hermes-workspace-fresh-hermes-workspace-1 | Exited 16h ago |
| hermes-gamedev | Exited 16h ago |
| hermes-loyx | Exited 16h ago |
| hermes-kanban-hermes-kanban-1 | Exited 16h ago |

## Key Findings

1. **Role model #1 is live**: Upshalter TUI (:9120) runs with `HERMES_HOME` + working directory pattern
2. **Role model #2 is live**: 6+ VPSO Units run as systemd services with auto-restart
3. **Role model #5 (Swarm) is split**: Senators run via Docker Compose (senator-pentahelix), not individual swarm agents
4. **New services emerged**: Infrastructure, Builder, Pariwisata, Finansial, Operation, Lingkungan Hidup were added but not documented in role models
5. **Bridge architecture exists**: hermes-dashboard-bridge bridges orchestrator to a specific dashboard instance
6. **Tunnel architecture**: tunnel-upshalternal provides SSH tunnel access (CEO access pattern)

## Implications for Productization

- The VPSO org structure is OPERATIONAL but not PRODUCTIZED
- No self-service provisioning for new "departments" (new hermes-*.service)
- No tenant isolation — all services share host network and filesystem
- No billing per department/unit
- The 7 role models need updating to reflect actual 20+ service deployment
- Only senator pentahelix (5 domain Docker Compose) is production-workflow-ready
