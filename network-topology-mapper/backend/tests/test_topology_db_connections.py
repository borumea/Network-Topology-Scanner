"""Tests for TopologyDB connection dedup.

The bug these tests guard against: prior to the fix, each call to
upsert_connection generated a fresh UUID in connection_inference and then
relied on ON CONFLICT(id) in topology_db, which always missed. That made
every rescan of a subnet insert another parallel edge for each existing
connection, producing the "doubled edges" seen in the RadLab VM frontend.
"""

import os
import tempfile
from unittest.mock import patch

import pytest

from app.db.topology_db import TopologyDB
from app.db.sqlite_db import SQLiteDB


@pytest.fixture
def db(monkeypatch, tmp_path):
    """Give each test its own SQLite DB and fresh singleton state."""
    db_path = tmp_path / "test_mapper.db"

    # Reset the singletons so each test gets a clean instance.
    TopologyDB._instance = None
    SQLiteDB._instance = None

    # Point the config at this tmpdir DB.
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setenv("SQLITE_PATH", str(db_path))

    sqlite_db = SQLiteDB()
    sqlite_db.connect()  # creates the schema
    topology = TopologyDB()
    topology.connect()

    # Insert two devices we can link.
    topology.upsert_device({"id": "dev-a", "ip": "10.0.0.1"})
    topology.upsert_device({"id": "dev-b", "ip": "10.0.0.2"})

    yield topology

    topology.close()
    sqlite_db.close()
    # Reset for other tests.
    TopologyDB._instance = None
    SQLiteDB._instance = None
    get_settings.cache_clear()


def _conn(id_, source, target):
    return {
        "id": id_,
        "source_id": source,
        "target_id": target,
        "connection_type": "ethernet",
        "status": "active",
    }


def test_same_direction_rescan_does_not_duplicate(db):
    """Inserting A→B twice with different UUIDs should leave one row."""
    db.upsert_connection(_conn("uuid-1", "dev-a", "dev-b"))
    db.upsert_connection(_conn("uuid-2", "dev-a", "dev-b"))

    all_conns = db.get_all_connections()
    assert len(all_conns) == 1
    # The existing row's ID should be preserved, not replaced.
    assert all_conns[0]["id"] == "uuid-1"


def test_reverse_direction_treated_as_same_edge(db):
    """Inserting A→B then B→A should not produce two rows (undirected)."""
    db.upsert_connection(_conn("uuid-1", "dev-a", "dev-b"))
    db.upsert_connection(_conn("uuid-2", "dev-b", "dev-a"))

    all_conns = db.get_all_connections()
    assert len(all_conns) == 1


def test_different_endpoint_pair_inserts_new_row(db):
    """Distinct edges should still be inserted separately."""
    db.upsert_device({"id": "dev-c", "ip": "10.0.0.3"})
    db.upsert_connection(_conn("uuid-1", "dev-a", "dev-b"))
    db.upsert_connection(_conn("uuid-2", "dev-a", "dev-c"))

    assert len(db.get_all_connections()) == 2


def test_self_loop_is_rejected(db):
    """An edge from a device to itself should never be inserted."""
    db.upsert_connection(_conn("uuid-1", "dev-a", "dev-a"))
    assert db.get_all_connections() == []


def test_missing_endpoint_ids_are_noop(db):
    """Connections missing source_id or target_id should be silently skipped."""
    db.upsert_connection({"id": "uuid-x", "source_id": "dev-a"})
    db.upsert_connection({"id": "uuid-y", "target_id": "dev-b"})
    assert db.get_all_connections() == []


def test_get_connection_by_endpoints_finds_either_direction(db):
    db.upsert_connection(_conn("uuid-1", "dev-a", "dev-b"))

    # Same direction
    found = db.get_connection_by_endpoints("dev-a", "dev-b")
    assert found is not None
    assert found["id"] == "uuid-1"

    # Reverse direction
    found_rev = db.get_connection_by_endpoints("dev-b", "dev-a")
    assert found_rev is not None
    assert found_rev["id"] == "uuid-1"

    # Nonexistent
    assert db.get_connection_by_endpoints("dev-a", "dev-nowhere") is None
