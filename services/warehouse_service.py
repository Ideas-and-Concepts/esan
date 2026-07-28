"""
Warehouse Service
Inventory, Stock Movements, Products
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Warehouse, Product, StockMovement

def get_all_warehouses():
    db = SessionLocal()
    try:
        return db.query(Warehouse).all()
    finally:
        db.close()

def create_warehouse(name, location=None, capacity=None):
    db = SessionLocal()
    try:
        wh = Warehouse(
            name=name,
            location=location,
            capacity=capacity,
            created_at=datetime.utcnow()
        )
        db.add(wh)
        db.commit()
        db.refresh(wh)
        return wh
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_all_products():
    db = SessionLocal()
    try:
        return db.query(Product).order_by(Product.name).all()
    finally:
        db.close()

def create_product(name, category=None, unit="Kg", quantity=0, cost_price=0, selling_price=0):
    db = SessionLocal()
    try:
        product = Product(
            name=name,
            category=category,
            unit=unit,
            quantity=quantity,
            cost_price=cost_price,
            selling_price=selling_price,
            created_at=datetime.utcnow()
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def update_product_quantity(product_id, quantity_change):
    """
    quantity_change: positive for addition, negative for deduction
    """
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None
        product.quantity = (product.quantity or 0) + quantity_change
        db.commit()
        return product
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def record_stock_movement(product_id, movement_type, quantity, reference=None):
    db = SessionLocal()
    try:
        movement = StockMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            reference=reference,
            created_at=datetime.utcnow()
        )
        db.add(movement)
        db.commit()
        db.refresh(movement)
        return movement
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_low_stock_products(threshold=100):
    db = SessionLocal()
    try:
        return db.query(Product).filter(Product.quantity <= threshold).all()
    finally:
        db.close()