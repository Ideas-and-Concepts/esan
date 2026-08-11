"""
Esan ERP Dashboard Service
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Provides aggregated KPI data for the main ERP dashboard.
"""

import logging

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

logger = logging.getLogger(name)

def get_kpis():
"""
Retrieve the main ERP dashboard KPIs.

Returns:
    dict: Dashboard KPI values.

The function is designed to fail safely. If a query cannot be
completed, the affected KPI is returned as 0 rather than
crashing the entire dashboard.
"""

db = SessionLocal()

try:
    # ----------------------------------------------
    # SALES & CRM
    # ----------------------------------------------

    try:
        total_customers = db.query(Customer).count()
    except Exception as e:
        logger.error("Failed to load customers KPI: %s", e)
        total_customers = 0

    try:
        total_orders = db.query(SalesOrder).count()
    except Exception as e:
        logger.error("Failed to load sales orders KPI: %s", e)
        total_orders = 0

    # ----------------------------------------------
    # FINANCE
    # ----------------------------------------------

    try:
        total_invoiced = (
            db.query(func.coalesce(func.sum(Invoice.amount), 0))
            .scalar()
            or 0
        )
    except Exception as e:
        logger.error("Failed to load invoiced KPI: %s", e)
        total_invoiced = 0

    try:
        total_collected = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .scalar()
            or 0
        )
    except Exception as e:
        logger.error("Failed to load collected KPI: %s", e)
        total_collected = 0

    # ----------------------------------------------
    # INVENTORY
    # ----------------------------------------------

    try:
        total_products = db.query(Product).count()
    except Exception as e:
        logger.error("Failed to load products KPI: %s", e)
        total_products = 0

    try:
        total_stock = (
            db.query(func.coalesce(func.sum(Product.quantity), 0))
            .scalar()
            or 0
        )
    except Exception as e:
        logger.error("Failed to load stock KPI: %s", e)
        total_stock = 0

    # ----------------------------------------------
    # PRODUCTION
    # ----------------------------------------------

    try:
        milling_runs = db.query(MillingBatch).count()
    except Exception as e:
        logger.error("Failed to load milling KPI: %s", e)
        milling_runs = 0

    try:
        packaging_runs = db.query(PackagingBatch).count()
    except Exception as e:
        logger.error("Failed to load packaging KPI: %s", e)
        packaging_runs = 0

    # ----------------------------------------------
    # RETURN KPI DATA
    # ----------------------------------------------

    return {
        "customers": int(total_customers or 0),
        "orders": int(total_orders or 0),
        "invoiced": float(total_invoiced or 0),
        "collected": float(total_collected or 0),
        "products": int(total_products or 0),
        "stock_kg": float(total_stock or 0),
        "milling_batches": int(milling_runs or 0),
        "packaging_batches": int(packaging_runs or 0),
    }

except Exception as e:
    logger.exception("Dashboard KPI loading failed: %s", e)

    # Always return a valid dashboard structure.
    return {
        "customers": 0,
        "orders": 0,
        "invoiced": 0.0,
        "collected": 0.0,
        "products": 0,
        "stock_kg": 0.0,
        "milling_batches": 0,
        "packaging_batches": 0,
    }

finally:
    db.close()