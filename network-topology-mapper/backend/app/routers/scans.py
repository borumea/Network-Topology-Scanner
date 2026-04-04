from fastapi import APIRouter
from typing import Optional
import threading
import uuid

from app.models.scan import ScanRequest
from app.services.scanner.scan_coordinator import scan_coordinator
from app.db.sqlite_db import sqlite_db
from app.db.redis_client import redis_client

router = APIRouter(prefix="/api", tags=["scans"])


@router.post("/scans")
def trigger_scan(request: ScanRequest):
    scan_id = str(uuid.uuid4())

    def run():
        scan_coordinator.start_scan(request.type.value, request.target, request.intensity, scan_id=scan_id)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return {"status": "started", "scan_id": scan_id, "message": f"Scan {request.type.value} initiated for {request.target}"}


@router.get("/scans")
def list_scans(limit: int = 50):
    scans = sqlite_db.get_scans(limit=limit)
    return {"scans": scans}


@router.post("/scans/clear")
def clear_scans():
    sqlite_db.clear_scans()
    return {"status": "ok", "message": "Scan history cleared."}


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
