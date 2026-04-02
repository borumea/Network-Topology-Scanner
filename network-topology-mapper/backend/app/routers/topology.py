from fastapi import APIRouter, Query
from typing import Optional

from app.services.graph.graph_builder import graph_builder
from app.db.topology_db import topology_db
from app.services.graph.resilience_scorer import resilience_scorer

router = APIRouter(prefix="/api", tags=["topology"])


@router.get("/topology")
def get_topology(
    layer: Optional[str] = Query(None, description="physical|logical|application"),
    vlan: Optional[int] = Query(None),
    subnet: Optional[str] = Query(None),
    device_type: Optional[str] = Query(None),
    risk_min: Optional[float] = Query(None),
):
    topology = graph_builder.get_full_topology(
        layer=layer, vlan=vlan, subnet=subnet,
        device_type=device_type, risk_min=risk_min,
    )
    return topology


@router.get("/topology/stats")
def get_topology_stats():
    topology = graph_builder.get_full_topology()
    devices = topology.get("devices", [])
    connections = topology.get("connections", [])

    online = sum(1 for d in devices if d.get("status") == "online")
    offline = sum(1 for d in devices if d.get("status") == "offline")
    degraded = sum(1 for d in devices if d.get("status") == "degraded")

    active_conns = sum(1 for c in connections if c.get("status", "active") == "active")

    type_counts = {}
    for d in devices:
        dt = d.get("device_type", "unknown")
        type_counts[dt] = type_counts.get(dt, 0) + 1

    avg_risk = sum(d.get("risk_score", 0) for d in devices) / max(len(devices), 1)

    # Get resilience info
    try:
        resilience = resilience_scorer.calculate_global_resilience()
        risk_score = resilience.get("score", 0)
        spof_count = resilience.get("spof_count", 0)
    except Exception:
        risk_score = round(avg_risk * 10, 1)
        spof_count = 0

    return {
        "total_devices": len(devices),
        "total_connections": len(connections),
        "online": online,
        "offline": offline,
        "degraded": degraded,
        "active_connections": active_conns,
        "connection_uptime_pct": round(active_conns / max(len(connections), 1) * 100, 1),
        "type_counts": type_counts,
        "risk_score": risk_score,
        "spof_count": spof_count,
        "avg_device_risk": round(avg_risk, 3),
    }


@router.post("/topology/clear")
def clear_topology():
    topology_db.clear_all()
    return {"status": "ok", "message": "All devices, connections, and dependencies cleared."}


@router.get("/devices/{device_id}")
def get_device(device_id: str):
    device = topology_db.get_device(device_id)
    if not device:
        # Search in topology
        topology = graph_builder.get_full_topology()
        for d in topology.get("devices", []):
            if d.get("id") == device_id:
                device = d
                break
    if not device:
        return {"error": "Device not found"}

    # Get risk details
    risk_details = resilience_scorer.calculate_device_risk(device_id)
    device["risk_details"] = risk_details

    return device


@router.get("/devices/{device_id}/connections")
def get_device_connections(device_id: str):
    topology = graph_builder.get_full_topology()
    connections = [
        c for c in topology.get("connections", [])
        if c.get("source_id") == device_id or c.get("target_id") == device_id
    ]
    return {"device_id": device_id, "connections": connections}


@router.get("/devices/{device_id}/dependencies")
def get_device_dependencies(device_id: str):
    topology = graph_builder.get_full_topology()
    deps = topology.get("dependencies", [])

    upstream = [d for d in deps if d.get("source_id") == device_id]
    downstream = [d for d in deps if d.get("target_id") == device_id]

    return {
        "device_id": device_id,
        "depends_on": upstream,
        "depended_by": downstream,
    }
