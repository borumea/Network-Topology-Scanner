import logging
from typing import Any
import networkx as nx

from app.db.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class PathAnalyzer:
    def _build_networkx_graph(self) -> nx.Graph:
        topology = neo4j_client.get_topology()
        G = nx.Graph()
        for device in topology["devices"]:
            G.add_node(device["id"], **device)
        for conn in topology["connections"]:
            weight = conn.get("latency_ms", 1.0) or 1.0
            G.add_edge(conn["source_id"], conn["target_id"], weight=weight, **{
                k: v for k, v in conn.items()
                if k not in ("source_id", "target_id", "weight")
            })
        return G

    def find_shortest_path(self, source_id: str, target_id: str) -> dict:
        G = self._build_networkx_graph()
        if source_id not in G or target_id not in G:
            return {"path": [], "length": -1, "error": "Source or target not found"}

        try:
            path = nx.shortest_path(G, source_id, target_id, weight="weight")
            length = nx.shortest_path_length(G, source_id, target_id, weight="weight")
            path_details = []
            for node_id in path:
                node_data = G.nodes[node_id]
                path_details.append({
                    "id": node_id,
                    "hostname": node_data.get("hostname", ""),
                    "device_type": node_data.get("device_type", ""),
                })
            return {"path": path_details, "length": round(length, 2), "hop_count": len(path) - 1}
        except nx.NetworkXNoPath:
            return {"path": [], "length": -1, "error": "No path exists"}

    def find_all_paths(self, source_id: str, target_id: str, max_paths: int = 5) -> list[dict]:
        G = self._build_networkx_graph()
        if source_id not in G or target_id not in G:
            return []

        try:
            paths = list(nx.shortest_simple_paths(G, source_id, target_id))[:max_paths]
            result = []
            for path in paths:
                path_details = []
                for node_id in path:
                    node_data = G.nodes[node_id]
                    path_details.append({
                        "id": node_id,
                        "hostname": node_data.get("hostname", ""),
                    })
                result.append({
                    "path": path_details,
                    "hop_count": len(path) - 1,
                })
            return result
        except nx.NetworkXNoPath:
            return []

    def find_bottlenecks(self, top_n: int = 10) -> list[dict]:
        G = self._build_networkx_graph()
        if len(G.nodes) == 0:
            return []

        edge_betweenness = nx.edge_betweenness_centrality(G)
        sorted_edges = sorted(edge_betweenness.items(), key=lambda x: x[1], reverse=True)[:top_n]

        result = []
        for (u, v), score in sorted_edges:
            result.append({
                "source_id": u,
                "target_id": v,
                "source_hostname": G.nodes[u].get("hostname", ""),
                "target_hostname": G.nodes[v].get("hostname", ""),
                "centrality": round(score, 4),
                "bandwidth": G.edges[u, v].get("bandwidth", ""),
            })
        return result

    def find_critical_paths_to_gateway(self) -> list[dict]:
        G = self._build_networkx_graph()
        gateways = [n for n, d in G.nodes(data=True) if d.get("is_gateway")]

        if not gateways:
            return []

        critical = []
        for node_id in G.nodes:
            if node_id in gateways:
                continue
            paths_to_gw = 0
            for gw in gateways:
                try:
                    paths = list(nx.node_disjoint_paths(G, node_id, gw))
                    paths_to_gw += len(paths)
                except (nx.NetworkXNoPath, nx.NetworkXError):
                    pass

            if paths_to_gw <= 1:
                node_data = G.nodes[node_id]
                critical.append({
                    "device_id": node_id,
                    "hostname": node_data.get("hostname", ""),
                    "device_type": node_data.get("device_type", ""),
                    "gateway_paths": paths_to_gw,
                    "risk": "high" if paths_to_gw == 0 else "medium",
                })
        return critical


path_analyzer = PathAnalyzer()
