# Network Topology Mapper

A real-time network topology mapping and analysis platform that discovers devices, visualizes network relationships, identifies single points of failure, and provides AI-powered resilience insights.

![Network Topology Mapper](docs/images/screenshot-main.png)

## Features

- **Automated Network Discovery**: Active scanning (nmap), passive monitoring (Scapy), SNMP polling, and device configuration retrieval
- **Interactive Graph Visualization**: Real-time network topology using Cytoscape.js with multiple layout algorithms
- **Failure Simulation**: Test network resilience by simulating device or link failures
- **SPOF Detection**: Automatically identify single points of failure using graph analysis
- **Real-time Monitoring**: WebSocket-based live updates for topology changes, alerts, and scan progress
- **Risk Scoring**: Composite risk assessment for devices and overall network health
- **AI-Powered Reports**: Natural language resilience reports powered by Claude API
- **Anomaly Detection**: Machine learning-based detection of unusual topology changes
- **Multi-Layer Views**: Physical, logical, and application layer visualization

## Tech Stack

### Frontend
- **React 18** + TypeScript + Vite
- **Cytoscape.js** for network graph visualization
- **Recharts** for metrics and analytics
- **Tailwind CSS** for styling
- **Zustand** for state management
- **WebSocket** for real-time updates

### Backend
- **FastAPI** (Python 3.11+)
- **Neo4j** graph database for device/connection storage
- **Redis** for caching and real-time pub/sub
- **SQLite** for scan history, alerts, topology snapshots, and settings
- **asyncio-based task scheduler** for periodic scans and post-scan analysis
- **NetworkX** for graph analysis
- **scikit-learn** for anomaly detection (IsolationForest)

### Networking Tools
- python-nmap for active scanning
- Scapy for passive packet capture
- pysnmp for SNMP interrogation
- Netmiko for device configuration retrieval

## Quick Start

### Demo Mode (Zero Configuration)

The fastest way to see NTS working end-to-end. Spins up the full stack plus 5 scannable demo containers on a private Docker network.

**Prerequisites:** Docker, docker-compose

```bash
git clone <repository-url>
cd network-topology-mapper

# Start the full stack + demo network
./demo.sh up

# Once all services are healthy (~60s), trigger a scan
./demo.sh scan

# Check backend health
./demo.sh status
```

**What happens:**
- 5 demo containers start on `nts-net` (172.20.0.0/24): `web-server` (nginx), `db-server` (postgres), `file-server` (SSH+SMB), `printer` (JetDirect+IPP), `snmp-device` (net-snmp)
- nmap discovers all containers on the bridge network
- Connection inference creates star-topology edges through the Docker gateway (172.20.0.1)
- Frontend at http://localhost:3000 renders the live topology graph
- Neo4j Browser at http://localhost:7474 (neo4j / changeme) for raw graph inspection

**Tear down:**
```bash
./demo.sh down
```

### Production Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- Neo4j, Redis (or use Docker Compose)

### Using Docker Compose

1. Clone the repository:
```bash
git clone <repository-url>
cd network-topology-mapper
```

2. Create environment configuration:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Start all services:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Neo4j Browser: http://localhost:7474

### Local Development

See [SETUP.md](docs/SETUP.md) for detailed local development setup instructions.

## Project Structure

```
network-topology-mapper/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── config.py          # Configuration management
│   │   ├── models/            # Pydantic and SQLAlchemy models
│   │   ├── routers/           # API route handlers
│   │   ├── services/          # Business logic
│   │   │   ├── scanner/       # Network scanning services
│   │   │   ├── graph/         # Graph analysis and manipulation
│   │   │   ├── ai/            # AI/ML services
│   │   │   └── realtime/      # WebSocket and event handling
│   │   ├── tasks/             # Celery background tasks
│   │   └── db/                # Database clients and connections
│   ├── requirements.txt
│   └── Dockerfile
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
│   ├── package.json
│   └── vite.config.ts
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md        # System architecture details
│   ├── API.md                 # API endpoint documentation
│   ├── SETUP.md               # Setup and installation guide
│   ├── CONTRIBUTING.md        # Contribution guidelines
│   └── DEPLOYMENT.md          # Deployment instructions
├── testing/                    # Test documentation
│   ├── SMOKE_TEST.md
│   └── TEST_CHECKLIST.md
├── docker-compose.yml
├── .env.example
└── README.md
```

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) - System design and data flow
- [API Documentation](docs/API.md) - Complete API reference
- [Setup Guide](docs/SETUP.md) - Installation and configuration
- [Contributing Guide](docs/CONTRIBUTING.md) - How to contribute
- [Frontend Components](docs/FRONTEND.md) - Component documentation
- [Backend Services](docs/BACKEND.md) - Backend service documentation
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment

