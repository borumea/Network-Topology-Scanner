# Network Topology Mapper — Implementation Plan

## Project Summary

A web-based network topology mapping agent that continuously discovers devices, maps relationships, identifies single points of failure, and visualizes everything in an interactive dashboard. The system combines passive/active scanning with graph analysis and AI-powered insights.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend (Vite)                  │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌─────────────┐  │
│  │ Graph   │ │ Device   │ │ Alert   │ │ Simulation  │  │
│  │ Canvas  │ │ Inspector│ │ Feed    │ │ Panel       │  │
│  └─────────┘ └──────────┘ └─────────┘ └─────────────┘  │
├─────────────────────────────────────────────────────────┤
│              WebSocket + REST API (FastAPI)              │
├─────────────────────────────────────────────────────────┤
│                    Backend Services                      │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐  │
│  │ Scanner  │ │ Graph     │ │ Anomaly   │ │ AI      │  │
│  │ Engine   │ │ Analyzer  │ │ Detector  │ │ Reports │  │
│  └──────────┘ └───────────┘ └───────────┘ └─────────┘  │
├─────────────────────────────────────────────────────────┤
│  Neo4j (Graph DB)  │  Redis (Cache/PubSub)  │  SQLite  │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend
- **Framework**: React 18 + TypeScript + Vite
- **Graph Visualization**: Cytoscape.js (primary network graph) + cytoscape-cola layout
- **Charts/Metrics**: Recharts
- **UI Components**: shadcn/ui + Tailwind CSS
- **Real-time**: Native WebSocket client
- **State Management**: Zustand
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Graph Database**: Neo4j (device/relationship storage and graph queries)
- **Cache/PubSub**: Redis (real-time event streaming, scan result caching)
- **Metadata Store**: SQLite via SQLAlchemy (scan history, user settings, alert log)
- **Task Queue**: Celery with Redis broker (scheduled scans, background analysis)
- **WebSocket**: FastAPI native WebSocket support

### Scanning & Network
- **Active Scanning**: python-nmap (wraps nmap)
- **Passive Capture**: Scapy (ARP, DNS, DHCP sniffing)
- **SNMP**: pysnmp (device interrogation, switch port mapping)
- **SSH/Device Config**: Netmiko (pulling configs from routers/switches)
- **Traffic Analysis**: pyshark (Wireshark/tshark wrapper for pcap analysis)

### AI/ML
- **Anomaly Detection**: scikit-learn IsolationForest + PyOD for topology anomalies
- **Graph ML**: PyTorch Geometric for graph neural network-based failure prediction
- **LLM Reports**: Claude API (anthropic SDK) for natural language summaries
- **Embeddings**: Node2Vec (via graspologic) for learning device behavior embeddings

---

## Directory Structure

