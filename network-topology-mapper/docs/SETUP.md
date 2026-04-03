# Setup Guide

Complete installation and configuration guide for Network Topology Mapper.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start (Local Development)](#quick-start-local-development)
- [Optional Demo Network (Docker)](#optional-demo-network-docker)
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

**Required for Local Development**:
- Python 3.11+
- Node.js 18+
- Redis 7.0+
- nmap (for network scanning)

**Optional (Demo Network Lab Only)**:
- Docker 20.10+
- Docker Compose 2.0+

---

## Quick Start (Local Development)

Use this path for day-to-day development. Docker is not required.

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
# Claude API key (for AI reports)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Network scan target (adjust to your network)
SCAN_DEFAULT_RANGE=192.168.0.0/16
```

### 3. Backend Setup

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start Redis (Local Service)

Use your OS package/service manager to run Redis locally.

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

**macOS**:
```bash
brew install redis
brew services start redis
```

Verify:
```bash
redis-cli ping
```

Expected output: `PONG`

### 5. Start Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 7. Trigger First Scan

```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "192.168.1.0/24"}'
```

### 8. Access Application

- **Main Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs

---

## Optional Demo Network (Docker)

Use this only when you want the simulated lab network in `demo/`.

### 1. Start Demo Environment

```bash
./demo.sh up
```

This starts demo containers on the `nts-net` bridge network.

### 2. Trigger Demo Scan

```bash
./demo.sh scan
```

### 3. Check Demo Status

```bash
./demo.sh status
```

### 4. Tear Down Demo

```bash
./demo.sh down
```

---

## Local Development Setup

For direct backend/frontend development.

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

#### 4. Start Redis (Local Service)

```bash
# Ubuntu/Debian
sudo systemctl start redis-server

# macOS (Homebrew)
brew services start redis
```

#### 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```bash
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

**Error: "Permission denied" on nmap**

```bash
# Grant capabilities
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3.11)
```

**Error: "Redis connection refused"**

```bash
# Ubuntu/Debian
sudo systemctl start redis-server

# macOS
brew services start redis
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
- Check backend logs in your active `uvicorn` terminal output

### Database Issues

**SQLite "Database locked"**

- Ensure only one backend instance is running
- Check file permissions on `data/mapper.db`
- Restart the backend service

### Performance Issues

**Slow graph rendering**

- Reduce visible nodes with filters
- Try dagre layout (faster than force-directed for large graphs)
- Profile frontend render performance in browser DevTools

---

## Next Steps

After successful setup:

1. **Configure scan targets**: Edit `.env` to match your network
2. **Trigger first scan**: Use `demo.sh scan` or the UI
3. **Explore documentation**: Read [ARCHITECTURE.md](ARCHITECTURE.md) and [API.md](API.md)

---

## Security Notes

- Change default password for Redis in `.env`
- Use HTTPS in production (nginx reverse proxy required)
- Restrict network access to services
- Rotate API keys regularly
- Review scan targets before running full scans
- Keep dependencies up to date
