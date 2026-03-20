import logging

from app.config import get_settings
from app.services.scanner.scan_coordinator import scan_coordinator

logger = logging.getLogger(__name__)


def run_scan(scan_type: str = "full", target: str = None, intensity: str = "normal") -> dict:
    settings = get_settings()
    target = target or settings.scan_default_range
    scan_id = scan_coordinator.start_scan(scan_type, target, intensity)
    return {"scan_id": scan_id, "status": "completed"}


def scheduled_full_scan() -> dict:
    settings = get_settings()
    logger.info("Running scheduled full scan on %s", settings.scan_default_range)
    return run_scan("full", settings.scan_default_range, "normal")


def scheduled_snmp_poll() -> dict:
    settings = get_settings()
    logger.info("Running scheduled SNMP poll on %s", settings.scan_default_range)
    return run_scan("snmp", settings.scan_default_range, "normal")
