# CLAUDE.md — Agent Constitution for NTS

> **AI agents:** Read this file first. It is the authoritative reference for this codebase.

## Project Overview

Network Topology Scanner (NTS) is a network discovery and visualization tool that scans your LAN, infers device connections, and renders an interactive topology graph. It uses nmap, SNMP, and passive scanning to build a SQLite + NetworkX topology database, then serves it to a React frontend via FastAPI WebSocket. An IsolationForest model flags anomalous devices. Claude Code headless (via the `claude` CLI) generates natural language resilience reports.

The project targets small-to-medium networks (home labs, small offices). Development runs bare metal (Python venv + npm). Redis is optional but some features (pub/sub, caching) are unavailable without it. A Docker-based demo mode (`demo.sh`) also ships for reproducible end-to-end testing against a containerized demo network.

## Directory Structure

```
Network-Topology-Scanner/
├── CLAUDE.md                       ← YOU ARE HERE. Read this first.
├── README.md                       ← Project overview, demo quickstart
├── INSTALL_GUIDE.md                ← Database setup for local dev
├── QUICK_START_GUIDE.md            ← Fast path to running demo
├── LICENSE
├── Research-Paper/                 ← Team research paper (do NOT modify without asking)
│   ├── Abstract.md
│   └── Problem-Statement.md
└── network-topology-mapper/        ← All application code lives here
    ├── demo.sh                     ← Docker demo helper: up/down/scan/status/logs
    ├── docker-compose.yml          ← Base compose file (backend, frontend, redis on nts-net)
    ├── docker-compose.demo.yml     ← Overlay: adds demo containers on 172.20.0.0/24
    ├── .env.example                ← Template — copy to .env for local dev
    ├── .env.dockerless             ← Pre-configured for bare-metal dev
    ├── .env.demo                   ← Pre-configured for `demo.sh up` (no secrets, committed)
    ├── .gitignore
    ├── README.md
    ├── backend/                    ← FastAPI Python backend
    │   ├── requirements.txt
    │   ├── Dockerfile              ← Used by docker-compose (demo mode only)
    │   ├── .dockerignore
    │   ├── seed_data.py            ← Script: seed SQLite from a topology JSON dump
    │   ├── scripts/                ← Standalone utility scripts
    │   │   └── import_topology_json.py
    │   ├── app/
    │   │   ├── main.py             ← App entry point, lifespan, router registration
    │   │   ├── config.py           ← Pydantic settings (reads .env)
    │   │   ├── db/                 ← Database clients
    │   │   │   ├── topology_db.py
    │   │   │   ├── redis_client.py
    │   │   │   └── sqlite_db.py
    │   │   ├── models/             ← Pydantic models
    │   │   │   ├── alert.py
    │   │   │   ├── connection.py
    │   │   │   ├── device.py
    │   │   │   └── scan.py
    │   │   ├── routers/            ← API route handlers (each gets its own file)
    │   │   │   ├── alerts.py
    │   │   │   ├── reports.py
    │   │   │   ├── scans.py
    │   │   │   ├── settings.py
    │   │   │   ├── simulation.py
    │   │   │   ├── snapshots.py
    │   │   │   └── topology.py
    │   │   ├── services/           ← Business logic (no HTTP handling here)
    │   │   │   ├── ai/             ← Anomaly detection, failure prediction, reports, scan optimizer
    │   │   │   │   ├── anomaly_detector.py
    │   │   │   │   ├── failure_predictor.py
    │   │   │   │   ├── report_generator.py  ← Wraps Claude Code CLI via subprocess
    │   │   │   │   └── scan_optimizer.py
    │   │   │   ├── graph/          ← Graph analysis (SPOF, resilience, simulation, paths)
    │   │   │   │   ├── failure_simulator.py
    │   │   │   │   ├── graph_builder.py
    │   │   │   │   ├── path_analyzer.py
    │   │   │   │   ├── resilience_scorer.py
    │   │   │   │   └── spof_detector.py
    │   │   │   ├── scanner/        ← Network scanning + connection inference
    │   │   │   │   ├── active_scanner.py
    │   │   │   │   ├── config_puller.py
    │   │   │   │   ├── connection_inference.py
    │   │   │   │   ├── passive_scanner.py
    │   │   │   │   ├── scan_coordinator.py
    │   │   │   │   └── snmp_poller.py
    │   │   │   ├── realtime/       ← WebSocket + event bus
    │   │   │   │   ├── event_bus.py
    │   │   │   │   └── ws_manager.py
    │   │   │   └── mock_data.py    ← Dev fallback data
    │   │   └── tasks/              ← Background tasks (asyncio, NOT Celery)
    │   │       ├── analysis_tasks.py
    │   │       └── scan_tasks.py
    │   └── tests/
    │       └── test_connection_inference.py
    ├── frontend/                   ← React 18 + TypeScript + Vite
    │   ├── package.json
    │   ├── vite.config.ts
    │   ├── tailwind.config.ts
    │   ├── postcss.config.js
    │   ├── tsconfig.json
    │   ├── index.html
    │   ├── Dockerfile              ← Used by docker-compose (demo mode only)
    │   ├── .dockerignore
    │   ├── nginx.conf              ← Served by nginx in the frontend container
    │   └── src/
    │       ├── App.tsx
    │       ├── main.tsx
    │       ├── index.css
    │       ├── components/
    │       │   ├── dashboard/      ← MetricsBar, DependencyMatrix, RiskHeatmap, TimelineView
    │       │   ├── graph/          ← NetworkCanvas, GraphControls, LayerToggle, MiniMap, NodeTooltip, EdgeLabel
    │       │   ├── layout/         ← AppShell, Sidebar, CommandPalette
    │       │   ├── panels/         ← AlertFeed, DeviceInspector, ResilienceReport, ScanStatus, SimulationPanel
    │       │   └── shared/         ← DeviceIcon, RiskScore, StatusBadge
    │       ├── hooks/              ← useAlerts, useSimulation, useTopology, useWebSocket
    │       ├── lib/                ← api.ts, cytoscape-config.ts, graph-utils.ts, node-icons.ts
    │       ├── stores/             ← filterStore, settingsStore, topologyStore (Zustand)
    │       └── types/              ← topology.ts, cytoscape-extensions.d.ts
    ├── demo/                       ← Dockerfiles for demo network containers
    │   ├── file-server/Dockerfile  ← Alpine + SSH + SMB
    │   ├── printer/Dockerfile      ← Alpine + socat (JetDirect + IPP)
    │   └── snmp-device/            ← Alpine + net-snmp
    │       ├── Dockerfile
    │       └── snmpd.conf
    ├── docs/                       ← Reference docs
    │   ├── API.md
    │   ├── ARCHITECTURE.md
    │   ├── CONTRIBUTING.md
    │   ├── SETUP.md
    │   └── TROUBLESHOOTING.md
    └── testing/                    ← Test checklists and health check scripts
        ├── health-checks.js
        ├── SMOKE_TEST.md
        └── TEST_CHECKLIST.md
```

