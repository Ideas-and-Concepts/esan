"""
Esan ERP
Stock Reservation Service

Reserves inventory for Sales Orders atomically.

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

from sqlalchemy.exc import SQLAlchemyError

from models import (
    Product,
    SalesOrder,
    SalesOrderItem,
)


# ============================================================
# HELPERS
# ============================================================

def _to_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _status(value):
    """Normalize a status value."""
    return str(value or "").strip().lower()


# ============================================================
# GET SALES ORDER
# ============================================================

def get_sales_order(db, sales_order_id):
    """Return a Sales Order by ID."""

    return (
        db.query(SalesOrder)
        .filter(
            SalesOrder.id == sales_order_id
        )
        .first()
    )


# ============================================================
# GET SALES ORDER ITEMS
# ============================================================

def get_sales_order_items(db, sales_order_id):
    """Return Sales Order items in stable order."""

    return (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == sales_order_id
        )
        .order_by(
            SalesOrderItem.id.asc()
        )
        .all()
    )


# ============================================================
# AVAILABLE STOCK
# ============================================================

def get_available_stock(product):
    """
    Return stock available for new reservations.

    Product.quantity represents physical/on-hand stock.

    Product does not currently contain a global
    reserved_quantity column, so existing reservations are
    calculated from SalesOrderItem.reserved_quantity.
    """

    quantity = _to_float(
        getattr(product, "quantity", 0.0)
    )

    return quantity


# ============================================================
# RESERVE SALES ORDER
# ============================================================

def reserve_sales_order_stock(
    db,
    sales_order_id,
):
    """
    Reserve stock for every item on a Sales Order.

    The operation is atomic:

        - Product rows are locked with FOR UPDATE.
        - Every line is validated first.
        - No line is permanently changed until every
          line has sufficient stock.
        - Any failure rolls back the entire transaction.

    Returns:
        SalesOrder

    Raises:
        ValueError:
            If the order does not exist, has no items,
            has invalid quantities, or insufficient stock.

        SQLAlchemyError:
            Database errors are rolled back and re-raised.
    """

    sales_order = get_sales_order(
        db,
        sales_order_id,
    )

    if not sales_order:
        raise ValueError(
            "Sales Order not found."
        )

    status = _status(
        getattr(
            sales_order,
            "status",
            None,
        )
    )

    if status in {
        "cancelled",
        "completed",
        "delivered",
    }:
        raise ValueError(
            "Stock cannot be reserved for a "
            f"Sales Order with status '{sales_order.status}'."
        )

    items = get_sales_order_items(
        db,
        sales_order_id,
    )

    if not items:
        raise ValueError(
            "Cannot reserve stock for a Sales Order "
            "with no items."
        )

    try:

        # ----------------------------------------------------
        # Phase 1
        # Lock and validate every product.
        #
        # Nothing is modified yet.
        # ----------------------------------------------------

        locked_products = {}

        for item in items:

            product_id = item.product_id

            if product_id is None:
                raise ValueError(
                    f"Sales Order Item {item.id} "
                    "has no product."
                )

            quantity = _to_float(
                item.quantity
            )

            if quantity <= 0:
                raise ValueError(
                    f"Sales Order Item {item.id} "
                    "has an invalid quantity."
                )

            # Lock the Product row.
            product = (
                db.query(Product)
                .filter(
                    Product.id == product_id
                )
                .with_for_update()
                .first()
            )

            if not product:
                raise ValueError(
                    f"Product {product_id} "
                    "was not found."
                )

            locked_products[
                product_id
            ] = product

        # ----------------------------------------------------
        # Phase 2
        # Validate all requested quantities.
        # ----------------------------------------------------

        reservations = []

        for item in items:

            product = locked_products[
                item.product_id
            ]

            requested = _to_float(
                item.quantity
            )

            already_reserved = _to_float(
                getattr(
                    item,
                    "reserved_quantity",
                    0.0,
                )
            )

            remaining_to_reserve = (
                requested
                - already_reserved
            )

            # Already completely reserved.
            if remaining_to_reserve <= 0:
                reservations.append(
                    {
                        "item": item,
                        "product": product,
                        "quantity": 0.0,
                    }
                )
                continue

            available = get_available_stock(
                product
            )

            if remaining_to_reserve > available:
                raise ValueError(
                    f"Insufficient stock for "
                    f"'{product.name}'. "
                    f"Required: {remaining_to_reserve:g}, "
                    f"Available: {available:g}."
                )

            reservations.append(
                {
                    "item": item,
                    "product": product,
                    "quantity": remaining_to_reserve,
                }
            )

        # ----------------------------------------------------
        # Phase 3
        # Apply reservations only after every line passed.
        # ----------------------------------------------------

        for reservation in reservations:

            item = reservation["item"]
            quantity = reservation["quantity"]

            if quantity <= 0:
                continue

            current_reserved = _to_float(
                getattr(
                    item,
                    "reserved_quantity",
                    0.0,
                )
            )

            item.reserved_quantity = (
                current_reserved
                + quantity
            )

        db.flush()

        # ----------------------------------------------------
        # Phase 4
        # Commit the complete reservation atomically.
        # ----------------------------------------------------

        db.commit()

        db.refresh(sales_order)

        return sales_order

    except Exception:
        # Any failure means no partial reservation survives.
        db.rollback()
        raise


# ============================================================
# RELEASE RESERVATION
# ============================================================

def release_sales_order_stock(
    db,
    sales_order_id,
):
    """
    Release reservations belonging to a Sales Order.

    This does not change physical stock.

    It simply reduces each SalesOrderItem's
    reserved_quantity back toward zero.
    """

    sales_order = get_sales_order(
        db,
        sales_order_id,
    )

    if not sales_order:
        raise ValueError(
            "Sales Order not found."
        )

    items = get_sales_order_items(
        db,
        sales_order_id,
    )

    try:

        for item in items:

            reserved = _to_float(
                getattr(
                    item,
                    "reserved_quantity",
                    0.0,
                )
            )

            if reserved > 0:
                item.reserved_quantity = 0.0

        db.commit()

        db.refresh(sales_order)

        return sales_order

    except Exception:
        db.rollback()
        raise


# ============================================================
# RESERVATION SUMMARY
# ============================================================

def get_sales_order_reservation_summary(
    db,
    sales_order_id,
):
    """
    Return reservation information for a Sales Order.
    """

    items = get_sales_order_items(
        db,
        sales_order_id,
    )

    result = []

    for item in items:

        product = (
            db.query(Product)
            .filter(
                Product.id == item.product_id
            )
            .first()
        )

        quantity = _to_float(
            item.quantity
        )

        reserved = _to_float(
            getattr(
                item,
                "reserved_quantity",
                0.0,
            )
        )

        result.append(
            {
                "item_id": item.id,
                "product_id": item.product_id,
                "product_name": (
                    item.product_name
                    if getattr(
                        item,
                        "product_name",
                        None,
                    )
                    else (
                        product.name
                        if product
                        else "Unknown Product"
                    )
                ),
                "ordered_quantity": quantity,
                "reserved_quantity": reserved,
                "remaining_quantity": max(
                    quantity - reserved,
                    0.0,
                ),
            }
        )

    return result