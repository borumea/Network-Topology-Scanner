# Troubleshooting Guide

Common issues and solutions for Network Topology Mapper.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Database Connection Problems](#database-connection-problems)
- [Scanning Issues](#scanning-issues)
- [WebSocket Problems](#websocket-problems)
- [Performance Issues](#performance-issues)
- [Frontend Problems](#frontend-problems)
- [API Errors](#api-errors)
- [Docker Issues](#docker-issues)

---

## Installation Issues

### Python Version Mismatch

**Problem**: `ERROR: Python 3.11 or higher required`

**Solution**:
```bash
# Check Python version
python --version

# Install Python 3.11
sudo apt install python3.11 python3.11-venv

# Use specific version
python3.11 -m venv venv
```

### Dependency Installation Fails

**Problem**: `ERROR: Could not install packages due to an EnvironmentError`

**Solution**:
```bash
# Update pip
pip install --upgrade pip setuptools wheel

# Install with verbose output to see errors
pip install -r requirements.txt -v

# For specific package issues, try system dependencies
sudo apt install python3-dev libpcap-dev build-essential
```

### Node.js Version Issues

**Problem**: `error: Unsupported engine`

**Solution**:
```bash
# Check Node.js version
node --version

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Or use nvm
nvm install 18
nvm use 18
```

---

## Database Connection Problems

### Redis Connection Failed

**Problem**: `redis.exceptions.ConnectionError: Connection refused`

**Diagnosis**:
```bash
# Check Redis status
redis-cli ping

# Should return "PONG"
```

**Solutions**:

1. **Start Redis**:
```bash
# Docker
docker-compose up -d redis

# System service
sudo systemctl start redis

# Check logs
docker logs redis
```

2. **Check configuration**:
```bash
# Verify Redis URL
echo $REDIS_URL

# Test connection
redis-cli -u redis://localhost:6379 ping
```

3. **Redis authentication**:
```bash
# If password protected
redis-cli -u redis://:password@localhost:6379 ping
```

### SQLite Database Locked

**Problem**: `sqlite3.OperationalError: database is locked`

**Solutions**:

1. **Check for multiple processes**:
```bash
# Find processes using database
lsof ./backend/data/mapper.db

# Kill old processes
pkill -f "uvicorn app.main"
```

2. **Enable WAL mode** (Write-Ahead Logging):
```bash
# Open database
sqlite3 ./backend/data/mapper.db

# Enable WAL
PRAGMA journal_mode=WAL;
```

3. **Check permissions**:
```bash
# Ensure write access
chmod 664 ./backend/data/mapper.db
chmod 775 ./backend/data/
```

---

## Scanning Issues

### Permission Denied on Network Scan

**Problem**: `OSError: [Errno 1] Operation not permitted`

**Cause**: Network scanning requires elevated privileges.

**Solutions**:

1. **Grant capabilities to Python** (recommended):
```bash
# Find Python binary
which python3.11

# Grant network capabilities
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3.11
```

2. **Run with sudo** (not recommended):
```bash
sudo uvicorn app.main:app --reload
```

3. **Add user to pcap group**:
```bash
sudo groupadd pcap
sudo usermod -a -G pcap $USER
sudo chgrp pcap /usr/bin/nmap
sudo chmod 750 /usr/bin/nmap
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/nmap

# Log out and back in for group change
```

4. **Docker**: Ensure proper capabilities (already configured in `docker-compose.yml`):
```yaml
# docker-compose.yml
services:
  backend:
    cap_add:
      - NET_RAW
      - NET_ADMIN
    # Uses bridge networking (nts-net) — do NOT set network_mode: host
```

### No Devices Found During Scan

**Problem**: Scan completes but finds 0 devices

**Diagnosis**:
```bash
# Test network connectivity
ping 192.168.1.1

# Test nmap directly
sudo nmap -sn 192.168.1.0/24

# Check interface
ip addr show
```

**Solutions**:

1. **Verify target range**:
```bash
# Check .env
cat .env | grep SCAN_DEFAULT_RANGE

# Ensure range matches your network
# Example: 192.168.1.0/24 for home network
```

2. **Check firewall**:
```bash
# Temporarily disable firewall for testing
sudo ufw disable

# If successful, add rules
sudo ufw allow out to 192.168.0.0/16
```

3. **Network interface**:
```bash
# List interfaces
ip addr show

# Update .env with correct interface
SCAN_PASSIVE_INTERFACE=eth0  # or wlan0, enp0s3, etc.
```

4. **Try passive scanning first**:
```bash
# Uses passive monitoring, no active probing
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"type": "passive", "target": "all"}'
```

### Scan Timeout

**Problem**: `ScanTimeoutError: Scan exceeded maximum duration`

**Solutions**:

1. **Reduce scan range**:
```bash
# Instead of /16, use smaller ranges
# /24 = 256 hosts
# /25 = 128 hosts
# /26 = 64 hosts
```

2. **Lower scan intensity**:
```json
{
  "type": "full",
  "target": "192.168.1.0/24",
  "intensity": "light"
}
```

3. **Increase rate limit** (.env):
```bash
SCAN_RATE_LIMIT=2000  # Increase from 1000
```

4. **Check network congestion**:
```bash
# Monitor network usage during scan
iftop -i eth0
```

### SNMP Polling Fails

**Problem**: `SNMPTimeout: No response from device`

**Solutions**:

1. **Verify SNMP is enabled** on target devices

2. **Check community string**:
```bash
# Test with snmpwalk
snmpwalk -v2c -c public 192.168.1.1 system

# Update .env if different
SNMP_COMMUNITY=public
SNMP_VERSION=2c
```

3. **Check firewall** on target device:
```bash
# SNMP uses UDP port 161
# Ensure devices allow SNMP from scanner IP
```

4. **Increase timeout** (.env):
```bash
SNMP_TIMEOUT=10  # Increase from 5
SNMP_RETRIES=5   # Increase from 3
```

---

## WebSocket Problems

### WebSocket Connection Refused

**Problem**: Frontend cannot connect to WebSocket

**Diagnosis**:
```javascript
// Check browser console
// Should see: "WebSocket connecting to ws://localhost:8000/ws/topology"
```

**Solutions**:

1. **Verify backend is running**:
```bash
curl http://localhost:8000/api/topology/stats
```

2. **Check WebSocket URL** in frontend .env:
```bash
# frontend/.env.local
VITE_WS_URL=ws://localhost:8000/ws/topology

# For HTTPS, use wss://
VITE_WS_URL=wss://yourdomain.com/ws/topology
```

3. **Check proxy configuration** (vite.config.ts):
```typescript
server: {
  proxy: {
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true
    }
  }
}
```

4. **Firewall/Security**:
```bash
# Allow WebSocket port
sudo ufw allow 8000/tcp
```

### Frequent WebSocket Disconnections

**Problem**: WebSocket disconnects and reconnects repeatedly

**Solutions**:

1. **Increase heartbeat interval** (.env):
```bash
WS_HEARTBEAT_INTERVAL=60  # Increase from 30
WS_TIMEOUT=600            # Increase from 300
```

2. **Check network stability**:
```bash
# Monitor connection
ping -c 100 localhost

# Check for packet loss
```

3. **Proxy/Load Balancer**:
- Ensure WebSocket upgrade headers are passed through
- Increase timeout on reverse proxy (nginx, traefik, etc.)

**nginx example**:
```nginx
location /ws {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

### WebSocket Events Not Received

**Problem**: Connected but no events arrive

**Diagnosis**:
```bash
# Check Redis pub/sub
redis-cli
> SUBSCRIBE topology:events
> # Should see messages when events occur
```

**Solutions**:

1. **Verify event publishing**:
```python
# Check backend logs
# Should see: "Publishing event: device_added"
```

2. **Check subscription**:
```javascript
// Frontend should subscribe to channels
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['topology:events', 'alerts:new']
}));
```

3. **Redis connection**:
```bash
# Ensure Redis is running and accessible
redis-cli ping
```

---

## Performance Issues

### Slow Graph Rendering

**Problem**: Graph takes a long time to render or is laggy

**Solutions**:

1. **Reduce visible nodes**:
- Apply filters (device type, VLAN, risk level)
- Limit graph to critical devices
- Use pagination for large networks

2. **Change layout algorithm**:
```typescript
// Default is dagre (hierarchical) - generally fast
// Force-directed (cola) can be slower on large graphs
// Try grid or circle for simpler layouts
setLayoutMode('dagre');   // Hierarchical (default, fast)
setLayoutMode('grid');    // Grid (fast)
setLayoutMode('cola');    // Force-directed (slower)
```

3. **Disable animations**:
```typescript
// In cytoscape-config.ts layout options
{
  name: 'dagre',
  animate: false,  // Disable animation for faster render
}
```

4. **Browser performance**:
- Close other tabs
- Disable browser extensions
- Use Chrome/Edge (better Cytoscape performance)

### High Backend CPU Usage

**Problem**: Backend consumes excessive CPU

**Diagnosis**:
```bash
# Monitor CPU usage
top -p $(pgrep -f uvicorn)

# Check running scans
curl http://localhost:8000/api/scans?status=running
```

**Solutions**:

1. **Reduce scan frequency**:
```bash
# .env - Increase interval (minutes, 0 = disabled)
SCAN_INTERVAL_MINUTES=30   # Every 30 minutes instead of 5
```

2. **Limit scan rate**:
```bash
SCAN_RATE_LIMIT=500  # Reduce from 1000
```

3. **Cancel unnecessary scans**:
```bash
# List active scans
curl http://localhost:8000/api/scans?status=running

# Cancel scan
curl -X DELETE http://localhost:8000/api/scans/{scan_id}
```

4. **Optimize database queries**:
```bash
# Ensure SQLite indexes exist
# See SETUP.md for database configuration
```

### Memory Leaks

**Problem**: Memory usage grows over time

**Solutions**:

1. **Graph cache cleanup**:
```python
# Ensure cache has TTL
CACHE_TTL_TOPOLOGY=60  # Expire after 60 seconds
```

2. **WebSocket connection cleanup**:
```python
# Check for orphaned connections
# Backend should clean up on disconnect
```

3. **Restart services**:
```bash
# Temporary fix
docker-compose restart backend

# Add healthcheck and auto-restart
```

---

## Frontend Problems

### Blank Page / White Screen

**Problem**: Frontend loads but shows blank page

**Diagnosis**:
```bash
# Check browser console for errors
# Common errors:
# - "Cannot read property of undefined"
# - "Module not found"
# - CORS error
```

**Solutions**:

1. **Clear cache and rebuild**:
```bash
cd frontend
rm -rf node_modules dist .vite
npm install
npm run dev
```

2. **Check API connection**:
```bash
# Verify backend is accessible
curl http://localhost:8000/api/topology/stats
```

3. **CORS configuration**:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Components Not Updating

**Problem**: UI doesn't reflect changes

**Solutions**:

1. **Check WebSocket connection**:
```javascript
// Browser console should show:
// "WebSocket connected"
```

2. **Verify state updates**:
```javascript
// Check Zustand store updates
console.log(useTopologyStore.getState());
```

3. **Force re-render**:
```bash
# Hard refresh browser
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

### Module Not Found Errors

**Problem**: `Error: Cannot find module '@/components/...'`

**Solutions**:

1. **Check TypeScript paths** (tsconfig.json):
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

2. **Check Vite alias** (vite.config.ts):
```typescript
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src')
  }
}
```

3. **Reinstall dependencies**:
```bash
rm -rf node_modules package-lock.json
npm install
```

---

## API Errors

### 400 Bad Request

**Problem**: `{"error": {"code": "VALIDATION_ERROR", ...}}`

**Solution**: Check request format matches API schema

```bash
# Example correct format
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{
    "type": "full",
    "target": "192.168.1.0/24",
    "intensity": "normal"
  }'
```

### 500 Internal Server Error

**Problem**: Backend returns 500 error

**Diagnosis**:
```bash
# Check backend logs
docker-compose logs backend

# Look for stack traces and exceptions
```

**Solutions**:

1. **Database connection issue** - See [Database Connection Problems](#database-connection-problems)

2. **Missing environment variables**:
```bash
# Verify all required vars are set
cat .env
```

3. **Check backend health**:
```bash
curl http://localhost:8000/health
```

### 503 Service Unavailable

**Problem**: Backend not responding

**Solutions**:

1. **Check backend is running**:
```bash
docker-compose ps backend
# or
ps aux | grep uvicorn
```

2. **Check resource limits**:
```bash
# Check available memory
free -h

# Check disk space
df -h
```

3. **Restart backend**:
```bash
docker-compose restart backend
```

---

## Docker Issues

### Container Won't Start

**Problem**: `Error: Container exited with code 1`

**Diagnosis**:
```bash
# Check container logs
docker-compose logs backend

# Check specific container
docker logs network-mapper-backend
```

**Solutions**:

1. **Port already in use**:
```bash
# Find process using port
lsof -i :8000

# Kill process or change port in docker-compose.yml
```

2. **Missing environment file**:
```bash
# Ensure .env exists
ls -la .env

# Copy from example if needed
cp .env.example .env
```

3. **Volume permission issues**:
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./data
```

### Docker Compose Network Issues

**Problem**: Services cannot communicate

**Solutions**:

1. **Check network**:
```bash
docker network ls
docker network inspect network-mapper_default
```

2. **Recreate network**:
```bash
docker-compose down
docker network prune
docker-compose up -d
```

3. **Use service names**:
```bash
# In .env, reference by service name
REDIS_URL=redis://redis:6379  # not localhost
```

### Docker Build Fails

**Problem**: `ERROR: failed to solve`

**Solutions**:

1. **Clear build cache**:
```bash
docker-compose build --no-cache
```

2. **Check Dockerfile syntax**:
```bash
docker build -t test ./backend
```

3. **Update base image**:
```bash
docker pull python:3.11-slim
```

---

## Getting Additional Help

If issues persist after trying these solutions:

1. **Check Documentation**:
   - [SETUP.md](SETUP.md)
   - [ARCHITECTURE.md](ARCHITECTURE.md)
   - [API.md](API.md)

2. **Enable Debug Mode**:
```bash
# Backend
LOG_LEVEL=DEBUG

# Frontend
VITE_DEBUG=true
```

3. **Collect Diagnostic Info**:
```bash
# System info
uname -a
python --version
node --version
docker --version

# Service status
docker-compose ps
systemctl status redis

# Logs
docker-compose logs > logs.txt
```

4. **Open GitHub Issue** with:
   - Problem description
   - Steps to reproduce
   - Error messages/logs
   - System info
   - What you've tried

5. **Join Community**:
   - GitHub Discussions
   - Discord (if available)
   - Stack Overflow (tag: `network-topology-mapper`)

---

**Remember**: Most issues are related to configuration, permissions, or environment setup. Double-check your .env file and ensure all services are running!
