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
from app.services.realtime.event_bus import event_bus
from app.db.sqlite_db import sqlite_db
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)

PASSIVE_SCAN_DURATION = 30  # seconds


class ScanCoordinator:
    """Orchestrates scan phases and deduplicates results."""

    def __init__(self):
        self._current_scan_id: Optional[str] = None
        self._devices_cache: dict[str, dict] = {}  # keyed by IP or MAC

    def start_scan(self, scan_type: str = "full", target: str = "192.168.0.0/24",
                   intensity: str = "normal") -> str:
        scan_id = str(uuid.uuid4())
        self._current_scan_id = scan_id
        self._devices_cache.clear()

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
            # Phase 1: Active scan (nmap)
            if scan_type in ("active", "full"):
                self._run_active_scan(scan_id, target, intensity)

            # Phase 2: Passive scan (scapy ARP/DNS/DHCP sniffing)
            if scan_type in ("passive", "full"):
                self._run_passive_scan(scan_id)

            # Phase 3: SNMP poll (device details for SNMP-capable devices)
            if scan_type in ("snmp", "full"):
                self._run_snmp_poll(scan_id)

            # Phase 4: Config pull (SSH + LLDP for manageable devices)
            if scan_type == "full":
                self._run_config_pull(scan_id)

            # Finalize
            device_count = len(self._devices_cache)
            sqlite_db.update_scan(scan_id, {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "devices_found": device_count,
            })

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
                for neighbor in neighbors:
                    neighbor_device = {
                        "id": str(uuid.uuid4()),
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
        key = device.get("mac") or device.get("ip", "")
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

    def cancel_scan(self, scan_id: str):
        if self._current_scan_id == scan_id:
            passive_scanner.stop()
            self._current_scan_id = None
            sqlite_db.update_scan(scan_id, {
                "status": "cancelled",
                "completed_at": datetime.utcnow().isoformat(),
            })


scan_coordinator = ScanCoordinator()
