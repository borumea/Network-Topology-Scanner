import logging
from typing import Any

logger = logging.getLogger(__name__)


class ScanOptimizer:
    """Basic scan scheduling optimization based on device change frequency."""

    def optimize_schedule(self, scan_history: list[dict],
                          topology: dict) -> dict:
        devices = topology.get("devices", [])
        total_devices = len(devices)

        # Calculate recommended intervals based on network size
        if total_devices < 50:
            full_interval = 3600  # 1 hour
            snmp_interval = 900  # 15 min
        elif total_devices < 200:
            full_interval = 7200  # 2 hours
            snmp_interval = 1800  # 30 min
        else:
            full_interval = 21600  # 6 hours
            snmp_interval = 3600  # 1 hour

        # Count high-risk devices that need more frequent monitoring
        high_risk = [d for d in devices if d.get("risk_score", 0) > 0.6]
        if len(high_risk) > 10:
            snmp_interval = min(snmp_interval, 900)

        return {
            "recommended": {
                "full_scan_interval_seconds": full_interval,
                "snmp_poll_interval_seconds": snmp_interval,
                "passive_scan": "continuous",
            },
            "reasoning": {
                "device_count": total_devices,
                "high_risk_count": len(high_risk),
            },
        }


scan_optimizer = ScanOptimizer()
