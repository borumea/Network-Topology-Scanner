# Quick Start Guide

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- nmap

### Install & Run

```bash
cd network-topology-mapper

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal, from network-topology-mapper/)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 to see the topology graph.

---

## Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

## Scan Your Network

Click **Scan** in the sidebar, enter your subnet (e.g. `192.168.1.0/24`), select intensity, and hit scan.

Or via CLI:

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"type": "full", "target": "192.168.1.0/24", "intensity": "normal"}'

# Check progress
curl http://localhost:8000/api/scans | jq

# View results
curl http://localhost:8000/api/topology/stats | jq
```

---

## Check Your Topology

```bash
# Stats
curl http://localhost:8000/api/topology/stats | jq

# Full topology (nodes + edges)
curl http://localhost:8000/api/topology | jq

# Alerts
curl http://localhost:8000/api/alerts | jq
```

---

## Troubleshooting

**Graph shows no devices after scan:**
- Wait for scan to complete: `curl http://localhost:8000/api/scans | jq`
- Verify nmap is installed: `nmap --version`
- On Linux, nmap may need elevated privileges: `sudo setcap cap_net_raw,cap_net_admin=eip $(which nmap)`

**Backend won't start:**
- Check Python version: `python --version` (needs 3.11+)
- Make sure venv is activated
- Check port 8000 isn't in use

**Frontend shows empty graph after scan completes:**
- Hard refresh: `Cmd+Shift+R` (macOS) or `Ctrl+Shift+R` (Windows/Linux)
- Check backend terminal for errors

---

## More Documentation

- `CLAUDE.md` — agent constitution, directory structure, sacred rules
- `INSTALL_GUIDE.md` — detailed setup
- `docs/ARCHITECTURE.md` — system architecture
- `docs/API.md` — full API reference
- `docs/TROUBLESHOOTING.md` — common issues
