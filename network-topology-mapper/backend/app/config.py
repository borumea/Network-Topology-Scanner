import logging
import socket
import struct

from pydantic_settings import BaseSettings
from functools import lru_cache

logger = logging.getLogger(__name__)


def _detect_local_subnet() -> str:
    """Detect the local machine's subnet (e.g. '192.168.1.0/24').

    Works cross-platform by connecting a UDP socket to a public IP
    (no traffic sent) to discover the default outbound interface IP,
    then uses /24 as the mask (correct for most home/small-office nets).
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        # Connect to a public IP — no data is actually sent
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        # Derive /24 network address from the local IP
        parts = local_ip.split(".")
        network = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        logger.info("Auto-detected local subnet: %s (from local IP %s)", network, local_ip)
        return network
    except Exception as e:
        logger.warning("Could not auto-detect subnet: %s — falling back to 192.168.1.0/24", e)
        return "192.168.1.0/24"


class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # SQLite
    sqlite_path: str = "./data/mapper.db"

    # Scanning — empty string means "auto-detect at startup"
    scan_default_range: str = ""
    scan_rate_limit: int = 1000
    scan_passive_interface: str = ""  # empty = auto-detect via Scapy
    snmp_community: str = "public"
    snmp_version: str = "2c"

    # Scan phase toggles
    enable_active_scan: bool = True
    enable_passive_scan: bool = True
    enable_snmp_scan: bool = True

    # SSH / Device Config
    ssh_username: str = "admin"
    ssh_password: str = ""
    ssh_timeout: int = 30

    # Claude API
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-5-20250929"

    # Scheduled scanning
    scan_interval_minutes: int = 5  # 0 = disabled

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    ws_heartbeat_interval: int = 30
    log_level: str = "INFO"

    # Agent Mode
    agent_mode: str = "alert"

    class Config:
        env_file = (".env", "../.env")
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    # Auto-detect subnet if not explicitly configured
    if not settings.scan_default_range:
        settings.scan_default_range = _detect_local_subnet()
    return settings