---

## Sacred Rules — Do NOT Violate

1. **Do NOT create new top-level directories** inside `network-topology-mapper/` without team discussion.
2. **Do NOT move files** between `backend/app/` subdirectories without understanding the import chain.
3. **Do NOT modify** environment variable names in `.env.example` — other config files depend on them.
4. **Do NOT add Celery back.** Scheduling uses asyncio in `main.py` lifespan. This was a deliberate architectural decision.
5. **Do NOT commit `.env` files.** Use `.env.example` as the template. `.env.demo` is committed intentionally (no secrets).
6. **Do NOT modify `Research-Paper/`** without explicit team discussion — this is shared academic work.
7. **All backend code** goes under `backend/app/`. The only Python files allowed at `backend/` root are `requirements.txt` and `seed_data.py` (a legacy standalone data-seeding helper). New utility scripts go in `backend/scripts/`, not at the root.
8. **All frontend components** follow the existing subdirectory convention: `components/dashboard/`, `components/graph/`, `components/layout/`, `components/panels/`, `components/shared/`.
9. **New API routes** get their own file in `routers/` and must be registered in `main.py`.
10. **New services** get their own file in the appropriate `services/` subdirectory.

---

## Branch + Commit Conventions

Branch from `main` for all work:
```
feature/short-description
fix/short-description
docs/short-description
```

Commit message format: `type(scope): description`

