"""
Esan ERP
Stock Reservation Service

Production-grade stock reservation for Sales Orders.

Rules:
- Product.quantity = physical on-hand stock.
- Existing SalesOrderItem.reserved_quantity represents
  stock already committed to sales orders.
- Available stock =
      Product.quantity
      - reservations belonging to OTHER sales-order lines.
- Product rows are locked with SELECT FOR UPDATE.
- All requested lines are validated before any reservation
  is committed.
- Any insufficient-stock failure rolls back the entire
  reservation transaction.

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from models import Product, SalesOrder, SalesOrderItem


# ============================================================
# HELPERS
# ============================================================

def _to_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_status(value):
    """Normalize a sales-order status."""
    return str(value or "").strip().lower()


# ============================================================
# AVAILABLE STOCK
# ============================================================

def get_reserved_quantity(
    db,
    product_id,
    exclude_sales_order_id=None,
):
    """
    Return stock already reserved for a product.

    Reservations belonging to the supplied sales order are
    excluded when exclude_sales_order_id is provided.

    This is important when re-reserving an existing order.
    """

    query = (
        db.query(
            func.coalesce(
                func.sum(
                    SalesOrderItem.reserved_quantity
                ),
                0.0,
            )
        )
        .join(
            SalesOrder,
            SalesOrder.id
            == SalesOrderItem.sales_order_id,
        )
        .filter(
            SalesOrderItem.product_id == product_id
        )
    )

    if exclude_sales_order_id is not None:
        query = query.filter(
            SalesOrderItem.sales_order_id
            != exclude_sales_order_id
        )

    return _to_float(
        query.scalar(),
        0.0,
    )


def get_available_stock(
    db,
    product_id,
    exclude_sales_order_id=None,
):
    """
    Return currently available stock.

    Available stock is:

        Product.quantity - committed reservations

    Reservations belonging to the current order may be
    excluded to allow safe re-reservation.
    """

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise ValueError(
            f"Product {product_id} not found."
        )

    on_hand = _to_float(
        product.quantity,
        0.0,
    )

    reserved = get_reserved_quantity(
        db,
        product_id,
        exclude_sales_order_id=exclude_sales_order_id,
    )

    return max(
        0.0,
        on_hand - reserved,
    )


# ============================================================
# LOCK PRODUCT
# ============================================================

def _lock_product(db, product_id):
    """
    Lock a product row for the duration of the transaction.

    On databases supporting row-level locking, SELECT FOR UPDATE
    prevents concurrent reservation transactions from changing
    the same product stock between validation and commit.
    """

    return (
        db.query(Product)
        .filter(Product.id == product_id)
        .with_for_update()
        .first()
    )


# ============================================================
# RESERVE SALES ORDER
# ============================================================

def reserve_sales_order_stock(
    db,
    sales_order_id,
):
    """
    Reserve stock for every line on a Sales Order.

    The operation is atomic:

    1. Load the Sales Order.
    2. Load its lines.
    3. Lock every affected Product row.
    4. Calculate reservations from OTHER orders.
    5. Validate every requested quantity.
    6. Only after every line passes, update reservations.
    7. Commit once.

    If any line does not have enough available stock,
    the entire transaction is rolled back.

    Returns:
        SalesOrder
    """

    sales_order = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.id == sales_order_id
        )
        .first()
    )

    if not sales_order:
        raise ValueError(
            "Sales Order not found."
        )

    status = _normalize_status(
        sales_order.status
    )

    if status in {
        "cancelled",
        "cancelled",
        "completed",
    }:
        raise ValueError(
            f"Sales Order cannot be reserved while "
            f"its status is '{sales_order.status}'."
        )

    items = (
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

    if not items:
        raise ValueError(
            "Cannot reserve stock for a Sales Order "
            "with no items."
        )

    try:

        # ----------------------------------------------------
        # Determine affected products.
        # ----------------------------------------------------

        product_ids = sorted(
            {
                item.product_id
                for item in items
                if item.product_id is not None
            }
        )

        if not product_ids:
            raise ValueError(
                "Sales Order contains no products "
                "eligible for stock reservation."
            )

        # ----------------------------------------------------
        # Lock ALL affected product rows before validation.
        #
        # Sorting IDs gives concurrent transactions a
        # consistent lock order and reduces deadlock risk.
        # ----------------------------------------------------

        locked_products = {}

        for product_id in product_ids:

            product = _lock_product(
                db,
                product_id,
            )

            if not product:
                raise ValueError(
                    f"Product {product_id} not found."
                )

            locked_products[
                product_id
            ] = product

        # ----------------------------------------------------
        # Validate every line before modifying anything.
        #
        # Multiple lines can reference the same product, so
        # validation must account for the requested quantity
        # across the entire order.
        # ----------------------------------------------------

        requested_by_product = {}

        for item in items:

            if item.product_id is None:
                raise ValueError(
                    f"Sales Order Item {item.id} "
                    "has no product."
                )

            quantity = _to_float(
                item.quantity,
                0.0,
            )

            if quantity <= 0:
                raise ValueError(
                    f"Sales Order Item {item.id} "
                    "has an invalid quantity."
                )

            requested_by_product[
                item.product_id
            ] = (
                requested_by_product.get(
                    item.product_id,
                    0.0,
                )
                + quantity
            )

        # ----------------------------------------------------
        # Check available stock for every product.
        # ----------------------------------------------------

        availability = {}

        for product_id, requested_quantity in (
            requested_by_product.items()
        ):

            product = locked_products[
                product_id
            ]

            on_hand = _to_float(
                product.quantity,
                0.0,
            )

            reserved_by_other_orders = (
                get_reserved_quantity(
                    db,
                    product_id,
                    exclude_sales_order_id=sales_order_id,
                )
            )

            available = (
                on_hand
                - reserved_by_other_orders
            )

            availability[
                product_id
            ] = available

            if requested_quantity > available:

                product_name = (
                    product.name
                    or f"Product {product_id}"
                )

                raise ValueError(
                    f"Insufficient stock for "
                    f"{product_name}. "
                    f"Requested: {requested_quantity:g}, "
                    f"Available: {max(available, 0.0):g}."
                )

        # ----------------------------------------------------
        # Every line passed validation.
        #
        # Now update reservations.
        # ----------------------------------------------------

        for item in items:

            quantity = _to_float(
                item.quantity,
                0.0,
            )

            item.reserved_quantity = quantity

            # A newly reserved order has not yet been delivered.
            #
            # Do not overwrite delivered_quantity if the service
            # is being used for re-reservation.
            if item.delivered_quantity is None:
                item.delivered_quantity = 0.0

        # ----------------------------------------------------
        # Flush all changes before committing.
        # ----------------------------------------------------

        db.flush()

        # ----------------------------------------------------
        # Optional order-state transition.
        #
        # Keep Draft/Confirmed workflows intact. If the order
        # is Draft, reservation changes it to Reserved.
        # ----------------------------------------------------

        if status == "draft":
            sales_order.status = "Reserved"

        db.commit()

        db.refresh(
            sales_order
        )

        return sales_order

    except Exception:
        # Critical:
        # If ANY line fails, none of the reservation updates
        # should survive.
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
    Release all reservations belonging to a Sales Order.

    This does NOT reduce Product.quantity because reservations
    are commitments against existing physical stock, not stock
    movements.
    """

    sales_order = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.id == sales_order_id
        )
        .first()
    )

    if not sales_order:
        raise ValueError(
            "Sales Order not found."
        )

    items = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == sales_order_id
        )
        .with_for_update()
        .all()
    )

    try:

        product_ids = sorted(
            {
                item.product_id
                for item in items
                if item.product_id is not None
            }
        )

        # Lock product rows consistently.
        for product_id in product_ids:

            product = _lock_product(
                db,
                product_id,
            )

            if not product:
                raise ValueError(
                    f"Product {product_id} not found."
                )

        for item in items:
            item.reserved_quantity = 0.0

        db.flush()

        if _normalize_status(
            sales_order.status
        ) == "reserved":
            sales_order.status = "Draft"

        db.commit()

        db.refresh(
            sales_order
        )

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

    Useful for the Sales Order UI and warehouse module.
    """

    sales_order = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.id == sales_order_id
        )
        .first()
    )

    if not sales_order:
        raise ValueError(
            "Sales Order not found."
        )

    items = (
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

    result = []

    for item in items:

        product = (
            db.query(Product)
            .filter(
                Product.id == item.product_id
            )
            .first()
        )

        reserved = _to_float(
            item.reserved_quantity,
            0.0,
        )

        delivered = _to_float(
            item.delivered_quantity,
            0.0,
        )

        ordered = _to_float(
            item.quantity,
            0.0,
        )

        result.append(
            {
                "sales_order_item_id": item.id,
                "product_id": item.product_id,
                "product_name": (
                    item.product_name
                    if item.product_name
                    else (
                        product.name
                        if product
                        else "Unknown Product"
                    )
                ),
                "ordered_quantity": ordered,
                "reserved_quantity": reserved,
                "delivered_quantity": delivered,
                "remaining_quantity": max(
                    0.0,
                    ordered - delivered,
                ),
                "reservation_complete": (
                    reserved >= ordered
                ),
            }
        )

    return result