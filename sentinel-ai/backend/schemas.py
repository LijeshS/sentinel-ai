from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class VendorBase(BaseModel):
    name: str
    status: str
    last_checked: Optional[datetime] = None


class VendorOut(VendorBase):
    id: int
    alert_count: Optional[int] = 0
    highest_severity: Optional[str] = None

    class Config:
        from_attributes = True


class RiskAlertBase(BaseModel):
    title: str
    severity: str
    incident_type: str
    summary: str
    business_impact: str
    recommended_action: str
    source_url: str


class RiskAlertOut(RiskAlertBase):
    id: int
    vendor_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class VendorDetailOut(VendorOut):
    alerts: List[RiskAlertOut] = []

    class Config:
        from_attributes = True


class ScanResult(BaseModel):
    vendor: str
    alerts_found: int
    status: str
    message: str


class HealthCheck(BaseModel):
    status: str
    version: str
    db_connected: bool


class DashboardStats(BaseModel):
    total_vendors: int
    healthy: int
    warnings: int
    critical: int
    total_alerts: int
