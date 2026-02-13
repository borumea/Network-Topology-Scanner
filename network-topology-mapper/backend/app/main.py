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
from app.routers import topology, scans, simulation, alerts, reports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_mock_data():
    """Load mock data if Neo4j is empty or unavailable."""
    from app.services.mock_data import generate_mock_topology, generate_mock_alerts, generate_mock_scans

    mock = generate_mock_topology()
    mock_alerts = generate_mock_alerts()
    mock_scans = generate_mock_scans()

    if neo4j_client.available:
        # Clear old data and load fresh mock data
        logger.info("Clearing Neo4j and loading mock data...")
        neo4j_client.clear_all()
        from app.services.graph.graph_builder import graph_builder
        graph_builder.bulk_upsert(
            mock["devices"], mock["connections"], mock.get("dependencies", [])
        )
        logger.info("Mock data loaded: %d devices, %d connections",
                    len(mock["devices"]), len(mock["connections"]))
    else:
        logger.info("Neo4j unavailable. Mock data stored in memory.")

    # Load mock alerts and scans into SQLite
    for alert in mock_alerts:
        try:
            sqlite_db.create_alert(alert)
        except Exception:
            pass

    for scan in mock_scans:
        try:
            sqlite_db.create_scan(scan)
        except Exception:
            pass

    return mock


# Global mock storage for when Neo4j is unavailable
_mock_topology = None


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

    # Load mock data into Neo4j so the UI has something to display
    global _mock_topology
    _mock_topology = load_mock_data()

    yield

    # Cleanup
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


@app.get("/")
def root():
    return {"message": "Network Topology Mapper API", "version": "1.0.0"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "neo4j": neo4j_client.available,
        "redis": redis_client.available,
        "websocket_clients": ws_manager.connection_count,
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
