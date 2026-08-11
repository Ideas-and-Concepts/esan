"""
Esan ERP Dashboard Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

from sqlalchemy import func

from database import SessionLocal
from models import (
    Customer,
    SalesOrder,
    Invoice,
    Payment,
    Product,
    MillingBatch,
    PackagingBatch,
)


def get_kpis():
    """
    Return aggregated KPI values for the main ERP dashboard.

    The function creates and closes its own database session so
    dashboard modules do not need to manage database connections.
    """

    db = SessionLocal()

    try:
        total_customers = (
            db.query(Customer).count()
        )

        total_orders = (
            db.query(SalesOrder).count()
        )

        total_invoiced = (
            db.query(func.sum(Invoice.amount)).scalar()
            or 0
        )

        total_collected = (
            db.query(func.sum(Payment.amount)).scalar()
            or 0
        )

        total_products = (
            db.query(Product).count()
        )

        total_stock = (
            db.query(func.sum(Product.quantity)).scalar()
            or 0
        )

        milling_runs = (
            db.query(MillingBatch).count()
        )

        packaging_runs = (
            db.query(PackagingBatch).count()
        )

        return {
            "customers": total_customers,
            "orders": total_orders,
            "invoiced": float(total_invoiced),
            "collected": float(total_collected),
            "products": total_products,
            "stock_kg": float(total_stock),
            "milling_batches": milling_runs,
            "packaging_batches": packaging_runs,
        }

    except Exception:
        raise

    finally:
        db.close()