import logging
from typing import Any

from app.db.neo4j_client import neo4j_client
from app.services.realtime.event_bus import event_bus

logger = logging.getLogger(__name__)


class GraphBuilder:
    def upsert_device(self, device: dict) -> bool:
        existing = neo4j_client.get_device(device["id"])
        is_new = existing is None
        neo4j_client.upsert_device(device)

        if is_new:
            event_bus.publish_device_update("device_added", device)
        else:
            event_bus.publish_device_update("device_update", device)

        return is_new

    def upsert_connection(self, connection: dict) -> None:
        neo4j_client.upsert_connection(connection)
        event_bus.publish_connection_change(connection)

    def upsert_dependency(self, dependency: dict) -> None:
        neo4j_client.upsert_dependency(dependency)

    def remove_device(self, device_id: str) -> None:
        neo4j_client.execute_write(
            "MATCH (d:Device {id: $id}) DETACH DELETE d",
            {"id": device_id}
        )
        event_bus.publish_device_update("device_removed", {"id": device_id})

    def bulk_upsert(self, devices: list[dict], connections: list[dict],
                    dependencies: list[dict] = None) -> dict:
        new_count = 0
        for device in devices:
            if self.upsert_device(device):
                new_count += 1

        for conn in connections:
            self.upsert_connection(conn)

        if dependencies:
            for dep in dependencies:
                self.upsert_dependency(dep)

        return {"total_devices": len(devices), "new_devices": new_count,
                "connections": len(connections)}

    def get_full_topology(self, layer: str = None, vlan: int = None,
                          subnet: str = None, device_type: str = None,
                          risk_min: float = None) -> dict:
        devices = neo4j_client.get_all_devices()
        connections = neo4j_client.get_all_connections()
        dependencies = neo4j_client.get_all_dependencies()

        if layer == "physical":
            device_types = {"router", "switch", "ap", "firewall"}
            conn_types = {"ethernet", "fiber", "wireless"}
            devices = [d for d in devices if d.get("device_type") in device_types]
            device_ids = {d["id"] for d in devices}
            connections = [c for c in connections
                          if c.get("connection_type") in conn_types
                          and c.get("source_id") in device_ids
                          and c.get("target_id") in device_ids]
            dependencies = []
        elif layer == "logical":
            pass
        elif layer == "application":
            device_types = {"server", "firewall"}
            devices = [d for d in devices if d.get("device_type") in device_types]
            device_ids = {d["id"] for d in devices}
            connections = [c for c in connections
                          if c.get("source_id") in device_ids
                          and c.get("target_id") in device_ids]

        if vlan is not None:
            devices = [d for d in devices if vlan in d.get("vlan_ids", [])]
        if subnet:
            devices = [d for d in devices if d.get("subnet") == subnet]
        if device_type:
            devices = [d for d in devices if d.get("device_type") == device_type]
        if risk_min is not None:
            devices = [d for d in devices if d.get("risk_score", 0) >= risk_min]

        device_ids = {d["id"] for d in devices}
        connections = [c for c in connections
                       if c.get("source_id") in device_ids and c.get("target_id") in device_ids]
        dependencies = [dep for dep in dependencies
                        if dep.get("source_id") in device_ids and dep.get("target_id") in device_ids]

        return {
            "devices": devices,
            "connections": connections,
            "dependencies": dependencies,
        }


graph_builder = GraphBuilder()
