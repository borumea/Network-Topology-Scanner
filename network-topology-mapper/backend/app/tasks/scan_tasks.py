import logging

from app.tasks.celery_app import celery_app
from app.services.scanner.scan_coordinator import scan_coordinator
from app.config import get_settings

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.scan_tasks.run_scan")
def run_scan(scan_type: str = "full", target: str = None, intensity: str = "normal"):
    settings = get_settings()
    target = target or settings.scan_default_range
    scan_id = scan_coordinator.start_scan(scan_type, target, intensity)
    return {"scan_id": scan_id, "status": "completed"}


@celery_app.task(name="app.tasks.scan_tasks.scheduled_full_scan")
def scheduled_full_scan():
    settings = get_settings()
    return run_scan("full", settings.scan_default_range, "normal")


@celery_app.task(name="app.tasks.scan_tasks.scheduled_snmp_poll")
def scheduled_snmp_poll():
    settings = get_settings()
    return run_scan("snmp", settings.scan_default_range, "normal")
