# Architecture Overview

## System Architecture

Network Topology Mapper follows a modern, scalable architecture with clear separation between frontend, backend, and data layers.

```
┌──────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                      │
│  ┌──────────┐  ┌───────────┐  ┌─────────┐  ┌─────────────┐  │
│  │ Graph    │  │ Device    │  │ Alert   │  │ Simulation  │  │
│  │ Canvas   │  │ Inspector │  │ Feed    │  │ Panel       │  │
│  └──────────┘  └───────────┘  └─────────┘  └─────────────┘  │
├──────────────────────────────────────────────────────────────┤
│               WebSocket + REST API (FastAPI)                  │
├──────────────────────────────────────────────────────────────┤
│                     Backend Services                          │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Scanner   │  │ Graph     │  │ Anomaly  │  │ AI       │  │
│  │ Engine    │  │ Analyzer  │  │ Detector │  │ Reports  │  │
│  └───────────┘  └───────────┘  └──────────┘  └──────────┘  │
├──────────────────────────────────────────────────────────────┤
│  Neo4j (Graph DB) │ Redis (Cache/PubSub) │ SQLite (Metadata)│
└──────────────────────────────────────────────────────────────┘
```

## Frontend Architecture

### Component Hierarchy

```
App
├── AppShell
│   ├── Sidebar (navigation)
│   ├── CommandPalette (Cmd+K search)
│   └── Main Content
│       ├── MetricsBar (top KPIs)
│       ├── NetworkCanvas (Cytoscape.js graph)
│       │   ├── GraphControls
│       │   ├── LayerToggle
│       │   ├── MiniMap
│       │   └── NodeTooltip
│       └── Side Panel (conditional)
│           ├── DeviceInspector
│           ├── AlertFeed
│           ├── SimulationPanel
│           └── ResilienceReport
```

### State Management (Zustand)

**topologyStore.ts**
- Devices (nodes)
- Connections (edges)
- Selected device
- Graph layout mode
- Filter state

**filterStore.ts**
- Active filters (device type, VLAN, risk level)
- Search query
- Layer selection (physical/logical/application)

**settingsStore.ts**
- User preferences
- Theme settings
- Scan schedules

### Data Flow

1. **Initial Load**:
   ```
   Component Mount → useTopology hook → API call → Store update → Re-render
   ```

2. **Real-time Updates**:
   ```
   Backend Event → WebSocket → useWebSocket hook → Store update → Cytoscape update
   ```

3. **User Interaction**:
   ```
   User Click → Event Handler → Store update → Component re-render + API call (if needed)
   ```

### Cytoscape.js Integration

The graph is the core of the application. Key integration points:

**Initialization** (NetworkCanvas.tsx):
```typescript
const cy = cytoscape({
  container: containerRef.current,
  style: cytoscapeStylesheet,
  layout: { name: 'preset' },  // Layout runs after data is added
});
// Default layout is dagre (hierarchical, top-down)
```

**Node Design**:
- Circular ellipse nodes with device-type colored fills
- Size tiers: infrastructure 50px, servers 44px, endpoints 36px
- Centered SVG icons with dark contrasting strokes
- Labels below nodes in Inter/system-ui font

**Edge Design**:
- Smooth bezier curves (replaced taxi/Manhattan routing)
- Connection-type styling (solid/dashed/dotted per type)
- Bandwidth-scaled widths

**Event Handling**:
- `cy.on('tap', 'node', ...)` for device selection
- `cy.on('mouseover', 'node', ...)` for tooltip + neighborhood highlighting
- `cy.on('mouseout', 'node', ...)` to clear highlighting
- `cy.on('mouseover', 'edge', ...)` for edge tooltip + hover feedback
- `cy.on('dbltap', 'node', ...)` for zoom-to-neighborhood animation

## Backend Architecture

### Service Layer Pattern

```
Request → Router → Service → Database
```

Each router delegates to specialized services:

**Routers** (`app/routers/`):
- `topology.py` - Topology and device endpoints
- `scans.py` - Scan management
- `simulation.py` - Failure simulation
- `alerts.py` - Alert management
- `reports.py` - AI report generation

**Services** (`app/services/`):
- Independent, testable business logic
- No direct HTTP handling
- Return Pydantic models

### Scanning Pipeline

