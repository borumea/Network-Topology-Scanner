"""
Connection Inference Engine — infers L2/L3 edges from discovered device data.

Called after all scan phases complete. Takes the coordinator's device cache
and produces connection dicts for graph_builder.upsert_connection().

Design spec: WO-048-connection-inference-spec.md
"""

import ipaddress
import logging
import uuid
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# Priority levels for deduplication. Higher number = higher confidence.
PRIORITY_GATEWAY = 10
PRIORITY_SWITCH_AWARE = 20
PRIORITY_LLDP = 30


class ConnectionInferenceEngine:
    """Infers network connections from discovered device data."""

    def infer_connections(
        self,
        devices: dict[str, dict],
        target_subnet: str,
        lldp_data: Optional[list[dict]] = None,
    ) -> list[dict]:
        """
        Run all inference strategies and return deduplicated connection dicts.

        Args:
            devices: The coordinator's _devices_cache (keyed by IP or MAC).
            target_subnet: The scan target, e.g. "192.168.0.0/24".
            lldp_data: Optional LLDP neighbor data from config_puller.
                       Each entry: {"querying_device_id": str, "neighbors": [...]}.
                       Wired in WO-050, used by LLDP strategy added in WO-051.

        Returns:
            List of connection dicts ready for graph_builder.upsert_connection().
        """
        if not devices:
            logger.warning("No devices provided for connection inference")
            return []

        try:
            network = ipaddress.ip_network(target_subnet, strict=False)
        except ValueError:
            logger.error("Invalid target subnet: %s", target_subnet)
            return []

        # Collect connections from all strategies with their priority
        # Each entry: (priority, connection_dict)
        scored_connections: list[tuple[int, dict]] = []

        # Determine if we have switches — this decides strategy 2 vs 3
        device_list = list(devices.values())
        switches = [d for d in device_list if d.get("device_type") == "switch"]

        if switches:
            # Strategy 3: Switch-aware inference
            conns = self._infer_from_switches(devices, network)
            scored_connections.extend((PRIORITY_SWITCH_AWARE, c) for c in conns)
            logger.info("Switch-aware inference: %d connections", len(conns))
        else:
            # Strategy 2: Flat gateway inference
            conns = self._infer_from_gateway(devices, network)
            scored_connections.extend((PRIORITY_GATEWAY, c) for c in conns)
            logger.info("Gateway inference: %d connections", len(conns))

        # Strategy 1 (LLDP) — placeholder for WO-051
        if lldp_data:
            lldp_conns = self._infer_from_lldp(devices, lldp_data)
            scored_connections.extend((PRIORITY_LLDP, c) for c in lldp_conns)
            logger.info("LLDP inference: %d connections", len(lldp_conns))

        # Deduplicate
        result = self._deduplicate_connections(scored_connections)
        logger.info("Connection inference complete: %d total edges after dedup", len(result))
        return result

    def _infer_from_gateway(
        self,
        devices: dict[str, dict],
        network: ipaddress.IPv4Network,
    ) -> list[dict]:
        """
        Strategy 2: Star topology through gateway.

        Every device on the subnet connects to the gateway. This is the
        correct model for flat home networks with a consumer router.
        """
        gateway = self._find_gateway(devices, network)
        if not gateway:
            logger.warning("No gateway found in devices — skipping gateway inference")
            return []

        connections = []
        now = datetime.utcnow().isoformat()

        for key, device in devices.items():
            # Don't connect gateway to itself
            if device.get("id") == gateway["id"]:
                continue

            # Only connect devices that are on this subnet
            device_ip = device.get("ip", "")
            if not self._ip_in_network(device_ip, network):
                continue

            connections.append(self._make_connection(
                source=gateway,
                target=device,
                connection_type=self._guess_connection_type(device),
                protocol="routed",
                now=now,
            ))

        return connections

    def _infer_from_switches(
        self,
        devices: dict[str, dict],
        network: ipaddress.IPv4Network,
    ) -> list[dict]:
        """
        Strategy 3: Hierarchical topology through switches.

        Infrastructure hierarchy: gateway -> switches -> end devices.
        End devices connect to a switch (matched by VLAN or subnet).
        Switches connect to the gateway (or to a core switch if one exists).
        """
        gateway = self._find_gateway(devices, network)
        device_list = list(devices.values())
        switches = [d for d in device_list if d.get("device_type") == "switch"]
        now = datetime.utcnow().isoformat()
        connections = []

        # Identify core switch vs access switches.
        # Heuristic: a switch on multiple VLANs is likely core.
        # If we can't tell, treat the first switch as core.
        core_switch = None
        access_switches = []
        for sw in switches:
            vlans = sw.get("vlan_ids", [])
            if len(vlans) >= 3:
                core_switch = sw
            else:
                access_switches.append(sw)

        # If no clear core switch, use the first one
        if not core_switch and switches:
            core_switch = switches[0]
            access_switches = switches[1:]

        # Connect gateway <-> core switch
        if gateway and core_switch and gateway["id"] != core_switch["id"]:
            connections.append(self._make_connection(
                source=gateway,
                target=core_switch,
                connection_type="ethernet",
                protocol="trunk",
                now=now,
            ))

        # Connect core switch <-> access switches
        if core_switch:
            for asw in access_switches:
                if asw["id"] == core_switch["id"]:
                    continue
                connections.append(self._make_connection(
                    source=core_switch,
                    target=asw,
                    connection_type="ethernet",
                    protocol="trunk",
                    now=now,
                ))

        # Connect end devices to the best-matching switch
        infrastructure_types = {"router", "switch", "firewall"}
        end_devices = [
            d for d in device_list
            if d.get("device_type") not in infrastructure_types
            and self._ip_in_network(d.get("ip", ""), network)
        ]

        for device in end_devices:
            best_switch = self._find_best_switch(device, access_switches) or self._find_best_switch(device, switches)
            if best_switch:
                connections.append(self._make_connection(
                    source=best_switch,
                    target=device,
                    connection_type=self._guess_connection_type(device),
                    protocol="access",
                    now=now,
                ))
            elif gateway:
                # Fallback: connect directly to gateway if no switch match
                connections.append(self._make_connection(
                    source=gateway,
                    target=device,
                    connection_type=self._guess_connection_type(device),
                    protocol="routed",
                    now=now,
                ))

        # Connect firewalls to gateway (or core switch)
        firewalls = [d for d in device_list if d.get("device_type") == "firewall"]
        for fw in firewalls:
            upstream = gateway or core_switch
            if upstream and fw["id"] != upstream["id"]:
                connections.append(self._make_connection(
                    source=upstream,
                    target=fw,
                    connection_type="ethernet",
                    protocol="routed",
                    now=now,
                ))

        return connections

    def _infer_from_lldp(
        self,
        devices: dict[str, dict],
        lldp_data: list[dict],
    ) -> list[dict]:
        """
        Strategy 1: LLDP neighbor data.

        Stub for WO-051. Returns empty list until LLDP wiring is complete.
        """
        # TODO WO-051: Implement LLDP-based connection inference.
        # Match lldp_data neighbors to devices by IP/hostname,
        # create high-confidence edges.
        return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_gateway(
        self,
        devices: dict[str, dict],
        network: ipaddress.IPv4Network,
    ) -> Optional[dict]:
        """
        Find the gateway device. Priority:
        1. Device with is_gateway=True
        2. Device with device_type="router"
        3. The .1 address on the subnet
        """
        device_list = list(devices.values())

        # Check is_gateway flag
        for d in device_list:
            if d.get("is_gateway"):
                return d

        # Check device_type
        for d in device_list:
            if d.get("device_type") == "router":
                return d

        # Fall back to .1 address
        gateway_ip = str(network.network_address + 1)
        for d in device_list:
            if d.get("ip") == gateway_ip:
                return d

        return None

    def _find_best_switch(
        self,
        device: dict,
        switches: list[dict],
    ) -> Optional[dict]:
        """
        Find the switch most likely to serve this device.
        Match by VLAN overlap first, then fall back to first switch.
        """
        if not switches:
            return None

        device_vlans = set(device.get("vlan_ids", []))

        if device_vlans:
            # Score each switch by VLAN overlap
            best = None
            best_overlap = 0
            for sw in switches:
                sw_vlans = set(sw.get("vlan_ids", []))
                overlap = len(device_vlans & sw_vlans)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best = sw
            if best:
                return best

        # No VLAN data — return the first switch (arbitrary but consistent)
        return switches[0]

    def _make_connection(
        self,
        source: dict,
        target: dict,
        connection_type: str,
        protocol: str,
        now: str,
    ) -> dict:
        """Build a connection dict matching the schema from mock_data.py."""
        return {
            "id": f"conn-{source['id']}-{target['id']}",
            "source_id": source["id"],
            "target_id": target["id"],
            "connection_type": connection_type,
            "bandwidth": "",
            "switch_port": "",
            "vlan": None,
            "latency_ms": 0.0,
            "packet_loss_pct": 0.0,
            "is_redundant": False,
            "protocol": protocol,
            "status": "active",
            "first_seen": now,
            "last_seen": now,
        }

    def _guess_connection_type(self, device: dict) -> str:
        """Guess physical connection type from device type."""
        dtype = device.get("device_type", "")
        if dtype == "ap":
            return "wireless"
        return "ethernet"

    def _ip_in_network(self, ip: str, network: ipaddress.IPv4Network) -> bool:
        """Check if an IP address belongs to the given network."""
        if not ip:
            return False
        try:
            return ipaddress.ip_address(ip) in network
        except ValueError:
            return False

    def _deduplicate_connections(
        self,
        scored_connections: list[tuple[int, dict]],
    ) -> list[dict]:
        """
        Remove duplicate edges. Connections are undirected at the physical
        layer, so A->B and B->A are the same edge.

        When duplicates exist, keep the one with higher priority
        (LLDP > switch-aware > gateway).
        """
        best: dict[frozenset, tuple[int, dict]] = {}

        for priority, conn in scored_connections:
            key = frozenset({conn["source_id"], conn["target_id"]})

            # Skip self-loops
            if conn["source_id"] == conn["target_id"]:
                continue

            if key not in best or priority > best[key][0]:
                best[key] = (priority, conn)

        return [conn for _, conn in best.values()]


connection_inference = ConnectionInferenceEngine()
