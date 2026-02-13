import logging
from typing import Any
import networkx as nx

from app.services.graph.graph_builder import graph_builder

logger = logging.getLogger(__name__)


class FailureSimulator:
    def _build_networkx_graph(self) -> nx.Graph:
        topology = graph_builder.get_full_topology()
        G = nx.Graph()
        for device in topology["devices"]:
            G.add_node(device["id"], **device)
        for conn in topology["connections"]:
            G.add_edge(conn["source_id"], conn["target_id"], **{
                k: v for k, v in conn.items()
                if k not in ("source_id", "target_id")
            })
        return G

    def simulate_failure(self, remove_nodes: list[str] = None,
                         remove_edges: list[tuple[str, str]] = None) -> dict:
        G = self._build_networkx_graph()
        original_components = nx.number_connected_components(G)
        total_nodes = len(G.nodes)

        G_sim = G.copy()

        removed_node_data = []
        if remove_nodes:
            for node_id in remove_nodes:
                if node_id in G_sim:
                    removed_node_data.append(G_sim.nodes[node_id])
                    G_sim.remove_node(node_id)

        if remove_edges:
            for u, v in remove_edges:
                if G_sim.has_edge(u, v):
                    G_sim.remove_edge(u, v)

        # Analyze impact
        new_components = list(nx.connected_components(G_sim))
        num_components = len(new_components)

        # Find the largest component (assumed to be the "surviving" network)
        if new_components:
            largest_component = max(new_components, key=len)
        else:
            largest_component = set()

        disconnected_devices = []
        degraded_devices = []
        safe_devices = list(largest_component)

        for component in new_components:
            if component != largest_component:
                for node_id in component:
                    node_data = G_sim.nodes[node_id]
                    disconnected_devices.append({
                        "id": node_id,
                        "hostname": node_data.get("hostname", ""),
                        "device_type": node_data.get("device_type", ""),
                        "status": "disconnected",
                    })

        # Check for nodes with reduced connectivity
        for node_id in largest_component:
            orig_degree = G.degree(node_id) if node_id in G else 0
            new_degree = G_sim.degree(node_id)
            if new_degree < orig_degree and new_degree > 0:
                node_data = G_sim.nodes[node_id]
                degraded_devices.append({
                    "id": node_id,
                    "hostname": node_data.get("hostname", ""),
                    "device_type": node_data.get("device_type", ""),
                    "status": "degraded",
                    "lost_connections": orig_degree - new_degree,
                })

        # Determine affected services
        affected_services = set()
        for dev in disconnected_devices + degraded_devices:
            dtype = dev.get("device_type", "")
            hostname = dev.get("hostname", "")
            if "dns" in hostname.lower():
                affected_services.add("DNS")
            if "dhcp" in hostname.lower():
                affected_services.add("DHCP")
            if "db" in hostname.lower():
                affected_services.add("Database")
            if "web" in hostname.lower():
                affected_services.add("Web")
            if "mail" in hostname.lower():
                affected_services.add("Email")
            if "auth" in hostname.lower() or "ldap" in hostname.lower():
                affected_services.add("Authentication")

        blast_radius = len(disconnected_devices) + len(degraded_devices)
        removed_count = len(remove_nodes or [])
        risk_delta = min(blast_radius / max(total_nodes, 1), 1.0) * 4.0

        # Generate recommendations
        recommendations = self._generate_recommendations(
            G, remove_nodes or [], disconnected_devices, degraded_devices
        )

        return {
            "blast_radius": blast_radius,
            "blast_radius_pct": round(blast_radius / max(total_nodes - removed_count, 1) * 100, 1),
            "disconnected_devices": disconnected_devices,
            "degraded_devices": degraded_devices,
            "safe_device_ids": list(safe_devices),
            "removed_node_ids": remove_nodes or [],
            "affected_services": list(affected_services),
            "risk_delta": round(risk_delta, 2),
            "new_components": num_components,
            "recommendations": recommendations,
        }

    def _generate_recommendations(self, G: nx.Graph, removed_nodes: list[str],
                                   disconnected: list, degraded: list) -> list[dict]:
        recommendations = []

        for node_id in removed_nodes:
            if node_id not in G:
                continue
            node_data = G.nodes[node_id]
            hostname = node_data.get("hostname", node_id)
            device_type = node_data.get("device_type", "device")
            neighbors = list(G.neighbors(node_id))

            if len(disconnected) > 10:
                recommendations.append({
                    "action": f"Add redundant uplink from {hostname}",
                    "impact": f"Reduces blast radius by ~{len(disconnected)} devices",
                    "priority": "critical",
                })

            if len(neighbors) > 5:
                recommendations.append({
                    "action": f"Deploy standby {device_type} as failover for {hostname}",
                    "impact": f"Provides automatic failover for {len(neighbors)} connected devices",
                    "priority": "high",
                })

        if not recommendations:
            recommendations.append({
                "action": "Network shows good redundancy for this failure scenario",
                "impact": "No critical improvements needed",
                "priority": "low",
            })

        return recommendations


failure_simulator = FailureSimulator()
