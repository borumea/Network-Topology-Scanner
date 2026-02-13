# Changelog

All notable changes to Network Topology Mapper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Graph Visualization Overhaul**: Complete redesign of network graph rendering
  - Nodes: Circular ellipses with device-type colored fills (replacing rectangular Tech Cards)
  - Node sizing: Tiered by importance (infrastructure 50px, servers 44px, endpoints 36px)
  - Icons: Centered SVG icons with dark contrasting stroke colors per device type
  - Edges: Smooth bezier curves (replacing taxi/Manhattan routing)
  - Labels: Below nodes in Inter/system-ui sans-serif font
  - Default layout: Hierarchical (dagre) with gateway at top (replacing force-directed cola)
  - Dagre spacing increased: nodeSep 100, rankSep 140
  - SPOF nodes: Red pulsing shadow glow ring
  - Selected state: White ring + blue glow + 8px scale-up

### Added
- **Neighborhood highlighting**: Hovering a node dims non-neighbors to 15% opacity
- **Edge tooltips**: Hovering an edge shows connection type, bandwidth, latency, status
- **Double-click zoom**: Double-clicking a node zooms camera to fit its 1-hop neighborhood
- **Edge hover feedback**: Visual highlight class on hovered edges
- **MiniMap colors**: Minimap nodes now use device-type color fills with larger dots
- **MiniMap refresh**: Update interval reduced from 1000ms to 500ms for smoother tracking
- Initial project documentation
- Comprehensive README files
- API documentation
- Architecture documentation
- Setup and troubleshooting guides

## [1.0.0] - 2026-02-11

### Added

#### Backend
- FastAPI application with RESTful API
- Neo4j integration for graph database
- Redis integration for caching and pub/sub
- SQLite for metadata storage
- WebSocket support for real-time updates
- Active network scanning (nmap wrapper)
- Passive network monitoring (Scapy)
- SNMP polling for device discovery
- Graph analysis services (SPOF detection, failure simulation)
- Resilience scoring algorithm
- Anomaly detection using IsolationForest
- AI-powered report generation (Claude API)
- Celery background task processing
- Scheduled scan tasks
- Mock data generator for development

#### Frontend
- React 18 + TypeScript application
- Cytoscape.js network graph visualization
- Interactive graph canvas with zoom/pan/fit controls
- Multiple layout algorithms (cola, dagre, circular)
- Real-time topology updates via WebSocket
- Device inspector panel
- Alert feed panel
- Simulation panel for failure testing
- Metrics bar with KPIs
- Risk heatmap view
- Timeline view for topology changes
- Zustand state management
- Tailwind CSS styling
- Custom hooks for topology, WebSocket, alerts
- Device type icons and status badges
- Command palette (Cmd+K)
- Responsive layout

#### Features
- Full network topology discovery
- Real-time device monitoring
- Single Point of Failure (SPOF) detection
- Device and network risk scoring
- Failure simulation with impact analysis
- AI-generated resilience reports
- Alert system with severity levels
- Topology changelog tracking
- Multi-layer views (physical/logical/application)
- Device filtering and search
- Connection visualization with bandwidth/latency
- Dependency tree visualization
- VLAN and subnet grouping

#### Documentation
- Comprehensive README with quick start guide
- Architecture overview documentation
- Complete API reference
- Setup guide for local and Docker deployment
- Contribution guidelines
- Backend service documentation
- Frontend component documentation
- Troubleshooting guide
- Environment configuration examples

#### Infrastructure
- Docker Compose setup for all services
- Neo4j database schema and indexes
- Redis pub/sub event system
- SQLite database schema
- Celery task queue configuration
- WebSocket event bus

### Security
- Neo4j authentication
- Redis password support
- CORS configuration
- Input validation with Pydantic
- Secure environment variable management

## Release Notes

### Version 1.0.0

**Network Topology Mapper** is a comprehensive network discovery and analysis platform that provides:

**Discovery & Monitoring**:
- Automated device discovery through active scanning, passive monitoring, and SNMP
- Real-time topology updates via WebSocket
- Support for various device types (routers, switches, servers, firewalls, etc.)
- Connection type detection (ethernet, fiber, wireless, VPN)

**Analysis & Intelligence**:
- Single Point of Failure (SPOF) detection using graph algorithms
- Network resilience scoring
- Failure simulation with blast radius calculation
- AI-powered natural language reports
- Anomaly detection for unusual topology changes
- Risk assessment per device and globally

**Visualization**:
- Interactive network graph with Cytoscape.js
- Multiple layout algorithms
- Device details and inspection
- Connection visualization with metrics
- Risk heatmaps
- Timeline of topology changes

**Technical Stack**:
- Backend: FastAPI, Python 3.11+, Neo4j, Redis, SQLite
- Frontend: React 18, TypeScript, Vite, Cytoscape.js, Tailwind CSS
- Tools: nmap, Scapy, pysnmp, NetworkX, scikit-learn
- AI: Claude API for natural language reports

**Deployment**:
- Docker Compose for easy setup
- Comprehensive documentation
- Environment-based configuration
- Background task processing with Celery

This is the first stable release and includes all core features for network topology mapping, analysis, and visualization.

### Known Issues

- Large networks (1000+ devices) may experience slow graph rendering
- Active scanning requires elevated privileges (NET_RAW capability)
- WebSocket may disconnect on slow networks (workaround: increase heartbeat interval)
- Neo4j initial setup requires password change

### Upgrade Notes

This is the initial release. No upgrade path available.

### Breaking Changes

N/A - Initial release

---

## Version History

- **1.0.0** (2026-02-11): Initial release with full feature set

---

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the [documentation](docs/)
- Review [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

[Unreleased]: https://github.com/your-org/network-topology-mapper/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-org/network-topology-mapper/releases/tag/v1.0.0
