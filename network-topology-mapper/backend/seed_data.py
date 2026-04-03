"""Seed the SQLite database with topology data from a JSON dump.

Usage:
    python seed_data.py <path-to-json>

Example:
    python seed_data.py "C:\\Users\\rbrad\\Downloads\\neo4j-dump (1).json"
"""
import json
import sys
from pathlib import Path

# Ensure app package is importable
sys.path.insert(0, str(Path(__file__).parent))

from app.db.sqlite_db import sqlite_db
from app.db.topology_db import topology_db


def seed(json_path: str) -> None:
    data = json.loads(Path(json_path).read_text())

    devices = data.get("devices", [])
    connections = data.get("connections", [])
    dependencies = data.get("dependencies", [])

    # Connect databases (creates tables if needed)
    sqlite_db.connect()
    topology_db.connect()

    try:
        for device in devices:
            topology_db.upsert_device(device)

        for conn in connections:
            topology_db.upsert_connection(conn)

        for dep in dependencies:
            topology_db.upsert_dependency(dep)

        print(f"Seeded {len(devices)} devices, {len(connections)} connections, {len(dependencies)} dependencies")
    finally:
        topology_db.close()
        sqlite_db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    seed(sys.argv[1])
