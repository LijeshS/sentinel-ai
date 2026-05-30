from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(50), default="Healthy")
    last_checked = Column(DateTime, nullable=True)

    alerts = relationship("RiskAlert", back_populates="vendor", cascade="all, delete-orphan")


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    title = Column(String(500), nullable=False)
    severity = Column(String(20), nullable=False)
    incident_type = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    business_impact = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="alerts")
