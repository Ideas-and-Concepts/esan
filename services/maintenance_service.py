"""
Maintenance Service
Equipment tracking
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Equipment

def get_all_equipment():
    db = SessionLocal()
    try:
        return db.query(Equipment).order_by(Equipment.name).all()
    finally:
        db.close()

def create_equipment(name, equipment_type, serial_number=None,
                     purchase_date=None, last_maintenance=None,
                     next_maintenance=None, status="Operational"):
    db = SessionLocal()
    try:
        eq = Equipment(
            name=name,
            equipment_type=equipment_type,
            serial_number=serial_number,
            purchase_date=purchase_date,
            last_maintenance=last_maintenance,
            next_maintenance=next_maintenance,
            status=status,
            created_at=datetime.utcnow()
        )
        db.add(eq)
        db.commit()
        db.refresh(eq)
        return eq
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
