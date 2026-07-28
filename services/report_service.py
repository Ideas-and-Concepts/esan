"""
Report Service
Data aggregation for reports module
"""

from sqlalchemy import func
from database import SessionLocal
from models import Invoice, Payment, Customer, Product, FinanceTransaction, SalesOrder

def revenue_by_customer():
    db = SessionLocal()
    try:
        payments = db.query(Payment).all()
        result = {}
        for p in payments:
            inv = db.query(Invoice).filter(Invoice.id == p.invoice_id).first()
            if inv:
                cust = db.query(Customer).filter(Customer.id == inv.customer_id).first()
                name = cust.name if cust else f"Invoice {inv.invoice_number}"
                result[name] = result.get(name, 0) + p.amount
        return result
    finally:
        db.close()

def monthly_revenue():
    db = SessionLocal()
    try:
        payments = db.query(Payment).all()
        monthly = {}
        for p in payments:
            month = p.created_at.strftime('%Y-%m')
            monthly[month] = monthly.get(month, 0) + p.amount
        return dict(sorted(monthly.items()))
    finally:
        db.close()

def inventory_levels():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return [{"name": p.name, "quantity": p.quantity, "category": p.category} for p in products]
    finally:
        db.close()

def expense_categories():
    db = SessionLocal()
    try:
        expenses = db.query(FinanceTransaction).filter(FinanceTransaction.transaction_type == "Expense").all()
        cats = {}
        for e in expenses:
            cat = e.category or "Other"
            cats[cat] = cats.get(cat, 0) + e.amount
        return cats
    finally:
        db.close()

def order_status_summary():
    db = SessionLocal()
    try:
        orders = db.query(SalesOrder).all()
        statuses = {}
        for o in orders:
            statuses[o.status] = statuses.get(o.status, 0) + 1
        return statuses
    finally:
        db.close()