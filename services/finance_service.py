"""
Finance Service
Financial Transactions, Summaries
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal
from models import FinanceTransaction, Invoice, Payment

def add_transaction(transaction_type, amount, category=None, description=None, reference=None):
    db = SessionLocal()
    try:
        t = FinanceTransaction(
            transaction_type=transaction_type,
            amount=amount,
            category=category,
            description=description,
            reference=reference,
            created_at=datetime.utcnow()
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        return t
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_all_transactions(limit=100):
    db = SessionLocal()
    try:
        return db.query(FinanceTransaction).order_by(FinanceTransaction.created_at.desc()).limit(limit).all()
    finally:
        db.close()

def get_total_revenue():
    db = SessionLocal()
    try:
        return db.query(func.sum(Payment.amount)).scalar() or 0
    finally:
        db.close()

def get_total_expenses():
    db = SessionLocal()
    try:
        return db.query(func.sum(FinanceTransaction.amount)).filter(FinanceTransaction.transaction_type == "Expense").scalar() or 0
    finally:
        db.close()

def get_net_profit():
    return get_total_revenue() - get_total_expenses()

def get_monthly_revenue():
    db = SessionLocal()
    try:
        payments = db.query(Payment).all()
        monthly = {}
        for p in payments:
            month = p.created_at.strftime('%Y-%m')
            monthly[month] = monthly.get(month, 0) + p.amount
        return monthly
    finally:
        db.close()

def get_monthly_expenses():
    db = SessionLocal()
    try:
        expenses = db.query(FinanceTransaction).filter(FinanceTransaction.transaction_type == "Expense").all()
        monthly = {}
        for e in expenses:
            month = e.created_at.strftime('%Y-%m')
            monthly[month] = monthly.get(month, 0) + e.amount
        return monthly
    finally:
        db.close()