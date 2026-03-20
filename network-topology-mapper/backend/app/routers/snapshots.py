from fastapi import APIRouter, HTTPException

from app.db.sqlite_db import sqlite_db

router = APIRouter(prefix="/api", tags=["snapshots"])


@router.get("/snapshots")
def list_snapshots(limit: int = 50):
    snapshots = sqlite_db.get_snapshots(limit=limit)
    return {"snapshots": snapshots, "count": len(snapshots)}


@router.get("/snapshots/{snapshot_id}")
def get_snapshot(snapshot_id: str):
    snapshot = sqlite_db.get_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot
