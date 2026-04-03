import asyncio
import logging
import json
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.topology_db import topology_db
from app.db.sqlite_db import sqlite_db
from app.db.redis_client import redis_client
from app.services.realtime.ws_manager import ws_manager
from app.services.realtime.event_bus import event_bus
from app.routers import topology, scans, simulation, alerts, reports, snapshots
from app.routers import settings as settings_router

# --- Logging setup: console + file ---
os.makedirs("data", exist_ok=True)
LOG_FILE = os.path.join("data", "nts-debug.log")

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Console: INFO and above
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
root_logger.addHandler(console_handler)

# File: DEBUG and above (everything)
file_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"))
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)
logger.info("=== NTS DEBUG LOG START === Log file: %s", os.path.abspath(LOG_FILE))


async def _scheduled_scan_loop(interval_seconds: int):
    """Runs a full scan on the configured interval until cancelled."""
    from app.tasks.scan_tasks import scheduled_full_scan
    import threading

    logger.info("Scheduled scan loop started (interval: %ds)", interval_seconds)
    while True:
        await asyncio.sleep(interval_seconds)
        logger.info("Scheduled scan firing...")
        thread = threading.Thread(target=scheduled_full_scan, daemon=True)
        thread.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting Network Topology Mapper...")

    # Dump ALL settings for debugging
    logger.debug("=== CONFIGURATION DUMP ===")
    logger.debug("  redis_url:              %s", settings.redis_url)
    logger.debug("  sqlite_path:            %s", settings.sqlite_path)
    logger.debug("  scan_default_range:     %s", settings.scan_default_range)
    logger.debug("  scan_rate_limit:        %d", settings.scan_rate_limit)
    logger.debug("  scan_passive_interface: '%s'", settings.scan_passive_interface)
    logger.debug("  snmp_community:         %s", settings.snmp_community)
    logger.debug("  ssh_username:           '%s'", settings.ssh_username)
    logger.debug("  scan_interval_minutes:  %d", settings.scan_interval_minutes)
    logger.debug("  app_host:               %s", settings.app_host)
    logger.debug("  app_port:               %d", settings.app_port)
    logger.debug("  log_level:              %s", settings.log_level)
    logger.debug("  agent_mode:             %s", settings.agent_mode)
    logger.debug("  CWD:                    %s", os.getcwd())
    logger.debug("  Python:                 %s", sys.version)
    logger.debug("=== END CONFIG DUMP ===")

    # Store event loop for thread-safe WebSocket broadcasts
    event_bus.set_loop(asyncio.get_event_loop())

    # Initialize databases
    logger.debug("Connecting to SQLite...")
    sqlite_db.connect()
    logger.debug("Connecting to TopologyDB...")
    topology_db.connect()
    logger.debug("Connecting to Redis...")
    redis_client.connect()

    device_count = len(topology_db.get_all_devices())
    logger.info("Database status: topology_db=connected (%d devices), redis=%s, sqlite=connected",
                device_count, redis_client.available)

    # Start scheduled scan loop if configured
    _scan_task = None
    if settings.scan_interval_minutes > 0:
        interval = settings.scan_interval_minutes * 60
        _scan_task = asyncio.create_task(_scheduled_scan_loop(interval))
        logger.info("Scheduled scans enabled every %d minutes", settings.scan_interval_minutes)

    yield

    # Cleanup
    if _scan_task:
        _scan_task.cancel()
    topology_db.close()
    sqlite_db.close()
    redis_client.close()
    logger.info("Network Topology Mapper stopped.")


app = FastAPI(
    title="Network Topology Mapper",
    version="1.0.0",
    description="Network topology mapping, analysis, and visualization API",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(topology.router)
app.include_router(scans.router)
app.include_router(simulation.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(snapshots.router)
app.include_router(settings_router.router)


@app.get("/")
def root():
    return {"message": "Network Topology Mapper API", "version": "1.0.0"}


@app.get("/api/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "topology_db": topology_db.available,
        "redis": redis_client.available,
        "websocket_clients": ws_manager.connection_count,
        "snapshot_count": sqlite_db.get_snapshot_count(),
        "scan_interval_minutes": settings.scan_interval_minutes,
    }


@app.websocket("/ws/topology")
async def websocket_topology(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "ping":
                    await ws_manager.send_to(websocket, {"type": "pong"})
                elif msg_type == "subscribe":
                    await ws_manager.send_to(websocket, {
                        "type": "subscribed",
                        "data": {"channel": message.get("channel", "topology")}
                    })
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        ws_manager.disconnect(websocket)