## Key Concepts

### Device Types
- **Routers**: Core routing devices
- **Switches**: Layer 2/3 switches
- **Servers**: Application and service hosts
- **Firewalls**: Security perimeter devices
- **Access Points**: Wireless infrastructure
- **Workstations**: End-user devices
- **IoT**: Smart devices and sensors
- **Unknown**: Unidentified devices

### Connection Types
- **Ethernet**: Standard wired connections
- **Fiber**: High-speed fiber links
- **Wireless**: Wi-Fi connections
- **VPN**: Virtual private network tunnels
- **Virtual**: Virtualized network connections

### Risk Scoring
Risk scores (0.0-1.0) are calculated based on:
- Connectivity redundancy
- Device criticality
- Number of dependencies
- Configuration vulnerabilities
- Historical reliability

## Usage Examples

### Trigger a Network Scan
```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"type": "full", "target": "192.168.0.0/16"}'
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

### View Topology Snapshots
```bash
curl http://localhost:8000/api/snapshots
```

### Get Scan Optimizer Recommendations
```bash
curl http://localhost:8000/api/scan-optimizer/recommendations
```

### Read / Update Settings
```bash
# Get current settings
curl http://localhost:8000/api/settings

# Update scan interval and target range
curl -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"scan_interval_minutes": 10, "scan_default_range": "172.20.0.0/24"}'
```

## Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Configuration

Key environment variables (see `.env.example` for full list):

```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Redis
REDIS_URL=redis://localhost:6379/0

# Scanning
SCAN_DEFAULT_RANGE=192.168.0.0/16
SNMP_COMMUNITY=public

# Claude API (for AI reports)
ANTHROPIC_API_KEY=sk-ant-...

# Agent Mode
AGENT_MODE=alert  # alert | interactive | autonomous
```

## Security Considerations

- Network scanning requires elevated privileges (NET_RAW, NET_ADMIN capabilities)
- Secure your Neo4j and Redis instances with strong passwords
- Keep SNMP community strings confidential
- Restrict API access in production environments
- Review firewall rules before active scanning

## Performance Tips

- Use targeted scans instead of full network sweeps for faster discovery
- Enable passive scanning for continuous monitoring without active probing
- Adjust scan rate limits based on network capacity
- Use Redis caching to reduce database load
- Limit WebSocket client connections in production

## Troubleshooting

### Neo4j Connection Issues
```bash
# Check Neo4j status
docker-compose logs neo4j

# Verify credentials
docker exec -it neo4j cypher-shell -u neo4j -p your-password
```

### Scanning Permission Errors
Ensure Docker container has proper capabilities:
```yaml
cap_add:
  - NET_RAW
  - NET_ADMIN
```

### WebSocket Disconnections
Check WebSocket heartbeat interval and firewall settings. Increase timeout in config if needed.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

[Specify your license here]

## Acknowledgments

- Built with [Cytoscape.js](https://js.cytoscape.org/) for graph visualization
- Powered by [FastAPI](https://fastapi.tiangolo.com/) for the backend
- Network analysis using [NetworkX](https://networkx.org/)
- AI insights from [Claude API](https://www.anthropic.com/api)

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the [documentation](docs/)
- Review [troubleshooting guide](docs/TROUBLESHOOTING.md)

## Roadmap

- [ ] Advanced traffic analysis integration
- [ ] Multi-site topology management
- [ ] Enhanced GNN-based failure prediction
- [ ] Mobile responsive interface
- [ ] SNMP trap receiver
- [ ] Integration with CMDB systems
- [ ] Custom alert rules engine
- [ ] Automated remediation workflows

---

**Status**: Active Development | **Version**: 1.0.0 | **Last Updated**: March 2026

## Known Limitations

- **Anomaly detection requires 5+ topology snapshots** to train the IsolationForest model. During initial demo runs, only rule-based detection (flapping links, unknown devices) is active. After 5 scheduled scans have run, the ML model trains automatically.
- **Passive scanning** (Scapy ARP sniffing) is disabled in demo mode — Docker bridge networking doesn't support raw packet capture across containers. Only nmap active scanning runs.
- **SNMP polling** requires the `snmp-device` demo container to respond to the `public` community string on UDP 161. If the container starts slowly, the first scan may miss it.
- **Settings changes** (via `PUT /api/settings`) take effect immediately for stored values, but `scan_interval_minutes` only applies to new scheduler instances. Restart the backend container to change the scan interval.
- **Neo4j memory**: Default Neo4j Docker config uses 512MB heap. For large topologies (500+ devices), increase `NEO4J_server_memory_heap_max__size` in `docker-compose.yml`.
