"""
Esan ERP
Dashboard Service

Aggregated KPIs for the main ERP dashboard.

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
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


logger = logging.getLogger("esan_erp.dashboard_service")


# ============================================================
# SAFE COUNT
# ============================================================

def _safe_count(db, model):
    """
    Safely count records in a model.

    Returns 0 if the query fails.
    """

    try:

        return db.query(model).count()

    except Exception as exc:

        logger.exception(
            "Unable to count %s: %s",
            getattr(model, "__name__", "model"),
            exc,
        )

        return 0


# ============================================================
# SAFE SUM
# ============================================================

def _safe_sum(db, model, column_name):
    """
    Safely calculate the sum of a model column.

    Returns 0 if the column does not exist or the query fails.
    """

    try:

        column = getattr(model, column_name, None)

        if column is None:

            logger.warning(
                "%s does not contain column '%s'.",
                getattr(model, "__name__", "model"),
                column_name,
            )

            return 0.0

        value = (
            db.query(func.sum(column))
            .scalar()
        )

        return float(value or 0)

    except Exception as exc:

        logger.exception(
            "Unable to sum %s.%s: %s",
            getattr(model, "__name__", "model"),
            column_name,
            exc,
        )

        return 0.0


# ============================================================
# GET DASHBOARD KPIs
# ============================================================

def get_kpis():

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # CUSTOMERS
        # ----------------------------------------------------

        total_customers = _safe_count(
            db,
            Customer,
        )


        # ----------------------------------------------------
        # SALES ORDERS
        # ----------------------------------------------------

        total_orders = _safe_count(
            db,
            SalesOrder,
        )


        # ----------------------------------------------------
        # INVOICED VALUE
        # ----------------------------------------------------

        total_invoiced = _safe_sum(
            db,
            Invoice,
            "amount",
        )


        # ----------------------------------------------------
        # COLLECTIONS
        # ----------------------------------------------------

        total_collected = _safe_sum(
            db,
            Payment,
            "amount",
        )


        # ----------------------------------------------------
        # PRODUCTS
        # ----------------------------------------------------

        total_products = _safe_count(
            db,
            Product,
        )


        # ----------------------------------------------------
        # CURRENT STOCK
        # ----------------------------------------------------

        total_stock = _safe_sum(
            db,
            Product,
            "quantity",
        )


        # ----------------------------------------------------
        # MILLING BATCHES
        # ----------------------------------------------------

        milling_runs = _safe_count(
            db,
            MillingBatch,
        )


        # ----------------------------------------------------
        # PACKAGING BATCHES
        # ----------------------------------------------------

        packaging_runs = _safe_count(
            db,
            PackagingBatch,
        )


        # ----------------------------------------------------
        # RETURN DASHBOARD DATA
        # ----------------------------------------------------

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


    except Exception as exc:

        logger.exception(
            "Dashboard KPI generation failed: %s",
            exc,
        )

        # ----------------------------------------------------
        # ALWAYS RETURN A VALID KPI STRUCTURE
        # ----------------------------------------------------

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