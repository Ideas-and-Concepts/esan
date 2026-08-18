"""
Esan ERP
Dashboard Services

Nile Harvest Foods Ltd.
"""

import logging

from database import SessionLocal


logger = logging.getLogger(__name__)


# ============================================================
# SAFE VALUE HELPERS
# ============================================================

def _number(value, default=0):
    """Return a safe numeric value."""

    try:
        if value is None:
            return default

        return value

    except Exception:
        return default


def _safe_query_count(db, model):
    """
    Safely count records from a SQLAlchemy model.

    Missing/broken tables return 0 instead of crashing
    the Overview Dashboard.
    """

    try:
        return db.query(model).count()

    except Exception as exc:

        logger.warning(
            "Unable to count %s: %s",
            getattr(model, "__name__", "model"),
            exc,
        )

        return 0


def _model(name):
    """
    Safely retrieve a model from models.py.

    Returns None if the model doesn't exist yet.
    """

    try:

        import models

        return getattr(
            models,
            name,
            None,
        )

    except Exception as exc:

        logger.warning(
            "Unable to load model %s: %s",
            name,
            exc,
        )

        return None


# ============================================================
# SALES
# ============================================================

def get_sales_summary():

    db = SessionLocal()

    try:

        SalesOrder = _model("SalesOrder")
        Customer = _model("Customer")
        Invoice = _model("Invoice")
        Payment = _model("Payment")

        orders = (
            _safe_query_count(db, SalesOrder)
            if SalesOrder
            else 0
        )

        customers = (
            _safe_query_count(db, Customer)
            if Customer
            else 0
        )

        invoices = (
            _safe_query_count(db, Invoice)
            if Invoice
            else 0
        )

        payments = (
            _safe_query_count(db, Payment)
            if Payment
            else 0
        )

        return {
            "total": 0,
            "orders": orders,
            "customers": customers,
            "invoices": invoices,
            "payments": payments,
        }

    except Exception as exc:

        logger.exception(
            "Sales dashboard summary failed: %s",
            exc,
        )

        return {
            "total": 0,
            "orders": 0,
            "customers": 0,
            "invoices": 0,
            "payments": 0,
        }

    finally:

        db.close()


# ============================================================
# PROCUREMENT
# ============================================================

def get_procurement_summary():

    db = SessionLocal()

    try:

        Supplier = _model("Supplier")
        PurchaseOrder = _model("PurchaseOrder")
        Purchase = _model("Purchase")

        suppliers = (
            _safe_query_count(db, Supplier)
            if Supplier
            else 0
        )

        purchase_orders = (
            _safe_query_count(db, PurchaseOrder)
            if PurchaseOrder
            else 0
        )

        purchases = (
            _safe_query_count(db, Purchase)
            if Purchase
            else 0
        )

        return {
            "total": 0,
            "suppliers": suppliers,
            "purchase_orders": purchase_orders,
            "purchases": purchases,
        }

    except Exception as exc:

        logger.exception(
            "Procurement dashboard summary failed: %s",
            exc,
        )

        return {
            "total": 0,
            "suppliers": 0,
            "purchase_orders": 0,
            "purchases": 0,
        }

    finally:

        db.close()


# ============================================================
# INVENTORY
# ============================================================

def get_inventory_summary():

    db = SessionLocal()

    try:

        Product = _model("Product")

        products = (
            _safe_query_count(db, Product)
            if Product
            else 0
        )

        return {
            "total": 0,
            "products": products,
            "quantity": 0,
            "low_stock": 0,
        }

    except Exception as exc:

        logger.exception(
            "Inventory dashboard summary failed: %s",
            exc,
        )

        return {
            "total": 0,
            "products": 0,
            "quantity": 0,
            "low_stock": 0,
        }

    finally:

        db.close()


# ============================================================
# PRODUCTION
# ============================================================

def get_production_summary():

    db = SessionLocal()

    try:

        MillingBatch = _model("MillingBatch")
        PackagingBatch = _model("PackagingBatch")

        milling_batches = (
            _safe_query_count(db, MillingBatch)
            if MillingBatch
            else 0
        )

        packaging_batches = (
            _safe_query_count(db, PackagingBatch)
            if PackagingBatch
            else 0
        )

        return {
            "total": 0,
            "milling_batches": milling_batches,
            "packaging_batches": packaging_batches,
            "quantity": 0,
        }

    except Exception as exc:

        logger.exception(
            "Production dashboard summary failed: %s",
            exc,
        )

        return {
            "total": 0,
            "milling_batches": 0,
            "packaging_batches": 0,
            "quantity": 0,
        }

    finally:

        db.close()


# ============================================================
# RECEIVABLES
# ============================================================

def get_receivables_summary():

    db = SessionLocal()

    try:

        Invoice = _model("Invoice")

        invoices = (
            _safe_query_count(db, Invoice)
            if Invoice
            else 0
        )

        return {
            "total": 0,
            "outstanding": 0,
            "invoices": invoices,
            "overdue": 0,
        }

    except Exception as exc:

        logger.exception(
            "Receivables dashboard summary failed: %s",
            exc,
        )

        return {
            "total": 0,
            "outstanding": 0,
            "invoices": 0,
            "overdue": 0,
        }

    finally:

        db.close()


# ============================================================
# ALERTS
# ============================================================

def get_dashboard_alerts():

    alerts = []

    try:

        inventory = get_inventory_summary()

        if inventory.get("low_stock", 0) > 0:

            alerts.append(
                {
                    "level": "warning",
                    "title": "Low Stock",
                    "message": (
                        f"{inventory['low_stock']} "
                        "item(s) are below the stock threshold."
                    ),
                }
            )

    except Exception as exc:

        logger.warning(
            "Unable to generate dashboard alerts: %s",
            exc,
        )

    return alerts


# ============================================================
# RECENT ACTIVITY
# ============================================================

def get_recent_activity():

    """
    Returns recent ERP activity.

    This starts empty until activity/date fields are confirmed
    in the current models.
    """

    try:

        return []

    except Exception as exc:

        logger.warning(
            "Unable to retrieve recent activity: %s",
            exc,
        )

        return []


# ============================================================
# COMPLETE DASHBOARD SUMMARY
# ============================================================

def get_dashboard_summary():

    """
    Return the complete Overview Dashboard structure.

    home.py depends on this exact structure.
    """

    return {
        "sales": get_sales_summary(),

        "procurement": get_procurement_summary(),

        "inventory": get_inventory_summary(),

        "production": get_production_summary(),

        "receivables": get_receivables_summary(),

        "alerts": get_dashboard_alerts(),

        "recent_activity": get_recent_activity(),
    }