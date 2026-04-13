"""Cross-platform utilities for network interface and privilege detection."""

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
