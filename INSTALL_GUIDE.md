# Installation Guide

> **Tip:** For the fastest start, use Demo Mode — no manual installation required. See `QUICK_START_GUIDE.md` or run `./demo.sh up` from `network-topology-mapper/`. This guide covers manual Neo4j and Redis installation for production or local development on Windows.

## Manual Installation - Neo4j & Redis

## Option A: Install Neo4j Desktop

### Download Neo4j Desktop
1. Go to: https://neo4j.com/download/
2. Download Neo4j Desktop for Windows
3. Install the application

### Set Up Neo4j
1. Open Neo4j Desktop
2. Click "New" → "Create Project"
3. Click "Add" → "Local DBMS"
4. Name: `network-mapper`
5. Password: `changeme` (or update .env)
6. Version: 5.x (latest)
7. Click "Create"
8. Click "Start" to start the database

### Verify Neo4j
- Web interface: http://localhost:7474
- Bolt connection: bolt://localhost:7687
- Login: neo4j / changeme

---

## Option B: Install Redis on Windows

### Method 1: Using Chocolatey

```powershell
# Install Chocolatey if not installed
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Redis
choco install redis-64 -y

# Start Redis
redis-server
```

### Method 2: Using MSI Installer

1. Download Redis for Windows: https://github.com/tporadowski/redis/releases
2. Download latest `Redis-x64-*.msi`
3. Run installer
4. Redis will run as a Windows service

### Method 3: Using WSL2 (Recommended)

```bash
# In WSL2 Ubuntu
sudo apt update
sudo apt install redis-server -y

# Start Redis
sudo service redis-server start

# Verify
redis-cli ping
# Should return: PONG
```

### Verify Redis
```bash
redis-cli ping
# Should return: PONG
```

---

## Configure Application

Update `.env` file:

```bash
# Neo4j (update password if different)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme

# Redis
REDIS_URL=redis://localhost:6379/0

# SQLite (already configured)
SQLITE_PATH=./data/mapper.db
```

---

## Restart Backend

```bash
cd backend

# Stop current backend (Ctrl+C)

# Restart with databases
venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend will now connect to:
- ✅ Neo4j (for graph storage)
- ✅ Redis (for caching and real-time events)
- ✅ SQLite (for metadata)

---

## Verify Connection

Check backend logs for:
```
[INFO] Connected to Neo4j at bolt://localhost:7687
[INFO] Connected to Redis at localhost:6379
[INFO] Connected to SQLite at data/mapper.db
```

---

## Troubleshooting

### Neo4j Connection Failed
- Ensure Neo4j Desktop is running
- Check firewall allows port 7687
- Verify password in .env matches Neo4j

### Redis Connection Failed
- Ensure Redis service is running
- Check port 6379 is not in use
- Verify Redis is accepting connections

### Permission Denied
- Run terminals as Administrator
- Check Windows Firewall settings

---

## Testing

```bash
# Test Neo4j connection
curl -u neo4j:changeme http://localhost:7474

# Test Redis connection
redis-cli ping

# Test Backend API
curl http://localhost:8000/api/topology/stats
```

---

## Next Steps

With databases running, you can:
1. **Scan your network** (requires nmap)
2. **Add devices manually** via API
3. **Import network data**
4. **Use full topology features**

See API documentation: http://localhost:8000/docs
