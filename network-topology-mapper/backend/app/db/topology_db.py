import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

# Fields stored as JSON text in SQLite
_JSON_FIELDS = {"open_ports", "services", "vlan_ids"}
# Fields stored as INTEGER (0/1) but exposed as bool
_BOOL_FIELDS = {"is_gateway", "is_redundant"}
# All known device columns (used for dynamic upsert)
_DEVICE_COLS = [
    "id", "ip", "hostname", "mac", "device_type", "vendor", "model", "os",
    "status", "risk_score", "criticality", "is_gateway", "first_seen",
    "last_seen", "discovery_method", "open_ports", "services", "vlan_ids",
    "subnet", "location",
]
_CONNECTION_COLS = [
    "id", "source_id", "target_id", "connection_type", "bandwidth",
    "switch_port", "vlan", "latency_ms", "packet_loss_pct", "is_redundant",
    "protocol", "status", "confidence", "inferred_by", "first_seen", "last_seen",
]
_DEPENDENCY_COLS = [
    "id", "source_id", "target_id", "dependency_type", "service_port",
    "criticality", "discovered_via",
]


def _serialize(key: str, value):
    """Prepare a value for SQLite storage."""
    if key in _JSON_FIELDS:
        if isinstance(value, str):
            return value
        return json.dumps(value if value is not None else [])
    if key in _BOOL_FIELDS:
        return int(bool(value)) if value is not None else 0
    return value


def _deserialize_device(row: dict) -> dict:
    """Convert a SQLite row dict back to the application dict format."""
    for field in _JSON_FIELDS:
        if field in row and isinstance(row[field], str):
            try:
                row[field] = json.loads(row[field])
            except (json.JSONDecodeError, TypeError):
                row[field] = []
    for field in _BOOL_FIELDS:
        if field in row:
            row[field] = bool(row[field])
    return row


def _deserialize_connection(row: dict) -> dict:
    if "is_redundant" in row:
        row["is_redundant"] = bool(row["is_redundant"])
    return row


class TopologyDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        settings = get_settings()
        db_path = Path(settings.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        logger.info("TopologyDB connected to %s", db_path)

    def close(self):
        if self._conn:
            self._conn.close()

    @property
    def available(self) -> bool:
        return self._conn is not None

    # ---- helpers ----

    def _clean_props(self, data: dict) -> dict:
        return {k: v for k, v in data.items() if v is not None}

    def _upsert(self, table: str, columns: list[str], data: dict) -> None:
        """Dynamic upsert matching Neo4j MERGE + SET += semantics.

        Only columns present in `data` (after removing Nones) are written.
        On conflict, only those columns are updated, preserving existing values
        for columns not in the dict.
        """
        clean = self._clean_props(data)
        # Only keep keys that are actual columns
        cols = [c for c in columns if c in clean]
        if "id" not in cols:
            return
        vals = [_serialize(c, clean[c]) for c in cols]
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        # ON CONFLICT: update only the columns we have
        updates = ", ".join(f"{c} = excluded.{c}" for c in cols if c != "id")

        sql = (
            f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}"
        )
        cursor = self._conn.cursor()
        cursor.execute(sql, vals)
        self._conn.commit()

    # ---- device operations ----

    def upsert_device(self, device: dict) -> None:
        self._upsert("devices", _DEVICE_COLS, device)

    def get_all_devices(self) -> list[dict]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM devices")
        return [_deserialize_device(dict(row)) for row in cursor.fetchall()]

    def get_device(self, device_id: str) -> Optional[dict]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
        row = cursor.fetchone()
        if row:
            return _deserialize_device(dict(row))
        return None

    def delete_device(self, device_id: str) -> None:
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM dependencies WHERE source_id = ? OR target_id = ?",
                        (device_id, device_id))
        cursor.execute("DELETE FROM connections WHERE source_id = ? OR target_id = ?",
                        (device_id, device_id))
        cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        self._conn.commit()

    # ---- connection operations ----

    def upsert_connection(self, conn: dict) -> None:
        """Upsert a connection, deduplicating by endpoint pair (undirected).

        If a connection already exists between these two devices in either
        direction, its existing row is updated instead of inserting a new one.
        This keeps inference reruns idempotent — otherwise each rescan
        generated a fresh UUID and produced parallel edges in the graph.
        """
        source_id = conn.get("source_id")
        target_id = conn.get("target_id")
        if not source_id or not target_id:
            return
        if source_id == target_id:
            return  # no self-loops

        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT id, source_id, target_id FROM connections "
            "WHERE (source_id = ? AND target_id = ?) "
            "OR (source_id = ? AND target_id = ?)",
            (source_id, target_id, target_id, source_id),
        )
        existing = cursor.fetchone()
        if existing:
            conn = dict(conn)
            conn["id"] = existing["id"]
            # Preserve the stored direction to keep the edge stable.
            conn["source_id"] = existing["source_id"]
            conn["target_id"] = existing["target_id"]

        self._upsert("connections", _CONNECTION_COLS, conn)

    def get_connection_by_endpoints(
        self, source_id: str, target_id: str
    ) -> Optional[dict]:
        """Return the stored connection row between two devices, if any."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM connections "
            "WHERE (source_id = ? AND target_id = ?) "
            "OR (source_id = ? AND target_id = ?)",
            (source_id, target_id, target_id, source_id),
        )
        row = cursor.fetchone()
        if row:
            return _deserialize_connection(dict(row))
        return None

    def get_all_connections(self) -> list[dict]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM connections")
        return [_deserialize_connection(dict(row)) for row in cursor.fetchall()]

    def get_device_connections(self, device_id: str) -> list[dict]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM connections WHERE source_id = ? OR target_id = ?",
            (device_id, device_id),
        )
        return [_deserialize_connection(dict(row)) for row in cursor.fetchall()]

    # ---- dependency operations ----

    def upsert_dependency(self, dep: dict) -> None:
        self._upsert("dependencies", _DEPENDENCY_COLS, dep)

    def get_all_dependencies(self) -> list[dict]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM dependencies")
        return [dict(row) for row in cursor.fetchall()]

    # ---- aggregate operations ----

    def get_topology(self) -> dict:
        return {
            "devices": self.get_all_devices(),
            "connections": self.get_all_connections(),
            "dependencies": self.get_all_dependencies(),
        }

    def clear_all(self) -> None:
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM dependencies")
        cursor.execute("DELETE FROM connections")
        cursor.execute("DELETE FROM devices")
        self._conn.commit()


topology_db = TopologyDB()
