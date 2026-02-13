import logging
import uuid
from datetime import datetime

from app.tasks.celery_app import celery_app
from app.services.graph.spof_detector import spof_detector
from app.services.graph.resilience_scorer import resilience_scorer
from app.services.ai.anomaly_detector import anomaly_detector
from app.services.graph.graph_builder import graph_builder
from app.db.sqlite_db import sqlite_db

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.analysis_tasks.run_analysis")
def run_analysis():
    topology = graph_builder.get_full_topology()

    # Run SPOF detection
    spofs = spof_detector.find_spofs()

    # Run resilience scoring
    resilience = resilience_scorer.calculate_global_resilience()

    # Run anomaly detection
    anomalies = anomaly_detector.detect(topology)

    # Save topology snapshot
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

    return {
        "spofs": len(spofs),
        "resilience_score": resilience.get("score", 0),
        "anomalies": len(anomalies),
    }
