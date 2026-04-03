# Network Topology Scanner

Network discovery and visualization tool. Scans your LAN with nmap + SNMP + passive capture, infers device connections, and renders an interactive topology graph. FastAPI backend, React + Cytoscape.js frontend, SQLite + NetworkX topology database.

> **AI agents:** Read `CLAUDE.md` first — it is the authoritative reference for this codebase.

---

## Quickstart

### Prerequisites

- Python 3.11+
- Node.js 18+
- nmap

### Run

```bash
cd network-topology-mapper

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd network-topology-mapper/frontend
npm install
npm run dev
```

Open http://localhost:3000, click **Scan** in the sidebar, and scan your network.

---

## Ports

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

## Scan Your Own Network

Use the Scan page in the UI, or via CLI:

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"type": "full", "target": "192.168.1.0/24", "intensity": "normal"}'
```

---

## Docs

- `CLAUDE.md` — agent constitution, directory structure, sacred rules
- `QUICK_START_GUIDE.md` — standalone quickstart path
- `INSTALL_GUIDE.md` — bare-metal setup details
- `docs/ARCHITECTURE.md` — system architecture, scan pipeline, data flow
- `docs/API.md` — full API reference
- `docs/CONTRIBUTING.md` — branch conventions, PR process
- `docs/TROUBLESHOOTING.md` — common issues and fixes

---

## Tech Stack

Python 3.11 / FastAPI / SQLite + NetworkX / Redis (optional) — React 18 / TypeScript / Vite / Cytoscape.js / Zustand / Tailwind CSS
