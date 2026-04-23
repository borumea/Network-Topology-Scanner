from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


def _get_default_interface() -> str:
    """Lazy import to avoid circular dependency."""
    try:
        from app.utils.platform_utils import get_default_interface
        return get_default_interface()
    except ImportError:
        return "eth0"


def _get_all_up_interfaces() -> list[str]:
    """Lazy import to avoid circular dependency."""
    try:
        from app.utils.platform_utils import get_all_up_interfaces
        return get_all_up_interfaces()
    except ImportError:
        return ["eth0"]


class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # SQLite
    sqlite_path: str = "./data/mapper.db"

    # Scanning
    # "auto" resolves to every UP interface's IPv4 subnet at scan time.
    # Set to an explicit CIDR (or comma-separated CIDRs) to override.
    scan_default_range: str = "auto"
    scan_rate_limit: int = 1000
    scan_passive_interface: str = ""  # Empty = auto-detect
    snmp_community: str = "public"
    snmp_version: str = "2c"

    # Feature toggles
    enable_active_scan: bool = True
    enable_passive_scan: bool = True
    enable_snmp_scan: bool = True

    # SSH / Device Config
    ssh_username: str = "admin"
    ssh_password: str = ""
    ssh_timeout: int = 30

    # Scheduled scanning — 0 = disabled (manual scans only).
    # Disabled by default to avoid firing a /16 nmap sweep at whatever
    # subnet happens to be in scan_default_range.
    scan_interval_minutes: int = 0

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    ws_heartbeat_interval: int = 30
    log_level: str = "INFO"

    # Agent Mode
    agent_mode: str = "alert"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def get_passive_interface(self) -> str:
        """Return configured interface or auto-detect.

        Kept for backward compatibility with callers that only want one
        interface. Prefer get_passive_interfaces() for full multi-homed
        coverage.
        """
        interfaces = self.get_passive_interfaces()
        return interfaces[0] if interfaces else _get_default_interface()

    def get_passive_interfaces(self) -> list[str]:
        """Return the list of interfaces to passively sniff.

        If SCAN_PASSIVE_INTERFACE is set, it's parsed as a comma-separated
        list (single values still work). If empty, auto-detect every UP
        non-loopback interface so multi-homed hosts aren't reduced to the
        default-route leg.
        """
        if self.scan_passive_interface:
            return [
                s.strip()
                for s in self.scan_passive_interface.split(",")
                if s.strip()
            ]
        return _get_all_up_interfaces()


@lru_cache()
def get_settings() -> Settings:
    return Settings()
