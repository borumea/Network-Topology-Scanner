from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Optional
import json
import asyncio

from app.models.alert import AlertUpdate
from app.db.sqlite_db import sqlite_db

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts")
def get_alerts(
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
):
    alerts = sqlite_db.get_alerts(
        severity=severity,
        alert_type=alert_type,
        status=status,
        limit=limit,
    )
    return {"alerts": alerts}


@router.patch("/alerts/{alert_id}")
def update_alert(alert_id: str, update: AlertUpdate):
    alert = sqlite_db.get_alert(alert_id)
    if not alert:
        return {"error": "Alert not found"}

    updates = {}
    if update.status:
        updates["status"] = update.status.value
        if update.status.value == "acknowledged":
            updates["acknowledged_at"] = datetime.utcnow().isoformat()
        elif update.status.value == "resolved":
            updates["resolved_at"] = datetime.utcnow().isoformat()

    sqlite_db.update_alert(alert_id, updates)
    return {"status": "updated", "alert_id": alert_id}


@router.get("/alerts/stream")
async def alert_stream():
    async def generate():
        last_check = datetime.utcnow().isoformat()
        while True:
            alerts = sqlite_db.get_alerts(status="open", limit=10)
            new_alerts = [a for a in alerts if a.get("created_at", "") > last_check]

            if new_alerts:
                last_check = datetime.utcnow().isoformat()
                for alert in new_alerts:
                    yield f"data: {json.dumps(alert)}\n\n"

            await asyncio.sleep(2)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