```
network-topology-mapper/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── graph/
│   │   │   │   ├── NetworkCanvas.tsx        # Main Cytoscape.js graph component
│   │   │   │   ├── GraphControls.tsx        # Zoom, filter, layout toggle controls
│   │   │   │   ├── LayerToggle.tsx          # Physical/Logical/Application layer switch
│   │   │   │   ├── MiniMap.tsx              # Small overview inset of full topology
│   │   │   │   ├── NodeTooltip.tsx          # Hover card for device quick info
│   │   │   │   └── EdgeLabel.tsx            # Connection type/bandwidth labels
│   │   │   ├── panels/
│   │   │   │   ├── DeviceInspector.tsx      # Full device detail sidebar
│   │   │   │   ├── AlertFeed.tsx            # Real-time alert/anomaly stream
│   │   │   │   ├── SimulationPanel.tsx      # Failure simulation controls + results
│   │   │   │   ├── ResilienceReport.tsx     # AI-generated resilience summary
│   │   │   │   └── ScanStatus.tsx           # Current scan progress/history
│   │   │   ├── dashboard/
│   │   │   │   ├── MetricsBar.tsx           # Top-level KPI strip
│   │   │   │   ├── RiskHeatmap.tsx          # Subnet/VLAN risk visualization
│   │   │   │   ├── TimelineView.tsx         # Topology changes over time
│   │   │   │   └── DependencyMatrix.tsx     # Service dependency grid
│   │   │   ├── shared/
│   │   │   │   ├── DeviceIcon.tsx           # Dynamic icon by device type
│   │   │   │   ├── StatusBadge.tsx          # Online/offline/warning indicator
│   │   │   │   └── RiskScore.tsx            # Color-coded risk display
│   │   │   └── layout/
│   │   │       ├── AppShell.tsx             # Main layout wrapper
│   │   │       ├── Sidebar.tsx              # Navigation sidebar
│   │   │       └── CommandPalette.tsx       # Quick search/filter (Cmd+K)
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts             # WebSocket connection + reconnect
│   │   │   ├── useTopology.ts              # Graph data fetching + caching
│   │   │   ├── useSimulation.ts            # Failure simulation state
│   │   │   └── useAlerts.ts                # Alert stream subscription
│   │   ├── stores/
│   │   │   ├── topologyStore.ts            # Zustand store for graph state
│   │   │   ├── filterStore.ts              # Active filters/layer selection
│   │   │   └── settingsStore.ts            # User preferences
│   │   ├── lib/
│   │   │   ├── cytoscape-config.ts         # Cytoscape styles, layouts, defaults
│   │   │   ├── graph-utils.ts              # Node/edge helpers, color mapping
│   │   │   └── api.ts                      # REST API client
│   │   ├── types/
│   │   │   └── topology.ts                 # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py                         # FastAPI app entry, CORS, WebSocket
│   │   ├── config.py                       # Settings (env vars, DB URLs, scan params)
│   │   ├── models/
│   │   │   ├── device.py                   # Device SQLAlchemy + Pydantic models
│   │   │   ├── connection.py               # Connection/edge models
│   │   │   ├── alert.py                    # Alert/anomaly models
│   │   │   └── scan.py                     # Scan job/history models
│   │   ├── routers/
│   │   │   ├── topology.py                 # GET /topology, GET /devices/{id}
│   │   │   ├── scans.py                    # POST /scans, GET /scans/status
│   │   │   ├── simulation.py               # POST /simulate/failure
│   │   │   ├── alerts.py                   # GET /alerts, PATCH /alerts/{id}
│   │   │   └── reports.py                  # GET /reports/resilience
│   │   ├── services/
│   │   │   ├── scanner/
│   │   │   │   ├── active_scanner.py       # Nmap/masscan wrapper
│   │   │   │   ├── passive_scanner.py      # Scapy ARP/DNS/DHCP listener
│   │   │   │   ├── snmp_poller.py          # SNMP device interrogation
│   │   │   │   ├── config_puller.py        # Netmiko SSH config retrieval
│   │   │   │   └── scan_coordinator.py     # Orchestrates scan phases
│   │   │   ├── graph/
│   │   │   │   ├── graph_builder.py        # Constructs/updates Neo4j graph
│   │   │   │   ├── failure_simulator.py    # Node/edge removal + impact calc
│   │   │   │   ├── spof_detector.py        # Single point of failure analysis
│   │   │   │   ├── path_analyzer.py        # Critical path + bottleneck detection
│   │   │   │   └── resilience_scorer.py    # Per-device and global risk scores
│   │   │   ├── ai/
│   │   │   │   ├── anomaly_detector.py     # IsolationForest on topology changes
│   │   │   │   ├── report_generator.py     # Claude API natural language reports
│   │   │   │   ├── failure_predictor.py    # GNN-based failure prediction
│   │   │   │   └── scan_optimizer.py       # RL-based scan scheduling
│   │   │   └── realtime/
│   │   │       ├── event_bus.py            # Redis pub/sub event distribution
│   │   │       └── ws_manager.py           # WebSocket connection manager
│   │   ├── tasks/
│   │   │   ├── celery_app.py              # Celery configuration
│   │   │   ├── scan_tasks.py              # Scheduled/on-demand scan jobs
│   │   │   └── analysis_tasks.py          # Background graph analysis jobs
│   │   └── db/
│   │       ├── neo4j_client.py            # Neo4j driver + query helpers
│   │       ├── sqlite_db.py               # SQLAlchemy session setup
│   │       └── redis_client.py            # Redis connection pool
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml                      # Neo4j, Redis, backend, frontend
├── .env.example
└── README.md
```

---

## Data Models

### Neo4j Node: Device
```
(:Device {
  id: UUID,
  ip: "192.168.1.1",
  mac: "AA:BB:CC:DD:EE:FF",
  hostname: "core-switch-01",
  device_type: "switch",          // router, switch, server, workstation, ap, firewall, printer, iot, unknown
  vendor: "Cisco",
  model: "Catalyst 9300",
  os: "IOS-XE 17.6",
  open_ports: [22, 80, 443, 161],
  services: ["ssh", "http", "https", "snmp"],
  first_seen: datetime,
  last_seen: datetime,
  discovery_method: "active_scan", // passive, snmp, integration
  vlan_ids: [10, 20, 30],
  subnet: "192.168.1.0/24",
  location: "Building A, Rack 3",  // if known from SNMP/LLDP
  risk_score: 0.73,               // 0-1 composite risk
  criticality: "high",            // high, medium, low
  is_gateway: true,
  status: "online"                // online, offline, degraded
})
```

