"""
Production Service
Milling & Packaging Batches
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import MillingBatch, PackagingBatch

def create_milling_batch(raw_material, input_quantity, output_quantity=None, wastage=None):
    db = SessionLocal()
    try:
        count = db.query(MillingBatch).count()
        batch_number = f"MB-{datetime.utcnow().strftime('%Y%m')}-{count+1:04d}"
        batch = MillingBatch(
            batch_number=batch_number,
            raw_material=raw_material,
            input_quantity=input_quantity,
            output_quantity=output_quantity,
            wastage=wastage,
            status="Processing",
            created_at=datetime.utcnow()
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def complete_milling_batch(batch_id, output_quantity, wastage):
    db = SessionLocal()
    try:
        batch = db.query(MillingBatch).filter(MillingBatch.id == batch_id).first()
        if batch:
            batch.output_quantity = output_quantity
            batch.wastage = wastage
            batch.status = "Completed"
            db.commit()
            return batch
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def create_packaging_batch(product_name, input_quantity, packed_quantity, package_size):
    db = SessionLocal()
    try:
        count = db.query(PackagingBatch).count()
        batch_number = f"PB-{datetime.utcnow().strftime('%Y%m')}-{count+1:04d}"
        batch = PackagingBatch(
            batch_number=batch_number,
            product_name=product_name,
            input_quantity=input_quantity,
            packed_quantity=packed_quantity,
            package_size=package_size,
            status="Processing",
            created_at=datetime.utcnow()
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_all_milling_batches():
    db = SessionLocal()
    try:
        return db.query(MillingBatch).order_by(MillingBatch.created_at.desc()).all()
    finally:
        db.close()

def get_all_packaging_batches():
    db = SessionLocal()
    try:
        return db.query(PackagingBatch).order_by(PackagingBatch.created_at.desc()).all()
    finally:
        db.close()


def update_purchase_order_status(po_id, new_status):
    """Update the status of a purchase order."""
    db = SessionLocal()
    try:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if po:
            po.status = new_status
            db.commit()
            return po
        return None
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()