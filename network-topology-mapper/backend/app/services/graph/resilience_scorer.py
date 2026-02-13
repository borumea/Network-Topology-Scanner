import logging
import networkx as nx

from app.services.graph.spof_detector import spof_detector

logger = logging.getLogger(__name__)


class ResilienceScorer:
    def _build_networkx_graph(self) -> nx.Graph:
        from app.services.graph.graph_builder import graph_builder
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

    def calculate_device_risk(self, device_id: str) -> dict:
        G = self._build_networkx_graph()
        if device_id not in G:
            return {"risk_score": 0, "factors": []}

        node_data = G.nodes[device_id]
        factors = []
        score = 0.0

        # Factor 1: Degree centrality (single connection = higher risk)
        degree = G.degree(device_id)
        if degree <= 1:
            score += 0.3
            factors.append("Single connection - no redundancy")
        elif degree == 2:
            score += 0.1
            factors.append("Limited connections")

        # Factor 2: Betweenness centrality
        centrality = nx.betweenness_centrality(G)
        bc = centrality.get(device_id, 0)
        if bc > 0.1:
            score += 0.25
            factors.append(f"High betweenness centrality ({bc:.3f})")

        # Factor 3: Is it an articulation point?
        art_points = set(nx.articulation_points(G))
        if device_id in art_points:
            score += 0.25
            factors.append("Articulation point - removal fragments network")

        # Factor 4: Device type criticality
        dtype = node_data.get("device_type", "")
        if dtype in ("firewall", "router"):
            score += 0.1
            factors.append(f"Critical infrastructure device ({dtype})")
        elif dtype == "switch" and node_data.get("hostname", "").startswith("core"):
            score += 0.1
            factors.append("Core switch")

        # Factor 5: Gateway
        if node_data.get("is_gateway"):
            score += 0.1
            factors.append("Gateway device")

        score = min(score, 1.0)

        return {
            "device_id": device_id,
            "risk_score": round(score, 2),
            "factors": factors,
        }

    def calculate_global_resilience(self) -> dict:
        G = self._build_networkx_graph()
        if len(G.nodes) == 0:
            return {"score": 10.0, "breakdown": {}}

        total_nodes = len(G.nodes)
        total_edges = len(G.edges)

        # Connectivity score (0-2.5)
        if nx.is_connected(G):
            connectivity = nx.node_connectivity(G) if total_nodes < 500 else 1
            conn_score = min(connectivity / 3.0 * 2.5, 2.5)
        else:
            conn_score = 0.0

        # Redundancy score (0-2.5) based on edge-to-node ratio
        redundancy_ratio = total_edges / max(total_nodes, 1)
        red_score = min(redundancy_ratio / 2.0 * 2.5, 2.5)

        # SPOF penalty (0-2.5)
        spofs = spof_detector.find_spofs()
        spof_penalty = min(len(spofs) * 0.5, 2.5)
        spof_score = 2.5 - spof_penalty

        # Average path diversity (0-2.5)
        gateways = [n for n, d in G.nodes(data=True) if d.get("is_gateway")]
        if gateways:
            path_diversity_sum = 0
            sampled = 0
            for node_id in list(G.nodes)[:50]:
                if node_id in gateways:
                    continue
                for gw in gateways[:2]:
                    try:
                        paths = list(nx.node_disjoint_paths(G, node_id, gw))
                        path_diversity_sum += len(paths)
                        sampled += 1
                    except (nx.NetworkXNoPath, nx.NetworkXError):
                        sampled += 1
            avg_diversity = path_diversity_sum / max(sampled, 1)
            path_score = min(avg_diversity / 3.0 * 2.5, 2.5)
        else:
            path_score = 1.0

        total_score = conn_score + red_score + spof_score + path_score
        total_score = round(min(max(total_score, 0), 10), 1)

        return {
            "score": total_score,
            "max_score": 10.0,
            "breakdown": {
                "connectivity": round(conn_score, 2),
                "redundancy": round(red_score, 2),
                "spof_resistance": round(spof_score, 2),
                "path_diversity": round(path_score, 2),
            },
            "total_devices": total_nodes,
            "total_connections": total_edges,
            "spof_count": len(spofs),
            "spofs": spofs[:5],
        }


resilience_scorer = ResilienceScorer()
