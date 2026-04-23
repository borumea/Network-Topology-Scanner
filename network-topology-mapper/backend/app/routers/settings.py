from fastapi import APIRouter
from typing import Any

from app.config import get_settings
from app.db.sqlite_db import sqlite_db
from app.services.ai.scan_optimizer import scan_optimizer
from app.services.graph.graph_builder import graph_builder
from app.utils.platform_utils import get_local_subnets


def _resolve_scan_range(value: Any) -> Any:
    """If `scan_default_range` is "auto" (or empty), expand it to the comma-
    joined list of locally-attached subnets so the frontend gets a real CIDR
    to show in the scan panel.
    """
    if not isinstance(value, str):
        return value
    if value.strip().lower() not in ("", "auto"):
        return value
    subnets = get_local_subnets()
    return ", ".join(subnets) if subnets else value

router = APIRouter(prefix="/api", tags=["settings"])

# Settings that can be overridden via the API
_ALLOWED_SETTINGS = {
    "scan_default_range",
    "scan_rate_limit",
    "scan_interval_minutes",
    "snmp_community",
    "enable_passive_scan",
    "agent_mode",
}


@router.get("/settings")
def get_all_settings():
    """Return effective settings: config defaults merged with any SQLite overrides."""
    cfg = get_settings()
    defaults = {
        "scan_default_range": cfg.scan_default_range,
        "scan_rate_limit": cfg.scan_rate_limit,
        "scan_interval_minutes": cfg.scan_interval_minutes,
        "snmp_community": cfg.snmp_community,
        "enable_passive_scan": True,
        "agent_mode": cfg.agent_mode,
    }
    # SQLite overrides take precedence
    overrides = sqlite_db.get_all_settings()
    merged = {**defaults}
    for key, val in overrides.items():
        if key in merged:
            # Coerce numeric types
            if isinstance(defaults.get(key), int):
                try:
                    merged[key] = int(val)
                except (ValueError, TypeError):
                    merged[key] = val
            elif isinstance(defaults.get(key), bool):
                merged[key] = val.lower() in ("true", "1", "yes")
            else:
                merged[key] = val

    merged["scan_default_range"] = _resolve_scan_range(merged.get("scan_default_range"))
    return {"settings": merged, "overrides": list(overrides.keys())}


@router.put("/settings")
def update_settings(body: dict[str, Any]):
    """Persist setting overrides to SQLite. Only allowed keys are accepted."""
    updated = {}
    rejected = []
    for key, value in body.items():
        if key in _ALLOWED_SETTINGS:
            sqlite_db.set_setting(key, str(value))
            updated[key] = value
        else:
            rejected.append(key)

    # Clear the pydantic settings cache so env-file reads pick up changes on restart
    get_settings.cache_clear()

    return {
        "updated": updated,
        "rejected": rejected,
        "message": "Settings saved. Restart not required for most values; scan_interval_minutes takes effect on next restart.",
    }


@router.get("/scan-optimizer/recommendations")
def get_scan_optimizer_recommendations():
    """Return scan schedule recommendations based on current topology."""
    topology = graph_builder.get_full_topology()
    history = []  # Could pass recent scan history here for richer recommendations
    recommendations = scan_optimizer.optimize_schedule(history, topology)
    cfg = get_settings()
    return {
        "recommendations": recommendations,
        "current": {
            "scan_interval_minutes": cfg.scan_interval_minutes,
            "scan_default_range": cfg.scan_default_range,
            "scan_rate_limit": cfg.scan_rate_limit,
        },
    }
