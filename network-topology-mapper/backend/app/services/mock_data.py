"""
Mock data generator for a realistic small-office network topology.

Generates ~35 devices: a gateway router, firewall, core switch, a few
access switches, servers, workstations, APs, printers, and IoT devices.
Sized to be immediately readable on a topology graph without overwhelming.
"""

import uuid
import random
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_id_cache: dict[str, str] = {}


def _id(name: str) -> str:
    if name not in _id_cache:
        _id_cache[name] = str(uuid.uuid5(uuid.NAMESPACE_DNS, name))
    return _id_cache[name]


_OUI = {
    "Cisco": "00:1A:2B",
    "HP": "3C:D9:2B",
    "Dell": "F8:BC:12",
    "Aruba": "00:0B:86",
    "Ubiquiti": "FC:EC:DA",
    "Intel": "A4:BB:6D",
    "Lenovo": "98:FA:9B",
    "Brother": "00:80:77",
    "Hikvision": "C0:56:E3",
    "Synology": "00:11:32",
}


def _mac(vendor: str, seq: int) -> str:
    oui = _OUI.get(vendor, "00:11:22")
    return f"{oui}:{(seq >> 16) & 0xFF:02X}:{(seq >> 8) & 0xFF:02X}:{seq & 0xFF:02X}"


_NOW = datetime.utcnow()


def _ts(days_ago: int = 0) -> str:
    return (_NOW - timedelta(days=days_ago)).isoformat()


# ---------------------------------------------------------------------------
# VLAN definitions
# ---------------------------------------------------------------------------
VLANS = {
    1:  {"name": "Management", "subnet": "10.0.1.0/24"},
    10: {"name": "Staff", "subnet": "10.0.10.0/24"},
    20: {"name": "Servers", "subnet": "10.0.20.0/24"},
    30: {"name": "Guest", "subnet": "10.0.30.0/24"},
    40: {"name": "IoT/Security", "subnet": "10.0.40.0/24"},
}


# ===================================================================
# Devices
# ===================================================================

