from fastapi import APIRouter
from typing import Optional
import logging
import threading
import uuid

from app.config import get_settings
from app.models.scan import ScanRequest
from app.services.scanner.scan_coordinator import scan_coordinator
from app.db.sqlite_db import sqlite_db
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["scans"])


@router.post("/scans")
def trigger_scan(request: ScanRequest):
    scan_id = str(uuid.uuid4())
    target = request.target or get_settings().scan_default_range

    logger.info("POST /api/scans received: type=%s, target='%s' (resolved='%s'), intensity=%s, scan_id=%s",
                request.type.value, request.target, target, request.intensity, scan_id)

    def run():
        logger.info("Scan thread started for %s", scan_id)
        try:
            scan_coordinator.start_scan(request.type.value, target, request.intensity, scan_id=scan_id)
            logger.info("Scan thread finished for %s", scan_id)
        except Exception as e:
            logger.error("Scan thread CRASHED for %s: %s", scan_id, e)
            import traceback
            logger.error("Crash traceback:\n%s", traceback.format_exc())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return {"status": "started", "scan_id": scan_id, "message": f"Scan {request.type.value} initiated for {target}"}


@router.get("/scans")
def list_scans(limit: int = 50):
    scans = sqlite_db.get_scans(limit=limit)
    return {"scans": scans}


@router.get("/scans/{scan_id}")
def get_scan(scan_id: str):
    scan = sqlite_db.get_scan(scan_id)
    if not scan:
        return {"error": "Scan not found"}

    # Get progress from Redis if running
    if scan.get("status") == "running":
        progress = redis_client.get_scan_progress(scan_id)
        if progress:
            scan["progress"] = progress

    return scan


@router.delete("/scans/{scan_id}")
def cancel_scan(scan_id: str):
    scan_coordinator.cancel_scan(scan_id)
    return {"status": "cancelled", "scan_id": scan_id}
