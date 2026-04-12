# Backend - Network Topology Mapper

FastAPI-based backend for network topology mapping and analysis.

## Overview

The backend handles:
- Network device discovery (active/passive scanning, SNMP)
- Topology database management (SQLite + NetworkX)
- Real-time WebSocket communication
- Graph analysis and failure simulation
- AI-powered report generation
- Background task processing (asyncio)

## Architecture

```
app/
├── main.py                 # FastAPI application entry point + asyncio lifespan
├── config.py              # Pydantic settings (reads .env)
├── models/                # Pydantic request/response models
│   ├── device.py
│   ├── connection.py
│   ├── alert.py
│   └── scan.py
├── routers/               # API route handlers (device routes live in topology.py)
│   ├── topology.py
│   ├── scans.py
│   ├── simulation.py
│   ├── alerts.py
│   ├── reports.py
│   ├── snapshots.py
│   └── settings.py
├── services/              # Business logic layer
│   ├── scanner/           # Network scanning services
│   │   ├── active_scanner.py
│   │   ├── passive_scanner.py
│   │   ├── snmp_poller.py
│   │   ├── config_puller.py
│   │   ├── connection_inference.py
│   │   └── scan_coordinator.py
│   ├── graph/             # Graph analysis services
│   │   ├── graph_builder.py
│   │   ├── failure_simulator.py
│   │   ├── spof_detector.py
│   │   ├── resilience_scorer.py
│   │   └── path_analyzer.py
│   ├── ai/                # AI/ML services
│   │   ├── anomaly_detector.py
│   │   ├── failure_predictor.py
│   │   ├── report_generator.py   # Wraps the `claude` CLI via subprocess
│   │   └── scan_optimizer.py
│   ├── realtime/          # WebSocket & events
│   │   ├── event_bus.py
│   │   └── ws_manager.py
│   └── mock_data.py       # Dev fallback data
├── tasks/                 # Asyncio background tasks
│   ├── scan_tasks.py
│   └── analysis_tasks.py
└── db/                    # Database clients
    ├── topology_db.py
    ├── redis_client.py
    └── sqlite_db.py
```

## Quick Start

### Local Development

1. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Start Redis** (optional — app works without it):
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

5. **Run server**:
```bash
uvicorn app.main:app --reload
```

Server runs at http://localhost:8000

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Development

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/services/test_scanner.py

# With coverage
pytest --cov=app tests/

# Watch mode
ptw
```

### Code Quality

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint
flake8 app/

# Type check
mypy app/
```

### Database

SQLite schemas are created on first run by `sqlite_db.connect()` and `topology_db.connect()`. There are no Alembic migrations — the schema is applied idempotently on every startup.

## Key Services

### Scanner Services

**Active Scanner** (`services/scanner/active_scanner.py`):
- Shells out to `nmap` via `subprocess` (NOT python-nmap)
- Discovers devices via network probing
- Identifies open ports and services
- Supports `light` / `normal` / `deep` intensity profiles

**Passive Scanner** (`services/scanner/passive_scanner.py`):
- Scapy-based packet capture
- Monitors ARP, DNS, DHCP traffic
- No network impact

**SNMP Poller** (`services/scanner/snmp_poller.py`):
- Queries SNMP-enabled devices
- Retrieves switch port tables
- Discovers device details

**Scan Coordinator** (`services/scanner/scan_coordinator.py`):
- Orchestrates scan phases
- Deduplicates results
- Triggers graph updates

### Graph Services

**Graph Builder** (`services/graph/graph_builder.py`):
- Creates/updates topology database records
- Correlates scan results
- Maintains graph consistency

**SPOF Detector** (`services/graph/spof_detector.py`):
- Uses NetworkX articulation points algorithm
- Identifies single points of failure
- Calculates impact radius

**Failure Simulator** (`services/graph/failure_simulator.py`):
- Simulates device/link removal
- Calculates affected devices
- Provides mitigation recommendations

**Resilience Scorer** (`services/graph/resilience_scorer.py`):
- Computes device risk scores
- Calculates network health metrics
- Tracks trends over time

### AI Services

**Anomaly Detector** (`services/ai/anomaly_detector.py`):
- IsolationForest for topology anomalies
- Detects unusual network changes
- Generates alerts

**Report Generator** (`services/ai/report_generator.py`):
- Wraps the `claude` CLI (Claude Code headless) via `subprocess`
- Produces natural language resilience reports with executive summaries
- Falls back to a deterministic rule-based report when `claude` is not on PATH
- No Anthropic SDK dependency; no API key required

### Real-time Services

**Event Bus** (`services/realtime/event_bus.py`):
- Redis pub/sub for event distribution
- Broadcasts topology changes
- Alert notifications

**WebSocket Manager** (`services/realtime/ws_manager.py`):
- Manages WebSocket connections
- Heartbeat/keepalive
- Event broadcasting to clients

## API Endpoints

### Topology

```
GET    /api/topology              - Get full topology with filters
GET    /api/topology/stats        - Aggregate statistics
GET    /api/devices/{id}          - Device details
GET    /api/devices/{id}/connections - Device connections
GET    /api/devices/{id}/dependencies - Dependency tree
```

