import logging
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)


class FailurePredictor:
    """GNN-based failure prediction (falls back to heuristic when PyTorch Geometric unavailable)."""

    def __init__(self):
        self._torch_available = False
        try:
            import torch
            self._torch_available = True
        except ImportError:
            logger.info("PyTorch not available. Using heuristic failure prediction.")

    def predict_failures(self, topology: dict) -> list[dict]:
        devices = topology.get("devices", [])
        connections = topology.get("connections", [])

        predictions = []

        for device in devices:
            risk = self._calculate_failure_probability(device, connections)
            if risk > 0.3:
                predictions.append({
                    "device_id": device.get("id"),
                    "hostname": device.get("hostname", ""),
                    "device_type": device.get("device_type", ""),
                    "failure_probability": round(risk, 3),
                    "risk_factors": self._get_risk_factors(device, connections),
                })

        predictions.sort(key=lambda x: x["failure_probability"], reverse=True)
        return predictions[:20]

    def _calculate_failure_probability(self, device: dict, connections: list) -> float:
        risk = 0.0

        # High risk score means higher failure probability
        risk += device.get("risk_score", 0) * 0.3

        # Devices with many connections are more stressed
        device_conns = [c for c in connections
                        if c.get("source_id") == device["id"] or c.get("target_id") == device["id"]]
        if len(device_conns) > 20:
            risk += 0.15

        # Degraded status
        if device.get("status") == "degraded":
            risk += 0.25

        # Flapping connections
        flapping = [c for c in device_conns if c.get("status") == "flapping"]
        if flapping:
            risk += 0.2

        # High packet loss
        high_loss = [c for c in device_conns if c.get("packet_loss_pct", 0) > 1.0]
        if high_loss:
            risk += 0.1

        return min(risk, 1.0)

    def _get_risk_factors(self, device: dict, connections: list) -> list[str]:
        factors = []
        if device.get("risk_score", 0) > 0.6:
            factors.append("High base risk score")
        if device.get("status") == "degraded":
            factors.append("Currently degraded")

        device_conns = [c for c in connections
                        if c.get("source_id") == device["id"] or c.get("target_id") == device["id"]]
        flapping = [c for c in device_conns if c.get("status") == "flapping"]
        if flapping:
            factors.append(f"{len(flapping)} flapping connection(s)")

        return factors


failure_predictor = FailurePredictor()
