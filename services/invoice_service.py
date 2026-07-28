"""
Invoice Service
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Invoice, SalesOrder, Payment

def create_invoice(order_id):
    db = SessionLocal()
    try:
        order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not order:
            return None
        count = db.query(Invoice).count()
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m')}-{count+1:04d}"
        invoice = Invoice(
            invoice_number=invoice_number,
            customer_id=order.customer_id,
            order_id=order.id,
            amount=order.total_amount,
            status="Unpaid",
            created_at=datetime.utcnow()
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_all_invoices():
    db = SessionLocal()
    try:
        return db.query(Invoice).order_by(Invoice.created_at.desc()).all()
    finally:
        db.close()

def get_invoice_balance(invoice_id):
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return 0
        payments = db.query(Payment).filter(Payment.invoice_id == invoice_id).all()
        total_paid = sum(p.amount for p in payments)
        return invoice.amount - total_paid
    finally:
        db.close()

def update_invoice_status(invoice_id):
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return
        payments = db.query(Payment).filter(Payment.invoice_id == invoice_id).all()
        total_paid = sum(p.amount for p in payments)
        if total_paid >= invoice.amount:
            invoice.status = "Paid"
        elif total_paid > 0:
            invoice.status = "Partial"
        else:
            invoice.status = "Unpaid"
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()