### Neo4j Relationships
```
(:Device)-[:CONNECTS_TO {
  connection_type: "ethernet",     // ethernet, fiber, wireless, vpn, virtual
  bandwidth: "10Gbps",
  switch_port: "Gi1/0/24",
  vlan: 10,
  latency_ms: 0.5,
  packet_loss_pct: 0.01,
  is_redundant: false,
  protocol: "trunk",              // access, trunk, lacp
  status: "active",               // active, disabled, degraded, flapping
  first_seen: datetime,
  last_seen: datetime
}]->(:Device)

(:Device)-[:DEPENDS_ON {
  dependency_type: "dns",          // dns, dhcp, auth, database, api, load_balancer, storage
  service_port: 53,
  criticality: "high",
  discovered_via: "traffic_analysis"
}]->(:Device)

(:Device)-[:MEMBER_OF]->(:VLAN { id: 10, name: "Engineering", subnet: "10.10.10.0/24" })

(:Device)-[:ROUTES_THROUGH]->(:Device)  // routing path edges
```

### SQLite Tables

```sql
-- Scan history
CREATE TABLE scans (
    id TEXT PRIMARY KEY,
    scan_type TEXT NOT NULL,          -- 'active', 'passive', 'snmp', 'full'
    status TEXT NOT NULL,             -- 'running', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    target_range TEXT,                -- CIDR or 'all'
    devices_found INTEGER DEFAULT 0,
    new_devices INTEGER DEFAULT 0,
    config JSON                       -- scan parameters
);

-- Alert/anomaly log
CREATE TABLE alerts (
    id TEXT PRIMARY KEY,
    alert_type TEXT NOT NULL,         -- 'new_device', 'topology_change', 'spof', 'anomaly', 'flapping'
    severity TEXT NOT NULL,           -- 'critical', 'high', 'medium', 'low', 'info'
    title TEXT NOT NULL,
    description TEXT,
    device_id TEXT,                   -- related device if applicable
    details JSON,                     -- structured alert data
    created_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    status TEXT DEFAULT 'open'        -- 'open', 'acknowledged', 'resolved', 'dismissed'
);

-- Topology snapshots (for timeline/diff)
CREATE TABLE topology_snapshots (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    device_count INTEGER,
    connection_count INTEGER,
    risk_score FLOAT,
    snapshot_data JSON                -- serialized graph summary
);
```

---

## API Endpoints

### Topology
```
GET  /api/topology                    → Full graph (nodes + edges) with filters
     ?layer=physical|logical|application
     ?vlan=10
     ?subnet=192.168.1.0/24
     ?device_type=switch
     ?risk_min=0.5

GET  /api/topology/stats              → Aggregate metrics (device counts, risk scores, etc.)
GET  /api/devices/{id}                → Full device detail
GET  /api/devices/{id}/connections    → All connections for a device
GET  /api/devices/{id}/dependencies   → Upstream/downstream dependency tree
```

### Scanning
```
POST /api/scans                       → Trigger a scan
     { "type": "full", "target": "192.168.0.0/16", "intensity": "normal" }
GET  /api/scans                       → List scan history
GET  /api/scans/{id}                  → Scan status + results
DELETE /api/scans/{id}                → Cancel running scan
```

### Simulation
```
POST /api/simulate/failure            → Simulate device/link failure
     { "remove_nodes": ["device-uuid"], "remove_edges": ["edge-uuid"] }
     Response: { "impact": { "disconnected_devices": [...], "affected_services": [...],
                             "blast_radius": 47, "risk_delta": 0.23 } }

GET  /api/simulate/spof               → List all detected single points of failure
GET  /api/simulate/resilience         → Overall resilience score + breakdown
```

### Alerts
```
GET   /api/alerts                     → List alerts (filterable by severity, type, status)
PATCH /api/alerts/{id}                → Update status (acknowledge, resolve, dismiss)
GET   /api/alerts/stream              → SSE stream for real-time alerts
```

### Reports
```
GET  /api/reports/resilience          → AI-generated resilience report (Claude API)
GET  /api/reports/changelog           → Topology changes over time period
     ?from=2025-01-01&to=2025-02-01
```

### WebSocket
```
WS   /ws/topology                     → Real-time topology updates
     Messages:
       { "type": "device_update", "data": {...} }
       { "type": "device_added", "data": {...} }
       { "type": "device_removed", "data": {...} }
       { "type": "connection_change", "data": {...} }
       { "type": "alert", "data": {...} }
       { "type": "scan_progress", "data": { "percent": 45, "phase": "port_scan" } }
```

---

## Visual Design Specification