def _build_devices() -> list[dict]:
    devices = []

    def dev(hostname, ip, dtype, vendor, model, os, ports, services,
            vlans, subnet, location, risk=10.0, crit="low",
            gateway=False, status="online", mac_seq=0, tier=5):
        devices.append({
            "id": _id(hostname),
            "ip": ip,
            "mac": _mac(vendor, mac_seq),
            "hostname": hostname,
            "device_type": dtype,
            "vendor": vendor,
            "model": model,
            "os": os,
            "open_ports": ports,
            "services": services,
            "first_seen": _ts(60),
            "last_seen": _ts(0) if status != "offline" else _ts(3),
            "discovery_method": "active_scan",
            "vlan_ids": vlans,
            "subnet": subnet,
            "location": location,
            "risk_score": risk,
            "criticality": crit,
            "is_gateway": gateway,
            "status": status,
            "tier": tier,
        })

    # --- Gateway router (ISP edge) ---
    dev("gw-router", "10.0.1.1", "router", "Cisco", "ISR 4331",
        "IOS-XE 17.6", [22, 161, 443], ["SSH", "SNMP", "HTTPS"],
        [1, 10, 20, 30, 40], "10.0.1.0/24", "Server Room Rack A",
        risk=30.0, crit="high", gateway=True, mac_seq=0xF00001, tier=0)

    # --- Firewall ---
    dev("fw-01", "10.0.1.2", "firewall", "Cisco", "ASA 5506-X",
        "ASA 9.16", [443, 22], ["HTTPS", "SSH"],
        [1, 10, 20, 30, 40], "10.0.1.0/24", "Server Room Rack A",
        risk=25.0, crit="high", mac_seq=0xF00002, tier=1)

    # --- Core switch ---
    dev("core-sw-01", "10.0.1.3", "switch", "Cisco", "Catalyst 2960-X",
        "IOS 15.2", [22, 161, 443], ["SSH", "SNMP", "HTTPS"],
        [1, 10, 20, 30, 40], "10.0.1.0/24", "Server Room Rack A",
        risk=35.0, crit="high", mac_seq=0xC00001, tier=2)

    # --- Access switches (one per zone) ---
    dev("access-sw-01", "10.0.1.11", "switch", "HP", "Aruba 2530-24G",
        "ArubaOS-Switch 16.10", [22, 161], ["SSH", "SNMP"],
        [10, 1], "10.0.1.0/24", "Office Area - East Wall",
        risk=15.0, crit="medium", mac_seq=0xA00001, tier=4)

    dev("access-sw-02", "10.0.1.12", "switch", "HP", "Aruba 2530-24G",
        "ArubaOS-Switch 16.10", [22, 161], ["SSH", "SNMP"],
        [10, 30, 1], "10.0.1.0/24", "Office Area - West Wall",
        risk=15.0, crit="medium", mac_seq=0xA00002, tier=4)

    # SPOF: access-sw-03 is the only switch for the server VLAN
    dev("access-sw-03", "10.0.1.13", "switch", "HP", "Aruba 2530-8G",
        "ArubaOS-Switch 16.10", [22, 161], ["SSH", "SNMP"],
        [20, 1], "10.0.1.0/24", "Server Room Rack B",
        risk=50.0, crit="high", mac_seq=0xA00003, tier=3)

    # --- Wireless AP ---
    dev("ap-01", "10.0.1.20", "ap", "Ubiquiti", "UniFi U6 Pro",
        "UniFi 7.1", [22, 443], ["SSH", "HTTPS"],
        [10, 30], "10.0.1.0/24", "Office Ceiling - Center",
        risk=10.0, crit="medium", mac_seq=0xAA0001, tier=5)

    # --- Servers ---
    dev("file-srv", "10.0.20.10", "server", "Synology", "DS920+",
        "DSM 7.2", [445, 5000, 22], ["SMB", "DSM Web", "SSH"],
        [20], "10.0.20.0/24", "Server Room Rack B",
        risk=40.0, crit="high", mac_seq=0x500001, tier=4)

    dev("web-srv", "10.0.20.11", "server", "Dell", "PowerEdge T340",
        "Ubuntu 22.04 LTS", [80, 443, 22], ["HTTP", "HTTPS", "SSH"],
        [20], "10.0.20.0/24", "Server Room Rack B",
        risk=45.0, crit="high", mac_seq=0x500002, tier=4)

    dev("db-srv", "10.0.20.12", "server", "Dell", "PowerEdge T340",
        "Ubuntu 22.04 LTS", [5432, 22], ["PostgreSQL", "SSH"],
        [20], "10.0.20.0/24", "Server Room Rack B",
        risk=55.0, crit="high", mac_seq=0x500003, tier=4)

    # SPOF: single DNS/DHCP server
    dev("dns-dhcp-srv", "10.0.20.13", "server", "Dell", "OptiPlex 7000",
        "Windows Server 2022", [53, 67, 68, 445, 3389], ["DNS", "DHCP", "SMB", "RDP"],
        [20], "10.0.20.0/24", "Server Room Rack B",
        risk=70.0, crit="high", mac_seq=0x500004, tier=4)

    dev("backup-srv", "10.0.20.14", "server", "Synology", "DS220+",
        "DSM 7.2", [445, 5000, 22], ["SMB", "DSM Web", "SSH"],
        [20], "10.0.20.0/24", "Server Room Rack B",
        risk=30.0, crit="medium", mac_seq=0x500005, tier=4)

    # --- Workstations ---
    ws_defs = [
        ("ws-ryan",   "10.0.10.101", "Lenovo", "ThinkPad T14s",    "Windows 11 Pro", "Desk 1",  "online"),
        ("ws-sarah",  "10.0.10.102", "Dell",   "Latitude 5540",    "Windows 11 Pro", "Desk 2",  "online"),
        ("ws-mike",   "10.0.10.103", "Lenovo", "ThinkPad X1 Carbon","Windows 11 Pro","Desk 3",  "online"),
        ("ws-emma",   "10.0.10.104", "Dell",   "Precision 5680",   "Ubuntu 22.04",   "Desk 4",  "online"),
        ("ws-alex",   "10.0.10.105", "HP",     "EliteBook 860 G9", "Windows 11 Pro", "Desk 5",  "online"),
        ("ws-jess",   "10.0.10.106", "Lenovo", "ThinkPad T14s",    "Windows 11 Pro", "Desk 6",  "online"),
        ("ws-chris",  "10.0.10.107", "Dell",   "Latitude 5540",    "Windows 11 Pro", "Desk 7",  "degraded"),
        ("ws-taylor", "10.0.10.108", "Lenovo", "ThinkPad X1 Carbon","Windows 11 Pro","Desk 8",  "online"),
        ("ws-jordan", "10.0.10.109", "Dell",   "Latitude 5540",    "Windows 11 Pro", "Desk 9",  "offline"),
        ("ws-pat",    "10.0.10.110", "HP",     "EliteBook 860 G9", "Windows 11 Pro", "Desk 10", "online"),
        ("ws-sam",    "10.0.10.111", "Lenovo", "ThinkPad T14s",    "Windows 11 Pro", "Desk 11", "online"),
        ("ws-casey",  "10.0.10.112", "Dell",   "Precision 5680",   "Ubuntu 22.04",   "Desk 12", "online"),
    ]
    for i, (name, ip, vendor, model, os_name, loc, status) in enumerate(ws_defs):
        ports = [22] if "Ubuntu" in os_name else [445, 3389]
        svcs = ["SSH"] if "Ubuntu" in os_name else ["SMB", "RDP"]
        risk = 5.0 if status == "online" else (15.0 if status == "degraded" else 0.0)
        dev(name, ip, "workstation", vendor, model, os_name, ports, svcs,
            [10], "10.0.10.0/24", loc, risk=risk, status=status, mac_seq=0x100001 + i, tier=5)

    # --- Printers ---
    dev("printer-office", "10.0.10.200", "printer", "Brother", "MFC-L8900CDW",
        "Embedded", [9100, 631, 80], ["RAW Print", "IPP", "HTTP"],
        [10], "10.0.10.0/24", "Office Print Area",
        risk=15.0, mac_seq=0xBB0001, tier=5)

    dev("printer-exec", "10.0.10.201", "printer", "HP", "LaserJet Pro M404n",
        "Embedded", [9100, 631, 443], ["RAW Print", "IPP", "HTTPS"],
        [10], "10.0.10.0/24", "Conference Room",
        risk=15.0, mac_seq=0xBB0002, tier=5)

    # --- IoT ---
    dev("camera-entrance", "10.0.40.10", "iot", "Hikvision", "DS-2CD2143G2-I",
        "Embedded Firmware", [80, 443, 554], ["HTTP", "HTTPS", "RTSP"],
        [40], "10.0.40.0/24", "Main Entrance",
        risk=25.0, mac_seq=0xEE0001, tier=5)

    dev("camera-parking", "10.0.40.11", "iot", "Hikvision", "DS-2CD2143G2-I",
        "Embedded Firmware", [80, 443, 554], ["HTTP", "HTTPS", "RTSP"],
        [40], "10.0.40.0/24", "Parking Lot",
        risk=25.0, mac_seq=0xEE0002, tier=5)

    dev("smart-thermostat", "10.0.40.20", "iot", "Honeywell", "T9 Smart",
        "Embedded Firmware", [80, 443], ["HTTP", "HTTPS"],
        [40], "10.0.40.0/24", "Office - Main Hall",
        risk=10.0, mac_seq=0xEE0003, tier=5)

    return devices


