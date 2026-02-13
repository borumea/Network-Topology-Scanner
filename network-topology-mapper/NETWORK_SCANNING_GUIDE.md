# Real Network Scanning Guide

## 🎯 Your System is Ready!

✅ Docker Desktop installed
✅ nmap installed
✅ Neo4j running (port 7687)
✅ Redis running (port 6379)
✅ Backend configured for real data

---

## 🚀 Start the Application

### Option 1: Run Backend Manually (Recommended)

Open PowerShell **as Administrator** and run:

```powershell
cd C:\Users\rbrad\Desktop\Claude_Workspace\NetworkTOPO\network-topology-mapper\backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or simply **double-click**: `start_backend.bat`

### Option 2: Run via Command Prompt

```cmd
cd C:\Users\rbrad\Desktop\Claude_Workspace\NetworkTOPO\network-topology-mapper
start_backend.bat
```

---

## 🔍 Scan Your Network

Once the backend is running:

### 1. Check Your Network Range

```powershell
# Find your local IP
ipconfig | findstr /i "ipv4"

# Common ranges:
# Home: 192.168.1.0/24
# Office: 10.0.0.0/8 or 172.16.0.0/12
```

### 2. Trigger a Scan

**Small scan (recommended first)**:
```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{
    "type": "active",
    "target": "192.168.1.0/24",
    "intensity": "light"
  }'
```

**Full network scan**:
```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{
    "type": "full",
    "target": "192.168.1.0/24",
    "intensity": "normal"
  }'
```

### 3. Monitor Scan Progress

```bash
# View scan status
curl http://localhost:8000/api/scans

# View discovered devices
curl http://localhost:8000/api/topology/stats
```

### 4. View in Browser

- Open: http://localhost:3000
- API docs: http://localhost:8000/docs

---

## 📊 Scan Types

### Light Scan
- Fast ping sweep
- Basic device discovery
- No port scanning
- ~30 seconds for /24 network

### Normal Scan
- Ping sweep + common ports
- Service detection
- ~2-4 minutes for /24 network

### Deep Scan
- Full port scan (1-65535)
- OS detection
- Service version detection
- ~10-20 minutes for /24 network

---

## 🎮 Example Workflow

```powershell
# 1. Start databases
cd network-topology-mapper
docker-compose -f docker-compose.databases.yml up -d

# 2. Start backend (in new terminal)
.\start_backend.bat

# 3. Start frontend (in another terminal)
cd frontend
npm run dev

# 4. Trigger scan
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"type":"active","target":"192.168.1.0/24"}'

# 5. Watch it discover!
# Open http://localhost:3000
```

---

## 🔧 Troubleshooting

### Backend won't start on port 8000

Run as Administrator or use a different port:
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 9000
```

Then update frontend .env:
```
VITE_API_URL=http://localhost:9000
```

### nmap permission denied

Run PowerShell as Administrator

### No devices found

1. Check you're scanning the right network range
2. Ensure firewall allows nmap
3. Try ping sweep first: `nmap -sn 192.168.1.0/24`

### Scan timeout

- Reduce target range (use /26 or /27)
- Lower intensity to "light"
- Check network connectivity

---

## 📝 What Gets Discovered

**Device Information**:
- IP address
- MAC address
- Hostname (if available)
- Device type (router, switch, server, etc.)
- Open ports and services
- Operating system (with deep scan)

**Network Connections**:
- Direct connections between devices
- Connection types
- Bandwidth estimates

**Topology Analysis**:
- Single Points of Failure (SPOFs)
- Critical devices
- Network resilience score
- Risk assessment

---

## 🎯 Next Steps After First Scan

1. **Explore the Graph** - Click on devices to see details
2. **Simulate Failures** - Test "what if" scenarios
3. **View Risk Analysis** - Identify weak points
4. **Generate AI Report** - Get recommendations
5. **Set Up Monitoring** - Schedule periodic scans

---

## 💡 Pro Tips

1. **Start Small**: Scan /26 or /27 first to test
2. **Off-Peak Hours**: Run deep scans during low-traffic times
3. **Whitelist IP**: Add your scanning IP to firewall whitelist
4. **Incremental**: Build topology over multiple scans
5. **Document**: Take screenshots of before/after network changes

---

## 🔐 Important Security Notes

- Only scan networks you own or have permission to scan
- Unauthorized network scanning may be illegal
- Use "light" intensity on production networks
- Schedule scans during maintenance windows
- Review your organization's security policy

---

**Ready to scan? Open a PowerShell terminal as Administrator and run `start_backend.bat`!**

Then trigger your first scan and watch your network topology appear in real-time! 🌐
