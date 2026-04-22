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
        self._scan_log: list[str] = []

    def _publish_progress(self, scan_id: str, percent: int, phase: str,
                          devices_found: int, log_msg: str = None):
        """Publish scan progress with optional log message."""
        if log_msg:
            self._scan_log.append(log_msg)
        event_bus.publish_scan_progress({
            "scan_id": scan_id,
            "percent": percent,
            "phase": phase,
            "devices_found": devices_found,
            "log_messages": list(self._scan_log),
        })

    def start_scan(self, scan_type: str = "full", target: str = "192.168.0.0/24",
                   intensity: str = "normal", scan_id: Optional[str] = None) -> str:
        scan_id = scan_id or str(uuid.uuid4())
        self._current_scan_id = scan_id
        self._devices_cache.clear()
        self._lldp_data.clear()
        self._scan_log.clear()

        logger.info("=" * 60)
        logger.info("SCAN STARTED: id=%s", scan_id)
        logger.info("  scan_type:  %s", scan_type)
        logger.info("  target:     %s", target)
        logger.info("  intensity:  %s", intensity)
        logger.info("=" * 60)

        # Pre-populate cache from DB so we merge with existing devices
        try:
            existing = graph_builder.get_full_topology()
            for dev in existing.get("devices", []):
                key = dev.get("ip") or dev.get("mac", "")
                if key:
                    self._devices_cache[key] = dev
            logger.info("Pre-loaded %d existing devices into scan cache", len(self._devices_cache))
        except Exception as e:
            logger.warning("Could not pre-load devices from DB: %s", e)
            import traceback
            logger.debug("Pre-load traceback:\n%s", traceback.format_exc())

        scan_record = {
            "id": scan_id,
            "scan_type": scan_type,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "target_range": target,
            "config": {"intensity": intensity},
        }
        sqlite_db.create_scan(scan_record)
        logger.debug("Scan record created in SQLite: %s", scan_record)

        self._publish_progress(scan_id, 0, "initializing", 0,
                               f"Starting {scan_type} scan on {target}")

        try:
            settings = get_settings()
            logger.debug("Scan settings: enable_active=%s, enable_passive=%s, enable_snmp=%s",
                         settings.enable_active_scan, settings.enable_passive_scan, settings.enable_snmp_scan)

            # Phase 1: Active scan (nmap)
            phase1_run = scan_type in ("active", "full") and settings.enable_active_scan
            logger.info("Phase 1 (active nmap): %s (scan_type=%s, enable_active=%s)",
                        "RUNNING" if phase1_run else "SKIPPED", scan_type, settings.enable_active_scan)
            if phase1_run:
                self._publish_progress(scan_id, 5, "active_scan", 0,
                                       "Phase 1: Running nmap host discovery...")
                self._run_active_scan(scan_id, target, intensity)
                self._publish_progress(scan_id, 35, "active_scan", len(self._devices_cache),
                                       f"Phase 1 complete: {len(self._devices_cache)} devices found")
            else:
                self._scan_log.append("Phase 1: Active scan skipped")
            logger.info("After Phase 1: %d devices in cache", len(self._devices_cache))

            # Phase 2: Passive scan (scapy ARP/DNS/DHCP sniffing)
            phase2_run = scan_type in ("passive", "full") and settings.enable_passive_scan
            logger.info("Phase 2 (passive scapy): %s (scan_type=%s, enable_passive=%s)",
                        "RUNNING" if phase2_run else "SKIPPED", scan_type, settings.enable_passive_scan)
            if phase2_run:
                self._publish_progress(scan_id, 40, "passive_scan", len(self._devices_cache),
                                       "Phase 2: Listening for network traffic...")
                self._run_passive_scan(scan_id)
                self._publish_progress(scan_id, 50, "passive_scan", len(self._devices_cache),
                                       f"Phase 2 complete: {len(self._devices_cache)} devices total")
            else:
                self._scan_log.append("Phase 2: Passive scan skipped")
            logger.info("After Phase 2: %d devices in cache", len(self._devices_cache))

            # Phase 3: SNMP poll (device details for SNMP-capable devices)
            phase3_run = scan_type in ("snmp", "full") and settings.enable_snmp_scan
            logger.info("Phase 3 (SNMP poll): %s (scan_type=%s, enable_snmp=%s)",
                        "RUNNING" if phase3_run else "SKIPPED", scan_type, settings.enable_snmp_scan)
            if phase3_run:
                self._publish_progress(scan_id, 55, "snmp_poll", len(self._devices_cache),
                                       "Phase 3: Polling SNMP-capable devices...")
                self._run_snmp_poll(scan_id)
                self._publish_progress(scan_id, 70, "snmp_poll", len(self._devices_cache),
                                       f"Phase 3 complete: {len(self._devices_cache)} devices total")
            else:
                self._scan_log.append("Phase 3: SNMP poll skipped")
            logger.info("After Phase 3: %d devices in cache", len(self._devices_cache))

            # Phase 4: Config pull (SSH + LLDP for manageable devices)
            phase4_run = scan_type == "full"
            logger.info("Phase 4 (config pull): %s", "RUNNING" if phase4_run else "SKIPPED")
            if phase4_run:
                self._publish_progress(scan_id, 80, "config_pull", len(self._devices_cache),
                                       "Phase 4: Pulling device configurations via SSH...")
                self._run_config_pull(scan_id)
                self._publish_progress(scan_id, 85, "config_pull", len(self._devices_cache),
                                       f"Phase 4 complete: {len(self._devices_cache)} devices total")
            else:
                self._scan_log.append("Phase 4: Config pull skipped")
            logger.info("After Phase 4: %d devices in cache", len(self._devices_cache))

            # Dump all cached devices before inference
            logger.debug("=== DEVICE CACHE BEFORE INFERENCE ===")
            for ip_key, dev in self._devices_cache.items():
                logger.debug("  [%s] id=%s hostname=%s type=%s ports=%s services=%s",
                             ip_key, dev.get("id"), dev.get("hostname"), dev.get("device_type"),
                             dev.get("open_ports", []), dev.get("services", []))
            logger.debug("=== END DEVICE CACHE ===")

            # Phase 5: Connection inference
            logger.info("Phase 5 (connection inference): RUNNING with %d devices", len(self._devices_cache))
            self._publish_progress(scan_id, 90, "connection_inference", len(self._devices_cache),
                                   "Phase 5: Inferring network connections...")

            inferred_connections = connection_inference.infer_connections(
                devices=self._devices_cache,
                target_subnet=target,
                lldp_data=self._lldp_data if self._lldp_data else None,
            )

            logger.info("Connection inference returned %d edges", len(inferred_connections))
            for conn in inferred_connections:
                logger.debug("  Edge: %s -> %s (type=%s)", conn.get("source_id"), conn.get("target_id"), conn.get("connection_type"))
                graph_builder.upsert_connection(conn)

            # Finalize
            device_count = len(self._devices_cache)
            logger.info("SCAN COMPLETE: %d devices, %d connections", device_count, len(inferred_connections))

            sqlite_db.update_scan(scan_id, {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "devices_found": device_count,
            })

            # Save topology snapshot
            topology = graph_builder.get_full_topology()
            logger.debug("Final topology: %d devices, %d connections, %d dependencies",
                         len(topology.get("devices", [])), len(topology.get("connections", [])),
                         len(topology.get("dependencies", [])))
            self._save_snapshot(topology, device_count, len(inferred_connections))

            # Run post-scan analysis in background
            def _run_analysis_bg():
                try:
                    from app.tasks.analysis_tasks import run_analysis
                    run_analysis()
                except Exception as exc:
                    logger.warning("Post-scan analysis failed: %s", exc)
            import threading as _th
            _th.Thread(target=_run_analysis_bg, daemon=True).start()

            self._publish_progress(scan_id, 100, "completed", device_count,
                                   f"Scan complete: {device_count} devices, {len(inferred_connections)} connections")

        except Exception as e:
            logger.error("SCAN %s FAILED: %s", scan_id, e)
            import traceback
            logger.error("Scan failure traceback:\n%s", traceback.format_exc())
            sqlite_db.update_scan(scan_id, {
                "status": "failed",
                "completed_at": datetime.utcnow().isoformat(),
            })

        self._current_scan_id = None
        return scan_id

    def _run_active_scan(self, scan_id: str, target: str, intensity: str):
        def on_device_found(device):
            self._deduplicate_and_store(device)
            self._publish_progress(scan_id, 20, "active_scan", len(self._devices_cache),
                                   f"Discovered: {device.get('hostname') or device.get('ip', '?')}")

        devices = active_scanner.scan_network(target, intensity, callback=on_device_found)
        for device in devices:
            self._deduplicate_and_store(device)

        logger.info("Active scan phase complete: %d devices", len(self._devices_cache))

    def _run_passive_scan(self, scan_id: str):
        if not passive_scanner.available:
            logger.warning("Passive scanner unavailable (scapy not installed), skipping")
            return

        settings = get_settings()
        interfaces = settings.get_passive_interfaces()

        collected = []

        def on_passive_device(device):
            collected.append(device)

        logger.info("Starting passive scan on %s for %ds",
                    ", ".join(interfaces) if interfaces else "(none)",
                    PASSIVE_SCAN_DURATION)
        passive_scanner.start(interface=interfaces, callback=on_passive_device)
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
