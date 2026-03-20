# Setup Guide

Complete installation and configuration guide for Network Topology Mapper.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start with Docker](#quick-start-with-docker)
- [Local Development Setup](#local-development-setup)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Network Permissions](#network-permissions)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB
- **OS**: Linux or macOS

### Recommended Requirements

- **CPU**: 4+ cores
- **RAM**: 8 GB
- **Storage**: 50 GB SSD

### Software Prerequisites

**For Docker Deployment** (recommended):
- Docker 20.10+
- Docker Compose 2.0+

**For Local Development**:
- Python 3.11+
- Node.js 18+
- Neo4j 5.0+
- Redis 7.0+
- nmap (for network scanning)

---

## Quick Start with Docker

The fastest way to get started is using the demo script.

### 1. Clone Repository

```bash
git clone <repository-url>
cd network-topology-mapper
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and update required variables:

```bash
# Neo4j password (change this!)
NEO4J_PASSWORD=your-secure-password

# Claude API key (for AI reports)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Network scan target (adjust to your network)
SCAN_DEFAULT_RANGE=192.168.0.0/16
```

### 3. Start Services

```bash
./demo.sh up
```

This starts all services on the `nts-net` bridge network:
- Frontend (React) on http://localhost:3000
- Backend (FastAPI) on http://localhost:8000
- Neo4j on http://localhost:7474
- Redis on localhost:6379

### 4. Trigger First Scan

```bash
./demo.sh scan
```

Or via API:

```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "172.20.0.0/24"}'
```

### 5. Access Application

- **Main Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (login: neo4j / your-password)

### 6. Status Check

```bash
./demo.sh status
```

---

## Local Development Setup

For development without Docker (editing Python or frontend code directly).

### Backend Setup

#### 1. Install System Dependencies

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nmap libpcap-dev
```

**macOS**:
```bash
brew install python@3.11 nmap libpcap
```

#### 2. Create Virtual Environment

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
```

#### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Start Neo4j + Redis via Docker

```bash
# Start just the databases (not the full app stack)
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:5-community

docker run -d --name redis -p 6379:6379 redis:7-alpine
```

#### 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
REDIS_URL=redis://localhost:6379/0
SQLITE_PATH=./data/mapper.db
SCAN_DEFAULT_RANGE=192.168.1.0/24
ANTHROPIC_API_KEY=sk-ant-your-key
```

#### 6. Start Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend is now running at http://localhost:8000

### Frontend Setup

#### 1. Install Node.js

**Ubuntu/Debian**:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

**macOS**:
```bash
brew install node@18
```

#### 2. Install Dependencies

```bash
cd frontend
npm install
```

#### 3. Start Development Server

```bash
npm run dev
```

Frontend is now running at http://localhost:3000

---

## Configuration

### Environment Variables

#### Database Configuration

```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme
NEO4J_DATABASE=neo4j

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# SQLite
SQLITE_PATH=./data/mapper.db
```

#### Scanning Configuration

```bash
# Default scan target
SCAN_DEFAULT_RANGE=192.168.0.0/16

# Scan rate limiting (packets per second)
SCAN_RATE_LIMIT=1000

# Passive scanning interface
SCAN_PASSIVE_INTERFACE=eth0

# SNMP settings
SNMP_COMMUNITY=public
SNMP_VERSION=2c
SNMP_TIMEOUT=5
SNMP_RETRIES=3

# SSH/Telnet credentials (for config retrieval)
SSH_USERNAME=admin
SSH_PASSWORD=
SSH_KEY_PATH=
```

#### AI Configuration

```bash
# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4000
```

#### Application Configuration

```bash
# Server
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## Database Setup

### Neo4j Configuration

#### 1. Access Neo4j Browser

Open http://localhost:7474

#### 2. Initial Login

- Username: `neo4j`
- Password: `neo4j`
- You'll be prompted to change password

#### 3. Create Indexes (for performance)

Run these Cypher queries:

```cypher
// Device indexes
CREATE INDEX device_id IF NOT EXISTS FOR (d:Device) ON (d.id);
CREATE INDEX device_ip IF NOT EXISTS FOR (d:Device) ON (d.ip);
CREATE INDEX device_mac IF NOT EXISTS FOR (d:Device) ON (d.mac);
CREATE INDEX device_hostname IF NOT EXISTS FOR (d:Device) ON (d.hostname);

// VLAN index
CREATE INDEX vlan_id IF NOT EXISTS FOR (v:VLAN) ON (v.id);
```

### SQLite Configuration

SQLite database is created automatically on first run.

**Manual initialization**:

```bash
cd backend
python -c "from app.db.sqlite_db import init_db; init_db()"
```

**Database location**: `backend/data/mapper.db`

---

## Network Permissions

Network scanning requires elevated privileges for nmap and Scapy.

### Docker Setup

The backend container runs with bridge networking (`nts-net`). Scanning capabilities are granted via `cap_add` in `docker-compose.yml`:

```yaml
services:
  backend:
    cap_add:
      - NET_RAW
      - NET_ADMIN
```

This is already configured — no changes needed for the demo.

### Local Development Permissions

**macOS**: nmap installed via Homebrew runs with the required capabilities by default.

**Linux**: Grant capabilities to Python and nmap:

```bash
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3.11)
sudo setcap cap_net_raw,cap_net_admin=eip $(which nmap)
```

Or add your user to the pcap group:

```bash
sudo groupadd pcap
sudo usermod -a -G pcap $USER
sudo chgrp pcap $(which nmap)
sudo chmod 750 $(which nmap)
```

Log out and back in for group changes to take effect.

---

## Troubleshooting

### Backend Won't Start

**Error: "Cannot connect to Neo4j"**

```bash
# Check Neo4j status
docker ps | grep neo4j

