"""
Delivery Service
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Delivery, SalesOrder

def create_delivery(order_id, destination, driver, vehicle, status="Scheduled"):
    db = SessionLocal()
    try:
        count = db.query(Delivery).count()
        delivery_number = f"DEL-{datetime.utcnow().strftime('%Y%m')}-{count+1:04d}"
        delivery = Delivery(
            delivery_number=delivery_number,
            order_id=order_id,
            destination=destination,
            driver=driver,
            vehicle=vehicle,
            status=status,
            created_at=datetime.utcnow()
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        return delivery
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_all_deliveries():
    db = SessionLocal()
    try:
        return db.query(Delivery).order_by(Delivery.created_at.desc()).all()
    finally:
        db.close()

def update_delivery_status(delivery_id, new_status, delivered_date=None):
    db = SessionLocal()
    try:
        delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
        if delivery:
            delivery.status = new_status
            if new_status == "Delivered" and delivered_date:
                delivery.delivered_date = delivered_date
            db.commit()
            return delivery
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_pending_deliveries():
    db = SessionLocal()
    try:
        return db.query(Delivery).filter(Delivery.status != "Delivered").all()
    finally:
        db.close()