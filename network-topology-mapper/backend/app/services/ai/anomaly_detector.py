import logging
import uuid
from datetime import datetime
from typing import Any
import numpy as np

from app.db.sqlite_db import sqlite_db
from app.services.realtime.event_bus import event_bus

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """IsolationForest-based anomaly detection on topology changes."""

    def __init__(self):
        self._model = None
        self._feature_history: list[list[float]] = []
        try:
            from sklearn.ensemble import IsolationForest
            self._model_class = IsolationForest
        except ImportError:
            logger.warning("scikit-learn not installed. Anomaly detection unavailable.")
            self._model_class = None

    def _extract_features(self, topology_snapshot: dict) -> list[float]:
        devices = topology_snapshot.get("devices", [])
        connections = topology_snapshot.get("connections", [])

        total_devices = len(devices)
        total_connections = len(connections)

        type_counts = {}
        for d in devices:
            dt = d.get("device_type", "unknown")
            type_counts[dt] = type_counts.get(dt, 0) + 1

        online = sum(1 for d in devices if d.get("status") == "online")
        offline = sum(1 for d in devices if d.get("status") == "offline")

        avg_risk = np.mean([d.get("risk_score", 0) for d in devices]) if devices else 0

        active_conns = sum(1 for c in connections if c.get("status") == "active")
        flapping = sum(1 for c in connections if c.get("status") == "flapping")

        return [
            total_devices,
            total_connections,
            online,
            offline,
            float(avg_risk),
            active_conns,
            flapping,
            type_counts.get("router", 0),
            type_counts.get("switch", 0),
            type_counts.get("server", 0),
            type_counts.get("workstation", 0),
        ]

    def train(self, snapshots: list[dict]):
        if not self._model_class or len(snapshots) < 5:
            return

        features = [self._extract_features(s) for s in snapshots]
        self._feature_history = features

        self._model = self._model_class(
            n_estimators=100,
            contamination=0.1,
            random_state=42,
        )
        X = np.array(features)
        self._model.fit(X)
        logger.info("Anomaly detector trained on %d snapshots", len(snapshots))

    def detect(self, current_topology: dict) -> list[dict]:
        anomalies = []

        if self._model:
            features = self._extract_features(current_topology)
            X = np.array([features])
            prediction = self._model.predict(X)
            score = self._model.decision_function(X)[0]

            if prediction[0] == -1:
                anomalies.append({
                    "id": str(uuid.uuid4()),
                    "alert_type": "anomaly",
                    "severity": "high" if score < -0.5 else "medium",
                    "title": "Topology anomaly detected",
                    "description": f"Current topology deviates from baseline (score: {score:.3f})",
                    "details": {"anomaly_score": float(score), "features": features},
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "open",
                })

        # Rule-based checks
        devices = current_topology.get("devices", [])
        connections = current_topology.get("connections", [])

        # Check for flapping links
        flapping = [c for c in connections if c.get("status") == "flapping"]
        for conn in flapping:
            anomalies.append({
                "id": str(uuid.uuid4()),
                "alert_type": "flapping",
                "severity": "high",
                "title": f"Link flapping: {conn.get('source_id', '')[:8]} <-> {conn.get('target_id', '')[:8]}",
                "description": "Connection state is unstable",
                "device_id": conn.get("source_id"),
                "details": conn,
                "created_at": datetime.utcnow().isoformat(),
                "status": "open",
            })

        # Check for new unknown devices
        for device in devices:
            if device.get("device_type") == "unknown" and device.get("discovery_method") == "passive":
                anomalies.append({
                    "id": str(uuid.uuid4()),
                    "alert_type": "new_device",
                    "severity": "medium",
                    "title": f"Unknown device detected: {device.get('ip', '')}",
                    "description": f"MAC: {device.get('mac', 'unknown')}, Vendor: {device.get('vendor', 'unknown')}",
                    "device_id": device.get("id"),
                    "details": device,
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "open",
                })

        # Store anomalies as alerts
        for anomaly in anomalies:
            sqlite_db.create_alert(anomaly)
            event_bus.publish_alert(anomaly)

        return anomalies


anomaly_detector = AnomalyDetector()
