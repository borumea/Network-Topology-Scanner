from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class AlertType(str, Enum):
    NEW_DEVICE = "new_device"
    TOPOLOGY_CHANGE = "topology_change"
    SPOF = "spof"
    ANOMALY = "anomaly"
    FLAPPING = "flapping"
    DEVICE_OFFLINE = "device_offline"
    CONFIG_DRIFT = "config_drift"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: AlertType
    severity: Severity
    title: str
    description: str = ""
    device_id: Optional[str] = None
    details: dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    status: AlertStatus = AlertStatus.OPEN


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