### Overall Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ ┌──────┐  Network Topology Mapper          [Cmd+K] [🔔 3] [⚙️]  │
│ │ Logo │  Last scan: 2 min ago • 247 devices                    │
├──┬───────────────────────────────────────────────────────────────┤
│  │                                                               │
│ S│   ┌─ Metrics Bar ──────────────────────────────────────┐      │
│ i│   │ 247 Devices │ 412 Links │ Risk: 6.2/10 │ 3 SPOFs  │      │
│ d│   └────────────────────────────────────────────────────┘      │
│ e│                                                               │
│ b│   ┌─ Network Graph Canvas ─────────────────────┐ ┌─ Panel ─┐ │
│ a│   │                                             │ │         │ │
│ r│   │     [Interactive Cytoscape.js Graph]        │ │ Device  │ │
│  │   │                                             │ │ Detail  │ │
│ N│   │  Physical │ Logical │ Application  [tabs]   │ │   OR    │ │
│ a│   │                                             │ │ Alert   │ │
│ v│   │  ┌──────┐                                   │ │ Feed    │ │
│  │   │  │MiniMap│                                  │ │   OR    │ │
│  │   │  └──────┘  [Zoom] [Fit] [Layout] [Filter]  │ │ Sim     │ │
│  │   └─────────────────────────────────────────────┘ │ Results │ │
│  │                                                    └─────────┘ │
└──┴───────────────────────────────────────────────────────────────┘
```

### Color System

```
Background:
  --bg-primary:    #0F1117          (deep navy-black)
  --bg-secondary:  #1A1D28          (card/panel background)
  --bg-tertiary:   #242736          (hover states, input fields)

Text:
  --text-primary:  #E8EAF0          (primary text)
  --text-secondary:#8B8FA3          (labels, secondary info)
  --text-muted:    #555B6E          (disabled, timestamps)

Device Node Colors (by type):
  --node-router:   #6366F1          (indigo)
  --node-switch:   #3B82F6          (blue)
  --node-server:   #10B981          (emerald)
  --node-firewall: #F59E0B          (amber)
  --node-ap:       #8B5CF6          (violet)
  --node-workstation: #64748B       (slate)
  --node-iot:      #EC4899          (pink)
  --node-unknown:  #6B7280          (gray)

Status Colors:
  --status-online:  #10B981         (green)
  --status-offline: #EF4444         (red)
  --status-degraded:#F59E0B         (amber)
  --status-new:     #3B82F6         (blue pulse animation)

Risk Gradient:
  0.0-0.3:  #10B981 (low, green)
  0.3-0.6:  #F59E0B (medium, amber)
  0.6-0.8:  #F97316 (high, orange)
  0.8-1.0:  #EF4444 (critical, red)

Edge Colors:
  --edge-ethernet:  #475569         (slate, solid line)
  --edge-fiber:     #6366F1         (indigo, thick line)
  --edge-wireless:  #8B5CF6         (violet, dashed line)
  --edge-vpn:       #F59E0B         (amber, dotted line)
  --edge-virtual:   #64748B         (gray, thin dashed)

Simulation Overlay:
  --sim-affected:   #EF4444 @ 40%   (red glow on impacted nodes)
  --sim-disconnected:#EF4444 @ 80%  (solid red on unreachable nodes)
  --sim-removed:    strikethrough    (X overlay on simulated-removed node)
  --sim-safe:       #10B981 @ 20%   (green tint on unaffected nodes)
