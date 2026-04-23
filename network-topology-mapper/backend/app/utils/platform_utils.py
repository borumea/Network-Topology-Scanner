"""Cross-platform utilities for network interface and privilege detection."""

import ipaddress
import json
import os
import sys
import socket
import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def is_windows() -> bool:
    return sys.platform == "win32"


def is_macos() -> bool:
    return sys.platform == "darwin"


def has_raw_socket_capability() -> bool:
    """Check if the current process can create raw sockets (for nmap/scapy)."""
    if is_windows():
        # Windows: raw sockets require admin, but nmap handles this internally
        # We use --unprivileged mode on Windows regardless
        return False

    # Linux/macOS: check if we're root or have CAP_NET_RAW
    if os.geteuid() == 0:
        return True

    # Check for CAP_NET_RAW capability (Linux only)
    if is_linux():
        try:
            result = subprocess.run(
                ["capsh", "--print"],
                capture_output=True, text=True, timeout=5
            )
            if "cap_net_raw" in result.stdout.lower():
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return False


def get_default_interface() -> str:
    """
    Detect the default network interface for the current platform.

    Returns:
        Interface name (e.g., 'eth0', 'enp3s0', 'en0', 'Ethernet')
    """
    if is_windows():
        return _get_windows_default_interface()
    else:
        return _get_unix_default_interface()


def get_all_up_interfaces() -> list[str]:
    """
    Return the names of every UP, non-loopback network interface.

    Used by the passive scanner so a multi-homed host (e.g. a VM on three
    Docker networks) sniffs every leg, not just the default route.
    Falls back to [get_default_interface()] on platforms we can't fully
    enumerate.
    """
    if is_linux():
        ifaces = _get_linux_up_interfaces()
        if ifaces:
            return ifaces
    # macOS / Windows / fallback: at least return the default route interface
    default = get_default_interface()
    return [default] if default else []


def get_local_addresses() -> list[dict]:
    """Return one dict per UP, non-loopback IPv4 interface.

    Each entry: {"name": str, "ip": str, "mac": str, "cidr": str}.
    Used so the scanner host can be rendered as a single node that bridges
    every subnet it sits on, instead of leaking one device record per leg
    of a multi-homed setup.
    """
    if is_linux():
        raw = _get_linux_addresses()
    elif is_windows():
        raw = _get_windows_addresses()
    elif is_macos():
        raw = _get_macos_addresses()
    else:
        raw = []

    result: list[dict] = []
    for entry in raw:
        cidr = entry.get("cidr")
        if not cidr:
            continue
        try:
            net = ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            continue
        if net.is_loopback or net.is_link_local or net.prefixlen == 32:
            continue
        entry["cidr"] = str(net)
        result.append(entry)
    return result


def get_local_subnets() -> list[str]:
    """Return IPv4 CIDRs for every UP, non-loopback interface (deduped)."""
    seen: set[str] = set()
    out: list[str] = []
    for addr in get_local_addresses():
        cidr = addr.get("cidr")
        if not cidr or cidr in seen:
            continue
        seen.add(cidr)
        out.append(cidr)
    return out