### Scanning

```
POST   /api/scans                 - Trigger scan
GET    /api/scans                 - List scan history
GET    /api/scans/{id}            - Scan status
DELETE /api/scans/{id}            - Cancel scan
```

### Simulation

```
POST   /api/simulate/failure      - Simulate failure
GET    /api/simulate/spof         - List SPOFs
GET    /api/simulate/resilience   - Resilience score
```

### Alerts

```
GET    /api/alerts                - List alerts
PATCH  /api/alerts/{id}           - Update alert
GET    /api/alerts/stream         - SSE alert stream
```

### Reports

```
GET    /api/reports/resilience    - Claude-Code-generated resilience report
GET    /api/reports/changelog     - Topology changes from snapshot history
```

### Snapshots

```
GET    /api/snapshots             - List topology snapshots
GET    /api/snapshots/{id}        - Specific snapshot
```

### Settings

```
GET    /api/settings              - Current effective settings
PUT    /api/settings              - Persist setting overrides to SQLite
GET    /api/scan-optimizer/recommendations - AI scan recommendations
```

### Health

```
GET    /api/health                - Liveness + component status
```

### WebSocket

```
WS     /ws/topology               - Real-time events
```

## Database Models

### SQLite Tables (topology_db + sqlite_db)

**devices**: All discovered devices (id, ip, mac, hostname, device_type, vendor, model, risk_score, status, etc.)
**connections**: Device-to-device connections (source_id, target_id, connection_type, bandwidth, latency_ms, etc.)
**scans**: Scan history and metadata
**alerts**: Alert log and status
**topology_snapshots**: Periodic topology snapshots
**settings**: User-configurable settings overrides

## Background Tasks

### Scheduled Tasks (asyncio, NOT Celery)

Scheduled via `asyncio.create_task()` in the FastAPI lifespan function (`main.py`). There is no Celery worker, broker config, or `celery_app.py` — this was a deliberate architectural decision.

### Current Schedule

- **Full scan**: Every `scan_interval_minutes` (default: 5; `0` disables)
- **Anomaly detection**: Runs after each scan completion (skipped silently until there are enough devices for IsolationForest to train)

## Configuration

Key environment variables (see `../.env.example`):

```bash
# Databases
REDIS_URL=redis://localhost:6379/0
SQLITE_PATH=./data/mapper.db

# Scanning
SCAN_DEFAULT_RANGE=192.168.0.0/16
SCAN_RATE_LIMIT=1000
SNMP_COMMUNITY=public

# Server
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# Scheduled scanning
SCAN_INTERVAL_MINUTES=5   # 0 = disabled
```

**Note on AI reports:** There is no `ANTHROPIC_API_KEY` or `CLAUDE_MODEL` setting. `report_generator.py` shells out to the `claude` CLI directly. Install the Claude Code CLI and ensure it is on PATH; otherwise the endpoint returns a deterministic rule-based report.

## Logging

Structured JSON logging:

```python
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Scan completed",
    extra={
        "scan_id": scan_id,
        "devices_found": count,
        "duration_ms": duration
    }
)
```

Logs are output to stdout in JSON format for easy parsing.

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

## Security

- Input validation via Pydantic models
- SQL injection protection (parameterized queries)
- Redis authentication recommended
- Rate limiting (future)
- CORS configuration in `main.py`

## Performance

### Caching

- Redis caching for topology data (60s TTL)
- Device detail caching (5min TTL)
- Scan result caching

### Database Optimization

- SQLite indexes on device IDs, IPs, MACs
- Connection pooling for Redis
- Async I/O throughout

### Monitoring

There is no Prometheus `/metrics` endpoint yet. Runtime health is exposed via `GET /api/health`, which reports topology_db status, Redis availability, WebSocket client count, snapshot count, and the current scheduled scan interval.

## Troubleshooting

### Common Issues

**"Permission denied" on nmap**
- Requires root or NET_RAW capability
- Run: `sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)`

**"Redis connection refused"**
- Start Redis: `redis-server`
- Check port 6379 is available

**"Scan timeout"**
- Reduce scan range
- Lower scan intensity
- Check network connectivity

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload
```

## Testing

### Unit Tests

Test individual services:
```bash
pytest tests/services/
```

### Integration Tests

Test full workflows:
```bash
pytest tests/integration/
```

### Mock Data

Use mock data for development:
```python
from app.services.mock_data import generate_mock_topology

topology = generate_mock_topology(device_count=100)
```

## Deployment

### Docker

```bash
docker build -t network-mapper-backend .
docker run -p 8000:8000 --env-file .env network-mapper-backend
```

### Production Checklist

- [ ] Set `APP_DEBUG=false`
- [ ] Use strong password for Redis
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS (reverse proxy)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Review network permissions

## Resources

- [API Documentation](../docs/API.md)
- [Architecture Overview](../docs/ARCHITECTURE.md)
- [Setup Guide](../docs/SETUP.md)
- [Contributing Guide](../docs/CONTRIBUTING.md)

## Support

For issues or questions:
- Check documentation
- Open GitHub issue
- Join community channels

---

**Happy coding!** 🚀
