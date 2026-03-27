import logging
import time
import uuid
from datetime import datetime
from typing import Any, Optional

from app.config import get_settings
from app.services.scanner.active_scanner import active_scanner
from app.services.scanner.passive_scanner import passive_scanner
from app.services.scanner.snmp_poller import snmp_poller
from app.services.scanner.config_puller import config_puller
from app.services.graph.graph_builder import graph_builder
from app.services.scanner.connection_inference import connection_inference
from app.services.realtime.event_bus import event_bus
from app.db.sqlite_db import sqlite_db
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)

PASSIVE_SCAN_DURATION = 30  # seconds


def _device_id_from_ip(ip: str, mac: str = "") -> str:
    """Generate a deterministic device ID from IP (preferred) or MAC."""
    if ip:
        return f"device-{ip}"
    if mac:
        return f"device-{mac}"
    return str(uuid.uuid4())


class ScanCoordinator:
    """Orchestrates scan phases and deduplicates results."""

    def __init__(self):
        self._current_scan_id: Optional[str] = None
        self._devices_cache: dict[str, dict] = {}  # keyed by IP or MAC
        self._lldp_data: list[dict] = []

    def start_scan(self, scan_type: str = "full", target: str = "192.168.0.0/24",
                   intensity: str = "normal", scan_id: Optional[str] = None) -> str:
        scan_id = scan_id or str(uuid.uuid4())
        self._current_scan_id = scan_id
        self._devices_cache.clear()
        self._lldp_data.clear()

        # Pre-populate cache from Neo4j so we merge with existing devices
        try:
            existing = graph_builder.get_full_topology()
            for dev in existing.get("devices", []):
                key = dev.get("ip") or dev.get("mac", "")
                if key:
                    self._devices_cache[key] = dev
            logger.info("Pre-loaded %d existing devices into scan cache", len(self._devices_cache))
        except Exception as e:
            logger.warning("Could not pre-load devices: %s", e)

        scan_record = {
            "id": scan_id,
            "scan_type": scan_type,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "target_range": target,
            "config": {"intensity": intensity},
        }
        sqlite_db.create_scan(scan_record)

        event_bus.publish_scan_progress({
            "scan_id": scan_id,
            "percent": 0,
            "phase": "initializing",
            "devices_found": 0,
        })

        try:
            settings = get_settings()

            # Phase 1: Active scan (nmap)
            if scan_type in ("active", "full") and settings.enable_active_scan:
                self._run_active_scan(scan_id, target, intensity)

            # Phase 2: Passive scan (scapy ARP/DNS/DHCP sniffing)
            if scan_type in ("passive", "full") and settings.enable_passive_scan:
                self._run_passive_scan(scan_id)

            # Phase 3: SNMP poll (device details for SNMP-capable devices)
            if scan_type in ("snmp", "full") and settings.enable_snmp_scan:
                self._run_snmp_poll(scan_id)

            # Phase 4: Config pull (SSH + LLDP for manageable devices)
            if scan_type == "full":
                self._run_config_pull(scan_id)

            # Phase 5: Connection inference — create edges from device data
            event_bus.publish_scan_progress({
                "scan_id": scan_id,
                "percent": 90,
                "phase": "connection_inference",
                "devices_found": len(self._devices_cache),
            })

            inferred_connections = connection_inference.infer_connections(
                devices=self._devices_cache,
                target_subnet=target,
                lldp_data=self._lldp_data if self._lldp_data else None,
            )

            for conn in inferred_connections:
                graph_builder.upsert_connection(conn)

            logger.info(
                "Connection inference complete: %d edges created",
                len(inferred_connections),
            )

            # Finalize
            device_count = len(self._devices_cache)
            sqlite_db.update_scan(scan_id, {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "devices_found": device_count,
            })

            # Save topology snapshot
            topology = graph_builder.get_full_topology()
            self._save_snapshot(topology, device_count, len(inferred_connections))

            # Run post-scan analysis in background (anomaly detection, SPOF, resilience)
            def _run_analysis_bg():
                try:
                    from app.tasks.analysis_tasks import run_analysis
                    run_analysis()
                except Exception as exc:
                    logger.warning("Post-scan analysis failed: %s", exc)
            import threading as _th
            _th.Thread(target=_run_analysis_bg, daemon=True).start()

            event_bus.publish_scan_progress({
                "scan_id": scan_id,
                "percent": 100,
                "phase": "completed",
                "devices_found": device_count,
            })

        except Exception as e:
            logger.error("Scan %s failed: %s", scan_id, e)
            sqlite_db.update_scan(scan_id, {
                "status": "failed",
                "completed_at": datetime.utcnow().isoformat(),
            })

        self._current_scan_id = None
        return scan_id

    def _run_active_scan(self, scan_id: str, target: str, intensity: str):
        event_bus.publish_scan_progress({
            "scan_id": scan_id,
            "percent": 5,
            "phase": "active_scan",
            "devices_found": 0,
        })

        def on_device_found(device):
            self._deduplicate_and_store(device)
            event_bus.publish_scan_progress({
                "scan_id": scan_id,
                "percent": 30,
                "phase": "active_scan",
                "devices_found": len(self._devices_cache),
            })

        devices = active_scanner.scan_network(target, intensity, callback=on_device_found)
        for device in devices:
            self._deduplicate_and_store(device)

        logger.info("Active scan phase complete: %d devices", len(self._devices_cache))

    def _run_passive_scan(self, scan_id: str):
        if not passive_scanner.available:
            logger.warning("Passive scanner unavailable (scapy not installed), skipping")
            return

        settings = get_settings()
        interface = settings.scan_passive_interface

        event_bus.publish_scan_progress({
            "scan_id": scan_id,
            "percent": 40,
            "phase": "passive_scan",
            "devices_found": len(self._devices_cache),
        })

        collected = []

        def on_passive_device(device):
            collected.append(device)

        logger.info("Starting passive scan on %s for %ds", interface, PASSIVE_SCAN_DURATION)
        passive_scanner.start(interface=interface, callback=on_passive_device)
        time.sleep(PASSIVE_SCAN_DURATION)
        passive_scanner.stop()

        for device in collected:
            self._deduplicate_and_store(device)

        logger.info("Passive scan phase complete: %d new devices from sniffing", len(collected))

    def _run_snmp_poll(self, scan_id: str):
        if not snmp_poller.available:
            logger.warning("SNMP poller unavailable (pysnmp not installed), skipping")
            return

        settings = get_settings()
        community = settings.snmp_community
        version = settings.snmp_version

        event_bus.publish_scan_progress({
            "scan_id": scan_id,
            "percent": 55,
            "phase": "snmp_poll",
            "devices_found": len(self._devices_cache),
        })

        polled = 0
        for ip, device in list(self._devices_cache.items()):
            if 161 in device.get("open_ports", []):
                snmp_data = snmp_poller.poll_device(ip, community=community, version=version)
                if snmp_data:
                    device.update({k: v for k, v in snmp_data.items() if v})
                    graph_builder.upsert_device(device)
                    polled += 1

        logger.info("SNMP poll phase complete: %d devices polled", polled)

    def _run_config_pull(self, scan_id: str):
        if not config_puller.available:
            logger.warning("Config puller unavailable (netmiko not installed), skipping")
            return

        settings = get_settings()
        username = settings.ssh_username
        password = settings.ssh_password

        if not username:
            logger.info("No SSH credentials configured, skipping config pull phase")
            return

        event_bus.publish_scan_progress({
            "scan_id": scan_id,
            "percent": 80,
            "phase": "config_pull",
            "devices_found": len(self._devices_cache),
        })

        pulled = 0
        for ip, device in list(self._devices_cache.items()):
            if 22 not in device.get("open_ports", []):
                continue

            # Determine netmiko device type from our device_type
            dev_type = device.get("device_type", "unknown")
            netmiko_type = {
                "router": "cisco_ios",
                "switch": "cisco_ios",
                "firewall": "cisco_asa",
            }.get(dev_type, "cisco_ios")

            # Try LLDP neighbor discovery
            neighbors = config_puller.get_lldp_neighbors(
                ip, device_type=netmiko_type,
                username=username, password=password
            )
            if neighbors:
                logger.info("Found %d LLDP neighbors on %s", len(neighbors), ip)
                # Preserve adjacency data for connection inference
                self._lldp_data.append({
                    "querying_device_id": device["id"],
                    "querying_device_ip": ip,
                    "neighbors": neighbors,
                })
                for neighbor in neighbors:
                    neighbor_device = {
                        "id": _device_id_from_ip(neighbor.get("ip", ""), ""),
                        "ip": neighbor.get("ip", ""),
                        "hostname": neighbor.get("hostname", ""),
                        "device_type": "unknown",
                        "discovery_method": "lldp",
                        "first_seen": datetime.utcnow().isoformat(),
                        "last_seen": datetime.utcnow().isoformat(),
                        "status": "online",
                    }
                    if neighbor_device["ip"] or neighbor_device["hostname"]:
                        self._deduplicate_and_store(neighbor_device)
                pulled += 1

        logger.info("Config pull phase complete: %d devices queried via SSH", pulled)

    def _deduplicate_and_store(self, device: dict):
        key = device.get("ip") or device.get("mac", "")
        if not key:
            return

        if key in self._devices_cache:
            existing = self._devices_cache[key]
            # Merge: keep existing ID, update fields
            for k, v in device.items():
                if v and k != "id":
                    existing[k] = v
            existing["last_seen"] = datetime.utcnow().isoformat()
            graph_builder.upsert_device(existing)
        else:
            self._devices_cache[key] = device
            graph_builder.upsert_device(device)

    def _save_snapshot(self, topology: dict, device_count: int, edge_count: int):
        try:
            snapshot = {
                "id": str(uuid.uuid4()),
                "created_at": datetime.utcnow().isoformat(),
                "device_count": device_count,
                "connection_count": edge_count,
                "risk_score": 0.0,
                "snapshot_data": {
                    "topology_json": topology,
                },
            }
            sqlite_db.create_snapshot(snapshot)
            logger.info("Topology snapshot saved: %d devices, %d edges", device_count, edge_count)
        except Exception as e:
            logger.warning("Failed to save topology snapshot: %s", e)

    def cancel_scan(self, scan_id: str):
        if self._current_scan_id == scan_id:
            passive_scanner.stop()
            self._current_scan_id = None
            sqlite_db.update_scan(scan_id, {
                "status": "cancelled",
                "completed_at": datetime.utcnow().isoformat(),
            })


scan_coordinator = ScanCoordinator()
