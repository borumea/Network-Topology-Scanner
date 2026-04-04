from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache
import ipaddress
import socket


def _detect_local_subnet() -> str:
    """Detect the local network subnet (e.g. 192.168.1.0/24)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
        return str(network)
    except Exception:
        return "192.168.0.0/24"


class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # SQLite
    sqlite_path: str = "./data/mapper.db"

    # Scanning (empty/blank = auto-detect local subnet)
    scan_default_range: str = ""
    scan_rate_limit: int = 1000
    scan_passive_interface: str = "eth0"
    snmp_community: str = "public"
    snmp_version: str = "2c"
    enable_active_scan: bool = True
    enable_passive_scan: bool = True
    enable_snmp_scan: bool = True

    @model_validator(mode="after")
    def _auto_detect_subnet(self):
        if not self.scan_default_range.strip():
            self.scan_default_range = _detect_local_subnet()
        return self

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
        env_file = ("../.env", ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
