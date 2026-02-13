# Network Scanning Issue - Troubleshooting Guide for Next Claude

## 🔴 CRITICAL ISSUE: nmap Scanning Fails on Windows

**Date**: 2026-02-12
**Status**: RESOLVED - bypassed python-nmap, using direct subprocess calls
**Priority**: HIGH - Prevents core functionality (network device discovery)

---

## 📋 Current System State

### ✅ Working Components
- **Backend**: Running on port 5000 (http://0.0.0.0:5000)
- **Frontend**: Running on port 3002 (http://localhost:3002)
- **WebSocket**: Connected and working (direct connection to ws://localhost:5000/ws/topology)
- **Databases**:
  - Neo4j: bolt://localhost:7687 (Docker container: network-topology-mapper-neo4j-1)
  - Redis: redis://localhost:6379 (Docker container: network-topology-mapper-redis-1)
  - SQLite: backend/data/mapper.db
- **nmap**: Installed at `C:\Program Files (x86)\Nmap\nmap.exe`

### ❌ Broken Component
- **Network Scanning**: ALL scan types fail with nmap assertion error

---

## 🐛 The Problem

### Error Message
```
[ERROR] app.services.scanner.active_scanner: Nmap scan failed:
'Assertion failed: htn.toclock_running == true, file ..\Target.cc, line 503\r\n'
```

### What Fails
- **ALL intensity levels** fail with the same error:
  - **Light** (`-sn -T3`): Simple ping sweep - FAILS
  - **Normal** (`-sS -sV -T4 --top-ports 100`): Port scan - FAILS
  - **Deep** (`-sS -sV -sC -O -T4 -p-`): Full scan - FAILS

### What Works
- **Direct nmap call** works fine:
  ```bash
  "C:\Program Files (x86)\Nmap\nmap.exe" -sn 172.16.19.249
  # Result: Successfully scans and returns results
  ```

### Root Cause
The **python-nmap library** (used in `backend/app/services/scanner/active_scanner.py`) is calling nmap incorrectly on Windows, causing nmap to crash internally. This is a known issue with python-nmap on Windows.

---

## 🔍 What We've Tried

1. ✅ Verified nmap is installed and in PATH
2. ✅ Tested nmap manually - works fine
3. ✅ Tried different scan intensities (light, normal, deep) - all fail
4. ✅ Checked scan parameters are being passed correctly
5. ✅ Confirmed the backend is receiving scan requests
6. ❌ Attempted to modify scanner to call nmap directly (incomplete)

---

## 💡 Solution Options

### Option 1: Bypass python-nmap Library (RECOMMENDED)

**File**: `backend/app/services/scanner/active_scanner.py`

Replace the python-nmap library call with a direct subprocess call:

```python
# Instead of:
self._nmap.scan(hosts=target, arguments=args)

# Use subprocess:
import subprocess
cmd = ["nmap", "-oX", "-"] + args.split() + [target]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

# Then parse the XML output manually
import xml.etree.ElementTree as ET
root = ET.fromstring(result.stdout)
# Parse hosts, ports, services, etc.
```

**Pros**:
- Works around python-nmap Windows bug
- Uses nmap directly (which we know works)
- More control over nmap execution

**Cons**:
- Need to implement XML parsing
- More code to maintain

---

### Option 2: Use WSL (Windows Subsystem for Linux)

Run the backend in WSL instead of native Windows:

```bash
# In WSL Ubuntu
cd /mnt/c/Users/rbrad/Desktop/Claude_Workspace/NetworkTOPO/network-topology-mapper/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo apt install nmap
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

**Pros**:
- python-nmap works correctly on Linux
- True Linux environment
- Nmap runs with proper privileges

**Cons**:
- Requires WSL setup
- Additional complexity
- May need to update Docker connection strings

---

### Option 3: Replace python-nmap with python-nmap3

There's a newer library `python-nmap3` that might not have this bug:

```bash
pip uninstall python-nmap
pip install python-nmap3
```

Then update the scanner code to use the new API.

---

### Option 4: Enable Mock Data (TEMPORARY WORKAROUND)

**File**: `backend/app/main.py` (lines 73-77)

Currently disabled:
```python
# Skip mock data - using real network scanning
global _mock_topology
_mock_topology = {"devices": [], "connections": []}
```

Change to:
```python
# Load mock data
global _mock_topology
_mock_topology = load_mock_data()
```

This loads 260 mock devices so the UI can be fully tested while fixing the real scanning issue.

---

## 📁 Relevant Files

### Backend Scanner Files
- `backend/app/services/scanner/active_scanner.py` - Main scanner (line 40 has the failing call)
- `backend/app/services/scanner/scan_coordinator.py` - Orchestrates scans
- `backend/app/routers/scans.py` - API endpoint for triggering scans
- `backend/app/main.py` - Lines 73-77 for mock data toggle

### Configuration
- `backend/.env` - Environment configuration
- `backend/requirements.txt` - Has `python-nmap==0.7.1`

---

## 🌐 Network Information

**User's Network**: 172.16.0.0/16
**User's IP**: 172.16.19.249
**Recommended Scan Target**: 172.16.19.0/24 (their local subnet)

---

## 🔧 Port Configuration History

We had to change ports due to Hyper-V reservations:

**Hyper-V Reserved Ports on this machine**:
- 7922-8021 (includes port 8000)
- 8022-8121 (includes port 8080)

**Current Port Configuration**:
- Backend: **5000** ✅
- Frontend: **3002** ✅ (3000 and 3001 were in use)
- Neo4j: 7474 (web), 7687 (bolt)
- Redis: 6379

**Files Updated for Port 5000**:
- `backend/start_backend.bat` - Line 17
- `frontend/vite.config.ts` - Lines 16, 20
- `frontend/src/hooks/useWebSocket.ts` - Line 5
- `frontend/.env.local` - Lines 1-2

---

## 📊 Database Status

### Docker Containers Running
```bash
docker ps
# Should show:
# - network-topology-mapper-neo4j-1 (healthy)
# - network-topology-mapper-redis-1 (healthy)
```

### Start Databases
```bash
cd network-topology-mapper
docker-compose -f docker-compose.databases.yml up -d
```

---

## 🚀 How to Start the Application

### Backend
```bash
cd network-topology-mapper
start_backend.bat  # Run as Administrator
# Or manually:
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

### Frontend
```bash
cd network-topology-mapper/frontend
npm run dev
# Will start on port 3000/3001/3002 depending on availability
```

---

## 🧪 Testing nmap

### Manual Test (This Works!)
```bash
"C:\Program Files (x86)\Nmap\nmap.exe" -sn 172.16.19.0/24
```

### Via Python (This Fails!)
```python
import nmap
nm = nmap.PortScanner()
nm.scan(hosts='172.16.19.0/24', arguments='-sn -T3')
# ERROR: Assertion failed: htn.toclock_running == true
```

---

## 📝 Recommended Fix Steps

1. **Immediate**: Implement Option 1 (subprocess call) in `active_scanner.py`
   - Replace python-nmap library call with subprocess
   - Parse nmap XML output
   - Test with: `172.16.19.0/24` using `-sn` flag

2. **Parse XML Output**: Implement helper function to parse nmap XML:
   ```python
   def _parse_nmap_xml(self, xml_string: str) -> list[dict]:
       root = ET.fromstring(xml_string)
       devices = []
       for host in root.findall('.//host'):
           # Parse host status, IP, MAC, ports, services
           # Return device dict matching current format
       return devices
   ```

3. **Test Light Scan**: Start with simple ping sweep
   - Target: `172.16.19.0/24`
   - Args: `-sn -T3`
   - Should discover at least the user's machine (172.16.19.249)

4. **Verify in UI**:
   - Open http://localhost:3002
   - Trigger scan
   - Watch devices appear on graph in real-time

---

## 🎯 Success Criteria

- [ ] Scan completes without assertion error
- [ ] At least 1 device discovered (user's machine: 172.16.19.249)
- [ ] Devices appear in Neo4j database
- [ ] Devices render on frontend graph visualization
- [ ] WebSocket broadcasts device discovery events

---

## 📚 Additional Context

### Mock Data Location
- Generator: `backend/app/services/mock_data.py`
- Generates 260 devices with realistic corporate topology
- Includes routers, switches, servers, workstations, APs, IoT devices

### Documentation
- Full API docs: http://localhost:5000/docs (when backend running)
- Project documentation: `docs/` folder
- Architecture: `docs/ARCHITECTURE.md`
- Setup guide: `docs/SETUP.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`

---

## 🔗 Related Issues

- WebSocket connection issue: RESOLVED (changed to direct connection on port 5000)
- Port binding issues: RESOLVED (using port 5000 now)
- Frontend proxy issues: RESOLVED (using direct WebSocket connection)

---

## ⚠️ Important Notes

1. **Mock data is currently DISABLED** - need to fix scanning or re-enable mock data
2. **Backend must run as Admin** for some nmap scans (SYN scan requires privileges)
3. **All previous scans show 0 devices** - this is expected due to the nmap crash
4. **User IP is 172.16.x.x** - NOT 192.168.x.x (update default scan targets)

---

## 💬 User Expectations

User wants to scan their **real network** (172.16.19.0/24) and discover actual devices. They've already tried multiple times and are frustrated that it's finding 0 devices. They need:

1. Working network scanning
2. Real device discovery
3. To see devices on the topology graph
4. To explore the full application features

---

**Good luck fixing this! The subprocess approach should work since we verified nmap works manually.** 🚀
