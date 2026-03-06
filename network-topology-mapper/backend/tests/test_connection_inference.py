"""
Unit tests for ConnectionInferenceEngine.

These tests import connection_inference.py directly — no app dependencies needed
since the module uses only stdlib.
"""

import sys
import os
import pytest

# Add backend to path so we can import without the full app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.services.scanner.connection_inference import ConnectionInferenceEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_device(
    id: str,
    ip: str,
    device_type: str = "unknown",
    mac: str = "",
    hostname: str = "",
    is_gateway: bool = False,
    vlan_ids: list = None,
    open_ports: list = None,
) -> dict:
    """Build a minimal device dict for testing."""
    return {
        "id": id,
        "ip": ip,
        "mac": mac or f"AA:BB:CC:00:00:{id[-2:]}",
        "hostname": hostname or ip,
        "device_type": device_type,
        "is_gateway": is_gateway,
        "vlan_ids": vlan_ids or [],
        "open_ports": open_ports or [],
        "status": "online",
        "discovery_method": "active_scan",
    }


def devices_to_cache(devices: list) -> dict:
    """Convert a list of device dicts to a coordinator-style cache keyed by IP."""
    return {d["ip"]: d for d in devices}


def edge_set(connections: list) -> set:
    """Extract a set of frozensets of (source_id, target_id) for easy comparison."""
    return {frozenset({c["source_id"], c["target_id"]}) for c in connections}


# ---------------------------------------------------------------------------
# Test: Flat /24 — Gateway Star Topology
# ---------------------------------------------------------------------------

class TestGatewayInference:
    """Strategy 2: Flat network, all devices connect to gateway."""

    def setup_method(self):
        self.engine = ConnectionInferenceEngine()

    def test_star_topology(self):
        """Router + N devices on a flat /24 → N edges, all to router."""
        router = make_device("router-01", "192.168.1.1", "router", is_gateway=True)
        laptop = make_device("laptop-01", "192.168.1.100", "workstation")
        phone = make_device("phone-01", "192.168.1.101", "unknown")
        printer = make_device("printer-01", "192.168.1.200", "printer")

        cache = devices_to_cache([router, laptop, phone, printer])
        conns = self.engine.infer_connections(cache, "192.168.1.0/24")

        assert len(conns) == 3  # 3 devices connect to router
        edges = edge_set(conns)
        assert frozenset({"router-01", "laptop-01"}) in edges
        assert frozenset({"router-01", "phone-01"}) in edges
        assert frozenset({"router-01", "printer-01"}) in edges

    def test_gateway_detection_by_device_type(self):
        """Router identified by device_type, not is_gateway flag."""
        router = make_device("rtr", "192.168.1.1", "router")
        host = make_device("host-01", "192.168.1.50", "workstation")

        cache = devices_to_cache([router, host])
        conns = self.engine.infer_connections(cache, "192.168.1.0/24")

        assert len(conns) == 1
        assert conns[0]["source_id"] == "rtr" or conns[0]["target_id"] == "rtr"

    def test_gateway_fallback_to_dot_one(self):
        """No router type or is_gateway — falls back to .1 address."""
        mystery_gw = make_device("gw-01", "10.0.0.1", "unknown")
        host = make_device("host-01", "10.0.0.50", "workstation")

        cache = devices_to_cache([mystery_gw, host])
        conns = self.engine.infer_connections(cache, "10.0.0.0/24")

        assert len(conns) == 1
        edges = edge_set(conns)
        assert frozenset({"gw-01", "host-01"}) in edges

    def test_no_gateway_found(self):
        """No router, no .1 address → zero edges, no crash."""
        host_a = make_device("host-a", "10.0.0.50", "workstation")
        host_b = make_device("host-b", "10.0.0.51", "workstation")

        cache = devices_to_cache([host_a, host_b])
        conns = self.engine.infer_connections(cache, "10.0.0.0/24")

        assert len(conns) == 0

    def test_device_outside_subnet_excluded(self):
        """Device on a different subnet shouldn't get an edge."""
        router = make_device("rtr", "192.168.1.1", "router")
        local = make_device("local-01", "192.168.1.100", "workstation")
        remote = make_device("remote-01", "10.0.0.50", "workstation")

        cache = devices_to_cache([router, local, remote])
        conns = self.engine.infer_connections(cache, "192.168.1.0/24")

        assert len(conns) == 1  # only local device
        edges = edge_set(conns)
        assert frozenset({"rtr", "local-01"}) in edges
        assert frozenset({"rtr", "remote-01"}) not in edges

    def test_no_self_loop(self):
        """Gateway should not connect to itself."""
        router = make_device("rtr", "192.168.1.1", "router")
        cache = devices_to_cache([router])
        conns = self.engine.infer_connections(cache, "192.168.1.0/24")

        assert len(conns) == 0

    def test_connection_schema(self):
        """Verify returned connection dicts have all required fields."""
        router = make_device("rtr", "192.168.1.1", "router")
        host = make_device("host-01", "192.168.1.50", "workstation")

        cache = devices_to_cache([router, host])
        conns = self.engine.infer_connections(cache, "192.168.1.0/24")

        assert len(conns) == 1
        conn = conns[0]
        required_fields = {
            "id", "source_id", "target_id", "connection_type", "bandwidth",
            "switch_port", "vlan", "latency_ms", "packet_loss_pct",
            "is_redundant", "protocol", "status", "first_seen", "last_seen",
        }
        assert required_fields.issubset(conn.keys())
        assert conn["status"] == "active"
        assert isinstance(conn["id"], str) and len(conn["id"]) > 0

    def test_ap_gets_wireless_connection_type(self):
        """Access point device should get connection_type 'wireless'."""
        router = make_device("rtr", "192.168.1.1", "router")
        ap = make_device("ap-01", "192.168.1.10", "ap")

        cache = devices_to_cache([router, ap])
        conns = self.engine.infer_connections(cache, "192.168.1.0/24")

        assert len(conns) == 1
        assert conns[0]["connection_type"] == "wireless"


