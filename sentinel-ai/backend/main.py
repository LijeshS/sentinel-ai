import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db, init_db
from models import Vendor, RiskAlert
from schemas import (
    VendorOut,
    VendorDetailOut,
    RiskAlertOut,
    ScanResult,
    HealthCheck,
    DashboardStats,
)
from scheduler import start_scheduler, stop_scheduler, run_monitoring_cycle, scan_single_vendor
from config import DEFAULT_VENDORS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def seed_vendors(db: Session):
    for name in DEFAULT_VENDORS:
        existing = db.query(Vendor).filter(Vendor.name == name).first()
        if not existing:
            vendor = Vendor(name=name, status="Healthy")
            db.add(vendor)
    db.commit()
    logger.info(f"Seeded {len(DEFAULT_VENDORS)} default vendors")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Sentinel AI...")
    init_db()
    db = next(get_db())
    seed_vendors(db)
    db.close()
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Sentinel AI shutdown complete")


app = FastAPI(
    title="Sentinel AI",
    description="Real-Time Third-Party Vendor Risk Monitoring Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _highest_severity(alerts: list) -> Optional[str]:
    if not alerts:
        return None
    return max(alerts, key=lambda a: SEVERITY_ORDER.get(a.severity, 0)).severity


@app.get("/health", response_model=HealthCheck)
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return HealthCheck(status="ok", version="1.0.0", db_connected=db_ok)


@app.get("/vendors", response_model=List[VendorOut])
def list_vendors(db: Session = Depends(get_db)):
    vendors = db.query(Vendor).order_by(Vendor.name).all()
    result = []
    for v in vendors:
        highest = _highest_severity(v.alerts)
        result.append(
            VendorOut(
                id=v.id,
                name=v.name,
                status=v.status,
                last_checked=v.last_checked,
                alert_count=len(v.alerts),
                highest_severity=highest,
            )
        )
    return result


@app.get("/vendors/{vendor_id}", response_model=VendorDetailOut)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    alerts_sorted = sorted(vendor.alerts, key=lambda a: a.created_at, reverse=True)
    highest = _highest_severity(vendor.alerts)

    return VendorDetailOut(
        id=vendor.id,
        name=vendor.name,
        status=vendor.status,
        last_checked=vendor.last_checked,
        alert_count=len(vendor.alerts),
        highest_severity=highest,
        alerts=[
            RiskAlertOut(
                id=a.id,
                vendor_id=a.vendor_id,
                title=a.title,
                severity=a.severity,
                incident_type=a.incident_type,
                summary=a.summary,
                business_impact=a.business_impact,
                recommended_action=a.recommended_action,
                source_url=a.source_url,
                created_at=a.created_at,
            )
            for a in alerts_sorted
        ],
    )


@app.get("/alerts", response_model=List[RiskAlertOut])
def list_alerts(
    severity: Optional[str] = None,
    vendor_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(RiskAlert)
    if severity:
        query = query.filter(RiskAlert.severity == severity.upper())
    if vendor_id:
        query = query.filter(RiskAlert.vendor_id == vendor_id)
    alerts = query.order_by(RiskAlert.created_at.desc()).limit(limit).all()
    return [
        RiskAlertOut(
            id=a.id,
            vendor_id=a.vendor_id,
            title=a.title,
            severity=a.severity,
            incident_type=a.incident_type,
            summary=a.summary,
            business_impact=a.business_impact,
            recommended_action=a.recommended_action,
            source_url=a.source_url,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@app.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    vendors = db.query(Vendor).all()
    healthy = sum(1 for v in vendors if v.status == "Healthy")
    warnings = sum(1 for v in vendors if v.status == "Warning")
    critical = sum(1 for v in vendors if v.status in ("High Alert", "Critical"))
    total_alerts = db.query(RiskAlert).count()
    return DashboardStats(
        total_vendors=len(vendors),
        healthy=healthy,
        warnings=warnings,
        critical=critical,
        total_alerts=total_alerts,
    )


@app.post("/scan", response_model=List[ScanResult])
def trigger_scan(background_tasks: BackgroundTasks, vendor_id: Optional[int] = None, db: Session = Depends(get_db)):
    if vendor_id:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        background_tasks.add_task(scan_single_vendor, vendor.name)
        return [ScanResult(vendor=vendor.name, alerts_found=0, status="scanning", message="Scan initiated")]
    else:
        background_tasks.add_task(run_monitoring_cycle)
        vendors = db.query(Vendor).all()
        return [
            ScanResult(vendor=v.name, alerts_found=0, status="scanning", message="Scan initiated")
            for v in vendors
        ]
