# CLAUDE.md — Agent Constitution for NTS

> **AI agents:** Read this file first. It is the authoritative reference for this codebase.

## Project Overview

Network Topology Scanner (NTS) is a network discovery and visualization tool that scans your LAN, infers device connections, and renders an interactive topology graph. It uses nmap, SNMP, and passive scanning to build a SQLite + NetworkX topology database, then serves it to a React frontend via FastAPI WebSocket. An IsolationForest model flags anomalous devices. Claude API generates natural language resilience reports.

The project targets small-to-medium networks (home labs, small offices). The team uses local bare-metal development by default; Docker Compose is optional for demo network simulation.

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
    ├── demo.sh                     ← Start/stop/scan/status commands
    ├── docker-compose.yml          ← Core services (backend, frontend, redis, demo containers)
    ├── docker-compose.demo.yml     ← Demo network overlay (5 simulated devices on nts-net)
    ├── .env.example                ← Template — copy to .env for local dev
    ├── .env.demo                   ← Pre-configured for Docker demo
    ├── .gitignore
    ├── README.md
    ├── backend/                    ← FastAPI Python backend
    │   ├── Dockerfile
    │   ├── requirements.txt
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
    │   │   │   │   ├── report_generator.py
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
    │   ├── Dockerfile
    │   ├── nginx.conf
    │   └── src/
    │       ├── App.tsx
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
3. **Do NOT modify** optional demo `docker-compose.yml` service names or `nts-net` network configuration — other compose files depend on it.
4. **Do NOT add Celery back.** Scheduling uses asyncio in `main.py` lifespan. This was a deliberate architectural decision.
5. **Do NOT commit `.env` files.** Use `.env.example` as the template. `.env.demo` is committed intentionally (no secrets).
6. **Do NOT modify `Research-Paper/`** without explicit team discussion — this is shared academic work.
7. **All backend code** goes under `backend/app/`. No Python files at `backend/` root except `requirements.txt` and `Dockerfile`.
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
chore(deps): bump redis client version
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Scopes: `scanner`, `inference`, `graph`, `frontend`, `api`, `demo`, `ai`, `deps`

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
| AI reports | Anthropic Claude API |
| Infra | Local services by default; optional Docker Compose demo networking (`nts-net`); nginx reverse proxy |

---

## Key Architecture Decisions

**Optional demo bridge networking (`nts-net`) — NOT `network_mode: host`.**
Required for Mac compatibility in demo mode.

**Connection inference runs unconditionally as Phase 5 of every scan.**
`scan_coordinator.py` runs 5 phases: active nmap → passive Scapy → SNMP → config pull → inference. Phase 5 (`connection_inference.py`) uses gateway + switch-aware strategies to infer edges even when LLDP is unavailable (home networks).

**Asyncio scheduling, not Celery.**
Periodic scans and analysis are scheduled via `asyncio` tasks in the FastAPI `lifespan` function (`main.py`). There is no Celery worker or broker config.

**Topology is stored in SQLite via `topology_db.py`.**
All device and connection data is persisted in SQLite with NetworkX used for in-memory graph analysis (SPOF detection, path analysis, resilience scoring).

**IsolationForest requires a minimum number of devices to train.**
`analysis_tasks.py` has a minimum-data guard; anomaly detection silently skips if there aren't enough devices.

**WebSocket flow:** service → `event_bus` → `ws_manager` → all connected clients. Frontend `useWebSocket` hook dispatches to Zustand store. The `event_bus.py` uses Redis pub/sub as the transport.

---

## Development Workflow

```bash
# Backend bare-metal dev (default for editing Python code):
cd network-topology-mapper/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend dev:
cd network-topology-mapper/frontend
npm install && npm run dev

# Optional demo network mode (requires Docker):
cd network-topology-mapper
./demo.sh up        # Starts all services + demo network (~60s for healthy state)
./demo.sh scan      # Triggers a scan against 172.20.0.0/24
./demo.sh status    # Health check
./demo.sh down      # Tear down
# Frontend:   http://localhost:3000
# Backend API: http://localhost:8000/api
# API docs:   http://localhost:8000/docs
```

---

## Testing Before Committing

- **Backend:** `cd backend && python -m pytest tests/` — must pass
- **Frontend:** `cd frontend && npm run build` — must succeed (no TypeScript errors)
- **Optional demo Docker config changed:** `./demo.sh down && ./demo.sh up` — all services must reach healthy state
- **Scan logic changed:** run a scan from local backend and verify devices + edges appear in the frontend graph

---

## API Quick Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/scan` | Trigger scan (body: `{"target": "172.20.0.0/24"}`) |
| `GET` | `/api/topology` | Full topology (nodes + edges) |
| `GET` | `/api/topology/stats` | Aggregate stats |
| `GET` | `/api/devices/{id}` | Device details |
| `GET` | `/api/devices/{id}/connections` | Device connections |
| `GET` | `/api/devices/{id}/dependencies` | Device dependencies |
| `GET` | `/api/scans` | Scan history |
| `GET` | `/api/scans/{id}` | Scan status |
| `DELETE` | `/api/scans/{id}` | Cancel scan |
| `GET` | `/api/alerts` | Alert list |
| `PATCH` | `/api/alerts/{id}` | Update alert status |
| `POST` | `/api/simulate/failure` | Simulate device/link failure |
| `GET` | `/api/simulate/spof` | Single points of failure |
| `GET` | `/api/simulate/resilience` | Resilience score |
| `GET` | `/api/reports/resilience` | AI resilience report |
| `GET` | `/api/snapshots` | Topology snapshot history |
| `GET` | `/api/snapshots/{id}` | Specific snapshot |
| `GET` | `/api/settings` | Current settings |
| `PUT` | `/api/settings` | Update settings |
| `GET` | `/api/scan-optimizer/recommendations` | AI scan recommendations |
| `WS` | `/ws` | Real-time events |
