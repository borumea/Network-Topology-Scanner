#!/usr/bin/env python3
"""
Add sample devices to Network Topology Mapper via API
Run: python add_sample_devices.py
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api"

def add_device(device_data):
    """Add a device via API"""
    response = requests.post(f"{API_BASE}/devices", json=device_data)
    if response.status_code in [200, 201]:
        print(f"✅ Added: {device_data['hostname']} ({device_data['ip']})")
        return response.json()
    else:
        print(f"❌ Failed to add {device_data['hostname']}: {response.text}")
        return None

def add_connection(connection_data):
    """Add a connection between devices"""
    response = requests.post(f"{API_BASE}/connections", json=connection_data)
    if response.status_code in [200, 201]:
        print(f"✅ Connected: {connection_data['source']} ↔ {connection_data['target']}")
        return response.json()
    else:
        print(f"❌ Failed to add connection: {response.text}")
        return None

def main():
    print("=" * 60)
    print("Adding Sample Network Topology")
    print("=" * 60)
    print()

    # Define sample devices
    devices = [
        {
            "ip": "192.168.1.1",
            "mac": "00:11:22:33:44:01",
            "hostname": "core-router-01",
            "device_type": "router",
            "vendor": "Cisco",
            "model": "ISR 4451",
            "os": "IOS-XE 17.6",
            "status": "online",
            "criticality": "critical",
            "vlan_ids": [10, 20, 30],
            "open_ports": [22, 80, 443, 161]
        },
        {
            "ip": "192.168.1.2",
            "mac": "00:11:22:33:44:02",
            "hostname": "firewall-01",
            "device_type": "firewall",
            "vendor": "Palo Alto",
            "model": "PA-5220",
            "os": "PAN-OS 11.0",
            "status": "online",
            "criticality": "critical",
            "open_ports": [22, 443]
        },
        {
            "ip": "192.168.1.10",
            "mac": "00:11:22:33:44:10",
            "hostname": "core-switch-01",
            "device_type": "switch",
            "vendor": "Cisco",
            "model": "Catalyst 9300",
            "os": "IOS-XE 17.6",
            "status": "online",
            "criticality": "high",
            "vlan_ids": [10, 20, 30],
            "open_ports": [22, 80, 443, 161]
        },
        {
            "ip": "192.168.1.11",
            "mac": "00:11:22:33:44:11",
            "hostname": "distribution-switch-01",
            "device_type": "switch",
            "vendor": "Cisco",
            "model": "Catalyst 9500",
            "os": "IOS-XE 17.6",
            "status": "online",
            "criticality": "high",
            "vlan_ids": [10, 20],
            "open_ports": [22, 161]
        },
        {
            "ip": "192.168.1.20",
            "mac": "00:11:22:33:44:20",
            "hostname": "web-server-01",
            "device_type": "server",
            "vendor": "Dell",
            "model": "PowerEdge R740",
            "os": "Ubuntu 22.04",
            "status": "online",
            "criticality": "high",
            "open_ports": [22, 80, 443],
            "services": ["nginx", "ssh"]
        },
        {
            "ip": "192.168.1.21",
            "mac": "00:11:22:33:44:21",
            "hostname": "database-server-01",
            "device_type": "server",
            "vendor": "Dell",
            "model": "PowerEdge R740",
            "os": "Ubuntu 22.04",
            "status": "online",
            "criticality": "critical",
            "open_ports": [22, 5432],
            "services": ["postgresql", "ssh"]
        },
        {
            "ip": "192.168.1.100",
            "mac": "00:11:22:33:44:A0",
            "hostname": "workstation-01",
            "device_type": "workstation",
            "vendor": "HP",
            "model": "EliteDesk 800",
            "os": "Windows 11",
            "status": "online",
            "criticality": "low",
            "open_ports": [135, 139, 445]
        },
        {
            "ip": "192.168.1.200",
            "mac": "00:11:22:33:44:C8",
            "hostname": "access-point-01",
            "device_type": "ap",
            "vendor": "Ubiquiti",
            "model": "UniFi AP AC Pro",
            "os": "UniFi 6.0",
            "status": "online",
            "criticality": "medium",
            "open_ports": [22, 80, 443]
        }
    ]

    # Add devices
    print("Adding devices...")
    added_devices = {}
    for device in devices:
        result = add_device(device)
        if result:
            added_devices[device['hostname']] = result.get('id')

    print(f"\n✅ Added {len(added_devices)} devices")
    print()

    # Define connections
    if len(added_devices) > 0:
        print("Adding connections...")
        connections = [
            {
                "source_ip": "192.168.1.1",
                "target_ip": "192.168.1.2",
                "connection_type": "fiber",
                "bandwidth": "10Gbps",
                "status": "active"
            },
            {
                "source_ip": "192.168.1.2",
                "target_ip": "192.168.1.10",
                "connection_type": "fiber",
                "bandwidth": "10Gbps",
                "status": "active"
            },
            {
                "source_ip": "192.168.1.10",
                "target_ip": "192.168.1.11",
                "connection_type": "fiber",
                "bandwidth": "10Gbps",
                "status": "active"
            },
            {
                "source_ip": "192.168.1.11",
                "target_ip": "192.168.1.20",
                "connection_type": "ethernet",
                "bandwidth": "1Gbps",
                "status": "active"
            },
            {
                "source_ip": "192.168.1.11",
                "target_ip": "192.168.1.21",
                "connection_type": "ethernet",
                "bandwidth": "1Gbps",
                "status": "active"
            },
            {
                "source_ip": "192.168.1.10",
                "target_ip": "192.168.1.100",
                "connection_type": "ethernet",
                "bandwidth": "1Gbps",
                "status": "active"
            },
            {
                "source_ip": "192.168.1.10",
                "target_ip": "192.168.1.200",
                "connection_type": "ethernet",
                "bandwidth": "1Gbps",
                "status": "active"
            }
        ]

        for conn in connections:
            add_connection(conn)

    print()
    print("=" * 60)
    print("✅ Sample topology added successfully!")
    print("=" * 60)
    print()
    print("View your topology at: http://localhost:3000")
    print("API documentation: http://localhost:8000/docs")
    print()

    # Show statistics
    response = requests.get(f"{API_BASE}/topology/stats")
    if response.status_code == 200:
        stats = response.json()
        print("Topology Statistics:")
        print(f"  Devices: {stats['total_devices']}")
        print(f"  Connections: {stats['total_connections']}")
        print(f"  Online: {stats['online']}")
        print(f"  Device Types: {json.dumps(stats['type_counts'], indent=4)}")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to backend API at http://localhost:8000")
        print("   Make sure the backend server is running!")
    except Exception as e:
        print(f"❌ Error: {e}")
