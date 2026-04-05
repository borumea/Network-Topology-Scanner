"""Tests for subnet_discovery module."""
import ipaddress
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.scanner.subnet_discovery import SubnetDiscovery


class TestResolveTargets:
    """Tests for _resolve_targets logic (via discover_subnets)."""

    def test_single_24_returns_as_is(self):
        sd = SubnetDiscovery()
        result = sd.discover_subnets("192.168.1.0/24")
        assert result == ["192.168.1.0/24"]

    def test_single_25_returns_as_is(self):
        sd = SubnetDiscovery()
        result = sd.discover_subnets("192.168.1.0/25")
        assert result == ["192.168.1.0/25"]

    def test_invalid_range_returns_empty(self):
        sd = SubnetDiscovery()
        result = sd.discover_subnets("not-a-cidr")
        assert result == []


class TestWithinParent:
    def test_subnet_inside_parent(self):
        parent = ipaddress.ip_network("192.168.0.0/16")
        subnet = ipaddress.ip_network("192.168.10.0/24")
        assert SubnetDiscovery._within_parent(subnet, parent) is True

    def test_subnet_outside_parent(self):
        parent = ipaddress.ip_network("192.168.0.0/16")
        subnet = ipaddress.ip_network("10.0.1.0/24")
        assert SubnetDiscovery._within_parent(subnet, parent) is False

    def test_subnet_at_boundary(self):
        parent = ipaddress.ip_network("192.168.0.0/16")
        subnet = ipaddress.ip_network("192.168.0.0/24")
        assert SubnetDiscovery._within_parent(subnet, parent) is True

    def test_subnet_at_end_boundary(self):
        parent = ipaddress.ip_network("192.168.0.0/16")
        subnet = ipaddress.ip_network("192.168.255.0/24")
        assert SubnetDiscovery._within_parent(subnet, parent) is True


class TestTo24:
    def test_24_unchanged(self):
        net = ipaddress.ip_network("192.168.1.0/24")
        result = SubnetDiscovery._to_24(net)
        assert result == ipaddress.ip_network("192.168.1.0/24")

    def test_28_normalized_to_24(self):
        net = ipaddress.ip_network("192.168.1.16/28")
        result = SubnetDiscovery._to_24(net)
        assert result == ipaddress.ip_network("192.168.1.0/24")

    def test_20_returns_base_24(self):
        net = ipaddress.ip_network("192.168.16.0/20")
        result = SubnetDiscovery._to_24(net)
        assert result == ipaddress.ip_network("192.168.16.0/24")

    def test_8_returns_none(self):
        net = ipaddress.ip_network("10.0.0.0/8")
        result = SubnetDiscovery._to_24(net)
        assert result is None


class TestParseWindowsRoutes:
    def test_parse_typical_output(self):
        sd = SubnetDiscovery()
        parent = ipaddress.ip_network("192.168.0.0/16")
        output = """
===========================================================================
Interface List
  6 ...00 15 5d 00 00 01 ...... Ethernet
===========================================================================

IPv4 Route Table
===========================================================================
Active Routes:
Network Destination        Netmask          Gateway       Interface  Metric
          0.0.0.0          0.0.0.0      192.168.1.1    192.168.1.100     25
      192.168.1.0    255.255.255.0         On-link     192.168.1.100    281
     192.168.10.0    255.255.255.0      192.168.1.1    192.168.1.100     26
     192.168.20.0    255.255.255.0      192.168.1.1    192.168.1.100     26
===========================================================================
"""
        subnets = sd._parse_windows_routes(output, parent)
        assert "192.168.1.0/24" in subnets
        assert "192.168.10.0/24" in subnets
        assert "192.168.20.0/24" in subnets

    def test_filters_out_of_range_subnets(self):
        sd = SubnetDiscovery()
        parent = ipaddress.ip_network("192.168.0.0/16")
        output = """
Network Destination        Netmask          Gateway       Interface  Metric
      10.0.0.0    255.255.255.0      192.168.1.1    192.168.1.100     26
"""
        subnets = sd._parse_windows_routes(output, parent)
        assert "10.0.0.0/24" not in subnets


class TestParseLinuxRoutes:
    def test_parse_typical_output(self):
        sd = SubnetDiscovery()
        parent = ipaddress.ip_network("192.168.0.0/16")
        output = """default via 192.168.1.1 dev eth0 proto dhcp metric 100
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100
192.168.10.0/24 via 192.168.1.1 dev eth0
192.168.20.0/24 via 192.168.1.1 dev eth0
"""
        subnets = sd._parse_linux_routes(output, parent)
        assert "192.168.1.0/24" in subnets
        assert "192.168.10.0/24" in subnets
        assert "192.168.20.0/24" in subnets

    def test_skips_default_route(self):
        sd = SubnetDiscovery()
        parent = ipaddress.ip_network("192.168.0.0/16")
        output = "default via 192.168.1.1 dev eth0\n"
        subnets = sd._parse_linux_routes(output, parent)
        assert len(subnets) == 0


