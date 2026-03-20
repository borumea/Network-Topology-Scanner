# Quick Start Guide

## Recommended: Demo Mode (Zero Config, Works Right Away)

The fastest path to a working topology graph. Uses a Docker overlay with 5 scannable demo containers.

```bash
cd network-topology-mapper

# Start full stack + demo network (takes ~60s for all containers to be healthy)
./demo.sh up

# Trigger a scan once services are healthy
./demo.sh scan

# Open http://localhost:3000 to see the topology graph
```

**What you get:** nginx web server, postgres DB, file server (SSH+SMB), JetDirect printer, SNMP device — all on `nts-net` (172.20.0.0/24). The backend scans them with nmap, runs connection inference, and renders a star topology graph.

**Tear down:**
```bash
./demo.sh down
```

---

## Manual Setup Options

You have **3 options** to add real network data:

---

## 🚀 Option 1: Docker Desktop (FASTEST & EASIEST)

**Best for**: Full production setup with all features

### Install Docker Desktop
```powershell
winget install Docker.DockerDesktop
```

Or download from: https://www.docker.com/products/docker-desktop/

### Start Everything
```bash
cd network-topology-mapper

# Start all services (Neo4j, Redis, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Neo4j Browser: http://localhost:7474 (login: neo4j/changeme)

---

## 🗄️ Option 2: Install Neo4j & Redis Locally

**Best for**: Running without Docker

### Install Neo4j Desktop
1. Download: https://neo4j.com/download/
2. Install Neo4j Desktop
3. Create new database:
   - Name: `network-mapper`
   - Password: `changeme`
   - Version: 5.x
4. Start the database

### Install Redis

**Option A: Using Chocolatey**
```powershell
choco install redis-64 -y
redis-server
```

**Option B: Using WSL2**
```bash
sudo apt install redis-server -y
sudo service redis-server start
```

**Option C: Download MSI**
- https://github.com/tporadowski/redis/releases
- Install Redis-x64-*.msi

### Restart Backend
```bash
cd backend

# Stop current backend (Ctrl+C)

# Start with real databases
venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

See full instructions: `INSTALL_GUIDE.md`

---

## 🔌 Option 3: Add Devices via API (NO SETUP REQUIRED)

**Best for**: Testing immediately, manual device entry

### Quick Method: Run Python Script

```bash
cd network-topology-mapper

# Run the sample device script
python add_sample_devices.py
```

This adds:
- 1 Router (192.168.1.1)
- 1 Firewall (192.168.1.2)
- 2 Switches (192.168.1.10, 192.168.1.11)
- 2 Servers (192.168.1.20, 192.168.1.21)
- 1 Workstation (192.168.1.100)
- 1 Access Point (192.168.1.200)
- All connections between them

### Manual Method: Using curl

**Add a single device:**
```bash
curl -X POST http://localhost:8000/api/devices \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.1",
    "mac": "00:11:22:33:44:01",
    "hostname": "my-router",
    "device_type": "router",
    "vendor": "Cisco",
    "status": "online"
  }'
```

**Add a connection:**
```bash
curl -X POST http://localhost:8000/api/connections \
  -H "Content-Type: application/json" \
  -d '{
    "source_ip": "192.168.1.1",
    "target_ip": "192.168.1.2",
    "connection_type": "ethernet",
    "bandwidth": "1Gbps",
    "status": "active"
  }'
```

**Run the bash script:**
```bash
bash add_devices_curl.sh
```

---

## 🔍 Option 4: Network Scanning (Real Device Discovery)

**Best for**: Automatically discovering devices on your network

### Install nmap

**Windows:**
```powershell
winget install Insecure.Nmap
```

Or download from: https://nmap.org/download.html

**After installing nmap**, restart your backend and trigger a scan:

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{
    "type": "full",
    "target": "192.168.1.0/24",
    "intensity": "normal"
  }'
```

**View scan progress:**
```bash
curl http://localhost:8000/api/scans
```

---

## 📊 Check Your Topology

**Get statistics:**
```bash
curl http://localhost:8000/api/topology/stats
```

**Get full topology:**
```bash
curl http://localhost:8000/api/topology
```

**View in browser:**
- Main UI: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## 🎯 Quick Command Reference

### Start Application
```bash
# Backend
cd backend
venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (in another terminal)
cd frontend
npm run dev
```

### Add Sample Data
```bash
python add_sample_devices.py
```

### View Data
```bash
# Statistics
curl http://localhost:8000/api/topology/stats | jq

# All devices
curl http://localhost:8000/api/devices | jq

# Specific device
curl http://localhost:8000/api/devices/{device-id} | jq
```

### Trigger Network Scan (requires nmap)
```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"type":"active","target":"192.168.1.0/24"}' | jq
```

---

## 🆘 Troubleshooting

### Backend shows "0 devices"
- Add devices via API (Option 3)
- Or install databases (Option 1 or 2)

### "Connection refused" errors
- Neo4j: Install and start Neo4j
- Redis: Install and start Redis
- Or use Docker Desktop (Option 1)

### Can't scan network
- Install nmap: `winget install Insecure.Nmap`
- Restart backend after installing nmap

### Frontend shows empty graph
- Check backend is running: `curl http://localhost:8000/api/topology/stats`
- Add some devices first (Option 3)
- Refresh browser (Ctrl+F5)

---

## 📚 More Information

- Full Documentation: `docs/` folder
- Architecture: `docs/ARCHITECTURE.md`
- API Reference: `docs/API.md`
- Setup Guide: `docs/SETUP.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`

---

## 🎉 Recommended Path

1. **Right Now**: Use Option 3 to add sample devices
   ```bash
   python add_sample_devices.py
   ```

2. **This Week**: Install Docker Desktop (Option 1)
   - Full database support
   - Easy to manage
   - Best for development

3. **Later**: Set up network scanning
   - Install nmap
   - Scan your real network
   - Discover actual devices

---

**Choose your option and start mapping your network!** 🌐
