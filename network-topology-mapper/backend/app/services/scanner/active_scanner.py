import logging
import re
import shutil
import subprocess
import threading
import time
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

        cmd = [
            "stdbuf", "-oL", "-eL",
            self._nmap_path,
            "--stats-every", "5s",
            "-v",
            "-oX", "-",
        ] + args.split() + [target]
        logger.info("Running nmap command: %s", " ".join(cmd))

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            xml_lines: list[str] = []
            stop_heartbeat = threading.Event()
            started_at = time.time()
            last_stats_at = [started_at]

            def _safe_callback(payload: dict):
                if not callback:
                    return
                try:
                    callback(payload)
                except Exception as cb_exc:
                    logger.debug("Progress callback failed: %s", cb_exc)

            def _parse_stats_line(line: str):
                # nmap periodically emits lines like:
                # Stats: 0:00:30 elapsed; 45 hosts completed (12 up), 209 remaining
                # or: About 34.50% done; ETC: ...
                percent = None
                hosts_completed = None
                hosts_up = None
                hosts_total = None
                elapsed = None

                m_pct = re.search(r"About\s+([0-9]+(?:\.[0-9]+)?)%\s+done", line)
                if m_pct:
                    percent = float(m_pct.group(1))

                m_elapsed = re.search(r"Stats:\s*([0-9:]+)\s+elapsed;", line)
                if m_elapsed:
                    elapsed = m_elapsed.group(1)

                m_hosts = re.search(
                    r"([0-9]+)\s+hosts\s+completed(?:\s*\(([0-9]+)\s+up\))?(?:,\s*([0-9]+)\s+remaining)?",
                    line,
                )
                if m_hosts:
                    hosts_completed = int(m_hosts.group(1))
                    if m_hosts.group(2):
                        hosts_up = int(m_hosts.group(2))
                    if m_hosts.group(3):
                        remaining = int(m_hosts.group(3))
                        hosts_total = hosts_completed + remaining
                        if percent is None and hosts_total > 0:
                            percent = (hosts_completed / hosts_total) * 100.0

                if percent is None and hosts_completed is None:
                    return

                msg_parts = []
                if elapsed:
                    msg_parts.append(f"elapsed {elapsed}")
                if hosts_completed is not None and hosts_total:
                    msg_parts.append(f"hosts {hosts_completed}/{hosts_total}")
                elif hosts_completed is not None:
                    msg_parts.append(f"hosts scanned {hosts_completed}")
                if hosts_up is not None:
                    msg_parts.append(f"up {hosts_up}")
                if percent is not None:
                    msg_parts.append(f"nmap {percent:.1f}%")

                _safe_callback({
                    "event": "nmap_progress",
                    "percent": float(percent) if percent is not None else None,
                    "hosts_completed": hosts_completed,
                    "hosts_total": hosts_total,
                    "hosts_up": hosts_up,
                    "elapsed": elapsed,
                    "message": "Nmap progress: " + ", ".join(msg_parts),
                })
                last_stats_at[0] = time.time()

            def _heartbeat():
                while not stop_heartbeat.is_set():
                    now = time.time()
                    # If nmap isn't emitting stats, provide a periodic progress heartbeat.
                    if now - last_stats_at[0] >= 5:
                        elapsed_s = int(now - started_at)
                        _safe_callback({
                            "event": "nmap_progress",
                            "percent": None,
                            "hosts_completed": None,
                            "hosts_total": None,
                            "hosts_up": None,
                            "elapsed": f"{elapsed_s}s",
                            "message": f"Nmap progress: elapsed {elapsed_s}s, running host/service probes...",
                        })
                        last_stats_at[0] = now
                    stop_heartbeat.wait(1.0)

            def _read_stdout():
                if process.stdout is None:
                    return
                for line in process.stdout:
                    xml_lines.append(line)

            def _read_stderr():
                if process.stderr is None:
                    return
                for line in process.stderr:
                    line = line.strip()
                    if not line:
                        continue
                    logger.info("[nmap] %s", line)
                    _parse_stats_line(line)

            t_out = threading.Thread(target=_read_stdout, daemon=True)
            t_err = threading.Thread(target=_read_stderr, daemon=True)
            t_hb = threading.Thread(target=_heartbeat, daemon=True)
            t_out.start()
            t_err.start()
            t_hb.start()

            process.wait()
            stop_heartbeat.set()
            t_out.join(timeout=2)
            t_err.join(timeout=2)
            t_hb.join(timeout=2)

            if process.returncode != 0:
                logger.error("Nmap failed with code %d", process.returncode)
                return []

            xml_output = "".join(xml_lines)
            root = ET.fromstring(xml_output)

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

        logger.info("Active scan complete: %d devices found", len(devices))
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
