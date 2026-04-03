from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # SQLite
    sqlite_path: str = "./data/mapper.db"

    # Scanning
    scan_default_range: str = "192.168.0.0/16"
    scan_rate_limit: int = 1000
    scan_passive_interface: str = "eth0"
    snmp_community: str = "public"
    snmp_version: str = "2c"
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
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
