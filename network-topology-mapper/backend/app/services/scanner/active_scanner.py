import ipaddress
import logging
import platform
import re
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system().lower() == "windows"


class ActiveScanner:
    """Network scanner: ping sweep + ARP for discovery, nmap for port details."""

    def __init__(self):
        self._nmap_path: Optional[str] = shutil.which("nmap")
        if not self._nmap_path:
            logger.warning("nmap binary not found in PATH. Port scanning unavailable.")
        else:
            logger.info("nmap found at: %s", self._nmap_path)

    @property
    def available(self) -> bool:
        return True

    def scan_network(self, target: str = "192.168.0.0/24",
                     intensity: str = "normal",
                     callback=None) -> list[dict]:
        # Phase A: Ping sweep + ARP table for host discovery
        self._ping_sweep(target)
        discovered = self._read_arp_table(target)
        logger.info("Host discovery found %d devices", len(discovered))

        # Phase B: nmap port scan on discovered hosts for service details
        nmap_results: dict[str, dict] = {}
        if self._nmap_path and discovered:
            nmap_results = self._nmap_port_scan(
                [d["ip"] for d in discovered], intensity,
            )

        # Merge discovery + port scan results
        devices = []
        for disc in discovered:
            ip = disc["ip"]
            nmap_info = nmap_results.get(ip, {})

            open_ports = nmap_info.get("open_ports", [])
            services = nmap_info.get("services", [])
            vendor = nmap_info.get("vendor", "")
            hostname = nmap_info.get("hostname", "")
            os_match = nmap_info.get("os", "")

            device_type = self._guess_device_type(open_ports, services, vendor, os_match)

            device = {
                "id": str(uuid.uuid4()),
                "ip": ip,
                "mac": disc.get("mac", ""),
                "hostname": hostname or ip,
                "device_type": device_type,
                "vendor": vendor,
                "os": os_match,
                "open_ports": open_ports,
                "services": services,
                "first_seen": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
                "discovery_method": "active_scan",
                "status": "online",
                "risk_score": 0.0,
            }
            devices.append(device)

            if callback:
                callback(device)

        logger.info("Active scan complete: %d devices found", len(devices))
        return devices

    # ------------------------------------------------------------------
    # Host discovery: ping sweep + ARP table
    # ------------------------------------------------------------------
    def _ping_sweep(self, target: str) -> None:
        """Ping all IPs in subnet to populate the OS ARP table."""
        try:
            network = ipaddress.ip_network(target, strict=False)
        except ValueError:
            return

        hosts = list(network.hosts())
        logger.info("Ping sweep: %d hosts in %s", len(hosts), target)

        ping_flag = "-n" if IS_WINDOWS else "-c"
        timeout_flag = "-w" if IS_WINDOWS else "-W"
        timeout_val = "500" if IS_WINDOWS else "1"

        def ping_one(ip: str):
            try:
                subprocess.run(
                    ["ping", ping_flag, "1", timeout_flag, timeout_val, ip],
                    capture_output=True, timeout=3,
                )
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=50) as pool:
            list(pool.map(lambda ip: ping_one(str(ip)), hosts))

        logger.info("Ping sweep complete")

    def _read_arp_table(self, target: str) -> list[dict]:
        """Read ARP table and return devices within the target subnet."""
        try:
            result = subprocess.run(
                ["arp", "-a"], capture_output=True, text=True, timeout=10,
            )
        except Exception as e:
            logger.error("Failed to read ARP table: %s", e)
            return []

        try:
            network = ipaddress.ip_network(target, strict=False)
        except ValueError:
            network = None

        devices = []
        for line in result.stdout.splitlines():
            # Windows: "  192.168.1.1          dc-45-46-63-3f-58     dynamic"
            win_match = re.match(
                r"\s+([\d.]+)\s+"
                r"([\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2}[:-]"
                r"[\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2})\s+(\w+)",
                line,
            )
            if win_match:
                ip = win_match.group(1)
                mac = win_match.group(2).upper().replace("-", ":")
                entry_type = win_match.group(3).lower()
                if entry_type == "static":
                    continue
                if mac.startswith("FF:FF:FF") or mac.startswith("01:00:5E"):
                    continue
                if network and ipaddress.ip_address(ip) not in network:
                    continue
                devices.append({"ip": ip, "mac": mac})

        logger.info("ARP table: %d devices in %s", len(devices), target)
        return devices

    # ------------------------------------------------------------------
    # Port scanning (unprivileged, runs on already-discovered hosts)
    # ------------------------------------------------------------------
    def _nmap_port_scan(self, ips: list[str], intensity: str) -> dict[str, dict]:
        """Run nmap port scan on specific IPs. Returns dict keyed by IP."""
        args = {
            "light": "--unprivileged -sT --top-ports 20 --host-timeout 5s -T4",
            "normal": "--unprivileged -sT -sV --top-ports 100 --host-timeout 10s -T4 --max-retries 1",
            "deep": "--unprivileged -sT -sV -sC --top-ports 1000 --host-timeout 30s -T4",
        }.get(intensity, "--unprivileged -sT -sV --top-ports 100 --host-timeout 10s -T4 --max-retries 1")

        cmd = [self._nmap_path, "-oX", "-"] + args.split() + ips
        logger.info("Running nmap port scan on %d hosts", len(ips))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                logger.error("Nmap port scan failed: %s", result.stderr)
                return {}
            root = ET.fromstring(result.stdout)
        except subprocess.TimeoutExpired:
            logger.error("Nmap port scan timed out")
            return {}
        except ET.ParseError as e:
            logger.error("Failed to parse nmap XML: %s", e)
            return {}
        except Exception as e:
            logger.error("Nmap port scan failed: %s", e)
            return {}

        results = {}
        for host_el in root.findall("host"):
            ip = vendor = ""
            for addr_el in host_el.findall("address"):
                if addr_el.get("addrtype") == "ipv4":
                    ip = addr_el.get("addr", "")
                elif addr_el.get("addrtype") == "mac" and addr_el.get("vendor"):
                    vendor = addr_el.get("vendor", "")
            if not ip:
                continue

            hostname = ""
            hostnames_el = host_el.find("hostnames")
            if hostnames_el is not None:
                for hn_el in hostnames_el.findall("hostname"):
                    name = hn_el.get("name", "")
                    if name:
                        hostname = name
                        break

            open_ports = []
            services = []
            ports_el = host_el.find("ports")
            if ports_el is not None:
                for port_el in ports_el.findall("port"):
                    state_el = port_el.find("state")
                    if state_el is not None and state_el.get("state") == "open":
                        port_num = int(port_el.get("portid", "0"))
                        open_ports.append(port_num)
                        svc_el = port_el.find("service")
                        if svc_el is not None:
                            svc_name = svc_el.get("name", "")
                            if svc_name:
                                services.append(svc_name)

            os_match = ""
            os_el = host_el.find("os")
            if os_el is not None:
                osmatch_el = os_el.find("osmatch")
                if osmatch_el is not None:
                    os_match = osmatch_el.get("name", "")

            results[ip] = {
                "hostname": hostname,
                "vendor": vendor,
                "os": os_match,
                "open_ports": open_ports,
                "services": services,
            }

        return results

    # ------------------------------------------------------------------
    # Device type heuristics
    # ------------------------------------------------------------------
    def _guess_device_type(self, ports: list[int], services: list[str],
                           vendor: str, os_info: str) -> str:
        vendor_lower = vendor.lower()
        os_lower = os_info.lower()

        if any(k in vendor_lower for k in ["cisco", "juniper", "arista"]):
            if 179 in ports:
                return "router"
            return "switch"

        if any(k in vendor_lower for k in ["ubiquiti", "ruckus", "aruba"]):
            return "ap"

        if any(k in vendor_lower for k in ["fortinet", "palo alto", "checkpoint"]):
            return "firewall"

        if 631 in ports or 9100 in ports or "printer" in vendor_lower:
            return "printer"

        if 80 in ports and 443 in ports and 22 in ports:
            if "linux" in os_lower or "ubuntu" in os_lower:
                return "server"

        if "windows" in os_lower:
            if 3389 in ports or 445 in ports:
                return "workstation"

        if len(ports) <= 2 and any(k in vendor_lower for k in ["espressif", "raspberry", "tuya"]):
            return "iot"

        return "unknown"


active_scanner = ActiveScanner()