def _get_linux_addresses() -> list[dict]:
    """Parse `ip -j -4 addr show` for IPv4 addresses + MACs per interface."""
    addresses: list[dict] = []
    try:
        result = subprocess.run(
            ["ip", "-j", "-4", "addr", "show"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        for iface in data:
            name = iface.get("ifname", "")
            if name == "lo":
                continue
            if iface.get("operstate") not in ("UP", "UNKNOWN"):
                continue
            mac = iface.get("address", "") or ""
            for addr in iface.get("addr_info", []) or []:
                if addr.get("family") != "inet":
                    continue
                local = addr.get("local")
                prefix = addr.get("prefixlen")
                if not local or prefix is None:
                    continue
                try:
                    cidr = str(ipaddress.ip_interface(f"{local}/{prefix}").network)
                except ValueError:
                    continue
                addresses.append({"name": name, "ip": local, "mac": mac, "cidr": cidr})
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logger.warning("Could not enumerate local addresses via 'ip -j addr': %s", e)
    return addresses


def _get_windows_addresses() -> list[dict]:
    """Use PowerShell to pair Get-NetIPAddress with Get-NetAdapter MACs."""
    addresses: list[dict] = []
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-NetIPAddress -AddressFamily IPv4 | "
             "Where-Object { $_.InterfaceAlias -notlike 'Loopback*' } | "
             "ForEach-Object { "
             "  $ad = Get-NetAdapter -InterfaceIndex $_.InterfaceIndex -ErrorAction SilentlyContinue; "
             "  [PSCustomObject]@{ "
             "    Name=$_.InterfaceAlias; "
             "    IPAddress=$_.IPAddress; "
             "    PrefixLength=$_.PrefixLength; "
             "    MacAddress=$ad.MacAddress "
             "  } "
             "} | ConvertTo-Json -Compress"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            data = [data]
        for entry in data:
            ip = entry.get("IPAddress")
            prefix = entry.get("PrefixLength")
            if not ip or prefix is None:
                continue
            try:
                cidr = str(ipaddress.ip_interface(f"{ip}/{prefix}").network)
            except ValueError:
                continue
            mac = (entry.get("MacAddress") or "").replace("-", ":").lower()
            addresses.append({
                "name": entry.get("Name", ""),
                "ip": ip,
                "mac": mac,
                "cidr": cidr,
            })
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Could not enumerate local addresses via PowerShell: %s", e)
    return addresses


def _get_macos_addresses() -> list[dict]:
    """Parse `ifconfig` to pair IPv4 addresses with MACs per interface."""
    addresses: list[dict] = []
    try:
        result = subprocess.run(
            ["ifconfig"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return []
        current_iface = None
        current_mac = ""
        for raw_line in result.stdout.splitlines():
            if raw_line and not raw_line.startswith("\t") and not raw_line.startswith(" "):
                current_iface = raw_line.split(":", 1)[0] if ":" in raw_line else None
                current_mac = ""
                continue
            line = raw_line.strip()
            if line.startswith("ether "):
                parts = line.split()
                if len(parts) >= 2:
                    current_mac = parts[1]
            elif line.startswith("inet ") and "netmask" in line:
                parts = line.split()
                try:
                    ip = parts[1]
                    nm_idx = parts.index("netmask") + 1
                    netmask_token = parts[nm_idx]
                    if netmask_token.startswith("0x"):
                        prefix = bin(int(netmask_token, 16)).count("1")
                    else:
                        prefix = int(netmask_token)
                    cidr = str(ipaddress.ip_interface(f"{ip}/{prefix}").network)
                except (ValueError, IndexError):
                    continue
                if current_iface and current_iface != "lo0":
                    addresses.append({
                        "name": current_iface,
                        "ip": ip,
                        "mac": current_mac,
                        "cidr": cidr,
                    })
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning("Could not enumerate local addresses via ifconfig: %s", e)
    return addresses


def _get_linux_up_interfaces() -> list[str]:
    """Enumerate UP, non-loopback interfaces from /sys/class/net."""
    interfaces = []
    try:
        for iface in sorted(os.listdir("/sys/class/net")):
            if iface == "lo":
                continue
            operstate_path = f"/sys/class/net/{iface}/operstate"
            try:
                with open(operstate_path) as f:
                    state = f.read().strip()
            except OSError:
                continue
            # "up" means administratively + operationally up.
            # Some virtual interfaces report "unknown" but still carry traffic
            # (e.g. tun/tap, some container veths); include those too.
            if state in ("up", "unknown"):
                interfaces.append(iface)
    except OSError as e:
        logger.warning("Could not enumerate /sys/class/net: %s", e)
    return interfaces


def _get_unix_default_interface() -> str:
    """Get default interface on Linux/macOS by checking the default route."""
    try:
        # Method 1: Parse 'ip route' output (Linux)
        if is_linux():
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout:
                # Output: "default via 192.168.1.1 dev eth0 proto ..."
                parts = result.stdout.split()
                if "dev" in parts:
                    idx = parts.index("dev")
                    if idx + 1 < len(parts):
                        iface = parts[idx + 1]
                        logger.debug("Detected default interface via 'ip route': %s", iface)
                        return iface

        # Method 2: Parse 'route' output (macOS fallback)
        if is_macos():
            result = subprocess.run(
                ["route", "-n", "get", "default"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "interface:" in line.lower():
                        iface = line.split(":")[-1].strip()
                        logger.debug("Detected default interface via 'route': %s", iface)
                        return iface

        # Method 3: Fallback - try common interface names
        for candidate in ["eth0", "enp0s3", "enp3s0", "ens33", "en0", "wlan0", "wlp2s0"]:
            if _interface_exists(candidate):
                logger.debug("Using fallback interface: %s", candidate)
                return candidate

    except Exception as e:
        logger.warning("Failed to detect default interface: %s", e)

    # Ultimate fallback
    logger.warning("Could not detect interface, defaulting to 'eth0'")
    return "eth0"


def _get_windows_default_interface() -> str:
    """Get default interface on Windows."""
    try:
        # Use PowerShell to get the interface with default route
        result = subprocess.run(
            ["powershell", "-Command",
             "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | "
             "Sort-Object -Property RouteMetric | "
             "Select-Object -First 1).InterfaceAlias"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            iface = result.stdout.strip()
            logger.debug("Detected Windows interface: %s", iface)
            return iface
    except Exception as e:
        logger.warning("Failed to detect Windows interface: %s", e)

    # Fallback to common Windows interface names
    return "Ethernet"


def _interface_exists(name: str) -> bool:
    """Check if a network interface exists."""
    try:
        if is_linux():
            return os.path.exists(f"/sys/class/net/{name}")
        elif is_macos():
            result = subprocess.run(
                ["ifconfig", name],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
    except Exception:
        pass
    return False


def get_nmap_privilege_flags() -> str:
    """
    Return nmap flags appropriate for the current privilege level.

    On Windows or without privileges: --unprivileged (TCP connect scans only)
    On Linux/macOS with privileges: empty string (allows SYN scans, faster)
    """
    if is_windows():
        # Always use unprivileged on Windows to avoid assertion crashes
        return "--unprivileged"

    if has_raw_socket_capability():
        logger.info("Running with raw socket capability - using privileged nmap mode")
        return ""

    logger.info("No raw socket capability - using unprivileged nmap mode")
    return "--unprivileged"
