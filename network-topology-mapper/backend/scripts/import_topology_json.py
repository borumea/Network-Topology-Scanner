"""Import a topology JSON dump into the SQLite topology database.

Usage:
    python scripts/import_topology_json.py <path-to-json-file>

The JSON file should have the format:
    {"devices": [...], "connections": [...], "dependencies": [...]}
"""
import json
import sys
import os

# Add the backend directory to the path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.sqlite_db import sqlite_db
from app.db.topology_db import topology_db


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_topology_json.py <path-to-json-file>")
        sys.exit(1)

    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    devices = data.get("devices", [])
    connections = data.get("connections", [])
    dependencies = data.get("dependencies", [])

    print(f"Loaded: {len(devices)} devices, {len(connections)} connections, {len(dependencies)} dependencies")

    # Initialize databases
    sqlite_db.connect()
    topology_db.connect()

    # Import devices first (connections have FK references)
    for device in devices:
        topology_db.upsert_device(device)
    print(f"Imported {len(devices)} devices")

    for conn in connections:
        topology_db.upsert_connection(conn)
    print(f"Imported {len(connections)} connections")

    for dep in dependencies:
        topology_db.upsert_dependency(dep)
    print(f"Imported {len(dependencies)} dependencies")

    # Verify
    topo = topology_db.get_topology()
    print(f"\nVerification - DB now contains:")
    print(f"  Devices:      {len(topo['devices'])}")
    print(f"  Connections:  {len(topo['connections'])}")
    print(f"  Dependencies: {len(topo['dependencies'])}")


if __name__ == "__main__":
    main()