# ---------------------------------------------------------------------------
# Test: Switch-Aware Hierarchical Topology
# ---------------------------------------------------------------------------

class TestSwitchAwareInference:
    """Strategy 3: Network with switches → hierarchical edges."""

    def setup_method(self):
        self.engine = ConnectionInferenceEngine()

    def test_basic_hierarchy(self):
        """Router + core switch + end device → router-switch + switch-device."""
        router = make_device("rtr", "10.0.1.1", "router")
        core_sw = make_device("sw-core", "10.0.1.2", "switch", vlan_ids=[1, 10, 20, 30])
        laptop = make_device("laptop", "10.0.1.100", "workstation", vlan_ids=[10])

        cache = devices_to_cache([router, core_sw, laptop])
        conns = self.engine.infer_connections(cache, "10.0.1.0/24")

        edges = edge_set(conns)
        assert frozenset({"rtr", "sw-core"}) in edges
        assert frozenset({"sw-core", "laptop"}) in edges
        assert frozenset({"rtr", "laptop"}) not in edges

    def test_access_switches(self):
        """Core switch + access switches → core-to-access edges."""
        router = make_device("rtr", "10.0.1.1", "router")
        core = make_device("sw-core", "10.0.1.2", "switch", vlan_ids=[1, 10, 20, 30])
        access1 = make_device("sw-acc1", "10.0.1.11", "switch", vlan_ids=[10])
        access2 = make_device("sw-acc2", "10.0.1.12", "switch", vlan_ids=[20])
        ws = make_device("ws-01", "10.0.1.100", "workstation", vlan_ids=[10])

        cache = devices_to_cache([router, core, access1, access2, ws])
        conns = self.engine.infer_connections(cache, "10.0.1.0/24")

        edges = edge_set(conns)
        assert frozenset({"rtr", "sw-core"}) in edges
        assert frozenset({"sw-core", "sw-acc1"}) in edges
        assert frozenset({"sw-core", "sw-acc2"}) in edges
        assert frozenset({"sw-acc1", "ws-01"}) in edges

    def test_vlan_matching(self):
        """Device with VLAN 20 connects to the switch that carries VLAN 20."""
        router = make_device("rtr", "10.0.1.1", "router")
        core = make_device("sw-core", "10.0.1.2", "switch", vlan_ids=[1, 10, 20, 30])
        sw_vlan10 = make_device("sw-10", "10.0.1.11", "switch", vlan_ids=[10])
        sw_vlan20 = make_device("sw-20", "10.0.1.12", "switch", vlan_ids=[20])
        server = make_device("srv", "10.0.1.50", "server", vlan_ids=[20])

        cache = devices_to_cache([router, core, sw_vlan10, sw_vlan20, server])
        conns = self.engine.infer_connections(cache, "10.0.1.0/24")

        edges = edge_set(conns)
        assert frozenset({"sw-20", "srv"}) in edges
        assert frozenset({"sw-10", "srv"}) not in edges

    def test_firewall_connects_to_gateway(self):
        """Firewalls should connect to the gateway, not to switches."""
        router = make_device("rtr", "10.0.1.1", "router")
        core = make_device("sw-core", "10.0.1.2", "switch", vlan_ids=[1, 10, 20])
        fw = make_device("fw-01", "10.0.1.3", "firewall")

        cache = devices_to_cache([router, core, fw])
        conns = self.engine.infer_connections(cache, "10.0.1.0/24")

        edges = edge_set(conns)
        assert frozenset({"rtr", "fw-01"}) in edges

    def test_no_vlan_data_falls_back_to_first_switch(self):
        """Device with no VLAN info connects to the first available switch."""
        router = make_device("rtr", "10.0.1.1", "router")
        sw = make_device("sw-01", "10.0.1.2", "switch")
        host = make_device("host", "10.0.1.50", "workstation")

        cache = devices_to_cache([router, sw, host])
        conns = self.engine.infer_connections(cache, "10.0.1.0/24")

        edges = edge_set(conns)
        assert frozenset({"sw-01", "host"}) in edges


