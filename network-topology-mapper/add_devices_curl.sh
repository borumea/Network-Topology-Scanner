#!/bin/bash
# Add sample devices using curl
# Run: bash add_devices_curl.sh

API_BASE="http://localhost:8000/api"

echo "========================================"
echo "Adding Sample Network Devices"
echo "========================================"
echo ""

# Add Router
echo "Adding core-router-01..."
curl -s -X POST "$API_BASE/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.1",
    "mac": "00:11:22:33:44:01",
    "hostname": "core-router-01",
    "device_type": "router",
    "vendor": "Cisco",
    "model": "ISR 4451",
    "status": "online",
    "criticality": "critical"
  }' | jq .

# Add Firewall
echo ""
echo "Adding firewall-01..."
curl -s -X POST "$API_BASE/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.2",
    "mac": "00:11:22:33:44:02",
    "hostname": "firewall-01",
    "device_type": "firewall",
    "vendor": "Palo Alto",
    "model": "PA-5220",
    "status": "online",
    "criticality": "critical"
  }' | jq .

# Add Core Switch
echo ""
echo "Adding core-switch-01..."
curl -s -X POST "$API_BASE/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.10",
    "mac": "00:11:22:33:44:10",
    "hostname": "core-switch-01",
    "device_type": "switch",
    "vendor": "Cisco",
    "model": "Catalyst 9300",
    "status": "online",
    "criticality": "high"
  }' | jq .

# Add Web Server
echo ""
echo "Adding web-server-01..."
curl -s -X POST "$API_BASE/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.20",
    "mac": "00:11:22:33:44:20",
    "hostname": "web-server-01",
    "device_type": "server",
    "vendor": "Dell",
    "model": "PowerEdge R740",
    "os": "Ubuntu 22.04",
    "status": "online",
    "criticality": "high"
  }' | jq .

# Add Database Server
echo ""
echo "Adding database-server-01..."
curl -s -X POST "$API_BASE/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.21",
    "mac": "00:11:22:33:44:21",
    "hostname": "database-server-01",
    "device_type": "server",
    "vendor": "Dell",
    "model": "PowerEdge R740",
    "os": "Ubuntu 22.04",
    "status": "online",
    "criticality": "critical"
  }' | jq .

echo ""
echo "========================================"
echo "✅ Devices Added Successfully!"
echo "========================================"
echo ""

# Show topology stats
echo "Topology Statistics:"
curl -s "$API_BASE/topology/stats" | jq .

echo ""
echo "View at: http://localhost:3000"
