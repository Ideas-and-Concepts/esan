"""
Sales Service
Handles Customers, Quotations, Sales Orders
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Customer, Quotation, QuotationItem, SalesOrder, SalesOrderItem

def get_all_customers():
    db: Session = SessionLocal()
    try:
        return db.query(Customer).order_by(Customer.name).all()
    finally:
        db.close()

def create_customer(name, customer_type="Retail", phone=None, email=None, address=None, location=None, country=None, contact_person=None):
    db = SessionLocal()
    try:
        customer = Customer(
            name=name,
            customer_type=customer_type,
            phone=phone,
            email=email,
            address=address,
            location=location,
            country=country,
            contact_person=contact_person,
            created_at=datetime.utcnow()
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def create_quotation(customer_id, items_data):
    """
    items_data: list of dict with keys: product_name, quantity, unit_price
    """
    db = SessionLocal()
    try:
        total = sum(item['quantity'] * item['unit_price'] for item in items_data)
        count = db.query(Quotation).count()
        number = f"Q-{datetime.utcnow().strftime('%Y%m')}-{count+1:04d}"
        quotation = Quotation(
            quotation_number=number,
            customer_id=customer_id,
            status="Draft",
            total_amount=total,
            created_at=datetime.utcnow()
        )
        db.add(quotation)
        db.flush()  # get id

        for item in items_data:
            qi = QuotationItem(
                quotation_id=quotation.id,
                product_name=item['product_name'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total=item['quantity'] * item['unit_price']
            )
            db.add(qi)

        db.commit()
        db.refresh(quotation)
        return quotation
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_all_quotations():
    db = SessionLocal()
    try:
        return db.query(Quotation).order_by(Quotation.created_at.desc()).all()
    finally:
        db.close()

def create_sales_order(customer_id, items_data, status="Pending"):
    db = SessionLocal()
    try:
        total = sum(item['quantity'] * item['unit_price'] for item in items_data)
        count = db.query(SalesOrder).count()
        order_number = f"SO-{datetime.utcnow().strftime('%Y%m')}-{count+1:04d}"
        order = SalesOrder(
            order_number=order_number,
            customer_id=customer_id,
            status=status,
            total_amount=total,
            created_at=datetime.utcnow()
        )
        db.add(order)
        db.flush()

        for item in items_data:
            soi = SalesOrderItem(
                order_id=order.id,
                product_name=item['product_name'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total=item['quantity'] * item['unit_price']
            )
            db.add(soi)

        db.commit()
        db.refresh(order)
        return order
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_all_sales_orders():
    db = SessionLocal()
    try:
        return db.query(SalesOrder).order_by(SalesOrder.created_at.desc()).all()
    finally:
        db.close()

def update_order_status(order_id, new_status):
    db = SessionLocal()
    try:
        order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if order:
            order.status = new_status
            db.commit()
            return order
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()