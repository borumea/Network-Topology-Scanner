import json
import logging
from datetime import datetime
from typing import Any, Optional
from pathlib import Path
import sqlite3

from app.config import get_settings

logger = logging.getLogger(__name__)


class SQLiteDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        settings = get_settings()
        db_path = Path(settings.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_tables()
        logger.info("Connected to SQLite at %s", db_path)

    def _init_tables(self):
        cursor = self._conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                scan_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT,
                target_range TEXT,
                devices_found INTEGER DEFAULT 0,
                new_devices INTEGER DEFAULT 0,
                config TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                device_id TEXT,
                details TEXT DEFAULT '{}',
                created_at TEXT,
                acknowledged_at TEXT,
                resolved_at TEXT,
                status TEXT DEFAULT 'open'
            );

            CREATE TABLE IF NOT EXISTS topology_snapshots (
                id TEXT PRIMARY KEY,
                created_at TEXT,
                device_count INTEGER DEFAULT 0,
                connection_count INTEGER DEFAULT 0,
                risk_score REAL DEFAULT 0.0,
                snapshot_data TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()

    # Scan operations
    def create_scan(self, scan: dict) -> dict:
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT INTO scans (id, scan_type, status, started_at, target_range, config)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (scan["id"], scan["scan_type"], scan.get("status", "pending"),
             scan.get("started_at", datetime.utcnow().isoformat()),
             scan.get("target_range", "all"),
             json.dumps(scan.get("config", {})))
        )
        self._conn.commit()
        return scan

    def update_scan(self, scan_id: str, updates: dict) -> None:
        sets = []
        vals = []
        for k, v in updates.items():
            if k == "config":
                v = json.dumps(v)
            sets.append(f"{k} = ?")
            vals.append(v)
        vals.append(scan_id)
        cursor = self._conn.cursor()
        cursor.execute(f"UPDATE scans SET {', '.join(sets)} WHERE id = ?", vals)
        self._conn.commit()

    def get_scan(self, scan_id: str) -> Optional[dict]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            d["config"] = json.loads(d.get("config", "{}"))
            return d
        return None

    def get_scans(self, limit: int = 50) -> list[dict]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM scans ORDER BY started_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["config"] = json.loads(d.get("config", "{}"))
            result.append(d)
        return result

    # Alert operations
    def create_alert(self, alert: dict) -> dict:
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT INTO alerts (id, alert_type, severity, title, description, device_id, details, created_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (alert["id"], alert["alert_type"], alert["severity"],
             alert["title"], alert.get("description", ""),
             alert.get("device_id"), json.dumps(alert.get("details", {})),
             alert.get("created_at", datetime.utcnow().isoformat()),
             alert.get("status", "open"))
        )
        self._conn.commit()
        return alert

    def update_alert(self, alert_id: str, updates: dict) -> None:
        sets = []
        vals = []
        for k, v in updates.items():
            if k == "details":
                v = json.dumps(v)
            sets.append(f"{k} = ?")
            vals.append(v)
        vals.append(alert_id)
        cursor = self._conn.cursor()
        cursor.execute(f"UPDATE alerts SET {', '.join(sets)} WHERE id = ?", vals)
        self._conn.commit()

    def get_alerts(self, severity: str = None, alert_type: str = None,
                   status: str = None, limit: int = 100) -> list[dict]:
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if alert_type:
            query += " AND alert_type = ?"
            params.append(alert_type)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = self._conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["details"] = json.loads(d.get("details", "{}"))
            result.append(d)
        return result

    def get_alert(self, alert_id: str) -> Optional[dict]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            d["details"] = json.loads(d.get("details", "{}"))
            return d
        return None

    # Snapshot operations
    def create_snapshot(self, snapshot: dict) -> dict:
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT INTO topology_snapshots (id, created_at, device_count, connection_count, risk_score, snapshot_data)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (snapshot["id"], snapshot.get("created_at", datetime.utcnow().isoformat()),
             snapshot.get("device_count", 0), snapshot.get("connection_count", 0),
             snapshot.get("risk_score", 0.0),
             json.dumps(snapshot.get("snapshot_data", {})))
        )
        self._conn.commit()
        return snapshot

    def get_snapshots(self, limit: int = 50) -> list[dict]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM topology_snapshots ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["snapshot_data"] = json.loads(d.get("snapshot_data", "{}"))
            result.append(d)
        return result


sqlite_db = SQLiteDB()
