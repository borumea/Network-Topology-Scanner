# API Documentation

Complete API reference for the Network Topology Mapper backend.

**Base URL**: `http://localhost:8000/api`

**API Version**: 1.0

---

## Table of Contents

- [Authentication](#authentication)
- [Topology Endpoints](#topology-endpoints)
- [Device Endpoints](#device-endpoints)
- [Scan Endpoints](#scan-endpoints)
- [Simulation Endpoints](#simulation-endpoints)
- [Alert Endpoints](#alert-endpoints)
- [Report Endpoints](#report-endpoints)
- [Snapshot Endpoints](#snapshot-endpoints)
- [Settings Endpoints](#settings-endpoints)
- [Scan Optimizer Endpoints](#scan-optimizer-endpoints)
- [WebSocket](#websocket)
- [Error Responses](#error-responses)

---

## Authentication

Currently, the API does not require authentication. Future versions will implement JWT-based authentication.

---

## Topology Endpoints

### Get Full Topology

Retrieve the complete network topology with optional filters.

```http
GET /api/topology
```

**Query Parameters**:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `layer` | string | Filter by layer | `physical`, `logical`, `application` |
| `vlan` | integer | Filter by VLAN ID | `10` |
| `subnet` | string | Filter by subnet | `192.168.1.0/24` |
| `device_type` | string | Filter by device type | `switch`, `router`, `server` |
| `risk_min` | float | Minimum risk score | `0.5` |
| `risk_max` | float | Maximum risk score | `0.9` |
| `status` | string | Device status | `online`, `offline`, `degraded` |

**Response** (`200 OK`):

```json
{
  "nodes": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "ip": "192.168.1.1",
      "mac": "AA:BB:CC:DD:EE:FF",
      "hostname": "core-switch-01",
      "device_type": "switch",
      "vendor": "Cisco",
      "model": "Catalyst 9300",
      "os": "IOS-XE 17.6",
      "open_ports": [22, 80, 443, 161],
      "services": ["ssh", "http", "https", "snmp"],
      "first_seen": "2026-01-15T09:23:00Z",
      "last_seen": "2026-02-11T10:30:00Z",
      "vlan_ids": [10, 20, 30],
      "subnet": "192.168.1.0/24",
      "risk_score": 0.73,
      "criticality": "high",
      "status": "online"
    }
  ],
  "edges": [
    {
      "id": "edge-uuid",
      "source": "device-uuid-1",
      "target": "device-uuid-2",
      "connection_type": "ethernet",
      "bandwidth": "10Gbps",
      "latency_ms": 0.5,
      "packet_loss_pct": 0.01,
      "is_redundant": false,
      "status": "active"
    }
  ],
  "metadata": {
    "total_devices": 247,
    "total_connections": 412,
    "avg_risk_score": 0.52,
    "spof_count": 3
  }
}
```

### Get Topology Statistics

Get aggregate statistics about the network topology.

```http
GET /api/topology/stats
```

**Response** (`200 OK`):

```json
{
  "total_devices": 247,
  "devices_by_type": {
    "switch": 32,
    "router": 6,
    "server": 58,
    "workstation": 142,
    "ap": 9
  },
  "total_connections": 412,
  "connections_by_type": {
    "ethernet": 380,
    "fiber": 24,
    "wireless": 8
  },
  "avg_risk_score": 0.52,
  "risk_distribution": {
    "low": 120,
    "medium": 95,
    "high": 28,
    "critical": 4
  },
  "spof_count": 3,
  "online_devices": 243,
  "offline_devices": 4
}
```

---

## Device Endpoints

### Get Device Details

Retrieve detailed information about a specific device.

```http
GET /api/devices/{device_id}
```

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | UUID | Device identifier |

**Response** (`200 OK`):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "ip": "192.168.1.1",
  "mac": "AA:BB:CC:DD:EE:FF",
  "hostname": "core-switch-01",
  "device_type": "switch",
  "vendor": "Cisco",
  "model": "Catalyst 9300",
  "os": "IOS-XE 17.6",
  "open_ports": [22, 80, 443, 161],
  "services": ["ssh", "http", "https", "snmp"],
  "first_seen": "2026-01-15T09:23:00Z",
  "last_seen": "2026-02-11T10:30:00Z",
  "vlan_ids": [10, 20, 30],
  "subnet": "192.168.1.0/24",
  "location": "Building A, Rack 3",
  "risk_score": 0.73,
  "risk_factors": [
    "Single uplink to core",
    "No redundant power supply"
  ],
  "criticality": "high",
  "is_gateway": true,
  "status": "online"
}
```

### Get Device Connections

Get all connections for a specific device.

```http
GET /api/devices/{device_id}/connections
```

**Response** (`200 OK`):

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "incoming": [
    {
      "connection_id": "edge-uuid-1",
      "from_device": {
        "id": "device-uuid-2",
        "hostname": "dist-switch-01",
        "device_type": "switch"
      },
      "connection_type": "fiber",
      "bandwidth": "10Gbps",
      "status": "active"
    }
  ],
  "outgoing": [
    {
      "connection_id": "edge-uuid-2",
      "to_device": {
        "id": "device-uuid-3",
        "hostname": "access-switch-01",
        "device_type": "switch"
      },
      "connection_type": "ethernet",
      "bandwidth": "1Gbps",
      "status": "active"
    }
  ]
}
```

### Get Device Dependencies

Get upstream and downstream dependencies for a device.

```http
GET /api/devices/{device_id}/dependencies
```

**Response** (`200 OK`):

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "depends_on": [
    {
      "device_id": "device-uuid-firewall",
      "hostname": "fw-01",
      "device_type": "firewall",
      "dependency_type": "gateway",
      "criticality": "critical"
    }
  ],
  "depended_by": [
    {
      "device_id": "device-uuid-server",
      "hostname": "web-server-01",
      "device_type": "server",
      "dependency_type": "network",
      "criticality": "high"
    }
  ],
  "dependency_count": {
    "upstream": 1,
    "downstream": 47
  }
}
```

---

## Scan Endpoints

### Trigger a Scan

Start a new network scan.

```http
POST /api/scans
```

**Request Body**:

```json
{
  "type": "full",
  "target": "192.168.0.0/16",
  "intensity": "normal",
  "options": {
    "active_scan": true,
    "snmp_poll": true,
    "port_scan": true
  }
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | `full`, `active`, `passive`, `snmp` |
| `target` | string | Yes | CIDR range or `all` |
| `intensity` | string | No | `light`, `normal`, `deep` (default: `normal`) |
| `options` | object | No | Scan configuration options |

**Response** (`201 Created`):

```json
{
  "scan_id": "scan-uuid",
  "status": "running",
  "started_at": "2026-02-11T10:35:00Z",
  "estimated_duration": "4m 30s"
}
```

### List Scans

Get scan history with filtering options.

```http
GET /api/scans
```

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `running`, `completed`, `failed` |
| `type` | string | Filter by scan type |
| `limit` | integer | Max results (default: 50) |
| `offset` | integer | Pagination offset |

**Response** (`200 OK`):

```json
{
  "scans": [
    {
      "id": "scan-uuid",
      "scan_type": "full",
      "status": "completed",
      "started_at": "2026-02-11T10:00:00Z",
      "completed_at": "2026-02-11T10:04:23Z",
      "target_range": "192.168.0.0/16",
      "devices_found": 247,
      "new_devices": 3
    }
  ],
  "total": 142,
  "limit": 50,
  "offset": 0
}
```

### Get Scan Status

Get detailed status of a specific scan.

```http
GET /api/scans/{scan_id}
```

**Response** (`200 OK`):

```json
{
  "id": "scan-uuid",
  "scan_type": "full",
  "status": "running",
  "started_at": "2026-02-11T10:35:00Z",
  "progress": {
    "percent": 67,
    "phase": "port_scan",
    "current_target": "192.168.1.142",
    "devices_scanned": 147,
    "devices_found": 12,
    "eta": "2m 10s"
  },
  "config": {
    "target": "192.168.0.0/16",
    "intensity": "normal",
    "options": {}
  }
}
```

### Cancel Scan

Stop a running scan.

```http
DELETE /api/scans/{scan_id}
```

**Response** (`200 OK`):

```json
{
  "scan_id": "scan-uuid",
  "status": "cancelled",
  "message": "Scan cancelled successfully"
}
```

---

## Simulation Endpoints

### Simulate Device/Link Failure

Simulate the removal of devices or connections and analyze impact.

```http
POST /api/simulate/failure
```

**Request Body**:

```json
{
  "remove_nodes": [
    "device-uuid-1",
    "device-uuid-2"
  ],
  "remove_edges": [
    "edge-uuid-1"
  ]
}
```

**Response** (`200 OK`):

```json
{
  "simulation_id": "sim-uuid",
  "impact": {
    "blast_radius": 47,
    "blast_radius_pct": 19.0,
    "disconnected_devices": [
      {
        "id": "device-uuid-3",
        "hostname": "server-db-01",
        "device_type": "server",
        "impact_level": "critical"
      }
    ],
    "degraded_devices": [
      {
        "id": "device-uuid-4",
        "hostname": "server-web-01",
        "device_type": "server",
        "impact_level": "medium",
        "alternative_paths": 1
      }
    ],
    "affected_services": ["dns", "dhcp"],
    "risk_delta": 0.23,
    "new_risk_score": 8.5
  },
  "recommendations": [
    {
      "priority": "high",
      "action": "Add redundant uplink from core-sw-01 to fw-02",
      "estimated_cost": "$2,500",
      "risk_reduction": 0.15
    }
  ]
}
```

### Get SPOFs

List all detected single points of failure.

```http
GET /api/simulate/spof
```

**Response** (`200 OK`):

```json
{
  "spofs": [
    {
      "device_id": "device-uuid-1",
      "hostname": "core-switch-01",
      "device_type": "switch",
      "blast_radius": 47,
      "affected_services": ["dns", "dhcp"],
      "criticality": "critical",
      "mitigation": "Add redundant device or connection"
    }
  ],
  "total_count": 3,
  "critical_count": 1,
  "high_count": 2
}
```

### Get Resilience Score

Get overall network resilience assessment.

```http
GET /api/simulate/resilience
```

**Response** (`200 OK`):

```json
{
  "overall_score": 6.2,
  "risk_level": "moderate",
  "breakdown": {
    "topology_health": 7.1,
    "redundancy_level": 5.3,
    "device_reliability": 6.8,
    "configuration_score": 6.0
  },
  "spof_count": 3,
  "redundant_paths_pct": 42.5,
  "avg_device_risk": 0.52,
  "trends": {
    "7_day_delta": -0.3,
    "30_day_delta": 0.1
  }
}
```

---

## Alert Endpoints

### List Alerts

Get alerts with filtering options.

```http
GET /api/alerts
```

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `severity` | string | `critical`, `high`, `medium`, `low`, `info` |
| `status` | string | `open`, `acknowledged`, `resolved`, `dismissed` |
| `type` | string | Alert type filter |
| `limit` | integer | Max results |
| `offset` | integer | Pagination offset |

**Response** (`200 OK`):

```json
{
  "alerts": [
    {
      "id": "alert-uuid",
      "alert_type": "new_device",
      "severity": "critical",
      "title": "New device on restricted VLAN 50",
      "description": "Unknown device detected on restricted VLAN",
      "device_id": "device-uuid",
      "details": {
        "mac": "FF:EE:DD:CC:BB:AA",
        "ip": "192.168.50.142",
        "vlan": 50
      },
      "created_at": "2026-02-11T10:27:00Z",
      "status": "open"
    }
  ],
  "total": 47,
  "unread": 12
}
```

### Update Alert Status

Acknowledge, resolve, or dismiss an alert.

```http
PATCH /api/alerts/{alert_id}
```

**Request Body**:

```json
{
  "status": "acknowledged",
  "notes": "Investigating with security team"
}
```

**Response** (`200 OK`):

```json
{
  "id": "alert-uuid",
  "status": "acknowledged",
  "acknowledged_at": "2026-02-11T10:45:00Z",
  "notes": "Investigating with security team"
}
```

### Get Alert Stream (SSE)

Subscribe to real-time alert stream via Server-Sent Events.

```http
GET /api/alerts/stream
```

**Response** (SSE stream):

```
data: {"id": "alert-uuid", "alert_type": "topology_change", ...}

data: {"id": "alert-uuid-2", "alert_type": "link_flapping", ...}
```

---

## Report Endpoints

### Get AI Resilience Report

Generate an AI-powered natural language resilience report.

```http
GET /api/reports/resilience
```

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `regenerate` | boolean | Force regeneration (default: false) |

**Response** (`200 OK`):

```json
{
  "report_id": "report-uuid",
  "generated_at": "2026-02-11T11:00:00Z",
  "executive_summary": "Your network has 3 critical single points of failure that could disconnect up to 47 devices (19% of your infrastructure)...",
  "overall_score": 6.2,
  "risk_level": "moderate",
  "critical_findings": [
    {
      "title": "Core switch lacks redundancy",
      "description": "The core-sw-01 device has no redundant uplink...",
      "priority": "critical",
      "estimated_impact": "47 devices disconnected"
    }
  ],
  "recommendations": [
    {
      "title": "Add redundant uplink",
      "description": "Install second fiber connection...",
      "priority": "high",
      "estimated_cost": "$2,500",
      "risk_reduction": 0.15,
      "implementation_time": "2-4 hours"
    }
  ],
  "trend_analysis": "Network risk has decreased by 0.3 points over the past 7 days...",
  "next_steps": ["Prioritize SPOF mitigation", "Schedule redundancy upgrades"]
}
```

### Get Topology Changelog

Get topology changes over a time period.

```http
GET /api/reports/changelog
```

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `from` | datetime | Start date (ISO 8601) |
| `to` | datetime | End date (ISO 8601) |
| `type` | string | Change type filter |

**Response** (`200 OK`):

```json
{
  "changes": [
    {
      "timestamp": "2026-02-11T10:27:00Z",
      "change_type": "device_added",
      "description": "New device detected: unknown-device-142",
      "device_id": "device-uuid",
      "details": {
        "ip": "192.168.1.142",
        "mac": "AA:BB:CC:DD:EE:FF"
      }
    },
    {
      "timestamp": "2026-02-11T10:10:00Z",
      "change_type": "connection_status_change",
      "description": "Link status changed to flapping",
      "connection_id": "edge-uuid",
      "details": {
        "from": "active",
        "to": "flapping"
      }
    }
  ],
  "total_changes": 47,
  "period": {
    "from": "2026-02-10T00:00:00Z",
    "to": "2026-02-11T11:00:00Z"
  }
}
```

---

## WebSocket

### Connect to WebSocket

Real-time event subscription via WebSocket.

```
WS /ws/topology
```

**Client → Server (Subscribe)**:

```json
{
  "type": "subscribe",
  "channel": "topology"
}
```

**Client → Server (Ping)**:

```json
{ "type": "ping" }
```

The server replies with `{"type": "pong"}`. The frontend pings every 30 seconds to keep the connection alive.

**Server → Client (Events)**:

```json
{
  "type": "device_added",
  "data": {
    "id": "device-uuid",
    "hostname": "new-device-01",
    "device_type": "workstation",
    "ip": "192.168.1.142"
  },
  "timestamp": "2026-02-11T10:30:00Z"
}
```

**Event Types**:

| Event Type | Description |
|------------|-------------|
| `device_added` | New device discovered |
| `device_removed` | Device went offline |
| `device_updated` | Device properties changed |
| `connection_change` | Link status or properties changed |
| `alert` | New alert generated |
| `scan_progress` | Scan status update |
| `topology_updated` | General topology change |

**Heartbeat**:

Server sends periodic heartbeat messages:

```json
{
  "type": "heartbeat",
  "timestamp": "2026-02-11T10:30:00Z"
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    }
  }
}
```

**HTTP Status Codes**:

| Code | Meaning |
|------|---------|
| `400` | Bad Request - Invalid parameters |
| `404` | Not Found - Resource doesn't exist |
| `422` | Unprocessable Entity - Validation error |
| `500` | Internal Server Error - Server-side issue |
| `503` | Service Unavailable - Service temporarily unavailable |

**Example Error Response** (`400 Bad Request`):

```json
{
  "error": {
    "code": "INVALID_CIDR",
    "message": "Invalid CIDR range format",
    "details": {
      "field": "target",
      "value": "192.168.1.0/99",
      "expected": "Valid CIDR notation (e.g., 192.168.0.0/16)"
    }
  }
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. Future versions will include:

- 100 requests per minute per IP for general endpoints
- 10 scans per hour per IP for scan endpoints
- 5 report generations per hour per IP

---

## Pagination

List endpoints support pagination via `limit` and `offset` parameters.

**Example**:

```http
GET /api/devices?limit=50&offset=100
```

**Response includes pagination metadata**:

```json
{
  "data": [...],
  "pagination": {
    "total": 247,
    "limit": 50,
    "offset": 100,
    "has_next": true,
    "has_prev": true
  }
}
```

---

---

## Snapshot Endpoints

Topology snapshots capture topology state at a point in time (stored in SQLite). Used for topology diff and history views.

### List Snapshots

```http
GET /api/snapshots
```

**Response** (`200 OK`):

```json
{
  "snapshots": [
    {
      "id": "snapshot-uuid",
      "created_at": "2026-03-20T10:00:00Z",
      "device_count": 10,
      "connection_count": 9,
      "risk_score": 0.42
    }
  ],
  "total": 14
}
```

### Get Snapshot

```http
GET /api/snapshots/{snapshot_id}
```

**Response** (`200 OK`):

```json
{
  "id": "snapshot-uuid",
  "created_at": "2026-03-20T10:00:00Z",
  "device_count": 10,
  "connection_count": 9,
  "risk_score": 0.42,
  "snapshot_data": {
    "devices": [...],
    "connections": [...]
  }
}
```

---

## Settings Endpoints

Settings are stored as key/value pairs in SQLite.

### Get Settings

```http
GET /api/settings
```

**Response** (`200 OK`):

```json
{
  "scan_interval_minutes": 60,
  "anomaly_detection_enabled": true,
  "snapshot_retention_days": 30,
  "default_scan_target": "172.20.0.0/24",
  "alert_severity_threshold": "medium"
}
```

### Update Settings

```http
PUT /api/settings
```

**Request Body** (partial update, send only changed keys):

```json
{
  "scan_interval_minutes": 120,
  "default_scan_target": "192.168.1.0/24"
}
```

**Response** (`200 OK`):

```json
{
  "updated": ["scan_interval_minutes", "default_scan_target"],
  "settings": {
    "scan_interval_minutes": 120,
    "anomaly_detection_enabled": true,
    "snapshot_retention_days": 30,
    "default_scan_target": "192.168.1.0/24",
    "alert_severity_threshold": "medium"
  }
}
```

---

## Scan Optimizer Endpoints

AI-powered scan recommendations based on current topology and anomaly history.

### Get Recommendations

```http
GET /api/scan-optimizer/recommendations
```

**Response** (`200 OK`):

```json
{
  "generated_at": "2026-03-20T10:05:00Z",
  "recommendations": [
    {
      "priority": "high",
      "target": "172.20.0.5",
      "reason": "Device shows anomalous port activity — deep scan recommended",
      "suggested_scan_type": "deep",
      "estimated_duration": "3-5 minutes"
    },
    {
      "priority": "medium",
      "target": "172.20.0.0/24",
      "reason": "No full scan in last 6 hours",
      "suggested_scan_type": "normal",
      "estimated_duration": "1-2 minutes"
    }
  ]
}
```

---

## API Versioning

Current version: `v1`

Future versions will use URL versioning: `/api/v2/topology`

---

## OpenAPI Documentation

Interactive API documentation available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
