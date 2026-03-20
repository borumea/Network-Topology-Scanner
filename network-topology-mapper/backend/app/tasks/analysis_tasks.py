import logging
import uuid
from datetime import datetime

from app.services.graph.spof_detector import spof_detector
from app.services.graph.resilience_scorer import resilience_scorer
from app.services.ai.anomaly_detector import anomaly_detector
from app.services.graph.graph_builder import graph_builder
from app.db.sqlite_db import sqlite_db

logger = logging.getLogger(__name__)


def _train_anomaly_detector():
    """Train the anomaly detector on stored topology snapshots if enough data exists."""
    snapshots = sqlite_db.get_snapshots(limit=100)
    training_topologies = []
    for s in snapshots:
        topo = s.get("snapshot_data", {}).get("topology_json")
        if topo and isinstance(topo, dict):
            training_topologies.append(topo)

    if len(training_topologies) >= 5:
        anomaly_detector.train(training_topologies)
    else:
        logger.info(
            "Insufficient snapshots for anomaly training (%d with topology < 5), skipping",
            len(training_topologies),
        )


def run_analysis() -> dict:
    topology = graph_builder.get_full_topology()

    # Train on historical snapshots before detecting
    _train_anomaly_detector()

    spofs = spof_detector.find_spofs()
    resilience = resilience_scorer.calculate_global_resilience()
    anomalies = anomaly_detector.detect(topology)

    snapshot = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        "device_count": len(topology.get("devices", [])),
        "connection_count": len(topology.get("connections", [])),
        "risk_score": resilience.get("score", 0),
        "snapshot_data": {
            "spof_count": len(spofs),
            "anomaly_count": len(anomalies),
        },
    }
    sqlite_db.create_snapshot(snapshot)
    logger.info(
        "Analysis complete: %d devices, %d SPOFs, %d anomalies",
        snapshot["device_count"], len(spofs), len(anomalies),
    )

    return {
        "spofs": len(spofs),
        "resilience_score": resilience.get("score", 0),
        "anomalies": len(anomalies),
    }
