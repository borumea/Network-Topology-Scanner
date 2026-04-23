# Network Topology Mapper

A real-time network topology mapping and analysis platform that discovers devices, visualizes network relationships, identifies single points of failure, and provides AI-powered resilience insights.

## Features

- **Automated Network Discovery**: Active scanning (nmap), passive monitoring (Scapy), SNMP polling, and device configuration retrieval
- **Interactive Graph Visualization**: Real-time network topology using Cytoscape.js with multiple layout algorithms
- **Failure Simulation**: Test network resilience by simulating device or link failures
- **SPOF Detection**: Automatically identify single points of failure using graph analysis
- **Real-time Monitoring**: WebSocket-based live updates for topology changes, alerts, and scan progress
- **Risk Scoring**: Composite risk assessment for devices and overall network health
- **AI-Powered Reports**: Natural language resilience reports powered by Claude
- **Anomaly Detection**: Machine learning-based detection of unusual topology changes
- **Multi-Layer Views**: Physical, logical, and application layer visualization

## Tech Stack

### Frontend
- **React 18** + TypeScript + Vite
- **Cytoscape.js** for network graph visualization
- **Tailwind CSS** for styling
- **Zustand** for state management
- **WebSocket** for real-time updates

### Backend
- **FastAPI** (Python 3.11+)
- **SQLite** + **NetworkX** for device/connection storage and graph analysis
- **Redis** for caching and real-time pub/sub (optional — Redis-backed features like pub/sub and cache are unavailable without it)
- **asyncio-based task scheduler** for periodic scans and post-scan analysis
- **scikit-learn** for anomaly detection (IsolationForest)

### Networking Tools
- nmap (subprocess) for active scanning
- Scapy for passive packet capture
- pysnmp for SNMP interrogation
- Netmiko for device configuration retrieval

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- nmap (`brew install nmap` / `apt install nmap` / [nmap.org](https://nmap.org/download))

### Setup

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal, from project root)
cd ../frontend
npm install
npm run dev
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Scan Your Network

Open http://localhost:3000, click **Scan** in the sidebar, enter your subnet (e.g. `192.168.1.0/24`), and hit scan. Or via CLI:

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"type": "full", "target": "192.168.1.0/24", "intensity": "normal"}'
```

## Project Structure

```
network-topology-mapper/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── config.py          # Configuration management
│   │   ├── models/            # Pydantic models
│   │   ├── routers/           # API route handlers
│   │   ├── services/          # Business logic
│   │   │   ├── scanner/       # Network scanning services
│   │   │   ├── graph/         # Graph analysis and manipulation
│   │   │   ├── ai/            # AI/ML services
│   │   │   └── realtime/      # WebSocket and event handling
│   │   ├── tasks/             # asyncio background tasks
│   │   └── db/                # Database clients (topology_db, sqlite_db, redis_client)
│   ├── requirements.txt
│   └── tests/
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── graph/         # Network graph components
│   │   │   ├── panels/        # Side panels and overlays
│   │   │   ├── dashboard/     # Dashboard widgets
│   │   │   ├── shared/        # Reusable UI components
│   │   │   └── layout/        # Layout components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── stores/            # Zustand state stores
│   │   ├── lib/               # Utilities and configurations
│   │   └── types/             # TypeScript type definitions
│   └── package.json
├── docs/                       # Documentation
└── testing/                    # Test checklists
```

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) - System design and data flow
- [API Documentation](docs/API.md) - Complete API reference
- [Setup Guide](docs/SETUP.md) - Installation and configuration
- [Contributing Guide](docs/CONTRIBUTING.md) - How to contribute

## Usage Examples

### Trigger a Network Scan
```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"type": "full", "target": "auto"}'
```

### Get Topology Data
```bash
curl http://localhost:8000/api/topology
```

### Simulate Device Failure
```bash
curl -X POST http://localhost:8000/api/simulate/failure \
  -H "Content-Type: application/json" \
  -d '{"remove_nodes": ["device-uuid-here"]}'
```

### Read / Update Settings
```bash
curl http://localhost:8000/api/settings

curl -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"scan_interval_minutes": 10, "scan_default_range": "192.168.1.0/24"}'
```

## Configuration

Key environment variables (see `.env.example` for full list):

```bash
# Redis (optional — pub/sub and cache unavailable without it)
REDIS_URL=redis://localhost:6379/0

# AI Reports (optional — resilience reports require this)
ANTHROPIC_API_KEY=your-api-key-here

# Scanning
SCAN_DEFAULT_RANGE=192.168.1.0/24
SNMP_COMMUNITY=public

# Agent Mode
AGENT_MODE=alert  # alert | interactive | autonomous
```

## Security Considerations

- Network scanning requires elevated privileges (nmap needs NET_RAW/NET_ADMIN or root)
- Keep SNMP community strings confidential
- Restrict API access in production environments
- Review firewall rules before active scanning

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## Acknowledgments

- Built with [Cytoscape.js](https://js.cytoscape.org/) for graph visualization
- Powered by [FastAPI](https://fastapi.tiangolo.com/) for the backend
- Network analysis using [NetworkX](https://networkx.org/)

## Known Limitations

- **Anomaly detection requires 5+ topology snapshots** to train the IsolationForest model. During initial use, only rule-based detection (flapping links, unknown devices) is active.
- **Passive scanning** (Scapy ARP sniffing) requires root/admin privileges and may not work on all platforms.
- **SNMP polling** requires devices that respond to the configured community string on UDP 161.
- **Large topologies** (500+ devices) may slow down NetworkX graph analysis operations. Consider increasing scan intervals for very large networks.
