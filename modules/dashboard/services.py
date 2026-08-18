"""
Esan ERP
Nile Harvest Foods Ltd.

Dashboard Data Services
Version 1.4.0 Alpha

Provides database-backed summary functions for the
Overview Dashboard.

Design goals:
- Use the current Esan ERP SQLAlchemy structure.
- Fail gracefully when optional models/tables are missing.
- Never allow a dashboard metric to crash the entire ERP.
- Keep database access separate from dashboard presentation.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func

from database import SessionLocal
from models import (
    SalesOrder,
    PurchaseOrder,
    Product,
    StockMovement,
    MillingBatch,
    PackagingBatch,
    Customer,
)

logger = logging.getLogger(__name__)


# ============================================================
# GENERIC HELPERS
# ============================================================

def _safe_float(value):
    """Safely convert a database value to float."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value):
    """Safely convert a database value to integer."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _get_model(model_name):
    """
    Safely retrieve a model from the models module.

    This allows dashboard services to continue working even
    when an optional model has not yet been created.
    """
    try:
        import models

        return getattr(models, model_name, None)

    except Exception as exc:
        logger.warning(
            "Unable to load model %s: %s",
            model_name,
            exc,
        )
        return None


def _has_column(model, column_name):
    """Return True when a SQLAlchemy model has the requested column."""
    try:
        return hasattr(model, column_name)
    except Exception:
        return False


def _query_count(db, model):
    """Safely count rows for a model."""
    try:
        return _safe_int(
            db.query(func.count(model.id)).scalar()
        )
    except Exception as exc:
        logger.warning(
            "Unable to count %s: %s",
            getattr(model, "__name__", "model"),
            exc,
        )
        return 0


def _query_sum(db, model, column_name):
    """Safely sum a numeric model column."""
    if not _has_column(model, column_name):
        return 0.0

    try:
        column = getattr(model, column_name)

        value = (
            db.query(func.coalesce(func.sum(column), 0))
            .scalar()
        )

        return _safe_float(value)

    except Exception as exc:
        logger.warning(
            "Unable to sum %s.%s: %s",
            getattr(model, "__name__", "model"),
            column_name,
            exc,
        )
        return 0.0


def _query_average(db, model, column_name):
    """Safely calculate an average."""
    if not _has_column(model, column_name):
        return 0.0

    try:
        column = getattr(model, column_name)

        value = (
            db.query(func.coalesce(func.avg(column), 0))
            .scalar()
        )

        return _safe_float(value)

    except Exception as exc:
        logger.warning(
            "Unable to average %s.%s: %s",
            getattr(model, "__name__", "model"),
            column_name,
            exc,
        )
        return 0.0


def _safe_date(value):
    """Convert a database date/datetime into an ISO string."""
    if value is None:
        return None

    try:
        if isinstance(value, datetime):
            return value.isoformat()

        return str(value)

    except Exception:
        return None


def _status_count(db, model, status):
    """
    Count records by status when a status column exists.
    """
    if not _has_column(model, "status"):
        return 0

    try:
        return _safe_int(
            db.query(func.count(model.id))
            .filter(
                func.lower(model.status)
                == str(status).lower()
            )
            .scalar()
        )

    except Exception as exc:
        logger.warning(
            "Status count failed for %s/%s: %s",
            getattr(model, "__name__", "model"),
            status,
            exc,
        )
        return 0


def _date_column(model):
    """
    Find the most useful date column available on a model.
    """
    for column_name in (
        "created_at",
        "order_date",
        "purchase_date",
        "date",
        "transaction_date",
        "created",
    ):
        if _has_column(model, column_name):
            return getattr(model, column_name)

    return None


# ============================================================
# SALES SUMMARY
# ============================================================

def get_sales_summary():
    """
    Return sales KPIs for the Overview Dashboard.

    Expected output:
    {
        "total_orders": int,
        "pending_orders": int,
        "completed_orders": int,
        "sales_value": float,
        "average_order_value": float,
    }
    """

    db = SessionLocal()

    try:
        model = SalesOrder or _get_model("SalesOrder")

        if model is None:
            return {
                "total_orders": 0,
                "pending_orders": 0,
                "completed_orders": 0,
                "sales_value": 0.0,
                "average_order_value": 0.0,
            }

        total_orders = _query_count(db, model)

        pending_orders = sum(
            _status_count(db, model, status)
            for status in (
                "pending",
                "draft",
                "confirmed",
                "processing",
            )
        )

        completed_orders = sum(
            _status_count(db, model, status)
            for status in (
                "completed",
                "complete",
                "delivered",
                "closed",
            )
        )

        sales_value = 0.0

        for column_name in (
            "total_amount",
            "grand_total",
            "total",
            "amount",
            "net_total",
        ):
            if _has_column(model, column_name):
                sales_value = _query_sum(
                    db,
                    model,
                    column_name,
                )
                break

        average_order_value = (
            sales_value / total_orders
            if total_orders
            else 0.0
        )

        return {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "sales_value": sales_value,
            "average_order_value": average_order_value,
        }

    except Exception as exc:
        logger.exception(
            "Sales dashboard summary failed: %s",
            exc,
        )

        return {
            "total_orders": 0,
            "pending_orders": 0,
            "completed_orders": 0,
            "sales_value": 0.0,
            "average_order_value": 0.0,
        }

    finally:
        db.close()


# ============================================================
# PROCUREMENT SUMMARY
# ============================================================

def get_procurement_summary():
    """
    Return procurement KPIs.

    Expected output:
    {
        "total_purchase_orders": int,
        "pending_purchase_orders": int,
        "completed_purchase_orders": int,
        "procurement_value": float,
    }
    """

    db = SessionLocal()

    try:
        model = PurchaseOrder or _get_model("PurchaseOrder")

        if model is None:
            return {
                "total_purchase_orders": 0,
                "pending_purchase_orders": 0,
                "completed_purchase_orders": 0,
                "procurement_value": 0.0,
            }

        total_orders = _query_count(db, model)

        pending_orders = sum(
            _status_count(db, model, status)
            for status in (
                "pending",
                "draft",
                "submitted",
                "approved",
                "processing",
            )
        )

        completed_orders = sum(
            _status_count(db, model, status)
            for status in (
                "completed",
                "received",
                "closed",
            )
        )

        procurement_value = 0.0

        for column_name in (
            "total_amount",
            "grand_total",
            "total",
            "amount",
            "net_total",
        ):
            if _has_column(model, column_name):
                procurement_value = _query_sum(
                    db,
                    model,
                    column_name,
                )
                break

        return {
            "total_purchase_orders": total_orders,
            "pending_purchase_orders": pending_orders,
            "completed_purchase_orders": completed_orders,
            "procurement_value": procurement_value,
        }

    except Exception as exc:
        logger.exception(
            "Procurement dashboard summary failed: %s",
            exc,
        )

        return {
            "total_purchase_orders": 0,
            "pending_purchase_orders": 0,
            "completed_purchase_orders": 0,
            "procurement_value": 0.0,
        }

    finally:
        db.close()


# ============================================================
# INVENTORY SUMMARY
# ============================================================

def get_inventory_summary():
    """
    Return warehouse/inventory KPIs.

    The current Product model contains quantity, cost_price,
    and selling_price in the Esan ERP structure.
    """

    db = SessionLocal()

    try:
        model = Product or _get_model("Product")

        if model is None:
            return {
                "product_count": 0,
                "total_quantity": 0.0,
                "inventory_value": 0.0,
                "low_stock_items": 0,
                "out_of_stock_items": 0,
            }

        product_count = _query_count(db, model)

        total_quantity = _query_sum(
            db,
            model,
            "quantity",
        )

        inventory_value = 0.0

        if (
            _has_column(model, "quantity")
            and _has_column(model, "cost_price")
        ):
            try:
                inventory_value = _safe_float(
                    db.query(
                        func.coalesce(
                            func.sum(
                                model.quantity
                                * model.cost_price
                            ),
                            0,
                        )
                    ).scalar()
                )
            except Exception as exc:
                logger.warning(
                    "Inventory valuation failed: %s",
                    exc,
                )

        low_stock_items = 0
        out_of_stock_items = 0

        if _has_column(model, "quantity"):

            try:
                out_of_stock_items = _safe_int(
                    db.query(
                        func.count(model.id)
                    )
                    .filter(
                        model.quantity <= 0
                    )
                    .scalar()
                )
            except Exception as exc:
                logger.warning(
                    "Out-of-stock calculation failed: %s",
                    exc,
                )

            # Use a conservative default threshold.
            try:
                low_stock_items = _safe_int(
                    db.query(
                        func.count(model.id)
                    )
                    .filter(
                        model.quantity > 0,
                        model.quantity <= 10,
                    )
                    .scalar()
                )
            except Exception as exc:
                logger.warning(
                    "Low-stock calculation failed: %s",
                    exc,
                )

        return {
            "product_count": product_count,
            "total_quantity": total_quantity,
            "inventory_value": inventory_value,
            "low_stock_items": low_stock_items,
            "out_of_stock_items": out_of_stock_items,
        }

    except Exception as exc:
        logger.exception(
            "Inventory dashboard summary failed: %s",
            exc,
        )

        return {
            "product_count": 0,
            "total_quantity": 0.0,
            "inventory_value": 0.0,
            "low_stock_items": 0,
            "out_of_stock_items": 0,
        }

    finally:
        db.close()


# ============================================================
# PRODUCTION SUMMARY
# ============================================================

def get_production_summary():
    """
    Return milling and packaging production KPIs.
    """

    db = SessionLocal()

    try:
        milling_model = MillingBatch or _get_model(
            "MillingBatch"
        )

        packaging_model = PackagingBatch or _get_model(
            "PackagingBatch"
        )

        milling_batches = (
            _query_count(db, milling_model)
            if milling_model is not None
            else 0
        )

        packaging_batches = (
            _query_count(db, packaging_model)
            if packaging_model is not None
            else 0
        )

        milling_quantity = 0.0
        packaging_quantity = 0.0

        if milling_model is not None:

            for column_name in (
                "output_quantity",
                "quantity_produced",
                "quantity",
                "output",
            ):
                if _has_column(
                    milling_model,
                    column_name,
                ):
                    milling_quantity = _query_sum(
                        db,
                        milling_model,
                        column_name,
                    )
                    break

        if packaging_model is not None:

            for column_name in (
                "output_quantity",
                "quantity_produced",
                "quantity",
                "output",
                "packages_produced",
            ):
                if _has_column(
                    packaging_model,
                    column_name,
                ):
                    packaging_quantity = _query_sum(
                        db,
                        packaging_model,
                        column_name,
                    )
                    break

        active_milling = 0
        active_packaging = 0

        if milling_model is not None:
            active_milling = sum(
                _status_count(
                    db,
                    milling_model,
                    status,
                )
                for status in (
                    "active",
                    "in_progress",
                    "processing",
                )
            )

        if packaging_model is not None:
            active_packaging = sum(
                _status_count(
                    db,
                    packaging_model,
                    status,
                )
                for status in (
                    "active",
                    "in_progress",
                    "processing",
                )
            )

        return {
            "milling_batches": milling_batches,
            "packaging_batches": packaging_batches,
            "milling_quantity": milling_quantity,
            "packaging_quantity": packaging_quantity,
            "active_milling": active_milling,
            "active_packaging": active_packaging,
        }

    except Exception as exc:
        logger.exception(
            "Production dashboard summary failed: %s",
            exc,
        )

        return {
            "milling_batches": 0,
            "packaging_batches": 0,
            "milling_quantity": 0.0,
            "packaging_quantity": 0.0,
            "active_milling": 0,
            "active_packaging": 0,
        }

    finally:
        db.close()


# ============================================================
# RECEIVABLES SUMMARY
# ============================================================

def get_receivables_summary():
    """
    Return accounts-receivable information.

    Invoice and Payment models are optional at this stage,
    therefore they are discovered dynamically.
    """

    db = SessionLocal()

    try:
        invoice_model = _get_model("Invoice")
        payment_model = _get_model("Payment")

        invoice_total = 0.0
        paid_total = 0.0

        if invoice_model is not None:

            for column_name in (
                "total_amount",
                "grand_total",
                "total",
                "amount",
            ):
                if _has_column(
                    invoice_model,
                    column_name,
                ):
                    invoice_total = _query_sum(
                        db,
                        invoice_model,
                        column_name,
                    )
                    break

        if payment_model is not None:

            for column_name in (
                "amount",
                "paid_amount",
                "payment_amount",
                "total_amount",
            ):
                if _has_column(
                    payment_model,
                    column_name,
                ):
                    paid_total = _query_sum(
                        db,
                        payment_model,
                        column_name,
                    )
                    break

        outstanding = max(
            invoice_total - paid_total,
            0.0,
        )

        outstanding_invoices = 0

        if invoice_model is not None:

            if _has_column(
                invoice_model,
                "status",
            ):

                outstanding_invoices = _safe_int(
                    db.query(
                        func.count(
                            invoice_model.id
                        )
                    )
                    .filter(
                        func.lower(
                            invoice_model.status
                        ).in_(
                            [
                                "unpaid",
                                "partial",
                                "overdue",
                                "pending",
                            ]
                        )
                    )
                    .scalar()
                )

        return {
            "invoice_total": invoice_total,
            "paid_total": paid_total,
            "outstanding": outstanding,
            "outstanding_invoices": outstanding_invoices,
        }

    except Exception as exc:
        logger.exception(
            "Receivables summary failed: %s",
            exc,
        )

        return {
            "invoice_total": 0.0,
            "paid_total": 0.0,
            "outstanding": 0.0,
            "outstanding_invoices": 0,
        }

    finally:
        db.close()


# ============================================================
# DASHBOARD ALERTS
# ============================================================

def get_dashboard_alerts():
    """
    Generate operational alerts for the Overview Dashboard.

    Returns a list of dictionaries:

    {
        "type": "warning",
        "title": "Low Stock",
        "message": "...",
        "count": 3
    }
    """

    alerts = []

    try:
        inventory = get_inventory_summary()

        low_stock = inventory.get(
            "low_stock_items",
            0,
        )

        out_of_stock = inventory.get(
            "out_of_stock_items",
            0,
        )

        if out_of_stock:
            alerts.append(
                {
                    "type": "error",
                    "title": "Out of Stock",
                    "message": (
                        f"{out_of_stock} product(s) "
                        "have no available stock."
                    ),
                    "count": out_of_stock,
                }
            )

        if low_stock:
            alerts.append(
                {
                    "type": "warning",
                    "title": "Low Stock",
                    "message": (
                        f"{low_stock} product(s) "
                        "are below the stock threshold."
                    ),
                    "count": low_stock,
                }
            )

    except Exception as exc:
        logger.warning(
            "Inventory alerts failed: %s",
            exc,
        )

    try:
        sales = get_sales_summary()

        pending_orders = sales.get(
            "pending_orders",
            0,
        )

        if pending_orders:
            alerts.append(
                {
                    "type": "info",
                    "title": "Pending Sales Orders",
                    "message": (
                        f"{pending_orders} sales order(s) "
                        "require processing."
                    ),
                    "count": pending_orders,
                }
            )

    except Exception as exc:
        logger.warning(
            "Sales alerts failed: %s",
            exc,
        )

    try:
        procurement = get_procurement_summary()

        pending_purchase_orders = procurement.get(
            "pending_purchase_orders",
            0,
        )

        if pending_purchase_orders:
            alerts.append(
                {
                    "type": "warning",
                    "title": "Pending Procurement",
                    "message": (
                        f"{pending_purchase_orders} "
                        "purchase order(s) require attention."
                    ),
                    "count": pending_purchase_orders,
                }
            )

    except Exception as exc:
        logger.warning(
            "Procurement alerts failed: %s",
            exc,
        )

    try:
        receivables = get_receivables_summary()

        outstanding = receivables.get(
            "outstanding",
            0.0,
        )

        if outstanding > 0:
            alerts.append(
                {
                    "type": "warning",
                    "title": "Outstanding Receivables",
                    "message": (
                        f"Outstanding customer receivables: "
                        f"{outstanding:,.2f}."
                    ),
                    "count": receivables.get(
                        "outstanding_invoices",
                        0,
                    ),
                }
            )

    except Exception as exc:
        logger.warning(
            "Receivables alerts failed: %s",
            exc,
        )

    return alerts


# ============================================================
# RECENT ACTIVITY
# ============================================================

def get_recent_activity(limit=10):
    """
    Return recent ERP activity.

    Activity is assembled from available models.
    Missing models are simply skipped.

    Returns:
    [
        {
            "module": "Sales",
            "action": "Sales Order",
            "record_id": 12,
            "date": "...",
            "status": "Pending"
        }
    ]
    """

    db = SessionLocal()

    activities = []

    try:

        sources = [
            (
                SalesOrder or _get_model("SalesOrder"),
                "Sales",
                "Sales Order",
            ),
            (
                PurchaseOrder or _get_model("PurchaseOrder"),
                "Procurement",
                "Purchase Order",
            ),
            (
                _get_model("Invoice"),
                "Finance",
                "Invoice",
            ),
            (
                _get_model("Payment"),
                "Finance",
                "Payment",
            ),
            (
                MillingBatch or _get_model("MillingBatch"),
                "Production",
                "Milling Batch",
            ),
            (
                PackagingBatch
                or _get_model("PackagingBatch"),
                "Production",
                "Packaging Batch",
            ),
            (
                StockMovement
                or _get_model("StockMovement"),
                "Warehouse",
                "Stock Movement",
            ),
        ]

        for model, module_name, action_name in sources:

            if model is None:
                continue

            date_column = _date_column(model)

            try:

                query = db.query(model)

                if date_column is not None:
                    query = query.order_by(
                        date_column.desc()
                    )

                else:
                    query = query.order_by(
                        model.id.desc()
                    )

                rows = query.limit(limit).all()

            except Exception as exc:

                logger.warning(
                    "Unable to retrieve recent %s activity: %s",
                    action_name,
                    exc,
                )

                continue

            for row in rows:

                record_id = getattr(
                    row,
                    "id",
                    None,
                )

                status = getattr(
                    row,
                    "status",
                    None,
                )

                activity_date = (
                    getattr(
                        row,
                        date_column.key,
                        None,
                    )
                    if date_column is not None
                    else None
                )

                activities.append(
                    {
                        "module": module_name,
                        "action": action_name,
                        "record_id": record_id,
                        "date": _safe_date(
                            activity_date
                        ),
                        "status": status,
                    }
                )

        # Newest activity first.
        activities.sort(
            key=lambda item: (
                item.get("date") or ""
            ),
            reverse=True,
        )

        return activities[:limit]

    except Exception as exc:

        logger.exception(
            "Recent activity retrieval failed: %s",
            exc,
        )

        return []

    finally:
        db.close()


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

def get_dashboard_summary():
    """
    Return the complete Overview Dashboard data package.

    This is the main service consumed by:
        modules.dashboard.home

    The function deliberately isolates failures so that one
    unavailable module/table does not break the Overview page.
    """

    summary = {
        "sales": {},
        "procurement": {},
        "inventory": {},
        "production": {},
        "receivables": {},
        "alerts": [],
        "recent_activity": [],
        "generated_at": datetime.utcnow().isoformat(),
    }

    try:
        summary["sales"] = get_sales_summary()
    except Exception as exc:
        logger.exception(
            "Unable to load sales summary: %s",
            exc,
        )

    try:
        summary["procurement"] = get_procurement_summary()
    except Exception as exc:
        logger.exception(
            "Unable to load procurement summary: %s",
            exc,
        )

    try:
        summary["inventory"] = get_inventory_summary()
    except Exception as exc:
        logger.exception(
            "Unable to load inventory summary: %s",
            exc,
        )

    try:
        summary["production"] = get_production_summary()
    except Exception as exc:
        logger.exception(
            "Unable to load production summary: %s",
            exc,
        )

    try:
        summary["receivables"] = get_receivables_summary()
    except Exception as exc:
        logger.exception(
            "Unable to load receivables summary: %s",
            exc,
        )

    try:
        summary["alerts"] = get_dashboard_alerts()
    except Exception as exc:
        logger.exception(
            "Unable to load dashboard alerts: %s",
            exc,
        )

    try:
        summary["recent_activity"] = get_recent_activity()
    except Exception as exc:
        logger.exception(
            "Unable to load recent activity: %s",
            exc,
        )

    return summary