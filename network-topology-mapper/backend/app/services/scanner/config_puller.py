import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ConfigPuller:
    """Uses Netmiko to SSH into network devices and pull running configurations."""

    def __init__(self):
        self._available = False
        try:
            from netmiko import ConnectHandler
            self._available = True
        except ImportError:
            logger.warning("Netmiko not installed. Config pulling unavailable.")

    @property
    def available(self) -> bool:
        return self._available

    def pull_config(self, ip: str, device_type: str = "cisco_ios",
                    username: str = "", password: str = "") -> Optional[str]:
        if not self._available:
            return None

        try:
            from netmiko import ConnectHandler

            device = {
                "device_type": device_type,
                "host": ip,
                "username": username,
                "password": password,
                "timeout": 10,
            }

            with ConnectHandler(**device) as conn:
                config = conn.send_command("show running-config")
                return config

        except Exception as e:
            logger.debug("Config pull failed for %s: %s", ip, e)
            return None

    def get_lldp_neighbors(self, ip: str, device_type: str = "cisco_ios",
                           username: str = "", password: str = "") -> list[dict]:
        if not self._available:
            return []

        try:
            from netmiko import ConnectHandler

            device = {
                "device_type": device_type,
                "host": ip,
                "username": username,
                "password": password,
                "timeout": 10,
            }

            with ConnectHandler(**device) as conn:
                output = conn.send_command("show lldp neighbors detail")
                return self._parse_lldp(output)

        except Exception as e:
            logger.debug("LLDP query failed for %s: %s", ip, e)
            return []

    def _parse_lldp(self, output: str) -> list[dict]:
        neighbors = []
        current = {}

        for line in output.split("\n"):
            line = line.strip()
            if "System Name:" in line:
                current["hostname"] = line.split(":")[-1].strip()
            elif "Port ID:" in line:
                current["port"] = line.split(":")[-1].strip()
            elif "Management Address:" in line:
                current["ip"] = line.split(":")[-1].strip()
            elif line == "" and current:
                if current.get("hostname"):
                    neighbors.append(current)
                current = {}

        if current and current.get("hostname"):
            neighbors.append(current)

        return neighbors


config_puller = ConfigPuller()
