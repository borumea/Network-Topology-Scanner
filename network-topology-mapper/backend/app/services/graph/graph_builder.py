import logging
from typing import Any

from app.db.topology_db import topology_db
from app.services.realtime.event_bus import event_bus

logger = logging.getLogger(__name__)


class GraphBuilder:
    def upsert_device(self, device: dict) -> bool:
        logger.debug("GraphBuilder.upsert_device: id=%s ip=%s hostname=%s",
                     device.get("id"), device.get("ip"), device.get("hostname"))
        existing = topology_db.get_device(device["id"])
        is_new = existing is None
        logger.debug("  -> is_new=%s (existing=%s)", is_new, "found" if existing else "None")
        topology_db.upsert_device(device)

        if is_new:
            event_bus.publish_device_update("device_added", device)
            logger.debug("  -> published device_added event")
        else:
            event_bus.publish_device_update("device_update", device)
            logger.debug("  -> published device_update event")

        return is_new

    def upsert_connection(self, connection: dict) -> None:
        logger.debug("GraphBuilder.upsert_connection: %s -> %s",
                     connection.get("source_id"), connection.get("target_id"))
        topology_db.upsert_connection(connection)
        event_bus.publish_connection_change(connection)

    def upsert_dependency(self, dependency: dict) -> None:
        topology_db.upsert_dependency(dependency)

    def remove_device(self, device_id: str) -> None:
        topology_db.delete_device(device_id)
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
        logger.debug("get_full_topology called: layer=%s, vlan=%s, subnet=%s, device_type=%s, risk_min=%s",
                     layer, vlan, subnet, device_type, risk_min)
        devices = topology_db.get_all_devices()
        connections = topology_db.get_all_connections()
        dependencies = topology_db.get_all_dependencies()
        logger.debug("get_full_topology raw from DB: %d devices, %d connections, %d dependencies",
                     len(devices), len(connections), len(dependencies))

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
