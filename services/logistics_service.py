"""
Logistics Service
Vehicles, Maintenance Records, Delivery queries
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Vehicle, MaintenanceRecord

def get_all_vehicles():
    db = SessionLocal()
    try:
        return db.query(Vehicle).all()
    finally:
        db.close()

def create_vehicle(vehicle_number, vehicle_type, make=None, model=None, capacity=None):
    db = SessionLocal()
    try:
        v = Vehicle(
            vehicle_number=vehicle_number,
            vehicle_type=vehicle_type,
            make=make,
            model=model,
            capacity=capacity,
            status="Available",
            created_at=datetime.utcnow()
        )
        db.add(v)
        db.commit()
        db.refresh(v)
        return v
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_all_maintenance_records():
    db = SessionLocal()
    try:
        return db.query(MaintenanceRecord).order_by(MaintenanceRecord.maintenance_date.desc()).all()
    finally:
        db.close()

def create_maintenance_record(vehicle_id, description, cost, maintenance_date, next_due_date=None):
    db = SessionLocal()
    try:
        m = MaintenanceRecord(
            vehicle_id=vehicle_id,
            description=description,
            cost=cost,
            maintenance_date=maintenance_date,
            next_due_date=next_due_date,
            created_at=datetime.utcnow()
        )
        db.add(m)
        db.commit()
        db.refresh(m)
        return m
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
