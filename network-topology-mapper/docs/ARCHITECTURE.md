# Architecture Overview

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                          │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Graph    │  │ Device    │  │ Alert    │  │ Simulation    │  │
│  │ Canvas   │  │ Inspector │  │ Feed     │  │ Panel         │  │
│  └──────────┘  └───────────┘  └──────────┘  └───────────────┘  │
├──────────────────────────────────────────────────────────────────┤
│           WebSocket (/ws/topology) + REST API (/api/*)           │
├──────────────────────────────────────────────────────────────────┤
│                     FastAPI Backend                               │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ Scanner  │  │ Graph     │  │ Anomaly      │  │ AI       │  │
│  │ Engine   │  │ Analyzer  │  │ Detection    │  │ Reports  │  │
│  └──────────┘  └───────────┘  └──────────────┘  └──────────┘  │
├──────────────────────────────────────────────────────────────────┤
│  SQLite (storage) │ NetworkX (graph analysis) │ Redis (pubsub) │
└──────────────────────────────────────────────────────────────────┘
```

---

## Scanning Pipeline

Every scan runs 5 phases in sequence via `scan_coordinator.py`:

```
POST /api/scans
      │
      ▼
ScanCoordinator.run_scan()
      │
      ├─── Phase 1: ActiveScanner      (nmap — discovers devices, open ports, services)
      ├─── Phase 2: PassiveScanner     (Scapy — ARP/DNS/DHCP passive capture)
      ├─── Phase 3: SnmpPoller         (SNMP GET/WALK — vendor, model, VLANs)
      ├─── Phase 4: ConfigPuller       (SSH/Netmiko — routing tables, interface lists)
      └─── Phase 5: ConnectionInference (UNCONDITIONAL — infer edges from topology data)
                        │
                        ▼
                   GraphBuilder    ← merges results, deduplicates, stores devices/edges in SQLite
                        │
                        ▼
                   EventBus.publish("topology_updated")
                        │
                        ▼
                   Redis pub/sub → WsManager → all WebSocket clients
```

**Phase 5 always runs.** Even if earlier phases find nothing, inference runs and attempts to infer gateway-based connections from whatever data is in the topology store.

**ActiveScanner** uses nmap via subprocess (NOT python-nmap). Configurable intensity: `light`, `normal`, `deep`.

**ConnectionInference** uses two strategies:
- Gateway-based: all devices route through the default gateway — infer star topology
- Switch-aware: if a switch is detected (via SNMP port tables), infer hierarchical topology

After the scan, `run_analysis()` is called in `scan_coordinator.py` to run anomaly detection if sufficient device count is met.

---

## Connection Inference Details

`connection_inference.py` is the key Plan B contribution. It infers the edge graph without LLDP (home networks don't have it).

```python
# Core strategy selection (simplified):
if switch_detected:
    infer_hierarchical_topology(devices, switch)
else:
    infer_gateway_star(devices, gateway_ip)
```

Edges are stored in SQLite and analyzed with NetworkX in-memory graphs. The frontend renders them as graph edges in Cytoscape.js.

---

## Demo Network Architecture

The Docker demo uses `docker-compose.demo.yml` as an overlay on top of `docker-compose.yml`. Five containers simulate a real network on the `nts-net` bridge (172.20.0.0/24):

```
nts-net (172.20.0.0/24)
   │
   ├── backend (172.20.0.2) ← scanner runs here, has cap_add: NET_RAW/NET_ADMIN
   ├── web-server (nginx)   ← ports 80
   ├── db-server (postgres) ← port 5432
   ├── file-server (alpine) ← ports 22 (SSH), 139/445 (SMB)
   ├── printer (alpine)     ← ports 631 (IPP), 9100 (JetDirect)
   └── snmp-device (alpine) ← port 161/UDP (SNMP)
```

The backend uses nmap to scan 172.20.0.0/24, discovers these containers, runs connection inference, and stores the topology in SQLite.

---

## Frontend Architecture

### Component Hierarchy

```
App
└── AppShell
    ├── Sidebar               (navigation + active scan status)
    ├── CommandPalette        (Cmd+K search)
    └── Main Content
        ├── MetricsBar        (device count, connections, risk score, alerts)
        ├── NetworkCanvas     (Cytoscape.js graph — core view)
        │   ├── GraphControls (zoom, fit, layout selector)
        │   ├── LayerToggle   (physical / logical / application)
        │   ├── MiniMap       (overview for large graphs)
        │   └── NodeTooltip   (hover card)
        └── Side Panel (conditional on selection)
            ├── DeviceInspector
            ├── AlertFeed
            ├── SimulationPanel
            └── ResilienceReport
```

### State Management (Zustand)

- **topologyStore** — devices, connections, selected device, graph layout, filter state
- **filterStore** — active filters (device type, VLAN, risk level), search query, layer selection
- **settingsStore** — user preferences, scan schedules

### Real-time Updates

```
Backend event → EventBus → Redis pub/sub → WsManager → WebSocket → useWebSocket hook → Zustand store → Cytoscape re-render
```

### Cytoscape.js Integration

Default layout: `dagre` (hierarchical, top-down). Other options: `cola` (force-directed), `grid`, `circle`.

Node design: circular ellipse, device-type colored fills, size tiers (infrastructure 50px, servers 44px, endpoints 36px), SVG icons.

Edge design: smooth bezier curves, connection-type styling (solid/dashed/dotted), bandwidth-scaled widths.

---

## Backend Architecture

### Request Flow

```
Request → Router (/api/...) → Service → Database
```

All routers are registered in `main.py` via `app.include_router()`. Each router file handles one domain (topology, scans, alerts, etc.).

Services return Pydantic models. They do not handle HTTP directly.

### Scheduled Tasks (asyncio, not Celery)

Periodic work is registered in `main.py`'s `lifespan` function using `asyncio.create_task()`:

- Periodic full scan (configurable interval)
- Topology snapshot (captures current topology state for diff/history)
- Anomaly detection run (IsolationForest, requires minimum device count)

There is no Celery worker, broker config, or `celery_app.py`.

### Anomaly Detection

`analysis_tasks.py` trains an IsolationForest on device feature vectors (open ports, scan frequency, risk score trends). It has a minimum-data guard — if fewer than N devices are in the graph, training is skipped silently.

Results are stored as alerts in SQLite with `alert_type = "anomaly"`.

### Real-time Event System

```
service.py calls: await event_bus.publish("device_added", data)
    ↓
event_bus.py publishes to Redis channel "topology:events"
    ↓
ws_manager.py subscribes to Redis, receives message
    ↓
ws_manager broadcasts JSON to all active WebSocket connections
    ↓
Frontend useWebSocket hook receives event, dispatches to Zustand store
```

Event types: `device_added`, `device_removed`, `device_updated`, `connection_change`, `alert`, `scan_progress`, `topology_updated`.

---

## Data Layer

### SQLite Schema

SQLite is the primary data store for all topology data:

- `scans` — scan history (id, type, status, start/end time, target, devices found)
- `alerts` — alert log (id, type, severity, title, device_id, created_at, status)
- `topology_snapshots` — snapshot history (id, created_at, device count, connection count, risk score, snapshot JSON)
- `settings` — key/value settings store

### Redis Usage

- `topology:full` — full topology cache (TTL: 60s)
- `device:{id}` — individual device cache (TTL: 300s)
- `scan:{id}:status` — active scan state
- `topology:events` — pub/sub channel for topology changes
- `alerts:new` — pub/sub channel for new alerts
- `scans:progress` — pub/sub channel for scan progress

---

## Security

- No authentication implemented (planned for future)
- Docker network isolation via `nts-net` bridge
- Redis requires authentication (configured in `.env`)
- SNMP community string configurable
- Scan capabilities granted via `cap_add: NET_RAW, NET_ADMIN` (not `network_mode: host`)

---

## Technology Rationale

**Cytoscape.js** — mature graph renderer, rich layout ecosystem, good TypeScript support.

**SQLite + NetworkX** — SQLite provides durable storage for devices and connections; NetworkX provides in-memory graph algorithms for SPOF detection, path analysis, and resilience scoring without requiring a separate database server.

**FastAPI** — async Python, automatic OpenAPI docs, built-in WebSocket support.

**asyncio over Celery** — simpler ops, no broker to manage, sufficient for the scan frequency (minutes to hours, not seconds).

**Bridge networking** — required for Mac compatibility; `network_mode: host` doesn't work on Mac Docker.
