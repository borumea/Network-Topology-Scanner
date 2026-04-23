from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class ScanType(str, Enum):
    ACTIVE = "active"
    PASSIVE = "passive"
    SNMP = "snmp"
    FULL = "full"


class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Scan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scan_type: ScanType
    status: ScanStatus = ScanStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    target_range: str = "all"
    devices_found: int = 0
    new_devices: int = 0
    config: dict[str, Any] = {}


class ScanRequest(BaseModel):
    type: ScanType = ScanType.FULL
    target: str = "auto"
    intensity: str = "normal"


class ScanProgress(BaseModel):
    scan_id: str
    percent: float
    phase: str
    devices_found: int = 0


class TopologySnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    device_count: int = 0
    connection_count: int = 0
    risk_score: float = 0.0
    snapshot_data: dict[str, Any] = {}
