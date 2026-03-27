import logging
import shutil
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
        logger.info("=== ACTIVE SCANNER START === target=%s, intensity=%s", target, intensity)

        if not self._nmap_path:
            logger.warning("Nmap unavailable (not in PATH), returning empty results")
            return []

        logger.debug("nmap binary: %s", self._nmap_path)

        args = {
            "light": "--unprivileged -sn -PS21,22,80,139,443,445,3389,8080 --host-timeout 1500ms -T4",
            "normal": "--unprivileged -sT -sV -PS21,22,80,139,443,445,3389,8080 --top-ports 100 --host-timeout 10s -T4 --max-retries 1",
            "deep": "--unprivileged -sT -sV -sC -PS21,22,80,139,443,445,3389,8080 --top-ports 1000 --host-timeout 30s -T4",
        }.get(intensity, "--unprivileged -sT -sV -PS21,22,80,443,445,3389 --top-ports 100 --host-timeout 10s -T4 --max-retries 1")

        cmd = [self._nmap_path, "-oX", "-"] + args.split() + [target]
        logger.info("Running nmap command: %s", " ".join(cmd))

        try:
            import time as _time
            t0 = _time.monotonic()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            elapsed = _time.monotonic() - t0

            logger.info("nmap finished in %.1f seconds, return code: %d", elapsed, result.returncode)
            logger.debug("nmap stderr: %s", result.stderr.strip() if result.stderr else "(empty)")
            logger.debug("nmap stdout length: %d bytes", len(result.stdout) if result.stdout else 0)

            if result.returncode != 0:
                logger.error("Nmap FAILED with code %d", result.returncode)
                logger.error("nmap stderr:\n%s", result.stderr)
                logger.error("nmap stdout (first 2000 chars):\n%s", result.stdout[:2000] if result.stdout else "(empty)")
                return []

            if not result.stdout or not result.stdout.strip():
                logger.error("nmap returned empty stdout!")
                return []

            # Log first 500 chars of XML for debugging
            logger.debug("nmap XML output (first 500 chars):\n%s", result.stdout[:500])

            root = ET.fromstring(result.stdout)

        except subprocess.TimeoutExpired:
            logger.error("Nmap scan timed out after 600 seconds")
            return []
        except ET.ParseError as e:
            logger.error("Failed to parse nmap XML: %s", e)
            logger.error("Raw stdout (first 2000 chars):\n%s", result.stdout[:2000] if result.stdout else "(empty)")
            return []
        except Exception as e:
            logger.error("Nmap scan failed with exception: %s", e)
            import traceback
            logger.error("Traceback:\n%s", traceback.format_exc())
            return []

        # Count total hosts in XML
        all_hosts = root.findall("host")
        logger.info("nmap XML contains %d host elements", len(all_hosts))

        devices = []
        for host_el in all_hosts:
            status_el = host_el.find("status")
            host_state = status_el.get("state") if status_el is not None else "unknown"

            # Log every host, even down ones
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

            device_type = self._guess_device_type(open_ports, services, vendor, os_match)

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

        logger.info("=== ACTIVE SCANNER DONE === %d devices found from %d hosts", len(devices), len(all_hosts))
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