```

### Network Graph Canvas

The graph is the centerpiece. Cytoscape.js renders all devices as nodes and connections as edges.

**Node Rendering:**
- Shape: Rounded rectangles (40x40px default) with device-type icon centered inside
- Icon: Lucide icon matching device type (Server, Router, Wifi, Shield, Monitor, Printer, Cpu)
- Border: 2px solid, color = device type color from palette
- Fill: `--bg-secondary` with slight transparency
- Label: hostname or IP below node, truncated to 16 chars, `--text-secondary`
- Status indicator: 6px circle at bottom-right corner (green/red/amber)
- Risk halo: If risk_score > 0.6, subtle pulsing glow ring in risk color
- Selection state: Bright border + elevated shadow + enlarged to 48x48px
- New device: Blue pulse animation for 30 seconds after first appearance

**Edge Rendering:**
- Width: scaled by bandwidth (1px for 100Mbps, 2px for 1Gbps, 4px for 10Gbps)
- Style: solid (ethernet), dashed (wireless), dotted (VPN), double-line (fiber/LACP)
- Color: by connection type from edge color palette
- Label: bandwidth shown on hover
- Redundant links: green accent line parallel to primary
- Flapping: red blinking animation
- Disabled: 50% opacity + strikethrough pattern

**Layout Modes:**
1. **Force-directed (cola)**: Default. Devices cluster by connectivity. Good for organic overview.
2. **Hierarchical**: Top-down tree. Internet → Firewall → Core → Distribution → Access → Endpoints. Best for understanding traffic flow.
3. **Circular by VLAN**: Devices grouped in circles by VLAN membership, with inter-VLAN links crossing between groups.
4. **Geographic** (if location data available): Devices positioned by building/rack location.

**Layer Toggle Tabs:**
Located above the graph. Three tabs: Physical | Logical | Application. Each filters nodes and edges:
- Physical: Shows switches, routers, APs, physical cabling (ethernet, fiber, wireless)
- Logical: Shows VLANs, subnets, routing relationships, VPN tunnels
- Application: Shows servers, databases, load balancers, and service dependencies (DNS, DHCP, auth, API calls)

Switching layers has a 200ms crossfade animation where non-relevant nodes shrink and fade while relevant ones expand.

**Interaction:**
- Click node → opens DeviceInspector panel on right
- Click edge → shows connection detail popover (bandwidth, latency, port info)
- Right-click node → context menu: "Simulate failure", "Show dependencies", "Show paths to internet", "Mark as critical"
- Drag to pan, scroll to zoom
- Box select multiple nodes for group simulation
- Double-click empty space → reset view

**MiniMap (bottom-left):**
120x80px inset showing the full graph with a viewport rectangle. Click to navigate. Semi-transparent background.

**Graph Controls (bottom-right toolbar):**
- Zoom in/out buttons
- Fit-to-screen
- Layout dropdown (Force / Hierarchical / Circular / Geographic)
- Filter button → opens filter panel (by device type, VLAN, risk score, status)
- Screenshot/export button (PNG or SVG)
- Toggle labels on/off
- Toggle risk halos on/off

### Metrics Bar

Horizontal strip above the graph. Four stat cards side by side:

```
┌────────────┐ ┌────────────┐ ┌─────────────┐ ┌────────────────┐
│ 📡 247     │ │ 🔗 412     │ │ ⚠️ 6.2/10   │ │ 🔴 3 SPOFs     │
│ Devices    │ │ Links      │ │ Risk Score   │ │ Critical       │
│ +3 new     │ │ 98.7% up   │ │ ▲ 0.4 24h   │ │ 12 high risk   │
└────────────┘ └────────────┘ └─────────────┘ └────────────────┘
```

- Each card has: large number, label, and a secondary metric below
- Risk score card has a mini trend sparkline (last 7 days)
- SPOF card is red-tinted when count > 0
- Cards are clickable: clicking "Devices" highlights all on graph, clicking "SPOFs" highlights failure points

### Device Inspector Panel (Right Sidebar)

Slides in from right when a device node is clicked. 380px wide.

```
┌─ Device Inspector ────────────────── [✕] ─┐
│                                            │
│  🔧 core-switch-01                         │
│  Cisco Catalyst 9300 • IOS-XE 17.6        │
│  ● Online                                  │
│                                            │
│  ┌─ Risk Score ──────────────────────────┐ │
│  │  ████████████░░░░  0.73 HIGH          │ │
│  │  Reason: Single uplink, no failover   │ │
│  └───────────────────────────────────────┘ │
│                                            │
│  ─── Identity ───────────────────────────  │
│  IP          192.168.1.1                   │
│  MAC         AA:BB:CC:DD:EE:FF             │
│  Vendor      Cisco                         │
│  First seen  2025-01-15 09:23              │
│  Last seen   2 min ago                     │
│                                            │
│  ─── Network ────────────────────────────  │
│  VLANs       10, 20, 30                   │
│  Subnet      192.168.1.0/24               │
│  Gateway     Yes                           │
│  Connections 24 (22 active)                │
│                                            │
│  ─── Open Ports ─────────────────────────  │
│  22/tcp   SSH         ● open               │
│  80/tcp   HTTP        ● open               │
│  161/udp  SNMP        ● open               │
│  443/tcp  HTTPS       ● open               │
│                                            │
│  ─── Dependencies ───────────────────────  │
│  ↑ Depends on: fw-01 (gateway)            │
│  ↓ 47 devices depend on this switch       │
│  [View dependency tree]                    │
│                                            │
│  ─── Actions ────────────────────────────  │
│  [Simulate Failure]  [Show Paths]          │
│  [View Config]       [Alert History]       │
└────────────────────────────────────────────┘
```

### Alert Feed Panel

Toggleable via sidebar or replaces DeviceInspector. Real-time stream via WebSocket.

```
┌─ Alerts ─────────────── [Filter ▾] [✕] ─┐
│                                           │
│  🔴 CRITICAL • 3 min ago                  │
│  New device on restricted VLAN 50         │
│  MAC: FF:EE:DD:CC:BB:AA • Unknown vendor  │
│  [Investigate]  [Dismiss]                  │
│  ─────────────────────────────────────── │
│  🟠 HIGH • 12 min ago                     │
│  Link flapping: core-sw-01 ↔ dist-sw-03  │
│  Port Gi1/0/48 • 6 state changes/min     │
│  [View device]  [Acknowledge]              │
│  ─────────────────────────────────────── │
│  🟡 MEDIUM • 1 hr ago                     │
│  Topology change detected                  │
│  New route: 10.0.0.0/8 via 192.168.1.5   │
│  [View diff]  [Dismiss]                    │
│  ─────────────────────────────────────── │
│  🔵 INFO • 2 hr ago                       │
│  Scan completed: 247 devices, 3 new       │
│  Duration: 4m 23s                          │
│                                           │
└───────────────────────────────────────────┘
```

Alert severity indicators: Critical (red dot + red left border), High (orange), Medium (yellow), Low (blue), Info (gray).

New alerts slide in from top with a brief flash animation.

### Simulation Panel

Accessible from "Simulate Failure" button or sidebar nav. Allows selecting nodes/edges to remove and shows impact analysis.

```
┌─ Failure Simulation ───────────────── [✕] ─┐
│                                              │
│  Select targets to simulate failure:         │
│  ┌──────────────────────────────────────┐   │
│  │ 🔧 core-switch-01          [✕ remove]│   │
│  │ 🔗 core-sw-01 ↔ fw-01     [✕ remove]│   │
│  └──────────────────────────────────────┘   │
│  [+ Add device] [+ Add link] [Select on map]│
│                                              │
│  [▶ Run Simulation]                          │
│                                              │
│  ═══ Results ════════════════════════════    │
│                                              │
│  Blast Radius: 47 devices (19%)              │
│  ████████████████████░░░░░░░░░░░░░           │
│                                              │
│  Disconnected:     38 devices                │
│  Degraded:          9 devices                │
│  Services down:     DNS, DHCP                │
│  Risk delta:        +0.23 (6.2 → 8.5)       │
│                                              │
│  ─── Affected Devices (top 10) ───────────  │
│  server-db-01      💀 Disconnected           │
│  server-app-01     💀 Disconnected           │
│  server-web-01     ⚠️  Degraded (alt route)  │
│  ...                                         │
│  [View all 47]                               │
│                                              │
│  ─── Recommendations ─────────────────────  │
│  1. Add redundant uplink from core-sw-01    │
│     to fw-02 (reduces blast radius to 3)    │
│  2. Deploy standby DNS on separate switch   │
│     (estimated cost: $800)                   │
│                                              │
│  [Generate Full Report]  [Clear Simulation]  │
└──────────────────────────────────────────────┘
```

When simulation runs, the graph canvas overlays impact visualization:
- Removed nodes/edges: Red X overlay, 50% opacity
- Disconnected nodes: Solid red glow, desaturated
- Degraded nodes: Amber glow, pulsing
- Unaffected nodes: Faint green tint
- Alternative paths: highlighted in green dashed lines
- A 1-second animation transitions from normal view to impact view

### Risk Heatmap View

Accessible from sidebar. Shows a treemap or grid visualization of subnets/VLANs colored by aggregate risk.

```
┌────────────────────────────────────────────┐
│  VLAN 10 - Engineering     VLAN 20 - Corp  │
│  ┌────────────────────┐   ┌──────────────┐ │
│  │                    │   │              │ │
│  │   Risk: 0.72       │   │  Risk: 0.34  │ │
│  │   48 devices       │   │  120 devices │ │
│  │   2 SPOFs          │   │  0 SPOFs     │ │
│  │                    │   │              │ │
│  └────────────────────┘   └──────────────┘ │
│  VLAN 30 - DMZ             VLAN 50 - IoT   │
│  ┌──────────────┐         ┌──────────────┐ │
│  │ Risk: 0.89   │         │ Risk: 0.45   │ │
│  │ 12 devices   │         │ 67 devices   │ │
│  │ 1 SPOF       │         │ 1 SPOF       │ │
│  └──────────────┘         └──────────────┘ │
└────────────────────────────────────────────┘
```

- Box size proportional to device count
- Background color follows risk gradient
- Click a box to filter the graph to that VLAN/subnet

### Timeline View

Sidebar-accessible. Shows topology changes over time as a vertical timeline.

```
┌─ Topology Timeline ──── [24h ▾] ─── [✕] ─┐
│                                            │
│  ● 14:23 ─── New device detected ──────── │
│  │  Unknown device on VLAN 50              │
│  │  MAC: FF:EE:DD:CC:BB:AA                │
│  │                                         │
│  ● 14:10 ─── Link status change ───────── │
│  │  core-sw-01 ↔ dist-sw-03               │
│  │  Status: active → flapping              │
│  │                                         │
│  ● 12:00 ─── Scan completed ───────────── │
│  │  Full scan • 247 devices found          │
│  │  Δ +3 devices, +5 connections           │
│  │                                         │
│  ● 08:15 ─── Configuration drift ──────── │
│  │  fw-01: 2 new firewall rules added      │
│  │  [View diff]                            │
│  │                                         │
│  ● 00:00 ─── Snapshot saved ───────────── │
│  │  Risk score: 5.8/10                     │
│                                            │
└────────────────────────────────────────────┘
```

### Sidebar Navigation

60px collapsed, 220px expanded. Dark background (`--bg-primary`).

Icons + labels:
1. 🗺️ Topology (main graph view)
2. 📊 Dashboard (metrics overview)
3. 🔍 Scan (trigger/manage scans)
4. ⚡ Simulate (failure simulation)
5. 🔔 Alerts (alert feed)
6. 📈 Heatmap (risk heatmap)
7. 📋 Timeline (change history)
8. 📄 Reports (AI-generated reports)
9. ⚙️ Settings (scan schedules, thresholds, agent mode)

Active item has a left accent bar (`--node-switch` blue) and brighter text.

### Command Palette (Cmd+K)

Modal overlay with search input. Searches across:
- Device names/IPs/MACs
- Alert titles
- Actions ("simulate failure", "run scan", "show SPOFs")
- Navigation ("go to heatmap", "open settings")

Results grouped by category with keyboard navigation.

### Scan Control Panel

Accessed from sidebar "Scan" item.

```
┌─ Network Scanner ──────────────────────────┐
│                                             │
│  ─── Quick Scan ─────────────────────────  │
│  Target: [192.168.0.0/16        ] [Scan]   │
│  Intensity:  ○ Light  ● Normal  ○ Deep     │
│                                             │
│  ─── Scheduled Scans ────────────────────  │
│  Full scan    Every 6 hours    [Edit]       │
│  Passive      Continuous       [Pause]      │
│  SNMP poll    Every 30 min     [Edit]       │
│                                             │
│  ─── Current Scan ───────────────────────  │
│  ████████████████░░░░░░░  67% Port Scan    │
│  147/247 devices scanned • ETA: 2m 10s     │
│                                             │
│  ─── Recent Scans ───────────────────────  │
│  14:23  Full scan    247 devices  4m 23s   │
│  08:15  SNMP poll    52 devices   1m 02s   │
│  02:00  Full scan    244 devices  4m 18s   │
└─────────────────────────────────────────────┘
```

### AI Resilience Report

Full-page view triggered from Reports sidebar item or "Generate Full Report" in simulation panel. The backend calls Claude API to synthesize graph analysis into readable prose.

```
┌─ Resilience Report ─── Generated 14:30 ──────────────────┐
│                                                           │
│  Network Resilience Assessment                            │
│  ═══════════════════════════                              │
│                                                           │
│  Overall Score: 6.2/10 (Moderate Risk)                   │
│  ████████████████████████░░░░░░░░░░░░░                    │
│                                                           │
│  Executive Summary                                        │
│  Your network has 3 critical single points of failure     │
│  that could disconnect up to 47 devices (19% of your      │
│  infrastructure). The most urgent issue is...             │
│                                                           │
│  Critical Findings                                        │
│  1. Core switch core-sw-01 has no redundant uplink...    │
│  2. Single DNS server running on aging hardware...        │
│  3. Disabled fiber link between buildings provides...     │
│                                                           │
│  Prioritized Recommendations                              │
│  [Table: Action | Est. Cost | Risk Reduction | Priority]  │
│                                                           │
│  [Export PDF]  [Share]  [Regenerate]                       │
└───────────────────────────────────────────────────────────┘
```

### Responsive Behavior
- **≥1440px**: Full layout as described (graph + side panel)
- **1024-1439px**: Side panel becomes overlay drawer instead of permanent sidebar
- **<1024px**: Not a priority target. Show a "best viewed on desktop" message, but allow basic graph interaction with stacked panels below.

### Animations & Transitions
- Panel open/close: 200ms slide + fade
- Graph layout change: 500ms animated node repositioning (Cytoscape built-in)
- New device appearance: Blue pulse ring expanding 3x then fading (1.5s)
- Alert arrival: Slide down from top of feed + brief yellow flash (300ms)
- Simulation overlay: 1s crossfade from normal to impact view
- Layer switch: 200ms crossfade
- Node hover: 150ms scale to 1.1x + shadow elevation
- Risk halo: Continuous slow pulse (2s cycle) for high-risk nodes

### Accessibility
- All interactive elements keyboard-navigable
- ARIA labels on graph nodes (device name + type + status)
- Color-blind safe: all status colors have distinct icons as well (checkmark, X, warning triangle)
- Focus indicators on all interactive elements
- Screen reader announces alert arrivals

---

## Implementation Phases

### Phase 1: Core Infrastructure (MVP)
Build the skeleton that everything else hangs on.

1. Set up monorepo with frontend (Vite + React + TS) and backend (FastAPI)
2. Docker Compose with Neo4j + Redis
3. Basic Cytoscape.js graph rendering with static mock data
4. Neo4j schema + CRUD operations for devices and connections
5. REST API: `/topology`, `/devices/{id}`
6. WebSocket connection for real-time updates
7. AppShell layout with sidebar navigation
8. DeviceInspector panel (opens on node click)
9. Basic dark theme with color system applied

**Deliverable**: App that renders a network graph from Neo4j data with clickable device details.

### Phase 2: Scanning Engine
Actually discover real network devices.

1. Active scanner service wrapping python-nmap
2. Passive scanner with Scapy (ARP, DNS, DHCP listeners)
3. SNMP poller for switch port mapping and device details
4. Scan coordinator that orchestrates phases and deduplicates results
5. Graph builder service that upserts discoveries into Neo4j
6. Scan control panel UI (trigger scan, view progress, history)
7. Celery tasks for scheduled scans
8. WebSocket broadcast of scan progress + new device events
9. "New device" pulse animation on graph

**Deliverable**: App that scans a real network and populates the graph automatically.

### Phase 3: Graph Intelligence
Find weaknesses and simulate failures.

1. SPOF detector using graph centrality algorithms (betweenness, articulation points)
2. Failure simulator: remove nodes/edges from graph copy, calculate disconnected components
3. Path analyzer for critical paths and bottleneck identification
4. Resilience scorer (composite risk per device and global)
5. Simulation panel UI with target selection and impact visualization
6. Simulation overlay on graph canvas (affected/disconnected/safe coloring)
7. Metrics bar with live stats from graph analysis
8. Risk halos on high-risk nodes

**Deliverable**: App identifies SPOFs, simulates failures with visual impact, and scores risk.

### Phase 4: Anomaly Detection & Alerts
Detect suspicious changes and notify.

1. Anomaly detector: IsolationForest on topology change vectors
2. Alert model and SQLite storage
3. Alert feed panel UI with real-time WebSocket updates
4. Alert severity classification logic
5. Topology snapshot system for diffing
6. Timeline view UI
7. Configuration drift detection (compare device configs over time)
8. Command palette for quick navigation

**Deliverable**: App detects anomalies, streams alerts in real-time, and shows topology history.

### Phase 5: AI & Reporting
Make it speak human.

1. Claude API integration for natural language report generation
2. Resilience report view with executive summary + prioritized recommendations
3. Risk heatmap view (treemap by VLAN/subnet)
4. Dependency matrix view
5. Node2Vec embeddings for device behavior profiling
6. GNN failure prediction model (PyTorch Geometric)
7. Scan schedule optimization with basic RL
8. PDF export for reports

**Deliverable**: Full-featured app with AI-generated reports, predictive analysis, and comprehensive visualization.

---

## Environment Variables (.env)

```
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme

