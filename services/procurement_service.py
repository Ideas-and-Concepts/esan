"""
Procurement Service
Suppliers, Purchase Orders
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Supplier, PurchaseOrder, PurchaseOrderItem

def get_all_suppliers():
    db = SessionLocal()
    try:
        return db.query(Supplier).order_by(Supplier.name).all()
    finally:
        db.close()

def create_supplier(name, phone=None, email=None, address=None, supplier_type="Agricultural Supplier", location=None, country=None, contact_person=None):
    db = SessionLocal()
    try:
        supplier = Supplier(
            name=name,
            phone=phone,
            email=email,
            address=address,
            supplier_type=supplier_type,
            location=location,
            country=country,
            contact_person=contact_person,
            created_at=datetime.utcnow()
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        return supplier
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_all_purchase_orders():
    db = SessionLocal()
    try:
        return db.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).all()
    finally:
        db.close()

def create_purchase_order(supplier_id, items_data, status="Draft"):
    """
    items_data: list of dict with product_name, quantity, unit_price
    """
    db = SessionLocal()
    try:
        total = sum(item['quantity'] * item['unit_price'] for item in items_data)
        count = db.query(PurchaseOrder).count()
        po_number = f"PO-{datetime.utcnow().strftime('%Y%m')}-{count+1:04d}"
        po = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            status=status,
            total_amount=total,
            created_at=datetime.utcnow()
        )
        db.add(po)
        db.flush()

        for item in items_data:
            poi = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_name=item['product_name'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total=item['quantity'] * item['unit_price']
            )
            db.add(poi)

        db.commit()
        db.refresh(po)
        return po
    except Exception:
        db.rollback()
        raise
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