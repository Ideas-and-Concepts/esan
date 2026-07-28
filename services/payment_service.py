"""
Payment Service
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Payment, Invoice

def record_payment(invoice_id, amount, payment_method, reference=None):
    db = SessionLocal()
    try:
        payment = Payment(
            invoice_id=invoice_id,
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            status="Completed",
            created_at=datetime.utcnow()
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        # Update invoice status
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if invoice:
            all_payments = db.query(Payment).filter(Payment.invoice_id == invoice_id).all()
            total_paid = sum(p.amount for p in all_payments)
            if total_paid >= invoice.amount:
                invoice.status = "Paid"
            elif total_paid > 0:
                invoice.status = "Partial"
            db.commit()

        return payment
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_all_payments():
    db = SessionLocal()
    try:
        return db.query(Payment).order_by(Payment.created_at.desc()).all()
    finally:
        db.close()

def get_payments_by_invoice(invoice_id):
    db = SessionLocal()
    try:
        return db.query(Payment).filter(Payment.invoice_id == invoice_id).order_by(Payment.created_at).all()
    finally:
        db.close()