# Redis
REDIS_URL=redis://localhost:6379/0

# SQLite
SQLITE_PATH=./data/mapper.db

# Scanning
SCAN_DEFAULT_RANGE=192.168.0.0/16
SCAN_RATE_LIMIT=1000                 # packets/sec for active scan
SCAN_PASSIVE_INTERFACE=eth0
SNMP_COMMUNITY=public
SNMP_VERSION=2c

# Claude API
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# App
APP_HOST=0.0.0.0
APP_PORT=8000
WS_HEARTBEAT_INTERVAL=30
LOG_LEVEL=INFO

# Agent Mode
AGENT_MODE=alert                     # alert | interactive | autonomous
```

---

## Docker Compose

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    cap_add: [NET_RAW, NET_ADMIN]     # Required for scapy/nmap
    network_mode: host                 # Required to see LAN traffic
    depends_on: [neo4j, redis]
    env_file: .env

  neo4j:
    image: neo4j:5-community
    ports: ["7474:7474", "7687:7687"]
    environment:
      NEO4J_AUTH: neo4j/changeme
    volumes: ["neo4j_data:/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  neo4j_data:
```

---

## Key Implementation Notes for Claude Code

1. **Start with Phase 1.** Get the graph rendering and basic API working before adding scanning. Use realistic mock data (generate 50-100 devices with varied types, connections, and risk scores) so the UI can be fully developed before real scanning works.