Examples:
```
feat(scanner): add LLDP neighbor discovery
fix(frontend): handle empty topology gracefully
docs: update API reference
chore(docker): bump redis to 7.4
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Scopes: `scanner`, `inference`, `graph`, `frontend`, `api`, `docker`, `demo`, `ai`

**Merge to `main` via PR. Never push directly to `main`.**

---

## Tech Stack

Do not change without team discussion.

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Topology DB | SQLite + NetworkX (graph storage + SPOF queries) |
| Cache / Pubsub | Redis 7 |
| Metadata / History | SQLite (scans, alerts, snapshots, settings) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Graph viz | Cytoscape.js |
| State management | Zustand |
| Scanning | nmap (subprocess, NOT python-nmap), Scapy (passive), pysnmp, Netmiko |
| Anomaly detection | scikit-learn IsolationForest |
| AI reports | Claude Code headless (shells out to the `claude` CLI — no Anthropic SDK dependency) |
| Infra | Bare metal (Python venv + npm) for dev. Redis optional. Docker Compose is used only for the demo mode (`./demo.sh up`). |

---

## Key Architecture Decisions

**Bare metal for development, Docker for demo only.**
Day-to-day development runs the backend via `uvicorn` and the frontend via the Vite dev server — no Docker required. `docker-compose.yml` + `docker-compose.demo.yml` + `demo.sh` exist only to spin up a reproducible containerized demo network for end-to-end testing. Do not treat Docker as the primary dev path.

**AI resilience reports use Claude Code headless, not the Anthropic SDK.**
`report_generator.py` shells out to the `claude` CLI with `--output-format json --max-turns 1`. If the `claude` binary is not on PATH, the endpoint falls back to a deterministic rule-based report. There is no `anthropic` package in `requirements.txt`, and `ANTHROPIC_API_KEY` / `CLAUDE_MODEL` env vars are not read by `config.py`.

**Connection inference runs unconditionally as Phase 5 of every scan.**
`scan_coordinator.py` runs 5 phases: active nmap → passive Scapy → SNMP → config pull → inference. Phase 5 (`connection_inference.py`) uses gateway + switch-aware strategies to infer edges even when LLDP is unavailable (home networks).

**Asyncio scheduling, not Celery.**
Periodic scans and analysis are scheduled via `asyncio` tasks in the FastAPI `lifespan` function (`main.py`). There is no Celery worker or broker config.

**Topology is stored in SQLite via `topology_db.py`.**
All device and connection data is persisted in SQLite with NetworkX used for in-memory graph analysis (SPOF detection, path analysis, resilience scoring).

**IsolationForest requires a minimum number of devices to train.**
`analysis_tasks.py` has a minimum-data guard; anomaly detection silently skips if there aren't enough devices.

**WebSocket flow:** service → `event_bus` → `ws_manager` → all connected clients on the `/ws/topology` endpoint. Frontend `useWebSocket` hook connects to `/ws/topology` and dispatches to the Zustand store. The `event_bus.py` uses Redis pub/sub as the transport when Redis is available, and falls back to an in-process channel otherwise.

---

## Development Workflow

```bash
# Backend:
cd network-topology-mapper/backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal):
cd network-topology-mapper/frontend
npm install && npm run dev

# Frontend:   http://localhost:3000
# Backend API: http://localhost:8000/api
# API docs:   http://localhost:8000/docs
```

---

## Testing Before Committing

- **Backend:** `cd backend && python -m pytest tests/` — must pass
- **Frontend:** `cd frontend && npm run build` — must succeed (no TypeScript errors)
- **Scan logic changed:** trigger a scan from the UI and verify devices + edges appear in the frontend graph

---

## API Quick Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness + component status (topology_db, redis, ws clients) |
| `GET` | `/api/topology` | Full topology (nodes + edges), supports `layer`/`vlan`/`subnet`/`device_type`/`risk_min` filters |
| `GET` | `/api/topology/stats` | Aggregate stats |
| `POST` | `/api/topology/import` | Bulk-upsert devices + connections + dependencies |
| `POST` | `/api/topology/clear` | Wipe all devices, connections, and dependencies |
| `GET` | `/api/devices/{id}` | Device details |
| `GET` | `/api/devices/{id}/connections` | Device connections |
| `GET` | `/api/devices/{id}/dependencies` | Device dependencies |
| `POST` | `/api/scans` | Trigger scan (body: `{"type": "full", "target": "172.20.0.0/24", "intensity": "normal"}`) |
| `GET` | `/api/scans` | Scan history |
| `GET` | `/api/scans/{id}` | Scan status (includes live progress from Redis when running) |
| `DELETE` | `/api/scans/{id}` | Cancel scan |
| `GET` | `/api/alerts` | Alert list |
| `PATCH` | `/api/alerts/{id}` | Update alert status |
| `GET` | `/api/alerts/stream` | Server-Sent Events stream of new alerts |
| `POST` | `/api/simulate/failure` | Simulate device/link failure |
| `GET` | `/api/simulate/spof` | Single points of failure |
| `GET` | `/api/simulate/resilience` | Resilience score |
| `GET` | `/api/reports/resilience` | Claude-Code-generated resilience report (rule-based fallback if `claude` CLI missing) |
| `GET` | `/api/reports/changelog` | Topology changelog derived from snapshot history |
| `GET` | `/api/snapshots` | Topology snapshot history |
| `GET` | `/api/snapshots/{id}` | Specific snapshot |
| `GET` | `/api/settings` | Current settings (defaults merged with SQLite overrides) |
| `PUT` | `/api/settings` | Persist setting overrides to SQLite |
| `GET` | `/api/scan-optimizer/recommendations` | AI scan recommendations |
| `WS` | `/ws/topology` | Real-time events (device/connection/scan/alert) |