# Verify credentials in .env match Neo4j password
# Check connectivity
curl http://localhost:7474
```

**Error: "Permission denied" on nmap**

```bash
# Grant capabilities
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3.11)
```

**Error: "Redis connection refused"**

```bash
docker start redis
# or: docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### Frontend Won't Start

**Error: "EADDRINUSE: Port 3000 in use"**

```bash
npx kill-port 3000
```

**Error: "Cannot reach backend API"**

- Verify backend is running: `curl http://localhost:8000/api/health`
- Check CORS settings in `backend/app/main.py`
- Verify proxy configuration in `frontend/vite.config.ts`

### Scanning Issues

**No devices found**

- Verify target network range in scan request
- Check network connectivity: `ping 172.20.0.1`
- Ensure backend has network permissions (see above)

**Scan timeout**

- Reduce scan intensity
- Reduce target subnet size
- Check backend logs: `docker logs network-mapper-backend`

### Database Issues

**Neo4j "Out of memory"**

Edit Neo4j configuration (via Docker env vars in `docker-compose.yml`):
```yaml
NEO4J_server_memory_heap_initial__size: 2G
NEO4J_server_memory_heap_max__size: 4G
```

**SQLite "Database locked"**

- Ensure only one backend instance is running
- Check file permissions on `data/mapper.db`
- Restart the backend service

### Performance Issues

**Slow graph rendering**

- Reduce visible nodes with filters
- Try dagre layout (faster than force-directed for large graphs)
- Increase hardware resources allocated to Docker

---

## Next Steps

After successful setup:

1. **Configure scan targets**: Edit `.env` to match your network
2. **Trigger first scan**: Use `demo.sh scan` or the UI
3. **Explore documentation**: Read [ARCHITECTURE.md](ARCHITECTURE.md) and [API.md](API.md)

---

## Security Notes

- Change default passwords for Neo4j and Redis in `.env`
- Use HTTPS in production (nginx reverse proxy required)
- Restrict network access to services
- Rotate API keys regularly
- Review scan targets before running full scans
- Keep dependencies up to date
