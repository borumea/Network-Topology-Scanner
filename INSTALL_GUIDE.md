# Installation Guide

> **Recommended:** Use Demo Mode for development — no manual installation required. Run `./demo.sh up` from `network-topology-mapper/`. This guide covers manual database installation for local bare-metal development.

---

## Manual Installation — Neo4j & Redis (macOS / Linux)

For running the backend directly (without Docker), you need Neo4j and Redis running locally.

### Option A: Run Databases via Docker (Easiest)

Start just the databases without the full app stack:

```bash
# Neo4j
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/changeme \
  neo4j:5-community

# Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Verify
curl http://localhost:7474        # Neo4j browser
redis-cli ping                    # Should return: PONG
```

---

### Option B: Install Neo4j via Homebrew (macOS)

```bash
brew install neo4j
brew services start neo4j

# Default credentials: neo4j / neo4j
# Change password on first login at http://localhost:7474
```

### Option B: Install Neo4j on Linux (Ubuntu/Debian)

```bash
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update && sudo apt install neo4j
sudo systemctl start neo4j && sudo systemctl enable neo4j
```

---

### Option C: Install Redis (macOS / Linux)

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis && sudo systemctl enable redis
```

**Verify:**
```bash
redis-cli ping   # Should return: PONG
```

---

## Configure the Backend

```bash
cd network-topology-mapper/backend
cp ../.env.example ../.env
```

Edit `.env`:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme

REDIS_URL=redis://localhost:6379/0

SQLITE_PATH=./data/mapper.db
```

---

## Start the Backend

```bash
cd network-topology-mapper/backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at http://localhost:8000

On startup, look for:
```
[INFO] Connected to Neo4j at bolt://localhost:7687
[INFO] Connected to Redis at localhost:6379
[INFO] SQLite initialized at data/mapper.db
```

---

## Verify

```bash
curl http://localhost:8000/api/health
# {"status": "ok"}

curl http://localhost:8000/api/topology/stats
# {"total_devices": 0, ...}
```

---

## Troubleshooting

**Neo4j connection failed:**
- Verify Neo4j is running: `curl http://localhost:7474`
- Check password in `.env` matches Neo4j
- Allow ports 7474 and 7687 through firewall if needed

**Redis connection refused:**
- macOS: `brew services start redis`
- Linux: `sudo systemctl start redis`
- Verify: `redis-cli ping`

**Permission denied on nmap:**
- macOS (Homebrew): nmap runs with required capabilities by default
- Linux: `sudo setcap cap_net_raw,cap_net_admin=eip $(which nmap)`
