# Network Topology Mapper — Deployment Guide (Windows + WSL2)

## Prerequisites

- **Windows 10/11** with WSL2 enabled
- **Docker Desktop** with WSL2 backend enabled
  Download: https://www.docker.com/products/docker-desktop/
- **Git** (to clone the repo)

> **For real LAN scanning**: Docker Desktop runs containers inside a Hyper-V VM, so `network_mode: host` gives containers the VM's network — not your physical LAN. If you need to scan your actual network, see [Advanced: Native Docker in WSL2](#advanced-native-docker-in-wsl2) below.

---

## Quick Start

### 1. Clone the repository

```powershell
git clone <repo-url>
cd network-topology-mapper
```

### 2. Create your environment file

```powershell
copy .env.docker .env
```

### 3. Edit `.env` — set your network range

Open `.env` in a text editor and set `SCAN_DEFAULT_RANGE` to your local subnet:

```
# Find your subnet: open PowerShell and run 'ipconfig'
# Look for "IPv4 Address" (e.g., 192.168.1.105) and "Subnet Mask" (e.g., 255.255.255.0)
# That means your range is: 192.168.1.0/24

SCAN_DEFAULT_RANGE=192.168.1.0/24
```

Optional settings to configure:
- `SNMP_COMMUNITY` — SNMP community string (default: `public`)
- `SSH_USERNAME` / `SSH_PASSWORD` — for managed switch/router config pulling
- `ANTHROPIC_API_KEY` — for AI-powered topology reports

### 4. Build and start

```powershell
docker compose up -d
```

First run will take a few minutes to download images and build containers.

### 5. Verify everything is running

```powershell
docker compose ps
```

You should see 4 services: `neo4j`, `redis`, `backend`, `frontend` — all with status `Up` or `healthy`.

Check the backend health:
```powershell
curl http://localhost:8000/api/health
```

Expected response:
```json
{"status": "ok", "neo4j": true, "redis": true, "websocket_clients": 0}
```

---

## Accessing the App

| Service | URL |
|---------|-----|
| **Topology UI** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **Neo4j Browser** | http://localhost:7474 (user: `neo4j`, pass: `changeme`) |

The UI loads with mock data (~35 devices) on first startup so you can explore the interface immediately.

---

## Running a Scan

### Via the UI
1. Open http://localhost:3000
2. Click the **Scan** tab in the sidebar
3. Click **Start Scan**
4. Watch progress in real-time via the progress bar and WebSocket updates

### Via the API
```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"type":"full","target":"192.168.1.0/24","intensity":"normal"}'
```

Scan types:
- `active` — nmap host discovery + port scanning
- `passive` — scapy ARP/DNS/DHCP traffic sniffing (30 seconds)
- `snmp` — SNMP device interrogation (for devices with port 161 open)
- `full` — all of the above + SSH config/LLDP pulling

Intensity levels (for active scans):
- `light` — ping sweep only, fast (~30 seconds)
- `normal` — top 100 ports + service detection (~2-5 minutes)
- `deep` — top 1000 ports + scripts (~5-15 minutes)

---

## Architecture Overview

```
Browser (localhost:3000)
    |
    ├── Static files served by nginx
    ├── /api/* proxied to backend (localhost:8000)
    └── /ws/* proxied to backend (WebSocket)

Backend (localhost:8000) — FastAPI + Python
    ├── nmap (active scanning)
    ├── scapy (passive ARP/DNS/DHCP sniffing)
    ├── pysnmp (SNMP device polling)
    ├── netmiko (SSH config pulling + LLDP)
    └── Databases:
        ├── Neo4j (localhost:7687) — topology graph
        ├── Redis (localhost:6379) — pub/sub + caching
        └── SQLite (./data/mapper.db) — scan history + alerts
```

---

## Managing the App

### View logs
```powershell
# All services
docker compose logs

# Backend only (most useful for debugging scans)
docker compose logs backend

# Follow logs in real-time
docker compose logs -f backend
```

### Stop the app
```powershell
docker compose down
```

### Stop and remove all data (fresh start)
```powershell
docker compose down -v
```

### Rebuild after code changes
```powershell
docker compose build
docker compose up -d
```

---

## Troubleshooting

### "neo4j: false" in health check
Neo4j takes 15-30 seconds to start. Wait and retry:
```powershell
docker compose logs neo4j
```
Look for `Started.` in the logs.

### Scans find 0 devices
1. **Check your subnet range** — make sure `SCAN_DEFAULT_RANGE` in `.env` matches your actual network
2. **Check Docker networking** — with Docker Desktop, the container may not have access to your physical LAN (see Advanced section below)
3. **Check nmap** — `docker compose exec backend nmap --version` should return the nmap version
4. **Try a light scan first** — deep scans can take a long time on large subnets

### Frontend shows blank page
```powershell
docker compose logs frontend
```
Check for nginx errors. The frontend container needs the backend to be running on port 8000.

### WebSocket not connecting
The browser connects to `ws://localhost:3000/ws/topology` which nginx proxies to `localhost:8000`. Check:
1. Backend is running: `curl http://localhost:8000/api/health`
2. Browser devtools → Network → WS tab → check for connection errors

### Port conflicts
If ports 3000, 7474, 7687, 6379, or 8000 are already in use:
```powershell
netstat -ano | findstr :8000
```
Stop the conflicting service, or change ports in `.env` and `docker-compose.yml`.

---

## Advanced: Native Docker in WSL2

For scanning your actual physical LAN (not just the Docker VM network), install Docker Engine directly inside WSL2 instead of using Docker Desktop.

### 1. Install WSL2 + Ubuntu
```powershell
wsl --install -d Ubuntu
```

### 2. Enable mirrored networking
Create/edit `%USERPROFILE%\.wslconfig`:
```ini
[wsl2]
networkingMode=mirrored
```
Then restart WSL: `wsl --shutdown`

### 3. Install Docker Engine in WSL2
Inside WSL2 Ubuntu:
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```
Log out and back in.

### 4. Verify LAN access
```bash
# Replace with your router's IP
ping -c 1 192.168.1.1
```

### 5. Run the app
```bash
cd /mnt/c/path/to/network-topology-mapper
cp .env.docker .env
# Edit .env with your settings
docker compose up -d
```

### 6. Find your WSL2 interface name
```bash
ip link
# Usually eth0 or eth1 — update SCAN_PASSIVE_INTERFACE in .env if needed
```

With mirrored networking, `network_mode: host` gives the container direct access to your physical LAN, and nmap/scapy can discover real devices.
