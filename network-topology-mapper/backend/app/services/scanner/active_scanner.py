import ipaddress
import logging
import platform
import re
import shutil
import socket
import subprocess
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _device_id_from_ip(ip: str, mac: str = "") -> str:
    """Generate a deterministic device ID from IP (preferred) or MAC."""
    if ip:
        return f"device-{ip}"
    if mac:
        return f"device-{mac}"
    return str(uuid.uuid4())


def _get_local_ip() -> str:
    """Get this machine's local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""


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

    def _run_nmap(self, args_str: str, target: str, timeout: int = 600) -> Optional[ET.Element]:
        """Run nmap with given args and return parsed XML root, or None on failure."""
        # target may be a single CIDR or multiple space-separated IPs
        cmd = [self._nmap_path, "-oX", "-"] + args_str.split() + target.split()
        logger.info("Running nmap command: %s", " ".join(cmd))

        import time as _time
        t0 = _time.monotonic()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.error("Nmap scan timed out after %d seconds", timeout)
            return None
        except Exception as e:
            logger.error("Nmap scan failed with exception: %s", e)
            import traceback
            logger.error("Traceback:\n%s", traceback.format_exc())
            return None
        elapsed = _time.monotonic() - t0

        logger.info("nmap finished in %.1f seconds, return code: %d", elapsed, result.returncode)
        logger.debug("nmap stderr: %s", result.stderr.strip() if result.stderr else "(empty)")
        logger.debug("nmap stdout length: %d bytes", len(result.stdout) if result.stdout else 0)

        if result.returncode != 0:
            logger.error("Nmap FAILED with code %d", result.returncode)
            logger.error("nmap stderr:\n%s", result.stderr)
            return None

        if not result.stdout or not result.stdout.strip():
            logger.error("nmap returned empty stdout!")
            return None

        logger.debug("nmap XML output (first 500 chars):\n%s", result.stdout[:500])

        try:
            return ET.fromstring(result.stdout)
        except ET.ParseError as e:
            logger.error("Failed to parse nmap XML: %s", e)
            return None

    def _read_arp_table(self, subnet: str) -> list[dict]:
        """Read the OS ARP table and return device stubs for IPs on the target subnet.

        This is instant and catches devices that don't respond to nmap probes
        (phones, IoT, etc.) because the OS has already seen their ARP traffic.
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
        # Parse lines like: "  192.168.50.11         78-9c-85-41-1e-89     dynamic"
        for line in result.stdout.splitlines():
            line = line.strip()
            # Match IP and MAC on the line
            match = re.match(
                r"(\d+\.\d+\.\d+\.\d+)\s+([\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2})\s+(\w+)",
                line,
            )
            if not match:
                continue

            ip = match.group(1)
            mac = match.group(2).upper().replace("-", ":")
            entry_type = match.group(3).lower()

            # Skip broadcast / static entries
            if entry_type == "static" or mac == "FF:FF:FF:FF:FF:FF":
                continue

            try:
                if ipaddress.ip_address(ip) not in network:
                    continue
            except ValueError:
                continue

            devices.append({
                "id": _device_id_from_ip(ip, mac),
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

    def scan_network(self, target: str = "192.168.0.0/24",
                     intensity: str = "normal",
                     callback=None) -> list[dict]:
        logger.info("=== ACTIVE SCANNER START === target=%s, intensity=%s", target, intensity)

        if not self._nmap_path:
            logger.warning("Nmap unavailable (not in PATH), returning empty results")
            return []

        logger.debug("nmap binary: %s", self._nmap_path)

        if intensity == "light":
            root = self._run_nmap(
                "-sn -T4 --host-timeout 3s",
                target, timeout=120,
            )
            devices = self._parse_hosts(root, callback) if root is not None else []
            devices = self._merge_arp_devices(devices, target, callback)
            return devices

        if intensity == "deep":
            root = self._run_nmap(
                "-sT -sV -sC -T4 --top-ports 1000 --host-timeout 30s",
                target, timeout=600,
            )
            devices = self._parse_hosts(root, callback) if root is not None else []
            devices = self._merge_arp_devices(devices, target, callback)
            return devices

        # --- Normal intensity: two-phase approach for speed ---

        # Phase A: ARP-based host discovery (uses Npcap, finds everything on LAN)
        logger.info("Normal scan phase A: ARP host discovery on %s", target)
        discovery_root = self._run_nmap(
            "-sn -T4 --host-timeout 3s",
            target, timeout=120,
        )

        # Collect live hosts from nmap discovery
        live_hosts: dict[str, dict] = {}  # ip -> {mac, vendor, hostname}
        if discovery_root is not None:
            for host_el in discovery_root.findall("host"):
                status_el = host_el.find("status")
                if status_el is None or status_el.get("state") != "up":
                    continue
                ip = ""
                mac = ""
                vendor = ""
                for addr_el in host_el.findall("address"):
                    if addr_el.get("addrtype") == "ipv4":
                        ip = addr_el.get("addr", "")
                    elif addr_el.get("addrtype") == "mac":
                        mac = addr_el.get("addr", "")
                        vendor = addr_el.get("vendor", "")
                if ip:
                    hostname = ""
                    hostnames_el = host_el.find("hostnames")
                    if hostnames_el is not None:
                        for hn_el in hostnames_el.findall("hostname"):
                            name = hn_el.get("name", "")
                            if name:
                                hostname = name
                                break
                    live_hosts[ip] = {"mac": mac, "vendor": vendor, "hostname": hostname}

        logger.info("Phase A (nmap) discovered %d live hosts", len(live_hosts))

        # Also pull ARP table — catches devices that didn't respond to nmap probes
        arp_devices = self._read_arp_table(target)
        for arp_dev in arp_devices:
            ip = arp_dev["ip"]
            if ip not in live_hosts:
                live_hosts[ip] = {"mac": arp_dev["mac"], "vendor": "", "hostname": ""}
                logger.info("  ARP table added: %s (mac=%s)", ip, arp_dev["mac"])

        # Include local machine
        local_ip = _get_local_ip()
        if local_ip and local_ip not in live_hosts:
            live_hosts[local_ip] = {"mac": "", "vendor": "", "hostname": platform.node()}
            logger.info("  Added local machine: %s (%s)", local_ip, platform.node())

        logger.info("Phase A total: %d live hosts", len(live_hosts))

        if not live_hosts:
            return []

        # Phase B: port scan a sample of hosts for richer device-type detection
        # Port-scan all hosts (they're already known live, so this is fast)
        all_ips = list(live_hosts.keys())
        target_list = " ".join(all_ips)
        logger.info("Normal scan phase B: port scan %d live hosts", len(all_ips))
        root = self._run_nmap(
            "-sT -T4 --top-ports 25 --host-timeout 5s --max-retries 1",
            target_list, timeout=300,
        )

        devices = self._parse_hosts(root, callback) if root is not None else []

        # Merge any hosts from Phase A that Phase B didn't return
        now = datetime.utcnow().isoformat()
        found_ips = {d["ip"] for d in devices}
        for ip, info in live_hosts.items():
            if ip not in found_ips:
                logger.info("  Adding discovery-only host as stub: %s (mac=%s)", ip, info["mac"])
                stub = {
                    "id": _device_id_from_ip(ip, info["mac"]),
                    "ip": ip,
                    "mac": info["mac"],
                    "hostname": info["hostname"] or ip,
                    "device_type": self._guess_device_type([], [], info["vendor"], "", ip),
                    "vendor": info["vendor"],
                    "os": "",
                    "open_ports": [],
                    "services": [],
                    "first_seen": now,
                    "last_seen": now,
                    "discovery_method": "active_scan",
                    "status": "online",
                    "risk_score": 0.0,
                }
                devices.append(stub)
                if callback:
                    callback(stub)
            else:
                # Enrich nmap-found device with Phase A metadata (MAC, vendor, hostname)
                for d in devices:
                    if d["ip"] == ip:
                        if not d["mac"] and info["mac"]:
                            d["mac"] = info["mac"]
                        if not d["vendor"] and info["vendor"]:
                            d["vendor"] = info["vendor"]
                        if (not d["hostname"] or d["hostname"] == ip) and info["hostname"]:
                            d["hostname"] = info["hostname"]
                        break

        logger.info("=== ACTIVE SCANNER DONE === %d total devices", len(devices))
        return devices

    def _merge_arp_devices(self, devices: list[dict], target: str, callback=None) -> list[dict]:
        """Add ARP table devices not already in the device list."""
        arp_devices = self._read_arp_table(target)
        found_ips = {d["ip"] for d in devices}
        for arp_dev in arp_devices:
            if arp_dev["ip"] not in found_ips:
                devices.append(arp_dev)
                if callback:
                    callback(arp_dev)
        return devices

    def _parse_hosts(self, root: ET.Element, callback=None) -> list[dict]:
        """Parse nmap XML output into device dicts."""
        all_hosts = root.findall("host")
        logger.info("nmap XML contains %d host elements", len(all_hosts))

        devices = []
        for host_el in all_hosts:
            status_el = host_el.find("status")
            host_state = status_el.get("state") if status_el is not None else "unknown"

            addr_els = host_el.findall("address")
            host_ip = ""
            for a in addr_els:
                if a.get("addrtype") == "ipv4":
                    host_ip = a.get("addr", "")
            logger.debug("  Host: %s state=%s", host_ip or "(no IP)", host_state)

            if status_el is None or host_state != "up":
                logger.debug("    -> skipped (not up)")
                continue

            ip = ""
            mac = ""
            for addr_el in host_el.findall("address"):
                if addr_el.get("addrtype") == "ipv4":
                    ip = addr_el.get("addr", "")
                elif addr_el.get("addrtype") == "mac":
                    mac = addr_el.get("addr", "")

            if not ip:
                logger.debug("    -> skipped (no IPv4 address)")
                continue

            vendor = ""
            for addr_el in host_el.findall("address"):
                if addr_el.get("addrtype") == "mac" and addr_el.get("vendor"):
                    vendor = addr_el.get("vendor", "")

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

            device_type = self._guess_device_type(open_ports, services, vendor, os_match, ip)

            device = {
                "id": _device_id_from_ip(ip, mac),
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
            logger.info("  FOUND DEVICE: %s (%s) type=%s vendor='%s' ports=%s services=%s",
                        ip, hostname, device_type, vendor, open_ports, services)

            if callback:
                callback(device)

        logger.info("=== nmap parse complete === %d devices from %d hosts", len(devices), len(all_hosts))
        return devices

    def _guess_device_type(self, ports: list[int], services: list[str],
                           vendor: str, os_info: str, ip: str = "") -> str:
        vendor_lower = vendor.lower()
        os_lower = os_info.lower()

        # Enterprise networking gear
        if any(k in vendor_lower for k in ["cisco", "juniper", "arista"]):
            if 179 in ports:
                return "router"
            return "switch"

        # Consumer routers / gateways
        consumer_router_vendors = [
            "netgear", "tp-link", "tplink", "linksys", "asus", "asustek",
            "d-link", "dlink", "belkin", "actiontec", "arris", "motorola",
            "huawei", "zyxel", "mikrotik", "synology", "buffalo", "tenda",
            "xiaomi", "google", "eero", "amazon", "compal", "sagemcom",
            "technicolor", "sercomm", "hitron", "calix",
        ]
        if any(k in vendor_lower for k in consumer_router_vendors):
            if ip and ip.endswith(".1"):
                return "router"
            if 80 in ports or 443 in ports or 53 in ports:
                return "router"

        # Wireless access points
        if any(k in vendor_lower for k in ["ubiquiti", "ruckus", "aruba"]):
            return "ap"

        # Firewalls
        if any(k in vendor_lower for k in ["fortinet", "palo alto", "checkpoint"]):
            return "firewall"

        # Printers
        if 631 in ports or 9100 in ports or "printer" in vendor_lower:
            return "printer"

        # Servers (Linux with SSH + HTTP)
        if 80 in ports and 443 in ports and 22 in ports:
            if "linux" in os_lower or "ubuntu" in os_lower:
                return "server"

        # Windows workstations
        if "windows" in os_lower:
            if 3389 in ports or 445 in ports:
                return "workstation"

        # IoT devices
        iot_vendors = [
            "espressif", "raspberry", "tuya", "sonos", "ring", "nest",
            "wyze", "philips", "wemo", "samsung", "shenzhen", "hangzhou",
        ]
        if len(ports) <= 2 and any(k in vendor_lower for k in iot_vendors):
            return "iot"

        # Fallback: .1 is almost always the gateway
        if ip and ip.endswith(".1"):
            return "router"

        return "unknown"


active_scanner = ActiveScanner()
