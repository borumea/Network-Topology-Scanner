import logging
import uuid
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SNMPPoller:
    """SNMP device interrogation for switch port mapping and device details."""

    def __init__(self):
        self._available = False
        self._import_error: Optional[str] = None
        try:
            from pysnmp.hlapi import getCmd, SnmpEngine
            self._available = True
        except ImportError as e:
            # Loud error — pysnmp is pinned in requirements.txt, so an
            # ImportError here means the install step silently failed
            # (which is exactly the bug observed on the RadLab VM).
            self._import_error = str(e)
            logger.error(
                "pysnmp import failed: %s. "
                "SNMP polling is unavailable. "
                "Check that `pip install -r requirements.txt` completed "
                "without errors; pysnmp==6.2.6 should install cleanly on "
                "Python 3.10+.",
                e,
            )

    @property
    def available(self) -> bool:
        return self._available

    def poll_device(self, ip: str, community: str = "public",
                    version: str = "2c") -> Optional[dict]:
        if not self._available:
            return None

        try:
            from pysnmp.hlapi import (
                getCmd, SnmpEngine, CommunityData, UdpTransportTarget,
                ContextData, ObjectType, ObjectIdentity
            )

            engine = SnmpEngine()
            oids = {
                "sysName": "1.3.6.1.2.1.1.5.0",
                "sysDescr": "1.3.6.1.2.1.1.1.0",
                "sysObjectID": "1.3.6.1.2.1.1.2.0",
                "sysUpTime": "1.3.6.1.2.1.1.3.0",
                "sysLocation": "1.3.6.1.2.1.1.6.0",
            }

            result = {}
            for name, oid in oids.items():
                error_indication, error_status, error_index, var_binds = next(
                    getCmd(
                        engine,
                        CommunityData(community, mpModel=0 if version == "1" else 1),
                        UdpTransportTarget((ip, 161), timeout=5, retries=1),
                        ContextData(),
                        ObjectType(ObjectIdentity(oid)),
                    )
                )
                if not error_indication and not error_status:
                    for var_bind in var_binds:
                        result[name] = str(var_bind[1])

            if result:
                return {
                    "ip": ip,
                    "hostname": result.get("sysName", ""),
                    "os": result.get("sysDescr", ""),
                    "location": result.get("sysLocation", ""),
                    "uptime": result.get("sysUpTime", ""),
                    "discovery_method": "snmp",
                    "open_ports": [161],
                    "services": ["snmp"],
                }

        except Exception as e:
            logger.debug("SNMP poll failed for %s: %s", ip, e)

        return None

    def get_switch_ports(self, ip: str, community: str = "public") -> list[dict]:
        if not self._available:
            return []

        try:
            from pysnmp.hlapi import (
                nextCmd, SnmpEngine, CommunityData, UdpTransportTarget,
                ContextData, ObjectType, ObjectIdentity
            )

            engine = SnmpEngine()
            ports = []

            for error_indication, error_status, error_index, var_binds in nextCmd(
                engine,
                CommunityData(community),
                UdpTransportTarget((ip, 161), timeout=5, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity("1.3.6.1.2.1.2.2.1.2")),  # ifDescr
                lexicographicMode=False,
            ):
                if error_indication or error_status:
                    break
                for var_bind in var_binds:
                    ports.append({
                        "index": str(var_bind[0]).split(".")[-1],
                        "name": str(var_bind[1]),
                    })

            return ports
        except Exception as e:
            logger.debug("SNMP port walk failed for %s: %s", ip, e)
            return []


snmp_poller = SNMPPoller()