# ===================================================================
# Connections
# ===================================================================

def _conn(src, tgt, ctype, bw, latency, vlan=None, redundant=False,
          protocol="trunk", status="active", port=""):
    return {
        "id": _id(f"conn-{src}-{tgt}"),
        "source_id": _id(src),
        "target_id": _id(tgt),
        "connection_type": ctype,
        "bandwidth": bw,
        "switch_port": port,
        "vlan": vlan,
        "latency_ms": latency,
        "packet_loss_pct": 0.0,
        "is_redundant": redundant,
        "protocol": protocol,
        "status": status,
        "first_seen": _ts(60),
        "last_seen": _ts(0),
    }


def _build_connections() -> list[dict]:
    conns = []

    # --- WAN uplink: router <-> firewall ---
    conns.append(_conn("gw-router", "fw-01", "ethernet", "1Gbps", 0.5, protocol="routed"))

    # --- Firewall <-> Core switch ---
    conns.append(_conn("fw-01", "core-sw-01", "ethernet", "1Gbps", 0.3, protocol="trunk"))

    # --- Core switch <-> Access switches ---
    conns.append(_conn("core-sw-01", "access-sw-01", "ethernet", "1Gbps", 0.4, protocol="trunk", port="Gi0/1"))
    conns.append(_conn("core-sw-01", "access-sw-02", "ethernet", "1Gbps", 0.4, protocol="trunk", port="Gi0/2"))
    conns.append(_conn("core-sw-01", "access-sw-03", "ethernet", "1Gbps", 0.4, protocol="trunk", port="Gi0/3"))

    # --- Core switch <-> AP (trunk for multiple VLANs) ---
    conns.append(_conn("core-sw-01", "ap-01", "ethernet", "1Gbps", 0.6, protocol="trunk", port="Gi0/4"))

    # --- Access-sw-03 <-> Servers (all servers through the one server switch - SPOF) ---
    for srv in ["file-srv", "web-srv", "db-srv", "dns-dhcp-srv", "backup-srv"]:
        conns.append(_conn("access-sw-03", srv, "ethernet", "1Gbps", 0.3, vlan=20, protocol="access"))

    # --- Access-sw-01 <-> Workstations (east side desks 1-6) ---
    for ws in ["ws-ryan", "ws-sarah", "ws-mike", "ws-emma", "ws-alex", "ws-jess"]:
        conns.append(_conn("access-sw-01", ws, "ethernet", "1Gbps", 0.5, vlan=10, protocol="access"))

    # --- Access-sw-02 <-> Workstations (west side desks 7-12) ---
    for ws in ["ws-chris", "ws-taylor", "ws-jordan", "ws-pat", "ws-sam", "ws-casey"]:
        conns.append(_conn("access-sw-02", ws, "ethernet", "1Gbps", 0.5, vlan=10, protocol="access"))

    # --- Access-sw-01 <-> Printers ---
    conns.append(_conn("access-sw-01", "printer-office", "ethernet", "100Mbps", 0.8, vlan=10, protocol="access"))
    conns.append(_conn("access-sw-02", "printer-exec", "ethernet", "100Mbps", 0.8, vlan=10, protocol="access"))

    # --- Core switch <-> IoT devices (on dedicated VLAN) ---
    conns.append(_conn("core-sw-01", "camera-entrance", "ethernet", "100Mbps", 1.0, vlan=40, protocol="access", port="Gi0/20"))
    conns.append(_conn("core-sw-01", "camera-parking", "ethernet", "100Mbps", 1.0, vlan=40, protocol="access", port="Gi0/21"))
    conns.append(_conn("core-sw-01", "smart-thermostat", "ethernet", "100Mbps", 1.2, vlan=40, protocol="access", port="Gi0/22"))

    # --- Service dependencies (web -> db, web -> dns, etc.) ---
    conns.append(_conn("web-srv", "db-srv", "ethernet", "1Gbps", 0.2, vlan=20, protocol="tcp"))
    conns.append(_conn("web-srv", "file-srv", "ethernet", "1Gbps", 0.3, vlan=20, protocol="tcp"))

    return conns


