# Documentation Index

Complete documentation for the Network Topology Mapper project.

## Getting Started

Start here if you're new to the project:

1. **[README.md](../README.md)** - Project overview, features, and quick start
2. **[SETUP.md](SETUP.md)** - Detailed installation and configuration guide
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and architecture overview

## Core Documentation

### For Users

- **[README.md](../README.md)** - Main project documentation
  - Features overview
  - Quick start with Docker
  - Usage examples
  - Configuration basics
  - Troubleshooting quick tips

- **[SETUP.md](SETUP.md)** - Complete setup guide
  - System requirements
  - Docker installation
  - Local development setup
  - Database configuration
  - Network permissions
  - Environment variables

- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Problem-solving guide
  - Installation issues
  - Database connection problems
  - Scanning issues
  - WebSocket problems
  - Performance optimization
  - Frontend issues
  - API errors
  - Docker troubleshooting

### For Developers

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture
  - System architecture diagram
  - Frontend architecture
  - Backend architecture
  - Data layer design
  - API design
  - Security architecture
  - Scalability considerations

- **[API.md](API.md)** - Complete API reference
  - All endpoints documented
  - Request/response examples
  - WebSocket protocol
  - Error responses
  - Authentication (future)
  - Rate limiting
  - Pagination

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
  - Code of conduct
  - Development workflow
  - Coding standards (Python & TypeScript)
  - Testing guidelines
  - Pull request process
  - Issue reporting

- **[Backend README](../backend/README.md)** - Backend documentation
  - Backend architecture
  - Service descriptions
  - API endpoints
  - Database models
  - Background tasks
  - Development guide

- **[Frontend README](../frontend/README.md)** - Frontend documentation
  - Component architecture
  - Key components
  - Custom hooks
  - State management
  - Cytoscape.js configuration
  - Styling guide
  - Testing

### Additional Resources

- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and release notes
  - Version history
  - Feature additions
  - Bug fixes
  - Breaking changes
  - Upgrade notes

## Documentation by Topic

### Installation & Setup

