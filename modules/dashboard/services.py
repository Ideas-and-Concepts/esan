"""
Esan ERP
Dashboard Services

Nile Harvest Foods Ltd.

Provides safe, database-backed summary services for the
Esan ERP Overview Dashboard.

Sections:
- Sales
- Procurement
- Inventory
- Production
- Receivables
- Alerts
- Recent Activity

Design principle:
The dashboard must remain usable even when individual ERP
modules, models, or database tables have not yet been created.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from database import SessionLocal


logger = logging.getLogger(__name__)


# ============================================================
# SAFE DEFAULT SCHEMAS
# ============================================================

def _sales_default() -> Dict[str, Any]:
    return {
        "total_sales": 0.0,
        "sales_today": 0.0,
        "sales_this_month": 0.0,
        "orders_count": 0,
        "orders_today": 0,
        "average_order_value": 0.0,
    }


def _procurement_default() -> Dict[str, Any]:
    return {
        "total_procurement": 0.0,
        "procurement_today": 0.0,
        "procurement_this_month": 0.0,
        "purchase_orders_count": 0,
        "pending_purchase_orders": 0,
    }


def _inventory_default() -> Dict[str, Any]:
    return {
        "total_items": 0,
        "total_stock_quantity": 0.0,
        "inventory_value": 0.0,
        "low_stock_items": 0,
        "out_of_stock_items": 0,
    }


def _production_default() -> Dict[str, Any]:
    return {
        "milling_batches": 0,
        "packaging_batches": 0,
        "production_quantity": 0.0,
        "completed_batches": 0,
        "pending_batches": 0,
    }


def _receivables_default() -> Dict[str, Any]:
    return {
        "total_receivables": 0.0,
        "overdue_receivables": 0.0,
        "due_today": 0.0,
        "customers_with_balance": 0,
        "overdue_invoices": 0,
    }


def _alerts_default() -> List[Dict[str, Any]]:
    return []


def _recent_activity_default() -> List[Dict[str, Any]]:
    return []


# ============================================================
# SAFE HELPERS
# ============================================================

def _safe_float(value: Any) -> float:
    """Convert a value to float without raising an exception."""

    try:
        if value is None:
            return 0.0

        return float(value)

    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any) -> int:
    """Convert a value to int without raising an exception."""

    try:
        if value is None:
            return 0

        return int(value)

    except (TypeError, ValueError):
        return 0


def _safe_count(query: Any) -> int:
    """Safely execute a SQLAlchemy count query."""

    try:
        return _safe_int(query.count())

    except Exception as exc:
        logger.debug(
            "Safe count failed: %s",
            exc,
        )
        return 0


def _model_exists(model_name: str) -> Any:
    """
    Safely locate a model.

    Returns:
        Model class when available.
        None when unavailable.
    """

    try:
        import models

        return getattr(
            models,
            model_name,
            None,
        )

    except Exception as exc:
        logger.debug(
            "Unable to inspect models for %s: %s",
            model_name,
            exc,
        )

        return None


def _column_exists(model: Any, column_name: str) -> bool:
    """Check whether a SQLAlchemy model contains a column."""

    try:
        return hasattr(
            model,
            column_name,
        )

    except Exception:
        return False


def _safe_sum(
    db: Any,
    model: Any,
    column_name: str,
) -> float:
    """
    Safely calculate the sum of a model column.

    Returns zero if the model, column, table, or query is
    unavailable.
    """

    try:

        if model is None:
            return 0.0

        if not _column_exists(
            model,
            column_name,
        ):
            return 0.0

        column = getattr(
            model,
            column_name,
        )

        result = (
            db.query(column)
            .all()
        )

        total = 0.0

        for row in result:

            if not row:
                continue

            total += _safe_float(
                row[0]
            )

        return total

    except Exception as exc:

        logger.debug(
            "Safe sum failed for %s.%s: %s",
            getattr(
                model,
                "__name__",
                "UnknownModel",
            ),
            column_name,
            exc,
        )

        return 0.0


def _safe_query_count(
    db: Any,
    model: Any,
) -> int:
    """Safely count rows in a model."""

    try:

        if model is None:
            return 0

        return _safe_int(
            db.query(model).count()
        )

    except Exception as exc:

        logger.debug(
            "Safe model count failed: %s",
            exc,
        )

        return 0


def _safe_session():
    """
    Create a database session safely.

    Returns None if the database session cannot be created.
    """

    try:
        return SessionLocal()

    except Exception as exc:

        logger.warning(
            "Unable to create dashboard database session: %s",
            exc,
        )

        return None


# ============================================================
# SALES SUMMARY
# ============================================================

def get_sales_summary() -> Dict[str, Any]:
    """
    Return the sales section using the canonical dashboard schema.
    """

    result = _sales_default()

    db = _safe_session()

    if db is None:
        return result

    try:

        SalesOrder = _model_exists(
            "SalesOrder"
        )

        if SalesOrder is None:
            return result

        result["orders_count"] = (
            _safe_query_count(
                db,
                SalesOrder,
            )
        )

        result["total_sales"] = (
            _safe_sum(
                db,
                SalesOrder,
                "total_amount",
            )
        )

        result["average_order_value"] = (
            result["total_sales"]
            / result["orders_count"]
            if result["orders_count"] > 0
            else 0.0
        )

        return result

    except Exception as exc:

        logger.warning(
            "Sales dashboard summary failed: %s",
            exc,
        )

        return result

    finally:

        try:
            db.close()
        except Exception:
            pass


# ============================================================
# PROCUREMENT SUMMARY
# ============================================================

def get_procurement_summary() -> Dict[str, Any]:
    """
    Return the procurement section using the canonical schema.
    """

    result = _procurement_default()

    db = _safe_session()

    if db is None:
        return result

    try:

        PurchaseOrder = _model_exists(
            "PurchaseOrder"
        )

        if PurchaseOrder is None:
            return result

        result["purchase_orders_count"] = (
            _safe_query_count(
                db,
                PurchaseOrder,
            )
        )

        result["total_procurement"] = (
            _safe_sum(
                db,
                PurchaseOrder,
                "total_amount",
            )
        )

        return result

    except Exception as exc:

        logger.warning(
            "Procurement dashboard summary failed: %s",
            exc,
        )

        return result

    finally:

        try:
            db.close()
        except Exception:
            pass


# ============================================================
# INVENTORY SUMMARY
# ============================================================

def get_inventory_summary() -> Dict[str, Any]:
    """
    Return the inventory section using the canonical schema.
    """

    result = _inventory_default()

    db = _safe_session()

    if db is None:
        return result

    try:

        Product = _model_exists(
            "Product"
        )

        if Product is None:
            return result

        result["total_items"] = (
            _safe_query_count(
                db,
                Product,
            )
        )

        result["total_stock_quantity"] = (
            _safe_sum(
                db,
                Product,
                "quantity",
            )
        )

        result["inventory_value"] = (
            _safe_sum(
                db,
                Product,
                "inventory_value",
            )
        )

        return result

    except Exception as exc:

        logger.warning(
            "Inventory dashboard summary failed: %s",
            exc,
        )

        return result

    finally:

        try:
            db.close()
        except Exception:
            pass


# ============================================================
# PRODUCTION SUMMARY
# ============================================================

def get_production_summary() -> Dict[str, Any]:
    """
    Return milling and packaging production statistics.
    """

    result = _production_default()

    db = _safe_session()

    if db is None:
        return result

    try:

        MillingBatch = _model_exists(
            "MillingBatch"
        )

        PackagingBatch = _model_exists(
            "PackagingBatch"
        )

        if MillingBatch is not None:

            result["milling_batches"] = (
                _safe_query_count(
                    db,
                    MillingBatch,
                )
            )

            result["production_quantity"] += (
                _safe_sum(
                    db,
                    MillingBatch,
                    "quantity",
                )
            )

        if PackagingBatch is not None:

            result["packaging_batches"] = (
                _safe_query_count(
                    db,
                    PackagingBatch,
                )
            )

            result["production_quantity"] += (
                _safe_sum(
                    db,
                    PackagingBatch,
                    "quantity",
                )
            )

        result["completed_batches"] = 0
        result["pending_batches"] = 0

        return result

    except Exception as exc:

        logger.warning(
            "Production dashboard summary failed: %s",
            exc,
        )

        return result

    finally:

        try:
            db.close()
        except Exception:
            pass


# ============================================================
# RECEIVABLES SUMMARY
# ============================================================

def get_receivables_summary() -> Dict[str, Any]:
    """
    Return accounts-receivable information.

    The service remains safe when invoice/payment models are
    not yet available.
    """

    result = _receivables_default()

    db = _safe_session()

    if db is None:
        return result

    try:

        Invoice = _model_exists(
            "Invoice"
        )

        Payment = _model_exists(
            "Payment"
        )

        if Invoice is None:
            return result

        invoice_total = _safe_sum(
            db,
            Invoice,
            "total_amount",
        )

        payment_total = 0.0

        if Payment is not None:

            payment_total = _safe_sum(
                db,
                Payment,
                "amount",
            )

        result["total_receivables"] = max(
            invoice_total - payment_total,
            0.0,
        )

        return result

    except Exception as exc:

        logger.warning(
            "Receivables dashboard summary failed: %s",
            exc,
        )

        return result

    finally:

        try:
            db.close()
        except Exception:
            pass


# ============================================================
# DASHBOARD ALERTS
# ============================================================

def get_dashboard_alerts() -> List[Dict[str, Any]]:
    """
    Return dashboard alerts.

    Canonical alert item structure:

        {
            "type": str,
            "title": str,
            "message": str,
            "severity": str
        }

    Missing tables produce an empty list.
    """

    alerts: List[Dict[str, Any]] = []

    db = _safe_session()

    if db is None:
        return alerts

    try:

        Product = _model_exists(
            "Product"
        )

        if Product is not None:

            if _column_exists(
                Product,
                "quantity",
            ):

                try:

                    products = (
                        db.query(Product)
                        .all()
                    )

                    for product in products:

                        quantity = _safe_float(
                            getattr(
                                product,
                                "quantity",
                                0,
                            )
                        )

                        if quantity <= 0:

                            product_name = (
                                getattr(
                                    product,
                                    "name",
                                    "Unknown product",
                                )
                            )

                            alerts.append(
                                {
                                    "type": "inventory",
                                    "title": "Out of stock",
                                    "message": (
                                        f"{product_name} "
                                        "is out of stock."
                                    ),
                                    "severity": "critical",
                                }
                            )

                        elif quantity <= 10:

                            product_name = (
                                getattr(
                                    product,
                                    "name",
                                    "Unknown product",
                                )
                            )

                            alerts.append(
                                {
                                    "type": "inventory",
                                    "title": "Low stock",
                                    "message": (
                                        f"{product_name} "
                                        "has low stock."
                                    ),
                                    "severity": "warning",
                                }
                            )

                except Exception as exc:

                    logger.debug(
                        "Inventory alert query failed: %s",
                        exc,
                    )

        return alerts

    except Exception as exc:

        logger.warning(
            "Dashboard alerts failed: %s",
            exc,
        )

        return []

    finally:

        try:
            db.close()
        except Exception:
            pass


# ============================================================
# RECENT ACTIVITY
# ============================================================

def get_recent_activity() -> List[Dict[str, Any]]:
    """
    Return recent ERP activity.

    Canonical item structure:

        {
            "type": str,
            "title": str,
            "description": str,
            "timestamp": Any
        }

    Missing activity models return an empty list.
    """

    activity: List[Dict[str, Any]] = []

    db = _safe_session()

    if db is None:
        return activity

    try:

        model_candidates = [
            (
                "SalesOrder",
                "Sales Order",
                "sales",
            ),
            (
                "PurchaseOrder",
                "Purchase Order",
                "procurement",
            ),
            (
                "Delivery",
                "Delivery",
                "delivery",
            ),
            (
                "Invoice",
                "Invoice",
                "finance",
            ),
            (
                "Payment",
                "Payment",
                "finance",
            ),
        ]

        for (
            model_name,
            display_name,
            activity_type,
        ) in model_candidates:

            if len(activity) >= 10:
                break

            model = _model_exists(
                model_name
            )

            if model is None:
                continue

            try:

                query = db.query(model)

                timestamp_column = None

                for candidate in [
                    "created_at",
                    "date",
                    "order_date",
                    "invoice_date",
                    "payment_date",
                ]:

                    if _column_exists(
                        model,
                        candidate,
                    ):

                        timestamp_column = getattr(
                            model,
                            candidate,
                        )

                        break

                if timestamp_column is not None:

                    query = query.order_by(
                        timestamp_column.desc()
                    )

                rows = query.limit(10).all()

                for row in rows:

                    timestamp = None

                    for candidate in [
                        "created_at",
                        "date",
                        "order_date",
                        "invoice_date",
                        "payment_date",
                    ]:

                        value = getattr(
                            row,
                            candidate,
                            None,
                        )

                        if value is not None:
                            timestamp = value
                            break

                    row_id = getattr(
                        row,
                        "id",
                        None,
                    )

                    activity.append(
                        {
                            "type": activity_type,
                            "title": (
                                f"{display_name} "
                                f"#{row_id}"
                                if row_id is not None
                                else display_name
                            ),
                            "description": (
                                f"{display_name} "
                                "record created."
                            ),
                            "timestamp": timestamp,
                        }
                    )

                    if len(activity) >= 10:
                        break

            except Exception as exc:

                logger.debug(
                    "Recent activity failed for %s: %s",
                    model_name,
                    exc,
                )

        return activity

    except Exception as exc:

        logger.warning(
            "Recent activity failed: %s",
            exc,
        )

        return []

    finally:

        try:
            db.close()
        except Exception:
            pass


# ============================================================
# COMPLETE DASHBOARD SUMMARY
# ============================================================

def get_dashboard_summary() -> Dict[str, Any]:
    """
    Return the complete Overview Dashboard structure.

    This is the primary service consumed by
    modules/dashboard/home.py.

    Guaranteed top-level structure:

        {
            "sales": {...},
            "procurement": {...},
            "inventory": {...},
            "production": {...},
            "receivables": {...},
            "alerts": [...],
            "recent_activity": [...]
        }
    """

    summary = {
        "sales": _sales_default(),
        "procurement": _procurement_default(),
        "inventory": _inventory_default(),
        "production": _production_default(),
        "receivables": _receivables_default(),
        "alerts": [],
        "recent_activity": [],
    }

    # --------------------------------------------------------
    # Individual services are deliberately isolated.
    # One broken module must not destroy the dashboard.
    # --------------------------------------------------------

    try:
        summary["sales"] = get_sales_summary()
    except Exception as exc:
        logger.exception(
            "Unable to load sales summary: %s",
            exc,
        )

    try:
        summary["procurement"] = (
            get_procurement_summary()
        )
    except Exception as exc:
        logger.exception(
            "Unable to load procurement summary: %s",
            exc,
        )

    try:
        summary["inventory"] = (
            get_inventory_summary()
        )
    except Exception as exc:
        logger.exception(
            "Unable to load inventory summary: %s",
            exc,
        )

    try:
        summary["production"] = (
            get_production_summary()
        )
    except Exception as exc:
        logger.exception(
            "Unable to load production summary: %s",
            exc,
        )

    try:
        summary["receivables"] = (
            get_receivables_summary()
        )
    except Exception as exc:
        logger.exception(
            "Unable to load receivables summary: %s",
            exc,
        )

    try:
        summary["alerts"] = (
            get_dashboard_alerts()
        )
    except Exception as exc:
        logger.exception(
            "Unable to load dashboard alerts: %s",
            exc,
        )

    try:
        summary["recent_activity"] = (
            get_recent_activity()
        )
    except Exception as exc:
        logger.exception(
            "Unable to load recent activity: %s",
            exc,
        )

    # --------------------------------------------------------
    # Final schema enforcement
    # --------------------------------------------------------

    if not isinstance(
        summary.get("sales"),
        dict,
    ):
        summary["sales"] = _sales_default()

    if not isinstance(
        summary.get("procurement"),
        dict,
    ):
        summary["procurement"] = (
            _procurement_default()
        )

    if not isinstance(
        summary.get("inventory"),
        dict,
    ):
        summary["inventory"] = (
            _inventory_default()
        )

    if not isinstance(
        summary.get("production"),
        dict,
    ):
        summary["production"] = (
            _production_default()
        )

    if not isinstance(
        summary.get("receivables"),
        dict,
    ):
        summary["receivables"] = (
            _receivables_default()
        )

    if not isinstance(
        summary.get("alerts"),
        list,
    ):
        summary["alerts"] = []

    if not isinstance(
        summary.get("recent_activity"),
        list,
    ):
        summary["recent_activity"] = []

    return summary