class TestNmapSweep:
    def test_no_nmap_returns_empty(self):
        sd = SubnetDiscovery()
        sd._nmap_path = None
        parent = ipaddress.ip_network("192.168.0.0/16")
        subnets, hosts = sd._nmap_sweep("192.168.0.0/16", parent)
        assert subnets == set()
        assert hosts == {}

    @patch("subprocess.run")
    def test_groups_hosts_by_24(self, mock_run):
        sd = SubnetDiscovery()
        sd._nmap_path = "/usr/bin/nmap"
        parent = ipaddress.ip_network("192.168.0.0/16")

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""<?xml version="1.0"?>
<nmaprun>
  <host><status state="up"/><address addr="192.168.10.5" addrtype="ipv4"/></host>
  <host><status state="up"/><address addr="192.168.10.20" addrtype="ipv4"/></host>
  <host><status state="up"/><address addr="192.168.20.1" addrtype="ipv4"/></host>
  <host><status state="up"/><address addr="192.168.20.100" addrtype="ipv4"/></host>
  <host><status state="up"/><address addr="192.168.30.50" addrtype="ipv4"/></host>
  <host><status state="down"/><address addr="192.168.40.1" addrtype="ipv4"/></host>
</nmaprun>""",
            stderr="",
        )

        subnets, hosts = sd._nmap_sweep("192.168.0.0/16", parent)
        assert "192.168.10.0/24" in subnets
        assert "192.168.20.0/24" in subnets
        assert "192.168.30.0/24" in subnets
        assert "192.168.40.0/24" not in subnets  # host was down
        assert len(subnets) == 3
        # Verify host tracking
        assert "192.168.10.5" in hosts["192.168.10.0/24"]
        assert "192.168.10.20" in hosts["192.168.10.0/24"]
        assert "192.168.20.1" in hosts["192.168.20.0/24"]
        assert "192.168.20.100" in hosts["192.168.20.0/24"]

    @patch("subprocess.run")
    def test_timeout_returns_empty(self, mock_run):
        import subprocess
        sd = SubnetDiscovery()
        sd._nmap_path = "/usr/bin/nmap"
        parent = ipaddress.ip_network("192.168.0.0/16")

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="nmap", timeout=300)

        subnets, hosts = sd._nmap_sweep("192.168.0.0/16", parent)
        assert subnets == set()
        assert hosts == {}


class TestCheckArpTable:
    @patch("subprocess.run")
    def test_extracts_subnets_from_arp(self, mock_run):
        sd = SubnetDiscovery()
        parent = ipaddress.ip_network("192.168.0.0/16")

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""
Interface: 192.168.1.100 --- 0x6
  Internet Address      Physical Address      Type
  192.168.1.1           00-15-5d-00-00-01     dynamic
  192.168.10.5          aa-bb-cc-dd-ee-ff     dynamic
  192.168.20.1          11-22-33-44-55-66     dynamic
  10.0.0.1              ff-ee-dd-cc-bb-aa     dynamic
""",
        )

        subnets, hosts = sd._check_arp_table(parent)
        assert "192.168.1.0/24" in subnets
        assert "192.168.10.0/24" in subnets
        assert "192.168.20.0/24" in subnets
        assert "10.0.0.0/24" not in subnets  # outside parent
        assert "192.168.1.1" in hosts["192.168.1.0/24"]


class TestDiscoverSubnetsCallback:
    @patch.object(SubnetDiscovery, "_get_local_ips", return_value={"192.168.1.100"})
    @patch.object(SubnetDiscovery, "_nmap_sweep", return_value=(
        {"192.168.10.0/24", "192.168.20.0/24"},
        {"192.168.10.0/24": {"192.168.10.5", "192.168.10.20"}, "192.168.20.0/24": {"192.168.20.1", "192.168.20.100"}},
    ))
    @patch.object(SubnetDiscovery, "_check_arp_table", return_value=(
        {"192.168.10.0/24"},
        {"192.168.10.0/24": {"192.168.10.5"}},
    ))
    @patch.object(SubnetDiscovery, "_read_routing_table", return_value={"192.168.1.0/24"})
    def test_combines_all_sources_and_deduplicates(self, mock_routes, mock_arp, mock_sweep, mock_ips):
        sd = SubnetDiscovery()
        messages = []
        result = sd.discover_subnets("192.168.0.0/16", callback=lambda m: messages.append(m))

        # Should have 3 unique subnets, sorted
        # 192.168.1.0/24 from routing table (no host data, so included)
        # 192.168.10.0/24 has non-local hosts, included
        # 192.168.20.0/24 has non-local hosts, included
        assert result == ["192.168.1.0/24", "192.168.10.0/24", "192.168.20.0/24"]
        assert len(messages) > 0  # callback was called

    @patch.object(SubnetDiscovery, "_get_local_ips", return_value={"192.168.50.70", "192.168.56.1", "192.168.170.1"})
    @patch.object(SubnetDiscovery, "_nmap_sweep", return_value=(
        {"192.168.50.0/24", "192.168.56.0/24", "192.168.170.0/24"},
        {
            "192.168.50.0/24": {"192.168.50.1", "192.168.50.70", "192.168.50.100"},
            "192.168.56.0/24": {"192.168.56.1"},
            "192.168.170.0/24": {"192.168.170.1"},
        },
    ))
    @patch.object(SubnetDiscovery, "_check_arp_table", return_value=(set(), {}))
    @patch.object(SubnetDiscovery, "_read_routing_table", return_value=set())
    def test_filters_virtual_adapter_subnets(self, mock_routes, mock_arp, mock_sweep, mock_ips):
        sd = SubnetDiscovery()
        result = sd.discover_subnets("192.168.0.0/16")

        # Only 192.168.50.0/24 has non-local hosts (50.1 and 50.100)
        # 192.168.56.0/24 and 192.168.170.0/24 only have local IPs
        assert result == ["192.168.50.0/24"]
        assert "192.168.56.0/24" not in result
        assert "192.168.170.0/24" not in result
