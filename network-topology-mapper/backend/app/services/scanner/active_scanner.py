import ipaddress
import logging
import re
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ActiveScanner:
    """Calls nmap directly via subprocess to avoid python-nmap Windows bugs."""

    def __init__(self):
        self._nmap_path: Optional[str] = shutil.which("nmap")
        if not self._nmap_path:
            logger.warning("nmap binary not found in PATH. Active scanning unavailable.")
        else:
            logger.info("nmap found at: %s", self._nmap_path)

    @property
    def available(self) -> bool:
        return self._nmap_path is not None

    def scan_network(self, target: str = "192.168.0.0/24",
                     intensity: str = "normal",
                     callback=None) -> list[dict]:
        if not self._nmap_path:
            logger.warning("Nmap unavailable, returning empty results")
            return []

        # --unprivileged: skip raw sockets (avoids Windows assertion crash in python-nmap)
        # -PS: TCP connect ping for host discovery (works without admin)
        # --host-timeout 1500ms: skip hosts that don't respond quickly (dead IPs timeout fast)
        args = {
            "light": "--unprivileged -sn -PS21,22,80,139,443,445,3389,8080 --host-timeout 1500ms -T4",
            "normal": "--unprivileged -sT -sV -PS21,22,80,139,443,445,3389,8080 --top-ports 100 --host-timeout 10s -T4 --max-retries 1",
            "deep": "--unprivileged -sT -sV -sC -PS21,22,80,139,443,445,3389,8080 --top-ports 1000 --host-timeout 30s -T4",
        }.get(intensity, "--unprivileged -sT -sV -PS21,22,80,443,445,3389 --top-ports 100 --host-timeout 10s -T4 --max-retries 1")

        cmd = [self._nmap_path, "-oX", "-"] + args.split() + [target]
        logger.info("Running nmap command: %s", " ".join(cmd))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                logger.error("Nmap failed with code %d: %s", result.returncode, result.stderr)
                return []

            root = ET.fromstring(result.stdout)

        except subprocess.TimeoutExpired:
            logger.error("Nmap scan timed out")
            return []
        except ET.ParseError as e:
            logger.error("Failed to parse nmap XML output: %s", e)
            return []
        except Exception as e:
            logger.error("Nmap scan failed: %s", e)
            return []

        devices = []
        for host_el in root.findall("host"):
            status_el = host_el.find("status")
            if status_el is None or status_el.get("state") != "up":
                continue

            # IP and MAC addresses
            ip = ""
            mac = ""
            for addr_el in host_el.findall("address"):
                if addr_el.get("addrtype") == "ipv4":
                    ip = addr_el.get("addr", "")
                elif addr_el.get("addrtype") == "mac":
                    mac = addr_el.get("addr", "")

            if not ip:
                continue

            # Vendor from MAC address element
            vendor = ""
            for addr_el in host_el.findall("address"):
                if addr_el.get("addrtype") == "mac" and addr_el.get("vendor"):
                    vendor = addr_el.get("vendor", "")

            # Hostname
            hostname = ""
            hostnames_el = host_el.find("hostnames")
            if hostnames_el is not None:
                for hn_el in hostnames_el.findall("hostname"):
                    name = hn_el.get("name", "")
                    if name:
                        hostname = name
                        break

            # Ports and services
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

            # OS detection
            os_match = ""
            os_el = host_el.find("os")
            if os_el is not None:
                osmatch_el = os_el.find("osmatch")
                if osmatch_el is not None:
                    os_match = osmatch_el.get("name", "")

            device_type = self._guess_device_type(open_ports, services, vendor, os_match)

            device = {
                "id": str(uuid.uuid4()),
                "ip": ip,
                "mac": mac,
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

        logger.info("Nmap scan found %d devices", len(devices))

        # Supplement with ARP table — catches devices that don't respond to TCP probes
        arp_devices = self._read_arp_table(target)
        nmap_ips = {d["ip"] for d in devices}
        arp_added = 0
        for arp_dev in arp_devices:
            if arp_dev["ip"] not in nmap_ips:
                devices.append(arp_dev)
                arp_added += 1
                if callback:
                    callback(arp_dev)
        if arp_added:
            logger.info("ARP table added %d devices that nmap missed", arp_added)

        logger.info("Active scan complete: %d devices total", len(devices))
        return devices

    def _read_arp_table(self, subnet: str) -> list[dict]:
        """Read the OS ARP table and return device stubs for IPs on the target subnet.

        This is instant and catches devices that don't respond to nmap TCP probes
        (phones, IoT, smart TVs, etc.) because the OS has already seen their ARP traffic.
        """
        try:
            network = ipaddress.ip_network(subnet, strict=False)
        except ValueError:
            return []

        try:
            result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return []
        except Exception as e:
            logger.debug("ARP table read failed: %s", e)
            return []

        devices = []
        now = datetime.utcnow().isoformat()
        for line in result.stdout.splitlines():
            line = line.strip()
            # Match IP and MAC — handles both Linux/macOS (colon-separated)
            # and Windows (dash-separated) formats
            match = re.match(
                r".*?(\d+\.\d+\.\d+\.\d+)\s+"
                r"([\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2}[:-]"
                r"[\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2})\s+(\w+)",
                line,
            )
            if not match:
                continue

            ip = match.group(1)
            mac = match.group(2).upper().replace("-", ":")
            entry_type = match.group(3).lower()

            if entry_type == "static" or mac == "FF:FF:FF:FF:FF:FF":
                continue

            try:
                if ipaddress.ip_address(ip) not in network:
                    continue
            except ValueError:
                continue

            devices.append({
                "id": str(uuid.uuid4()),
                "ip": ip,
                "mac": mac,
                "hostname": ip,
                "device_type": "unknown",
                "vendor": "",
                "os": "",
                "open_ports": [],
                "services": [],
                "first_seen": now,
                "last_seen": now,
                "discovery_method": "arp_table",
                "status": "online",
                "risk_score": 0.0,
            })

        logger.info("ARP table scan found %d devices on %s", len(devices), subnet)
        return devices

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
