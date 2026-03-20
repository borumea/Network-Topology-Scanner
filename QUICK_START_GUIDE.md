# Quick Start Guide

## Demo Mode (Recommended — Zero Config)

The fastest path to a working topology graph. Uses Docker with 5 simulated network containers.

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
| Neo4j browser | http://localhost:7474 (neo4j / changeme) |

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

## Local Development (Without Docker)

For bare-metal backend development, see `INSTALL_GUIDE.md`.

---

## Troubleshooting

**Graph shows no devices after scan:**
- Wait for scan to complete: `curl http://localhost:8000/api/scans | jq`
- Check scan target matches the demo network: `172.20.0.0/24`
- Try `./demo.sh scan` instead of a manual curl

**Services won't start:**
- Ensure Docker has at least 4 GB RAM allocated
- Check for port conflicts: `lsof -i :3000; lsof -i :8000; lsof -i :7474`
- Try `./demo.sh down && ./demo.sh up`

**Frontend shows empty graph after scan completes:**
- Hard refresh: `Cmd+Shift+R` (macOS) or `Ctrl+Shift+R` (Linux)
- Check backend logs: `docker logs network-topology-mapper-backend-1`

---

## More Documentation

- `CLAUDE.md` — agent constitution, directory structure, sacred rules
- `INSTALL_GUIDE.md` — manual database installation
- `docs/ARCHITECTURE.md` — system architecture
- `docs/API.md` — full API reference
- `docs/TROUBLESHOOTING.md` — common issues
