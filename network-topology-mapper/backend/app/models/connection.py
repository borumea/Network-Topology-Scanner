from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class ConnectionType(str, Enum):
    ETHERNET = "ethernet"
    FIBER = "fiber"
    WIRELESS = "wireless"
    VPN = "vpn"
    VIRTUAL = "virtual"


class ConnectionStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DEGRADED = "degraded"
    FLAPPING = "flapping"


class Connection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    target_id: str
    connection_type: ConnectionType = ConnectionType.ETHERNET
    bandwidth: str = ""
    switch_port: str = ""
    vlan: Optional[int] = None
    latency_ms: float = 0.0
    packet_loss_pct: float = 0.0
    is_redundant: bool = False
    protocol: str = "access"
    status: ConnectionStatus = ConnectionStatus.ACTIVE
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class DependencyType(str, Enum):
    DNS = "dns"
    DHCP = "dhcp"
    AUTH = "auth"
    DATABASE = "database"
    API = "api"
    LOAD_BALANCER = "load_balancer"
    STORAGE = "storage"


class Dependency(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    target_id: str
    dependency_type: DependencyType
    service_port: int = 0
    criticality: str = "medium"
    discovered_via: str = "traffic_analysis"