# ===================================================================
# Dependencies
# ===================================================================

def _dep(src, tgt, dep_type, port, crit="medium"):
    return {
        "id": _id(f"dep-{src}-{tgt}-{dep_type}"),
        "source_id": _id(src),
        "target_id": _id(tgt),
        "dependency_type": dep_type,
        "service_port": port,
        "criticality": crit,
        "discovered_via": "traffic_analysis",
    }


def _build_dependencies() -> list[dict]:
    deps = []

    # DNS dependency (SPOF: single DNS server)
    for c in ["web-srv", "file-srv", "db-srv", "backup-srv",
              "ws-ryan", "ws-sarah", "ws-mike", "ws-emma",
              "ws-alex", "ws-jess", "printer-office"]:
        deps.append(_dep(c, "dns-dhcp-srv", "dns", 53, "high"))

    # DHCP dependency
    for c in ["ws-ryan", "ws-sarah", "ws-mike", "ws-emma", "ws-alex",
              "ws-jess", "ws-chris", "ws-taylor", "ws-jordan", "ws-pat",
              "ws-sam", "ws-casey", "printer-office", "printer-exec"]:
        deps.append(_dep(c, "dns-dhcp-srv", "dhcp", 67, "high"))

    # Database dependency
    deps.append(_dep("web-srv", "db-srv", "database", 5432, "high"))

    # File share dependency
    for c in ["ws-ryan", "ws-sarah", "ws-mike", "ws-emma"]:
        deps.append(_dep(c, "file-srv", "storage", 445, "medium"))

    # Backup dependency
    deps.append(_dep("backup-srv", "file-srv", "storage", 445, "medium"))
    deps.append(_dep("backup-srv", "db-srv", "database", 5432, "medium"))

    return deps


# ===================================================================
# Alerts
# ===================================================================