# ---------------------------------------------------------------------------
# Test: Deduplication
# ---------------------------------------------------------------------------

class TestDeduplication:
    """Verify dedup logic: priority scoring and undirected edge handling."""

    def setup_method(self):
        self.engine = ConnectionInferenceEngine()

    def test_no_duplicate_edges(self):
        """Each device pair should appear at most once."""
        router = make_device("rtr", "192.168.1.1", "router")
        devices = [make_device(f"d-{i:02d}", f"192.168.1.{10+i}", "workstation") for i in range(5)]

        cache = devices_to_cache([router] + devices)
        conns = self.engine.infer_connections(cache, "192.168.1.0/24")

        edges = edge_set(conns)
        assert len(edges) == len(conns)

    def test_unique_connection_ids(self):
        """Every connection should have a unique UUID."""
        router = make_device("rtr", "192.168.1.1", "router")
        devices = [make_device(f"d-{i:02d}", f"192.168.1.{10+i}", "workstation") for i in range(5)]

        cache = devices_to_cache([router] + devices)
        conns = self.engine.infer_connections(cache, "192.168.1.0/24")

        ids = [c["id"] for c in conns]
        assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
# Test: Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def setup_method(self):
        self.engine = ConnectionInferenceEngine()

    def test_empty_device_cache(self):
        """Empty cache → empty connections, no crash."""
        conns = self.engine.infer_connections({}, "192.168.1.0/24")
        assert conns == []

    def test_single_device(self):
        """Only one device (the router) → no edges."""
        router = make_device("rtr", "192.168.1.1", "router")
        cache = devices_to_cache([router])
        conns = self.engine.infer_connections(cache, "192.168.1.0/24")
        assert conns == []

    def test_invalid_subnet(self):
        """Invalid subnet string → empty connections, no crash."""
        router = make_device("rtr", "192.168.1.1", "router")
        cache = devices_to_cache([router])
        conns = self.engine.infer_connections(cache, "not-a-subnet")
        assert conns == []

    def test_device_with_no_ip(self):
        """Device with empty IP should be skipped (can't determine subnet)."""
        router = make_device("rtr", "192.168.1.1", "router")
        no_ip = make_device("ghost", "", "unknown")

        cache = {"192.168.1.1": router, "AA:BB:CC:00:00:FF": no_ip}
        conns = self.engine.infer_connections(cache, "192.168.1.0/24")

        assert len(conns) == 0

    def test_lldp_stub_returns_empty(self):
        """LLDP strategy stub should return empty and not crash."""
        router = make_device("rtr", "192.168.1.1", "router")
        host = make_device("host", "192.168.1.50", "workstation")

        cache = devices_to_cache([router, host])
        lldp_data = [{"querying_device_id": "rtr", "querying_device_ip": "192.168.1.1", "neighbors": []}]
        conns = self.engine.infer_connections(cache, "192.168.1.0/24", lldp_data=lldp_data)

        # Should still get the gateway edge, LLDP stub adds nothing
        assert len(conns) == 1