2. **Cytoscape.js config is critical.** Spend time on `cytoscape-config.ts` — node styles, edge styles, layout options, and interaction handlers. The graph must feel responsive and polished. Use the cola layout as default with `nodeSpacing: 40`, `edgeLength: 200`, and `animate: true`.

3. **The DeviceInspector is the most-used panel.** Make it scroll well, load fast, and show data in a scannable layout. Use sections with thin dividers, not cards-in-cards.

4. **WebSocket events should update the Zustand store**, which Cytoscape.js observes. Don't re-render the whole graph — use `cy.add()`, `cy.remove()`, and element data updates for incremental changes.

5. **Nmap requires root/sudo.** The Docker container needs `NET_RAW` and `NET_ADMIN` capabilities. For development without Docker, scanning tests should use pre-captured results.

6. **Neo4j Cypher queries for graph analysis** are much faster than pulling the whole graph into Python. Use Cypher for articulation point detection, shortest paths, and component analysis where possible.

7. **The simulation overlay is a Cytoscape.js class toggle**, not a re-render. Define `.simulated-removed`, `.simulated-affected`, `.simulated-safe` classes in the stylesheet and toggle them on/off.

8. **Rate limit everything that touches the network.** Active scanning defaults to 1000 pps. Passive scanning is always safe. SNMP polling should be staggered.

9. **Generate mock data function**: Create `backend/app/services/mock_data.py` that generates a realistic corporate network: 2 firewalls, 4 core switches, 8 distribution switches, 20 access switches, 50 servers, 150 workstations, 10 APs, assorted IoT. Wire them in a realistic tree topology with some intentional SPOFs.
