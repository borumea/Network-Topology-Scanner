import ipaddress
import logging
import platform
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from typing import Optional

logger = logging.getLogger(__name__)


class SubnetDiscovery:
    """Discovers reachable subnets via routing table inspection and fast nmap sweep."""

    def __init__(self):
        self._nmap_path: Optional[str] = shutil.which("nmap")

    def discover_subnets(self, parent_range: str, callback=None) -> list[str]:
        """Discover active /24 subnets within a parent range.

        Strategy:
        1. Read the OS routing table for known subnets within parent_range.
        2. Run a fast nmap ping sweep across parent_range.
        3. Group responding hosts by /24 to identify active subnets.
        4. Return deduplicated, sorted list of /24 CIDR strings.
        """
        try:
            parent_net = ipaddress.ip_network(parent_range, strict=False)
        except ValueError:
            logger.error("Invalid parent range: %s", parent_range)
            return []

        # If the parent is already a /24 or smaller, just return it directly
        if parent_net.prefixlen >= 24:
            return [str(parent_net)]

        discovered: set[str] = set()

        # Step 1: routing table
        if callback:
            callback("Checking routing table for known subnets...")
        route_subnets = self._read_routing_table(parent_net)
        discovered.update(route_subnets)
        logger.info("Routing table: found %d subnets within %s", len(route_subnets), parent_range)
        if callback and route_subnets:
            callback(f"Routing table: {len(route_subnets)} known subnets")

        # Step 2: fast nmap sweep
        if callback:
            callback(f"Running fast discovery sweep on {parent_range}...")
        sweep_subnets = self._nmap_sweep(parent_range, parent_net)
        discovered.update(sweep_subnets)
        logger.info("Nmap sweep: found %d active subnets within %s", len(sweep_subnets), parent_range)
        if callback and sweep_subnets:
            callback(f"Network sweep: {len(sweep_subnets)} active subnets detected")

        # Step 3: also check ARP table for additional subnets
        arp_subnets = self._check_arp_table(parent_net)
        discovered.update(arp_subnets)
        if arp_subnets:
            logger.info("ARP table: found %d additional subnets", len(arp_subnets))
            if callback:
                callback(f"ARP table: {len(arp_subnets)} additional subnets")

        # Sort subnets by network address
        sorted_subnets = sorted(discovered, key=lambda s: ipaddress.ip_network(s).network_address)
        logger.info("Total discovered subnets: %d — %s", len(sorted_subnets), sorted_subnets)

        if callback:
            callback(f"Subnet discovery complete: {len(sorted_subnets)} subnets found")

        return sorted_subnets

    def _read_routing_table(self, parent_net: ipaddress.IPv4Network) -> set[str]:
        """Parse OS routing table for subnets that fall within parent_net."""
        subnets: set[str] = set()
        system = platform.system().lower()

        try:
            if system == "windows":
                result = subprocess.run(
                    ["route", "print", "-4"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    subnets.update(self._parse_windows_routes(result.stdout, parent_net))

            elif system == "linux":
                result = subprocess.run(
                    ["ip", "route", "show"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    subnets.update(self._parse_linux_routes(result.stdout, parent_net))

            elif system == "darwin":
                result = subprocess.run(
                    ["netstat", "-rn", "-f", "inet"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    subnets.update(self._parse_macos_routes(result.stdout, parent_net))

        except Exception as e:
            logger.warning("Failed to read routing table: %s", e)

        return subnets

    def _parse_windows_routes(self, output: str, parent_net: ipaddress.IPv4Network) -> set[str]:
        """Parse `route print -4` output on Windows."""
        subnets: set[str] = set()
        # Windows route print format:
        # Network Destination        Netmask          Gateway       Interface  Metric
        # 192.168.10.0       255.255.255.0      On-link      192.168.10.5     25
        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                dest = ipaddress.ip_address(parts[0])
                mask = ipaddress.ip_address(parts[1])
            except ValueError:
                continue

            # Convert dest + mask to a network
            try:
                prefix_len = ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
                network = ipaddress.ip_network(f"{dest}/{prefix_len}", strict=False)
            except ValueError:
                continue

            if network.prefixlen == 0 or network.prefixlen > 30:
                continue

            # Normalize to /24 if it falls within parent
            subnet_24 = self._to_24(network)
            if subnet_24 and self._within_parent(subnet_24, parent_net):
                subnets.add(str(subnet_24))

        return subnets

    def _parse_linux_routes(self, output: str, parent_net: ipaddress.IPv4Network) -> set[str]:
        """Parse `ip route show` output on Linux."""
        subnets: set[str] = set()
        for line in output.splitlines():
            parts = line.split()
            if not parts or parts[0] == "default":
                continue
            try:
                network = ipaddress.ip_network(parts[0], strict=False)
            except ValueError:
                continue

            if network.prefixlen == 0 or network.prefixlen > 30:
                continue

            subnet_24 = self._to_24(network)
            if subnet_24 and self._within_parent(subnet_24, parent_net):
                subnets.add(str(subnet_24))

        return subnets

    def _parse_macos_routes(self, output: str, parent_net: ipaddress.IPv4Network) -> set[str]:
        """Parse `netstat -rn` output on macOS."""
        subnets: set[str] = set()
        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            dest = parts[0]
            # macOS uses both CIDR notation and IP/mask pairs
            try:
                if "/" in dest:
                    network = ipaddress.ip_network(dest, strict=False)
                else:
                    continue
            except ValueError:
                continue

            if network.prefixlen == 0 or network.prefixlen > 30:
                continue

            subnet_24 = self._to_24(network)
            if subnet_24 and self._within_parent(subnet_24, parent_net):
                subnets.add(str(subnet_24))

        return subnets

    def _nmap_sweep(self, parent_range: str, parent_net: ipaddress.IPv4Network) -> set[str]:
        """Fast nmap ping sweep to find live hosts, then group by /24."""
        if not self._nmap_path:
            logger.warning("nmap not available for subnet discovery sweep")
            return set()

        # Use fast ping scan with high rate to quickly find live hosts
        cmd = [
            self._nmap_path, "-sn", "-T4",
            "--min-rate", "1000",
            "--max-retries", "1",
            "--host-timeout", "2s",
            "-oX", "-",
            parent_range,
        ]
        logger.info("Subnet discovery sweep: %s", " ".join(cmd))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            logger.error("Subnet discovery sweep timed out after 300s")
            return set()
        except Exception as e:
            logger.error("Subnet discovery sweep failed: %s", e)
            return set()

        if result.returncode != 0:
            logger.error("Subnet discovery sweep failed (code %d): %s", result.returncode, result.stderr)
            return set()

        if not result.stdout:
            return set()

        try:
            root = ET.fromstring(result.stdout)
        except ET.ParseError as e:
            logger.error("Failed to parse sweep XML: %s", e)
            return set()

        # Extract live host IPs and group by /24
        subnets: set[str] = set()
        for host_el in root.findall("host"):
            status_el = host_el.find("status")
            if status_el is None or status_el.get("state") != "up":
                continue

            for addr_el in host_el.findall("address"):
                if addr_el.get("addrtype") == "ipv4":
                    ip_str = addr_el.get("addr", "")
                    try:
                        ip = ipaddress.ip_address(ip_str)
                        subnet_24 = ipaddress.ip_network(f"{ip_str}/24", strict=False)
                        if self._within_parent(subnet_24, parent_net):
                            subnets.add(str(subnet_24))
                    except ValueError:
                        continue

        logger.info("Sweep found live hosts in %d subnets", len(subnets))
        return subnets

    def _check_arp_table(self, parent_net: ipaddress.IPv4Network) -> set[str]:
        """Check OS ARP table for additional subnets with known hosts."""
        subnets: set[str] = set()
        try:
            result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return subnets
        except Exception:
            return subnets

        for line in result.stdout.splitlines():
            match = re.match(r".*?(\d+\.\d+\.\d+\.\d+)", line)
            if not match:
                continue
            try:
                ip = ipaddress.ip_address(match.group(1))
                subnet_24 = ipaddress.ip_network(f"{ip}/24", strict=False)
                if self._within_parent(subnet_24, parent_net):
                    subnets.add(str(subnet_24))
            except ValueError:
                continue

        return subnets

    @staticmethod
    def _to_24(network: ipaddress.IPv4Network) -> Optional[ipaddress.IPv4Network]:
        """Normalize a network to its /24 boundary. Returns None for networks larger than /16."""
        if network.prefixlen >= 24:
            return ipaddress.ip_network(f"{network.network_address}/24", strict=False)
        elif network.prefixlen >= 16:
            # For ranges like /20, return the /24 of the network address
            # The sweep will find the rest
            return ipaddress.ip_network(f"{network.network_address}/24", strict=False)
        return None

    @staticmethod
    def _within_parent(subnet: ipaddress.IPv4Network, parent: ipaddress.IPv4Network) -> bool:
        """Check if a /24 subnet falls within the parent range."""
        return subnet.network_address >= parent.network_address and \
               subnet.broadcast_address <= parent.broadcast_address


subnet_discovery = SubnetDiscovery()