| Document | Description |
|----------|-------------|
| [README - Quick Start](../README.md#quick-start) | Get started with Docker in 5 minutes |
| [SETUP - Docker Setup](SETUP.md#quick-start-with-docker) | Complete Docker deployment guide |
| [SETUP - Local Development](SETUP.md#local-development-setup) | Set up for local development |
| [SETUP - Configuration](SETUP.md#configuration) | Environment variables and settings |

### Development

| Document | Description |
|----------|-------------|
| [ARCHITECTURE](ARCHITECTURE.md) | System architecture and design patterns |
| [Backend README](../backend/README.md) | Backend development guide |
| [Frontend README](../frontend/README.md) | Frontend development guide |
| [CONTRIBUTING](CONTRIBUTING.md) | How to contribute code |
| [API Reference](API.md) | Complete API documentation |

### Network Scanning

| Document | Description |
|----------|-------------|
| [SETUP - Network Permissions](SETUP.md#network-permissions) | Required permissions for scanning |
| [TROUBLESHOOTING - Scanning Issues](TROUBLESHOOTING.md#scanning-issues) | Common scanning problems |
| [Backend README - Scanner Services](../backend/README.md#scanner-services) | How scanners work |
| [API - Scan Endpoints](API.md#scan-endpoints) | Scan API reference |

### Graph Visualization

| Document | Description |
|----------|-------------|
| [Frontend README - Network Canvas](../frontend/README.md#network-canvas) | Graph component documentation |
| [Frontend README - Cytoscape Config](../frontend/README.md#cytoscapejs-configuration) | Graph styling and behavior |
| [ARCHITECTURE - Frontend](ARCHITECTURE.md#frontend-architecture) | Visualization architecture |

### Database & Data Models

| Document | Description |
|----------|-------------|
| [SETUP - Database Setup](SETUP.md#database-setup) | Database installation and configuration |
| [ARCHITECTURE - Data Layer](ARCHITECTURE.md#data-layer) | Database schema and design |
| [Backend README - Database Models](../backend/README.md#database-models) | Data model reference |
| [TROUBLESHOOTING - Database Issues](TROUBLESHOOTING.md#database-connection-problems) | Database troubleshooting |

### Real-time Features

| Document | Description |
|----------|-------------|
| [API - WebSocket](API.md#websocket) | WebSocket protocol documentation |
| [ARCHITECTURE - Real-time Event System](ARCHITECTURE.md#real-time-event-system) | How real-time updates work |
| [Frontend README - useWebSocket Hook](../frontend/README.md#usewebsocket) | WebSocket React hook |
| [TROUBLESHOOTING - WebSocket Problems](TROUBLESHOOTING.md#websocket-problems) | WebSocket troubleshooting |

### AI & Analysis

| Document | Description |
|----------|-------------|
| [Backend README - AI Services](../backend/README.md#ai-services) | AI service documentation |
| [API - Report Endpoints](API.md#report-endpoints) | AI report API |
| [ARCHITECTURE - Graph Analysis Engine](ARCHITECTURE.md#graph-analysis-engine) | How analysis works |

### Deployment

| Document | Description |
|----------|-------------|
| [README - Quick Start](../README.md#quick-start) | Quick Docker deployment |
| [SETUP - Docker Setup](SETUP.md#quick-start-with-docker) | Production Docker setup |
| [Backend README - Deployment](../backend/README.md#deployment) | Backend deployment guide |
| [Frontend README - Deployment](../frontend/README.md#deployment) | Frontend deployment guide |

## Documentation Structure

```
network-topology-mapper/
├── README.md                  # Main project README
├── CHANGELOG.md              # Version history
├── .env.example              # Environment configuration template
├── docs/                     # Documentation directory
│   ├── INDEX.md             # This file - documentation index
│   ├── ARCHITECTURE.md      # System architecture
│   ├── API.md               # API reference
│   ├── SETUP.md             # Setup guide
│   ├── CONTRIBUTING.md      # Contribution guidelines
│   └── TROUBLESHOOTING.md   # Troubleshooting guide
├── backend/
│   └── README.md            # Backend documentation
├── frontend/
│   └── README.md            # Frontend documentation
└── testing/
    ├── SMOKE_TEST.md        # Smoke test procedures
    └── TEST_CHECKLIST.md    # Testing checklist
```

## Quick Links

### Most Common Tasks

- **[First-time setup](SETUP.md#quick-start-with-docker)** - Get up and running
- **[Trigger a scan](API.md#trigger-a-scan)** - Start network discovery
- **[Troubleshoot scanning](TROUBLESHOOTING.md#scanning-issues)** - Fix scan problems
- **[Understand the architecture](ARCHITECTURE.md)** - Learn how it works
- **[Contribute code](CONTRIBUTING.md)** - Join development
- **[Report a bug](CONTRIBUTING.md#issue-reporting)** - File an issue

### For Specific Roles

**Network Engineers**:
1. [Quick Start](../README.md#quick-start)
2. [Network Permissions](SETUP.md#network-permissions)
3. [Scanning Configuration](SETUP.md#configuration)
4. [Scan API](API.md#scan-endpoints)

**Developers**:
1. [Local Development Setup](SETUP.md#local-development-setup)
2. [Architecture Overview](ARCHITECTURE.md)
3. [Contributing Guide](CONTRIBUTING.md)
4. [API Reference](API.md)

**System Administrators**:
1. [Docker Setup](SETUP.md#quick-start-with-docker)
2. [Configuration](SETUP.md#configuration)
3. [Database Setup](SETUP.md#database-setup)
4. [Troubleshooting](TROUBLESHOOTING.md)

**Security Analysts**:
1. [Features Overview](../README.md#features)
2. [SPOF Detection](API.md#get-spofs)
3. [Risk Scoring](ARCHITECTURE.md#resilience-scorer)
4. [Alerts](API.md#alert-endpoints)

## Documentation Standards

### Writing Style

- Use clear, concise language
- Include code examples
- Provide command-line examples with expected output
- Use bullet points and tables for readability
- Include troubleshooting tips

### Code Examples

- Python: Follow PEP 8
- TypeScript: Follow ESLint rules
- Bash: Include comments for complex commands
- Always include expected output

### Diagrams

- Use ASCII art for simple diagrams
- Use Mermaid for complex diagrams (future)
- Include textual descriptions

## Contributing to Documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Updating existing documentation
- Adding new documentation
- Documentation review process
- Style guidelines

## Version Information

- **Documentation Version**: 1.0.0
- **Project Version**: 1.0.0
- **Last Updated**: 2026-02-11

## Feedback

Found an issue with the documentation?
- Open an issue on GitHub
- Label it as "documentation"
- Suggest improvements

---

## Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| README.md | ✅ Complete | 2026-02-11 |
| ARCHITECTURE.md | ✅ Complete | 2026-02-11 |
| API.md | ✅ Complete | 2026-02-11 |
| SETUP.md | ✅ Complete | 2026-02-11 |
| CONTRIBUTING.md | ✅ Complete | 2026-02-11 |
| TROUBLESHOOTING.md | ✅ Complete | 2026-02-11 |
| Backend README | ✅ Complete | 2026-02-11 |
| Frontend README | ✅ Complete | 2026-02-11 |
| CHANGELOG.md | ✅ Complete | 2026-02-11 |

---

**Need help finding something?** Search the documentation or open an issue!
