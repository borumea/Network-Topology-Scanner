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
- **OS**: Linux, macOS, or Windows with WSL2

### Recommended Requirements

- **CPU**: 4+ cores
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **OS**: Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+)

### Software Prerequisites

**For Docker Deployment**:
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

The fastest way to get started is using Docker Compose.

### 1. Clone Repository

```bash
git clone <repository-url>
cd network-topology-mapper
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and update the following required variables:

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
docker-compose up -d
```

This will start:
- Frontend (React) on http://localhost:3000
- Backend (FastAPI) on http://localhost:8000
- Neo4j on http://localhost:7474
- Redis on localhost:6379

### 4. Verify Installation

Check all services are running:

```bash
docker-compose ps
```

Expected output:
```
NAME                STATUS          PORTS
network-mapper-frontend   running    0.0.0.0:3000->3000/tcp
network-mapper-backend    running    0.0.0.0:8000->8000/tcp
network-mapper-neo4j      running    0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
network-mapper-redis      running    0.0.0.0:6379->6379/tcp
```

### 5. Access Application

Open your browser:
- **Main Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (login: neo4j / your-password)

### 6. Trigger First Scan

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"type": "full", "target": "192.168.1.0/24", "intensity": "normal"}'
```

---

## Local Development Setup

For development without Docker.

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

**Windows** (requires WSL2):
```bash
# In WSL2 Ubuntu
sudo apt update
sudo apt install python3.11 python3.11-venv nmap libpcap-dev
```

#### 2. Create Virtual Environment

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Install Neo4j

**Ubuntu/Debian**:
```bash
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j=1:5.17.0
sudo systemctl start neo4j
sudo systemctl enable neo4j
```

**macOS**:
```bash
brew install neo4j
brew services start neo4j
```

**Docker** (alternative):
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:5-community
```

#### 5. Install Redis

**Ubuntu/Debian**:
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**macOS**:
```bash
brew install redis
brew services start redis
```

**Docker** (alternative):
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

#### 6. Configure Environment

```bash
cd backend
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

#### 7. Initialize Database

```bash
python -c "from app.db.sqlite_db import init_db; init_db()"
```

#### 8. Start Backend Server

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

**Windows**:
Download from https://nodejs.org/

#### 2. Install Dependencies

```bash
cd frontend
npm install
```

#### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

#### 4. Start Development Server

```bash
npm run dev
```

Frontend is now running at http://localhost:3000

### Celery Workers (Optional for Background Tasks)

#### 1. Start Celery Worker

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

#### 2. Start Celery Beat (Scheduler)

```bash
cd backend
celery -A app.tasks.celery_app beat --loglevel=info
```

---

## Configuration

### Environment Variables

Complete list of environment variables:

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

# Agent mode
AGENT_MODE=alert  # alert | interactive | autonomous
```

#### Celery Configuration

```bash
# Celery broker
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Task schedules (cron expressions)
SCHEDULE_FULL_SCAN=0 */6 * * *      # Every 6 hours
SCHEDULE_SNMP_POLL=*/30 * * * *     # Every 30 minutes
SCHEDULE_SNAPSHOT=0 0 * * *         # Daily at midnight
```

### Configuration Files

#### Backend Configuration (`backend/app/config.py`)

Application settings are managed via Pydantic Settings:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    redis_url: str
    # ... other settings

    class Config:
        env_file = ".env"
```

#### Frontend Configuration (`frontend/vite.config.ts`)

Vite configuration for development and build:

```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
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

#### 4. Verify Indexes

```cypher
SHOW INDEXES;
```

### SQLite Configuration

SQLite database is created automatically on first run.

**Manual initialization**:

```bash
cd backend
python -c "from app.db.sqlite_db import init_db; init_db()"
```

**Database location**: `backend/data/mapper.db`

### Redis Configuration

Redis typically works out of the box. For production, add authentication:

**Edit `/etc/redis/redis.conf`**:
```
requirepass your-redis-password
```

**Restart Redis**:
```bash
sudo systemctl restart redis
```

**Update `.env`**:
```bash
REDIS_URL=redis://:your-redis-password@localhost:6379/0
```

