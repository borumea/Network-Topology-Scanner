from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class DeviceType(str, Enum):
    ROUTER = "router"
    SWITCH = "switch"
    SERVER = "server"
    WORKSTATION = "workstation"
    FIREWALL = "firewall"
    AP = "ap"
    PRINTER = "printer"
    IOT = "iot"
    UNKNOWN = "unknown"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class Criticality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Device(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ip: str
    mac: str = ""
    hostname: str = ""
    device_type: DeviceType = DeviceType.UNKNOWN
    vendor: str = ""
    model: str = ""
    os: str = ""
    open_ports: list[int] = []
    services: list[str] = []
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    discovery_method: str = "active_scan"
    vlan_ids: list[int] = []
    subnet: str = ""
    location: str = ""
    risk_score: float = 0.0
    criticality: Criticality = Criticality.LOW
    is_gateway: bool = False
    status: DeviceStatus = DeviceStatus.ONLINE


class DeviceResponse(BaseModel):
    id: str
    ip: str
    mac: str
    hostname: str
    device_type: str
    vendor: str
    model: str
    os: str
    open_ports: list[int]
    services: list[str]
    first_seen: str
    last_seen: str
    discovery_method: str
    vlan_ids: list[int]
    subnet: str
    location: str
    risk_score: float
    criticality: str
    is_gateway: bool
    status: str


class DeviceSummary(BaseModel):
    id: str
    ip: str
    hostname: str
    device_type: str
    status: str
    risk_score: float
