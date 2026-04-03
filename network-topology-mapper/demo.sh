#!/usr/bin/env bash
# =============================================================================
# NTS Demo Convenience Script
# =============================================================================
# Usage:
#   ./demo.sh up      — bring up full stack + demo containers
#   ./demo.sh down    — tear down stack and remove volumes
#   ./demo.sh scan    — trigger an active scan against the demo subnet
#   ./demo.sh status  — check backend health
#   ./demo.sh logs    — follow all container logs

set -euo pipefail

DEMO_SUBNET="172.20.0.0/24"
COMPOSE="docker-compose -f docker-compose.yml -f docker-compose.demo.yml --env-file .env.demo"

case "${1:-}" in
  up)
    echo "Starting NTS + demo network..."
    $COMPOSE up -d --build
    echo ""
    echo "Stack is coming up. Services:"
    $COMPOSE ps
    echo ""
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo ""
    echo "Run './demo.sh scan' once all services are healthy."
    ;;

  down)
    echo "Stopping and removing volumes..."
    $COMPOSE down -v
    ;;

  scan)
    echo "Triggering active scan against demo subnet: $DEMO_SUBNET"
    RESPONSE=$(curl -s -X POST http://localhost:8000/api/scans \
      -H "Content-Type: application/json" \
      -d "{\"type\": \"active\", \"target\": \"$DEMO_SUBNET\", \"intensity\": \"normal\"}")
    echo "$RESPONSE"
    SCAN_ID=$(echo "$RESPONSE" | grep -o '"scan_id":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$SCAN_ID" ]; then
      echo ""
      echo "Scan started: $SCAN_ID"
      echo "Poll status: curl http://localhost:8000/api/scans/$SCAN_ID"
    fi
    ;;

  status)
    echo "Backend health:"
    curl -s http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null \
      || curl -s http://localhost:8000/api/health
    ;;

  logs)
    $COMPOSE logs -f
    ;;

  *)
    echo "Usage: $0 {up|down|scan|status|logs}"
    exit 1
    ;;
esac