---

## Network Permissions

Network scanning requires elevated privileges.

### Docker Network Mode

The backend container needs `host` network mode to see LAN traffic:

```yaml
# docker-compose.yml
services:
  backend:
    network_mode: host
    cap_add:
      - NET_RAW
      - NET_ADMIN
```

### Local Development Permissions

#### Option 1: Run as Root (Not Recommended)

```bash
sudo uvicorn app.main:app --reload
```

#### Option 2: Grant Capabilities to Python

```bash
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3.11)
```

#### Option 3: Add User to pcap Group

```bash
sudo groupadd pcap
sudo usermod -a -G pcap $USER
sudo chgrp pcap $(which nmap)
sudo chmod 750 $(which nmap)
sudo setcap cap_net_raw,cap_net_admin=eip $(which nmap)
```

Log out and back in for group changes to take effect.

### Firewall Configuration

Allow backend to send/receive network probes:

**UFW (Ubuntu)**:
```bash
sudo ufw allow 8000/tcp
sudo ufw allow from 192.168.0.0/16 to any port 161 proto udp  # SNMP
```

**firewalld (RHEL/CentOS)**:
```bash
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

---

## Troubleshooting

### Backend Won't Start

**Error: "Cannot connect to Neo4j"**

Solution:
```bash
# Check Neo4j status
docker ps | grep neo4j
# or
sudo systemctl status neo4j

# Verify credentials in .env match Neo4j password
# Check connectivity
curl http://localhost:7474
```

**Error: "Permission denied" on nmap**

Solution:
```bash
# Grant capabilities (see Network Permissions section)
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3.11)
```

**Error: "Redis connection refused"**

Solution:
```bash
# Start Redis
sudo systemctl start redis
# or
docker start redis
```

### Frontend Won't Start

**Error: "EADDRINUSE: Port 3000 in use"**

Solution:
```bash
# Kill process using port 3000
npx kill-port 3000
# or use different port
npm run dev -- --port 3001
```

**Error: "Cannot reach backend API"**

Solution:
- Verify backend is running: `curl http://localhost:8000/api/topology/stats`
- Check CORS settings in `backend/app/main.py`
- Verify proxy configuration in `frontend/vite.config.ts`

### Scanning Issues

**Error: "No devices found"**

Solution:
- Verify target network range in scan request
- Check network connectivity: `ping 192.168.1.1`
- Ensure backend has network permissions
- Try passive scanning first

**Error: "Scan timeout"**

Solution:
- Reduce scan intensity to "light"
- Reduce target range
- Increase scan rate limit in .env

### Database Issues

**Neo4j "Out of memory"**

Solution:
Edit `neo4j.conf`:
```
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
```

**SQLite "Database locked"**

Solution:
- Ensure only one backend instance is running
- Check file permissions on `data/mapper.db`
- Restart backend service

### Performance Issues

**Slow graph rendering**

Solution:
- Enable caching in browser
- Reduce visible nodes with filters
- Try a different layout algorithm (dagre/hierarchical is default; cola/force-directed can be slower on large graphs)
- Increase hardware resources

**High CPU usage during scans**

Solution:
- Reduce scan rate limit
- Use passive scanning instead of active
- Adjust scan schedule to off-peak hours

---

## Next Steps

After successful setup:

1. **Configure Scan Targets**: Edit `.env` to match your network
2. **Trigger First Scan**: Use API or UI to start discovery
3. **Explore Documentation**: Read [ARCHITECTURE.md](ARCHITECTURE.md) and [API.md](API.md)
4. **Set Up Monitoring**: Configure logging and metrics
5. **Production Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Getting Help

- **Documentation**: Check `docs/` directory
- **GitHub Issues**: Report bugs and feature requests
- **Community**: Join our discussion forum
- **Commercial Support**: Contact for enterprise support options

---

## Security Notes

- Change default passwords for Neo4j and Redis
- Use HTTPS in production (reverse proxy required)
- Restrict network access to services
- Rotate API keys regularly
- Review scan targets before running full scans
- Keep dependencies up to date

---

**Setup Complete!** 🎉

Your Network Topology Mapper is ready to use.