def generate_mock_alerts() -> list[dict]:
    if not _id_cache:
        generate_mock_topology()

    return [
        {
            "id": str(uuid.uuid4()),
            "alert_type": "spof",
            "severity": "critical",
            "title": "Single point of failure: DNS/DHCP Server",
            "description": "dns-dhcp-srv is the only DNS and DHCP server. Loss of this device will cause network-wide outage.",
            "device_id": _id("dns-dhcp-srv"),
            "details": {"affected_devices": 14, "recommendation": "Deploy secondary DNS/DHCP"},
            "created_at": _ts(2),
            "acknowledged_at": None,
            "resolved_at": None,
            "status": "open",
        },
        {
            "id": str(uuid.uuid4()),
            "alert_type": "spof",
            "severity": "high",
            "title": "Server switch has no redundancy",
            "description": "access-sw-03 is the only switch serving all 5 servers. A switch failure takes down all services.",
            "device_id": _id("access-sw-03"),
            "details": {"affected_devices": 5, "recommendation": "Add redundant uplink or second server switch"},
            "created_at": _ts(1),
            "acknowledged_at": None,
            "resolved_at": None,
            "status": "open",
        },
        {
            "id": str(uuid.uuid4()),
            "alert_type": "device_offline",
            "severity": "medium",
            "title": "Workstation ws-jordan offline",
            "description": "ws-jordan has been unreachable for 3 days. May be powered off or disconnected.",
            "device_id": _id("ws-jordan"),
            "details": {"last_ip": "10.0.10.109", "days_offline": 3},
            "created_at": _ts(3),
            "acknowledged_at": None,
            "resolved_at": None,
            "status": "open",
        },
        {
            "id": str(uuid.uuid4()),
            "alert_type": "anomaly",
            "severity": "high",
            "title": "Elevated risk score on db-srv",
            "description": "Database server risk score is 55.0 due to exposed PostgreSQL port and no redundancy.",
            "device_id": _id("db-srv"),
            "details": {"risk_score": 55.0, "open_ports": [5432, 22]},
            "created_at": _ts(0),
            "acknowledged_at": None,
            "resolved_at": None,
            "status": "open",
        },
        {
            "id": str(uuid.uuid4()),
            "alert_type": "anomaly",
            "severity": "medium",
            "title": "ws-chris connection degraded",
            "description": "ws-chris is experiencing intermittent connectivity on access-sw-02. Possible cable issue.",
            "device_id": _id("ws-chris"),
            "details": {"packet_loss_pct": 4.2, "switch_port": "Gi0/7"},
            "created_at": _ts(1),
            "acknowledged_at": None,
            "resolved_at": None,
            "status": "open",
        },
        {
            "id": str(uuid.uuid4()),
            "alert_type": "new_device",
            "severity": "low",
            "title": "Smart thermostat added to network",
            "description": "New IoT device detected on VLAN 40. Identified as Honeywell T9 Smart thermostat.",
            "device_id": _id("smart-thermostat"),
            "details": {"vendor": "Honeywell", "vlan": 40},
            "created_at": _ts(5),
            "acknowledged_at": _ts(4),
            "resolved_at": _ts(4),
            "status": "resolved",
        },
        {
            "id": str(uuid.uuid4()),
            "alert_type": "topology_change",
            "severity": "info",
            "title": "Scan completed successfully",
            "description": "Network scan found 35 devices. No changes from previous scan.",
            "device_id": None,
            "details": {"devices_total": 35, "new": 0, "removed": 0},
            "created_at": _ts(0),
            "acknowledged_at": None,
            "resolved_at": None,
            "status": "open",
        },
    ]


# ===================================================================
# Scans
# ===================================================================

def generate_mock_scans() -> list[dict]:
    return [
        {
            "id": str(uuid.uuid4()),
            "scan_type": "full",
            "status": "completed",
            "started_at": _ts(0),
            "completed_at": _ts(0),
            "target_range": "10.0.0.0/16",
            "devices_found": 35,
            "new_devices": 0,
            "config": {"intensity": "normal"},
        },
        {
            "id": str(uuid.uuid4()),
            "scan_type": "active",
            "status": "completed",
            "started_at": _ts(1),
            "completed_at": _ts(1),
            "target_range": "10.0.10.0/24",
            "devices_found": 14,
            "new_devices": 1,
            "config": {"intensity": "normal"},
        },
        {
            "id": str(uuid.uuid4()),
            "scan_type": "full",
            "status": "completed",
            "started_at": _ts(7),
            "completed_at": _ts(7),
            "target_range": "10.0.0.0/16",
            "devices_found": 34,
            "new_devices": 0,
            "config": {"intensity": "normal"},
        },
    ]


# ===================================================================
# Public API
# ===================================================================

def generate_mock_topology() -> dict:
    _id_cache.clear()

    devices = _build_devices()
    connections = _build_connections()
    dependencies = _build_dependencies()

    return {
        "devices": devices,
        "connections": connections,
        "dependencies": dependencies,
    }
