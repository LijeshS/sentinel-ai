import logging
from datetime import datetime
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Vendor, RiskAlert
from brightdata import search_vendor_news, extract_article
from ai_service import analyze_article
from config import SCAN_INTERVAL_MINUTES

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

STATUS_MAP = {
    "LOW": "Healthy",
    "MEDIUM": "Warning",
    "HIGH": "High Alert",
    "CRITICAL": "Critical",
}

SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _get_highest_severity(severities: List[str]) -> str:
    if not severities:
        return "LOW"
    return max(severities, key=lambda s: SEVERITY_ORDER.get(s, 0))


def scan_vendor(vendor_name: str, db: Session) -> int:
    logger.info(f"Scanning vendor: {vendor_name}")
    alerts_created = 0

    try:
        articles = search_vendor_news(vendor_name)
        logger.info(f"Found {len(articles)} articles for {vendor_name}")

        # Get existing source URLs for dedup
        vendor = db.query(Vendor).filter(Vendor.name == vendor_name).first()
        if not vendor:
            logger.warning(f"Vendor not found in DB: {vendor_name}")
            return 0

        existing_urls = {
            alert.source_url
            for alert in db.query(RiskAlert).filter(RiskAlert.vendor_id == vendor.id).all()
        }

        new_severities = []

        for article_meta in articles:
            url = article_meta.get("url", "")
            title = article_meta.get("title", "")

            if url in existing_urls:
                logger.debug(f"Skipping already-processed URL: {url}")
                continue

            # Extract article content
            article_data = extract_article(url)
            if not article_data:
                logger.debug(f"Could not extract content from: {url}")
                # Try analyzing just the title/snippet
                article_data = {
                    "title": title,
                    "content": title,
                    "source_url": url,
                }

            # AI analysis
            analysis = analyze_article(
                vendor_name=vendor_name,
                article_title=article_data.get("title") or title,
                article_content=article_data.get("content", ""),
                source_url=url,
            )

            if not analysis:
                logger.debug(f"Article deemed irrelevant by AI: {url}")
                continue

            # Store alert
            alert = RiskAlert(
                vendor_id=vendor.id,
                title=article_data.get("title") or title or f"{vendor_name} Risk Alert",
                severity=analysis["risk_level"],
                incident_type=analysis["incident_type"],
                summary=analysis["summary"],
                business_impact=analysis["business_impact"],
                recommended_action=analysis["recommended_action"],
                source_url=url,
                created_at=datetime.utcnow(),
            )
            db.add(alert)
            new_severities.append(analysis["risk_level"])
            existing_urls.add(url)
            alerts_created += 1
            logger.info(f"Alert created: {vendor_name} | {analysis['risk_level']} | {analysis['incident_type']}")

        # Update vendor status
        if new_severities:
            highest = _get_highest_severity(new_severities)
            vendor.status = STATUS_MAP.get(highest, "Warning")
        elif vendor.status == "Healthy":
            pass  # Keep healthy if no new alerts
        
        vendor.last_checked = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"Error scanning vendor {vendor_name}: {e}", exc_info=True)
        db.rollback()

    return alerts_created


def run_monitoring_cycle():
    logger.info("=== Starting monitoring cycle ===")
    db = SessionLocal()
    try:
        vendors = db.query(Vendor).all()
        total_alerts = 0
        for vendor in vendors:
            alerts = scan_vendor(vendor.name, db)
            total_alerts += alerts
        logger.info(f"=== Monitoring cycle complete. {total_alerts} new alerts ===")
    except Exception as e:
        logger.error(f"Monitoring cycle failed: {e}", exc_info=True)
    finally:
        db.close()


def scan_single_vendor(vendor_name: str) -> int:
    db = SessionLocal()
    try:
        return scan_vendor(vendor_name, db)
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            run_monitoring_cycle,
            trigger=IntervalTrigger(minutes=SCAN_INTERVAL_MINUTES),
            id="vendor_monitoring",
            name="Vendor Risk Monitoring",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(f"Scheduler started — running every {SCAN_INTERVAL_MINUTES} minutes")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
