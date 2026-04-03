# Quick Start Guide

## Local Development (Recommended)

The default path to a working topology graph runs directly on your machine.

```bash
cd network-topology-mapper/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

cd ../frontend
npm install
npm run dev
```

Open http://localhost:3000 to see the topology graph.

---

## Optional Demo Mode (Docker)

Use this mode when you want 5 simulated network devices.

```bash
cd network-topology-mapper

# Start full stack + demo network (~60s for all containers to reach healthy state)
./demo.sh up

# Trigger a scan once services are healthy
./demo.sh scan

# Open http://localhost:3000 to see the topology graph
```

**What you get:** nginx web server, Postgres DB, file server (SSH+SMB), JetDirect printer, SNMP device — all on `nts-net` (172.20.0.0/24). The backend scans them with nmap, runs connection inference, and renders a topology graph.

```bash
./demo.sh down    # tear down when done
```

---

## Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

## Scan Your Own Network

With the stack running, trigger a scan against your real LAN:

```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "192.168.1.0/24"}'

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

For detailed local setup steps, see `INSTALL_GUIDE.md`.

---

## Troubleshooting

**Graph shows no devices after scan:**
- Wait for scan to complete: `curl http://localhost:8000/api/scans | jq`
- Check scan target matches the demo network: `172.20.0.0/24`
- Try `./demo.sh scan` instead of a manual curl

**Services won't start:**
- Ensure backend and frontend terminals are both running
- Check for port conflicts: `lsof -i :3000; lsof -i :8000; lsof -i :7474`
- For demo mode only: try `./demo.sh down && ./demo.sh up`

**Frontend shows empty graph after scan completes:**
- Hard refresh: `Cmd+Shift+R` (macOS) or `Ctrl+Shift+R` (Linux)
- Check backend logs in the terminal running `uvicorn`

---

## More Documentation

- `CLAUDE.md` — agent constitution, directory structure, sacred rules
- `INSTALL_GUIDE.md` — manual database installation
- `docs/ARCHITECTURE.md` — system architecture
- `docs/API.md` — full API reference
- `docs/TROUBLESHOOTING.md` — common issues