```
Scan Trigger (API)
    ↓
Scan Coordinator
    ↓
┌───────────┬──────────────┬──────────────┐
│  Active   │   Passive    │    SNMP      │
│  Scanner  │   Scanner    │    Poller    │
└─────┬─────┴──────┬───────┴──────┬───────┘
      ↓            ↓              ↓
      └────────────┼──────────────┘
                   ↓
           Graph Builder
                   ↓
              Neo4j Update
                   ↓
           WebSocket Broadcast
```

**Active Scanner** (`active_scanner.py`):
- Uses python-nmap wrapper
- Discovers devices via ICMP/TCP/UDP probes
- Identifies open ports and services
- Configurable intensity (light/normal/deep)

**Passive Scanner** (`passive_scanner.py`):
- Scapy-based packet capture
- Monitors ARP, DNS, DHCP traffic
- No impact on network
- Runs continuously

**SNMP Poller** (`snmp_poller.py`):
- Queries switch port tables
- Retrieves vendor/model information
- Discovers VLAN configurations
- Maps physical connections

**Graph Builder** (`graph_builder.py`):
- Correlates scan results
- Deduplicates devices (by MAC/IP)
- Creates/updates Neo4j nodes and relationships
- Triggers alert generation

### Graph Analysis Engine

**SPOF Detector** (`spof_detector.py`):
```python
# Uses NetworkX articulation points
articulation_points = nx.articulation_points(graph)
# Devices whose removal disconnects the network
```

**Failure Simulator** (`failure_simulator.py`):
```python
# Creates graph copy
sim_graph = graph.copy()
# Removes specified nodes/edges
sim_graph.remove_nodes(target_nodes)
# Calculates impact
disconnected = nx.number_connected_components(sim_graph) - 1
affected_devices = [...]
```

**Path Analyzer** (`path_analyzer.py`):
- Shortest path calculations
- Critical path identification
- Bottleneck detection using betweenness centrality

**Resilience Scorer** (`resilience_scorer.py`):
- Per-device risk: based on redundancy, criticality, dependencies
- Global risk: aggregated network health score
- Uses composite metrics

### Real-time Event System

**Event Bus** (`event_bus.py`):
```
Service generates event → Redis pub/sub → Event bus → WebSocket manager → Clients
```

Event types:
- `device_added` - New device discovered
- `device_removed` - Device went offline
- `device_updated` - Device properties changed
- `connection_change` - Link status changed
- `alert` - New alert generated
- `scan_progress` - Scan status update

**WebSocket Manager** (`ws_manager.py`):
- Maintains active WebSocket connections
- Broadcasts events to all connected clients
- Handles heartbeat/keepalive
- Graceful reconnection

### Background Tasks (Celery)

**Scheduled Tasks** (`scan_tasks.py`):
- `periodic_full_scan` - Full network scan every 6 hours
- `periodic_snmp_poll` - SNMP polling every 30 minutes
- `snapshot_topology` - Daily topology snapshot for history

**Analysis Tasks** (`analysis_tasks.py`):
- `run_spof_detection` - SPOF analysis after topology changes
- `calculate_risk_scores` - Risk score recalculation
- `detect_anomalies` - ML-based anomaly detection

## Data Layer

### Neo4j Schema

**Device Node**:
```cypher
(:Device {
  id: UUID,
  ip: String,
  mac: String,
  hostname: String,
  device_type: Enum,
  vendor: String,
  model: String,
  os: String,
  open_ports: [Int],
  services: [String],
  first_seen: DateTime,
  last_seen: DateTime,
  vlan_ids: [Int],
  subnet: String,
  risk_score: Float,
  criticality: Enum,
  status: Enum
})
```

**Relationships**:
```cypher
(:Device)-[:CONNECTS_TO {
  connection_type: String,
  bandwidth: String,
  latency_ms: Float,
  packet_loss_pct: Float,
  is_redundant: Boolean,
  status: String
}]->(:Device)

(:Device)-[:DEPENDS_ON {
  dependency_type: String,
  service_port: Int,
  criticality: String
}]->(:Device)

(:Device)-[:MEMBER_OF]->(:VLAN)
```

**Query Patterns**:
```cypher
// Get device with all connections
MATCH (d:Device {id: $id})
OPTIONAL MATCH (d)-[c:CONNECTS_TO]->(other)
RETURN d, collect({rel: c, device: other})

// Find articulation points
MATCH (d:Device)
MATCH path = (d)-[:CONNECTS_TO*]-(other:Device)
WITH d, count(DISTINCT other) as connections
WHERE connections > 2
RETURN d
ORDER BY connections DESC
```

