from fastapi import APIRouter, Query
from typing import Optional

from app.services.ai.report_generator import report_generator
from app.services.graph.resilience_scorer import resilience_scorer
from app.services.graph.spof_detector import spof_detector
from app.services.graph.graph_builder import graph_builder
from app.db.sqlite_db import sqlite_db

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/reports/resilience")
async def get_resilience_report():
    resilience = resilience_scorer.calculate_global_resilience()
    spofs = spof_detector.find_spofs()
    topology = graph_builder.get_full_topology()

    stats = {
        "total_devices": len(topology.get("devices", [])),
        "total_connections": len(topology.get("connections", [])),
    }

    report = await report_generator.generate_resilience_report(resilience, spofs, stats)
    return report


@router.get("/reports/changelog")
def get_changelog(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    limit: int = Query(50),
):
    snapshots = sqlite_db.get_snapshots(limit=limit)

    if from_date:
        snapshots = [s for s in snapshots if s.get("created_at", "") >= from_date]
    if to_date:
        snapshots = [s for s in snapshots if s.get("created_at", "") <= to_date]

    changes = []
    for i in range(len(snapshots) - 1):
        current = snapshots[i]
        previous = snapshots[i + 1]

        device_diff = current.get("device_count", 0) - previous.get("device_count", 0)
        conn_diff = current.get("connection_count", 0) - previous.get("connection_count", 0)
        risk_diff = current.get("risk_score", 0) - previous.get("risk_score", 0)

        changes.append({
            "timestamp": current.get("created_at"),
            "device_count": current.get("device_count", 0),
            "device_diff": device_diff,
            "connection_count": current.get("connection_count", 0),
            "connection_diff": conn_diff,
            "risk_score": current.get("risk_score", 0),
            "risk_diff": round(risk_diff, 2),
        })

    return {"changes": changes, "snapshots": snapshots}
