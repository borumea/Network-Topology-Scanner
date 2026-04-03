# Network Topology Scanner

Network discovery and visualization tool. Scans your LAN with nmap + SNMP + passive capture, infers device connections, and renders an interactive topology graph. FastAPI backend, React + Cytoscape.js frontend, SQLite + NetworkX topology database.

> **AI agents:** Read `CLAUDE.md` first — it is the authoritative reference for this codebase.

---

## Quickstart (Local Development)

Local development is the default workflow. Docker is optional and used for the demo lab only.

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

## Optional Demo Mode (Docker)

Use this mode when you want the simulated network devices in `demo/`.

```bash
cd network-topology-mapper
./demo.sh up      # starts all services + 5 demo network containers (~60s)
./demo.sh scan    # triggers scan against demo network
./demo.sh status  # health check
```

The demo network has: nginx web server, Postgres DB, file server (SSH+SMB), JetDirect printer, SNMP device — all on `nts-net` (172.20.0.0/24).

```bash
./demo.sh down    # tear down when done
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- nmap
- Redis 7 (optional, recommended for pub/sub)

Optional for demo mode:
- Docker 20.10+ and Docker Compose 2.0+
- 4 GB RAM available for Docker

For local (non-Docker) development, see `INSTALL_GUIDE.md`.

---

## Ports

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

## Scan Your Own Network

```bash
# Trigger a scan against your LAN
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "192.168.1.0/24"}'

# Check topology stats
curl http://localhost:8000/api/topology/stats | jq
```

---

## Docs

- `CLAUDE.md` — agent constitution, directory structure, sacred rules
- `QUICK_START_GUIDE.md` — local quickstart + optional demo mode
- `INSTALL_GUIDE.md` — database setup for local dev
- `docs/ARCHITECTURE.md` — system architecture, scan pipeline, data flow
- `docs/API.md` — full API reference
- `docs/SETUP.md` — detailed setup guide
- `docs/CONTRIBUTING.md` — branch conventions, PR process
- `docs/TROUBLESHOOTING.md` — common issues and fixes

---

## Tech Stack

Python 3.11 / FastAPI / SQLite + NetworkX / Redis 7 — React 18 / TypeScript / Vite / Cytoscape.js / Zustand / Tailwind CSS
