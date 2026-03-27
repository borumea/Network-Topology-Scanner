import asyncio
import logging
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.neo4j_client import neo4j_client
from app.db.sqlite_db import sqlite_db
from app.db.redis_client import redis_client
from app.services.realtime.ws_manager import ws_manager
from app.services.realtime.event_bus import event_bus
from app.routers import topology, scans, simulation, alerts, reports, snapshots
from app.routers import settings as settings_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _load_inmemory_mock():
    """Generate mock data for in-memory fallback only. Never writes to Neo4j."""
    from app.services.mock_data import generate_mock_topology
    mock = generate_mock_topology()
    logger.info("In-memory mock data ready: %d devices, %d connections",
                len(mock["devices"]), len(mock["connections"]))
    return mock


# Global mock storage for when Neo4j is unavailable
_mock_topology = None


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

    # Store event loop for thread-safe WebSocket broadcasts
    event_bus.set_loop(asyncio.get_event_loop())

    # Initialize databases
    neo4j_client.connect()
    sqlite_db.connect()
    redis_client.connect()

    # Mock data is only used as in-memory fallback when Neo4j is unavailable.
    # When Neo4j is available, start with 0 devices — real scans populate the graph.
    global _mock_topology
    if neo4j_client.available:
        device_count = neo4j_client.execute_read(
            "MATCH (d:Device) RETURN count(d) AS cnt"
        )
        cnt = device_count[0]["cnt"] if device_count else 0
        logger.info("Neo4j available with %d devices. No mock data loaded.", cnt)
        _mock_topology = None
    else:
        logger.info("Neo4j unavailable — loading in-memory mock data for fallback.")
        _mock_topology = _load_inmemory_mock()

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
    neo4j_client.close()
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
        "neo4j": neo4j_client.available,
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


# Override graph_builder to use mock data when Neo4j unavailable
_original_get_full_topology = None


def _patched_get_full_topology(layer=None, vlan=None, subnet=None,
                                device_type=None, risk_min=None):
    global _mock_topology
    if not neo4j_client.available and _mock_topology:
        from app.services.graph.graph_builder import GraphBuilder
        devices = list(_mock_topology.get("devices", []))
        connections = list(_mock_topology.get("connections", []))
        dependencies = list(_mock_topology.get("dependencies", []))

        if layer == "physical":
            phys_types = {"router", "switch", "ap", "firewall"}
            conn_types = {"ethernet", "fiber", "wireless"}
            devices = [d for d in devices if d.get("device_type") in phys_types]
            device_ids = {d["id"] for d in devices}
            connections = [c for c in connections
                          if c.get("connection_type") in conn_types
                          and c.get("source_id") in device_ids
                          and c.get("target_id") in device_ids]
            dependencies = []
        elif layer == "application":
            app_types = {"server", "firewall"}
            devices = [d for d in devices if d.get("device_type") in app_types]
            device_ids = {d["id"] for d in devices}
            connections = [c for c in connections
                          if c.get("source_id") in device_ids and c.get("target_id") in device_ids]

        if vlan is not None:
            devices = [d for d in devices if vlan in d.get("vlan_ids", [])]
        if subnet:
            devices = [d for d in devices if d.get("subnet") == subnet]
        if device_type:
            devices = [d for d in devices if d.get("device_type") == device_type]
        if risk_min is not None:
            devices = [d for d in devices if d.get("risk_score", 0) >= risk_min]

        device_ids = {d["id"] for d in devices}
        connections = [c for c in connections
                       if c.get("source_id") in device_ids and c.get("target_id") in device_ids]
        dependencies = [dep for dep in dependencies
                        if dep.get("source_id") in device_ids and dep.get("target_id") in device_ids]

        return {"devices": devices, "connections": connections, "dependencies": dependencies}

    return _original_get_full_topology(layer, vlan, subnet, device_type, risk_min)


def _patch_graph_builder():
    global _original_get_full_topology
    from app.services.graph.graph_builder import graph_builder
    _original_get_full_topology = graph_builder.get_full_topology
    graph_builder.get_full_topology = _patched_get_full_topology


# Apply the patch after import
_patch_graph_builder()
