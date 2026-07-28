"""
Dashboard Service
Aggregated KPIs for the main dashboard
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal
from models import Customer, SalesOrder, Invoice, Payment, Product, MillingBatch, PackagingBatch

def get_kpis():
    db = SessionLocal()
    try:
        total_customers = db.query(Customer).count()
        total_orders = db.query(SalesOrder).count()
        total_invoiced = db.query(func.sum(Invoice.amount)).scalar() or 0
        total_collected = db.query(func.sum(Payment.amount)).scalar() or 0
        total_products = db.query(Product).count()
        total_stock = db.query(func.sum(Product.quantity)).scalar() or 0
        milling_runs = db.query(MillingBatch).count()
        packaging_runs = db.query(PackagingBatch).count()

        return {
            "customers": total_customers,
            "orders": total_orders,
            "invoiced": total_invoiced,
            "collected": total_collected,
            "products": total_products,
            "stock_kg": total_stock,
            "milling_batches": milling_runs,
            "packaging_batches": packaging_runs,
        }
    finally:
        db.close()