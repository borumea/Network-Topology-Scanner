import logging
from typing import Any
import networkx as nx

from app.services.graph.graph_builder import graph_builder

logger = logging.getLogger(__name__)


class SPOFDetector:
    def _build_networkx_graph(self) -> nx.Graph:
        topology = graph_builder.get_full_topology()
        G = nx.Graph()
        for device in topology["devices"]:
            G.add_node(device["id"], **device)
        for conn in topology["connections"]:
            G.add_edge(conn["source_id"], conn["target_id"], **conn)
        return G

    def find_spofs(self) -> list[dict]:
        G = self._build_networkx_graph()
        if len(G.nodes) == 0:
            return []

        spofs = []

        # Find articulation points (cut vertices)
        art_points = list(nx.articulation_points(G))
        for node_id in art_points:
            node_data = G.nodes[node_id]
            # Calculate impact
            G_copy = G.copy()
            G_copy.remove_node(node_id)
            components = list(nx.connected_components(G_copy))
            if len(components) > 1:
                largest = max(len(c) for c in components)
                disconnected = len(G.nodes) - 1 - largest
            else:
                disconnected = 0

            spofs.append({
                "device_id": node_id,
                "hostname": node_data.get("hostname", ""),
                "device_type": node_data.get("device_type", "unknown"),
                "impact": disconnected,
                "reason": f"Articulation point - removal disconnects {disconnected} devices",
                "risk_score": node_data.get("risk_score", 0),
            })

        # Find bridge edges
        bridges = list(nx.bridges(G))
        bridge_list = []
        for u, v in bridges:
            edge_data = G.edges[u, v]
            bridge_list.append({
                "source_id": u,
                "target_id": v,
                "source_hostname": G.nodes[u].get("hostname", ""),
                "target_hostname": G.nodes[v].get("hostname", ""),
                "connection_type": edge_data.get("connection_type", ""),
                "reason": "Bridge link - sole connection between network segments",
            })

        return spofs

    def find_bridges(self) -> list[dict]:
        G = self._build_networkx_graph()
        if len(G.nodes) == 0:
            return []

        bridges = list(nx.bridges(G))
        result = []
        for u, v in bridges:
            edge_data = G.edges[u, v]
            result.append({
                "source_id": u,
                "target_id": v,
                "source_hostname": G.nodes[u].get("hostname", ""),
                "target_hostname": G.nodes[v].get("hostname", ""),
                "connection_type": edge_data.get("connection_type", ""),
            })
        return result

    def get_betweenness_centrality(self, top_n: int = 10) -> list[dict]:
        G = self._build_networkx_graph()
        if len(G.nodes) == 0:
            return []

        centrality = nx.betweenness_centrality(G)
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:top_n]

        return [
            {
                "device_id": node_id,
                "hostname": G.nodes[node_id].get("hostname", ""),
                "centrality": score,
                "device_type": G.nodes[node_id].get("device_type", ""),
            }
            for node_id, score in sorted_nodes
        ]


spof_detector = SPOFDetector()