### Redis Usage

**Caching**:
- `topology:full` - Full topology cache (TTL: 60s)
- `device:{id}` - Individual device cache (TTL: 300s)
- `scan:{id}:status` - Active scan status

**Pub/Sub Channels**:
- `topology:events` - Topology change events
- `alerts:new` - New alert notifications
- `scans:progress` - Scan progress updates

### SQLite Schema

```sql
-- Scan history
CREATE TABLE scans (
    id TEXT PRIMARY KEY,
    scan_type TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    target_range TEXT,
    devices_found INTEGER,
    config JSON
);

-- Alert log
CREATE TABLE alerts (
    id TEXT PRIMARY KEY,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    device_id TEXT,
    details JSON,
    created_at TIMESTAMP,
    status TEXT DEFAULT 'open'
);

-- Topology snapshots (for timeline/diff)
CREATE TABLE topology_snapshots (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    device_count INTEGER,
    connection_count INTEGER,
    risk_score FLOAT,
    snapshot_data JSON
);
```

## API Design

### RESTful Principles

- Resource-based URLs: `/api/devices`, `/api/scans`
- HTTP verbs: GET (read), POST (create), PATCH (update), DELETE (remove)
- Pydantic models for request/response validation
- Consistent error responses

### WebSocket Protocol

**Client → Server**:
```json
{
  "type": "subscribe",
  "channels": ["topology:events", "alerts:new"]
}
```

**Server → Client**:
```json
{
  "type": "device_added",
  "data": {
    "id": "uuid",
    "device_type": "switch",
    ...
  },
  "timestamp": "2026-02-11T10:30:00Z"
}
```

## Security Architecture

### Authentication & Authorization
(Not yet implemented - placeholder for future)

- JWT-based authentication
- Role-based access control (RBAC)
- API key management for integrations

### Network Security

- Docker network isolation
- Redis and Neo4j authentication required
- SNMP community string protection
- Rate limiting on scan endpoints

### Data Privacy

- No sensitive data logged
- Scan results contain network metadata only
- Configurable data retention policies

## Scalability Considerations

### Horizontal Scaling

- **Frontend**: Static assets served via CDN
- **Backend**: Stateless API servers behind load balancer
- **Celery Workers**: Multiple workers for task parallelization
- **Redis**: Redis Cluster for high availability
- **Neo4j**: Neo4j Causal Cluster for read replicas

### Performance Optimization

- **Caching**: Redis caching for frequently accessed data
- **Database Indexing**: Neo4j indexes on device IDs, IPs, MACs
- **Lazy Loading**: Frontend loads topology in chunks for large networks
- **Incremental Updates**: WebSocket sends only changed data
- **Query Optimization**: Cypher query optimization for graph traversals

### Monitoring

- **Metrics**: Prometheus metrics exposed at `/metrics`
- **Logging**: Structured JSON logging
- **Tracing**: Distributed tracing with OpenTelemetry (future)

## Development Workflow

```
Developer makes changes
    ↓
Local testing
    ↓
Git commit
    ↓
CI/CD pipeline
    ↓
Automated tests
    ↓
Build Docker images
    ↓
Deploy to staging
    ↓
Integration tests
    ↓
Manual approval
    ↓
Deploy to production
```

## Technology Choices Rationale

**Why Cytoscape.js?**
- Mature, performant graph rendering
- Rich plugin ecosystem (layouts, extensions)
- Good TypeScript support

**Why Neo4j?**
- Native graph database for complex relationship queries
- Built-in graph algorithms
- Cypher query language optimized for graphs

**Why FastAPI?**
- Modern async Python framework
- Automatic API documentation (OpenAPI)
- Excellent performance
- Built-in WebSocket support

**Why Zustand?**
- Lightweight state management
- Simple API, no boilerplate
- Good TypeScript integration

**Why Redis?**
- Fast caching layer
- Pub/sub for real-time events
- Celery broker support

## Future Architecture Improvements

- **GraphQL API** for more flexible frontend queries
- **gRPC** for inter-service communication
- **Kafka** for event streaming at scale
- **PostgreSQL** to replace SQLite for production
- **Kubernetes** deployment manifests
- **Service mesh** for observability
