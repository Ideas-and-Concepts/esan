"""
Esan ERP
Sales Service

Sales Orders, Sales Order Items and Stock Reservation.

Nile Harvest Foods Ltd.
"""

from datetime import datetime

from models import (
    Customer,
    Product,
    SalesOrder,
    SalesOrderItem,
)


# ==========================================================
# GENERIC HELPERS
# ==========================================================

def _get(obj, field, default=None):
    """Safely read a model attribute."""
    return getattr(obj, field, default)


def _set(obj, field, value):
    """Safely set a model attribute when the field exists."""
    if hasattr(obj, field):
        setattr(obj, field, value)
        return True
    return False


def _number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _status(order):
    return _get(order, "status", "Draft") or "Draft"


def _is_draft(order):
    return _status(order).lower() == "draft"


def _is_confirmed(order):
    return _status(order).lower() == "confirmed"


# ==========================================================
# SALES ORDER QUERIES
# ==========================================================

def get_all_sales_orders(db):
    """Return all sales orders, newest first."""

    return (
        db.query(SalesOrder)
        .order_by(SalesOrder.id.desc())
        .all()
    )


def get_sales_order(db, order_id):
    """Return one sales order."""

    return (
        db.query(SalesOrder)
        .filter(SalesOrder.id == order_id)
        .first()
    )


def get_sales_order_items(db, order_id):
    """Return all items belonging to a sales order."""

    return (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id == order_id
        )
        .all()
    )


def get_sales_order_item(db, item_id):
    """Return one sales order item."""

    return (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.id == item_id
        )
        .first()
    )


# ==========================================================
# CUSTOMER
# ==========================================================

def get_customers(db):
    """Return customers for order forms."""

    return (
        db.query(Customer)
        .order_by(Customer.name)
        .all()
    )


# ==========================================================
# CREATE SALES ORDER
# ==========================================================

def create_sales_order(
    db,
    customer_id,
    quotation_id=None,
    order_date=None,
    notes=None,
):
    """
    Create a Draft Sales Order.
    """

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        raise ValueError(
            "Customer not found."
        )

    if quotation_id is not None:

        # Only validate if the SalesOrder model
        # supports quotation_id.
        if hasattr(SalesOrder, "quotation_id"):

            from models import Quotation

            quotation = (
                db.query(Quotation)
                .filter(
                    Quotation.id == quotation_id
                )
                .first()
            )

            if not quotation:
                raise ValueError(
                    "Quotation not found."
                )

    order = SalesOrder(
        customer_id=customer_id
    )

    _set(
        order,
        "quotation_id",
        quotation_id,
    )

    _set(
        order,
        "order_date",
        order_date or datetime.utcnow(),
    )

    _set(
        order,
        "notes",
        notes,
    )

    _set(
        order,
        "status",
        "Draft",
    )

    _set(
        order,
        "total_amount",
        0,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


# ==========================================================
# UPDATE SALES ORDER
# ==========================================================

def update_sales_order(
    db,
    order_id,
    customer_id=None,
    order_date=None,
    notes=None,
):
    """
    Edit a Draft Sales Order.
    """

    order = get_sales_order(
        db,
        order_id,
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    if not _is_draft(order):
        raise ValueError(
            "Only Draft Sales Orders can be edited."
        )

    if customer_id is not None:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
            .first()
        )

        if not customer:
            raise ValueError(
                "Customer not found."
            )

        order.customer_id = customer_id

    if order_date is not None:
        _set(
            order,
            "order_date",
            order_date,
        )

    if notes is not None:
        _set(
            order,
            "notes",
            notes,
        )

    db.commit()
    db.refresh(order)

    return order


# ==========================================================
# ADD ORDER ITEM
# ==========================================================

def add_sales_order_item(
    db,
    order_id,
    product_id,
    quantity,
    unit_price=None,
):
    """
    Add an item to a Draft Sales Order.
    """

    order = get_sales_order(
        db,
        order_id,
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    if not _is_draft(order):
        raise ValueError(
            "Items can only be added to Draft Sales Orders."
        )

    product = (
        db.query(Product)
        .filter(
            Product.id == product_id
        )
        .first()
    )

    if not product:
        raise ValueError(
            "Product not found."
        )

    quantity = _number(quantity)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    if unit_price is None:
        unit_price = _number(
            _get(
                product,
                "selling_price",
                0,
            )
        )

    unit_price = _number(unit_price)

    if unit_price < 0:
        raise ValueError(
            "Unit price cannot be negative."
        )

    item = SalesOrderItem(
        sales_order_id=order_id,
        product_id=product_id,
        quantity=quantity,
    )

    _set(
        item,
        "unit_price",
        unit_price,
    )

    _set(
        item,
        "price",
        unit_price,
    )

    _set(
        item,
        "total",
        quantity * unit_price,
    )

    _set(
        item,
        "total_price",
        quantity * unit_price,
    )

    db.add(item)

    db.flush()

    recalculate_sales_order_total(
        db,
        order_id,
        commit=False,
    )

    db.commit()
    db.refresh(item)

    return item


# ==========================================================
# UPDATE ORDER ITEM
# ==========================================================

def update_sales_order_item(
    db,
    item_id,
    quantity,
    unit_price=None,
):
    """Edit an item on a Draft Sales Order."""

    item = get_sales_order_item(
        db,
        item_id,
    )

    if not item:
        raise ValueError(
            "Sales Order item not found."
        )

    order = get_sales_order(
        db,
        item.sales_order_id,
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    if not _is_draft(order):
        raise ValueError(
            "Only Draft Sales Orders can be edited."
        )

    quantity = _number(quantity)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    if unit_price is None:
        unit_price = _number(
            _get(
                item,
                "unit_price",
                _get(item, "price", 0),
            )
        )

    unit_price = _number(unit_price)

    item.quantity = quantity

    _set(
        item,
        "unit_price",
        unit_price,
    )

    _set(
        item,
        "price",
        unit_price,
    )

    total = quantity * unit_price

    _set(
        item,
        "total",
        total,
    )

    _set(
        item,
        "total_price",
        total,
    )

    recalculate_sales_order_total(
        db,
        order.id,
        commit=False,
    )

    db.commit()
    db.refresh(item)

    return item


# ==========================================================
# DELETE ORDER ITEM
# ==========================================================

def delete_sales_order_item(
    db,
    item_id,
):
    """Delete an item from a Draft Sales Order."""

    item = get_sales_order_item(
        db,
        item_id,
    )

    if not item:
        raise ValueError(
            "Sales Order item not found."
        )

    order = get_sales_order(
        db,
        item.sales_order_id,
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    if not _is_draft(order):
        raise ValueError(
            "Only Draft Sales Orders can be edited."
        )

    order_id = order.id

    db.delete(item)
    db.flush()

    recalculate_sales_order_total(
        db,
        order_id,
        commit=False,
    )

    db.commit()

    return True


# ==========================================================
# CALCULATE TOTAL
# ==========================================================

def calculate_sales_order_total(
    db,
    order_id,
):
    """Calculate the order total from its items."""

    items = get_sales_order_items(
        db,
        order_id,
    )

    total = 0.0

    for item in items:

        quantity = _number(
            _get(item, "quantity", 0)
        )

        unit_price = _number(
            _get(
                item,
                "unit_price",
                _get(item, "price", 0),
            )
        )

        item_total = (
            _get(
                item,
                "total",
                None,
            )
        )

        if item_total is None:

            item_total = (
                quantity * unit_price
            )

        total += _number(
            item_total
        )

    return total


def recalculate_sales_order_total(
    db,
    order_id,
    commit=True,
):
    """Update the Sales Order total."""

    order = get_sales_order(
        db,
        order_id,
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    total = calculate_sales_order_total(
        db,
        order_id,
    )

    _set(
        order,
        "total_amount",
        total,
    )

    _set(
        order,
        "total",
        total,
    )

    if commit:
        db.commit()
        db.refresh(order)

    return total


# ==========================================================
# STOCK RESERVATION HELPERS
# ==========================================================

def _get_reserved_quantity(
    product,
    exclude_order_id=None,
):
    """
    Read an optional reserved quantity field.

    The existing Product model may not yet have
    reserved_quantity, so this remains compatible
    with older versions.
    """

    return _number(
        _get(
            product,
            "reserved_quantity",
            0,
        )
    )


def get_available_stock(
    db,
    product_id,
):
    """
    Return stock available for new reservations.

    Available = physical quantity - reserved quantity.
    """

    product = (
        db.query(Product)
        .filter(
            Product.id == product_id
        )
        .first()
    )

    if not product:
        raise ValueError(
            "Product not found."
        )

    quantity = _number(
        _get(
            product,
            "quantity",
            0,
        )
    )

    reserved = _get_reserved_quantity(
        product
    )

    return max(
        quantity - reserved,
        0,
    )


# ==========================================================
# CHECK STOCK FOR ORDER
# ==========================================================

def check_order_stock(
    db,
    order_id,
):
    """
    Check whether all Sales Order items
    can be reserved.
    """

    order = get_sales_order(
        db,
        order_id,
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    items = get_sales_order_items(
        db,
        order_id,
    )

    results = []
    all_available = True

    for item in items:

        product = (
            db.query(Product)
            .filter(
                Product.id
                == item.product_id
            )
            .first()
        )

        if not product:

            results.append(
                {
                    "product_id":
                        item.product_id,
                    "product":
                        "Unknown",
                    "requested":
                        _number(
                            item.quantity
                        ),
                    "available":
                        0,
                    "sufficient":
                        False,
                }
            )

            all_available = False
            continue

        requested = _number(
            item.quantity
        )

        available = get_available_stock(
            db,
            product.id,
        )

        sufficient = (
            available >= requested
        )

        if not sufficient:
            all_available = False

        results.append(
            {
                "product_id":
                    product.id,
                "product":
                    _get(
                        product,
                        "name",
                        "Unknown",
                    ),
                "requested":
                    requested,
                "available":
                    available,
                "sufficient":
                    sufficient,
            }
        )

    return {
        "available":
            all_available,
        "items":
            results,
    }


# ==========================================================
# RESERVE STOCK
# ==========================================================

def reserve_stock(
    db,
    order_id,
):
    """
    Reserve stock for a Sales Order.

    Reservation does NOT reduce physical stock.

    It increases Product.reserved_quantity when
    that field exists.
    """

    order = get_sales_order(
        db,
        order_id,
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    status = _status(order).lower()

    if status not in (
        "confirmed",
        "draft",
    ):
        raise ValueError(
            "Only Draft or Confirmed Sales Orders "
            "can reserve stock."
        )

    items = get_sales_order_items(
        db,
        order_id,
    )

    if not items:
        raise ValueError(
            "Sales Order has no items."
        )

    stock_check = check_order_stock(
        db,
        order_id,
    )

    if not stock_check["available"]:

        shortages = [
            x
            for x in stock_check["items"]
            if not x["sufficient"]
        ]

        message = "; ".join(
            f"{x['product']}: "
            f"requested {x['requested']}, "
            f"available {x['available']}"
            for x in shortages
        )

        raise ValueError(
            f"Insufficient stock: {message}"
        )

    # ------------------------------------------------------
    # Reserve each item
    # ------------------------------------------------------

    for item in items:

        product = (
            db.query(Product)
            .filter(
                Product.id
                == item.product_id
            )
            .first()
        )

        quantity = _number(
            item.quantity
        )

        # --------------------------------------------------
        # If Product.reserved_quantity exists,
        # maintain it directly.
        # --------------------------------------------------

        if hasattr(
            product,
            "reserved_quantity",
        ):

            current_reserved = (
                _get_reserved_quantity(
                    product
                )
            )

            product.reserved_quantity = (
                current_reserved
                + quantity
            )

        # --------------------------------------------------
        # Otherwise try the warehouse service.
        # --------------------------------------------------

        else:

            try:

                from services import warehouse_service

                if hasattr(
                    warehouse_service,
                    "reserve_stock",
                ):

                    warehouse_service.reserve_stock(
                        db=db,
                        product_id=product.id,
                        quantity=quantity,
                        reference_id=order.id,
                    )

            except Exception:
                # Older warehouse implementations
                # may not have reservation support.
                pass

    _set(
        order,
        "stock_reserved",
        True,
    )

    _set(
        order,
        "reserved",
        True,
    )

    _set(
        order,
        "stock_status",
        "Reserved",
    )

    _set(
        order,
        "reserved_at",
        datetime.utcnow(),
    )

    db.commit()
    db.refresh(order)

    return order


# ==========================================================
# RELEASE STOCK
# ==========================================================

def release_stock(
    db,
    order_id,
):
    """
    Release previously reserved stock.
    """

    order = get_sales_order(
        db,
        order_id,
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    items = get_sales_order_items(
        db,
        order_id,
    )

    for item in items:

        product = (
            db.query(Product)
            .filter(
                Product.id
                == item.product_id
            )
            .first()
        )

        if not product:
            continue

        quantity = _number(
            item.quantity
        )

        if hasattr(
            product,
            "reserved_quantity",
        ):

            reserved = _get_reserved_quantity(
                product
            )

            product.reserved_quantity = max(
                reserved - quantity,
                0,
            )

        else:

            try:

                from services import warehouse_service

                if hasattr(
                    warehouse_service,
                    "release_stock",
                ):

                    warehouse_service.release_stock(
                        db=db,
                        product_id=product.id,
                        quantity=quantity,
                        reference_id=order.id,
                    )

            except Exception:
                pass

    _set(
        order,
        "stock_reserved",
        False,
    )

    _set(
        order,
        "reserved",
        False,
    )

    _set(
        order,
        "stock_status",
        "Available",
    )

    _set(
        order,
        "released_at",
        datetime.utcnow(),
    )

    db.commit()
    db.refresh(order)

    return order


# ==========================================================
# CONFIRM SALES ORDER
# ==========================================================

def confirm_sales_order(
    db,
    order_id,
    reserve=True,
):
    """
    Confirm a Draft Sales Order.

    By default, confirmation also reserves stock.
    """

    order = get_sales_order(
        db,
        order_id,
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    if not _is_draft(order):
        raise ValueError(
            "Only Draft Sales Orders can be confirmed."
        )

    items = get_sales_order_items(
        db,
        order_id,
    )

    if not items:
        raise ValueError(
            "A Sales Order must contain at least "
            "one item before confirmation."
        )

    recalculate_sales_order_total(
        db,
        order_id,
        commit=False,
    )

    if reserve:

        # Check first, before changing status.
        stock_check = check_order_stock(
            db,
            order_id,
        )

        if not stock_check["available"]:

            shortages = [
                x
                for x in stock_check["items"]
                if not x["sufficient"]
            ]

            message = "; ".join(
                f"{x['product']}: "
                f"requested {x['requested']}, "
                f"available {x['available']}"
                for x in shortages
            )

            raise ValueError(
                f"Cannot confirm order because "
                f"stock is insufficient: {message}"
            )

    _set(
        order,
        "status",
        "Confirmed",
    )

    _set(
        order,
        "confirmed_at",
        datetime.utcnow(),
    )

    db.commit()

    if reserve:
        reserve_stock(
            db,
            order_id,
        )

    db.refresh(order)

    return order


# ==========================================================
# CANCEL SALES ORDER
# ==========================================================

def cancel_sales_order(
    db,
    order_id,
):
    """
    Cancel a Sales Order.

    Any reservation is released first.
    """

    order = get_sales_order(
        db,
        order_id,
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    status = _status(order).lower()

    if status == "cancelled":
        raise ValueError(
            "Sales Order is already cancelled."
        )

    if status in (
        "delivered",
        "completed",
        "closed",
    ):
        raise ValueError(
            "Completed Sales Orders cannot be cancelled."
        )

    reserved = (
        bool(
            _get(
                order,
                "stock_reserved",
                False,
            )
        )
        or bool(
            _get(
                order,
                "reserved",
                False,
            )
        )
    )

    if reserved:
        release_stock(
            db,
            order_id,
        )

    _set(
        order,
        "status",
        "Cancelled",
    )

    _set(
        order,
        "cancelled_at",
        datetime.utcnow(),
    )

    db.commit()
    db.refresh(order)

    return order


# ==========================================================
# ORDER SUMMARY
# ==========================================================

def get_sales_order_summary(
    db,
    order_id,
):
    """Return useful order information for the UI."""

    order = get_sales_order(
        db,
        order_id,
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    items = get_sales_order_items(
        db,
        order_id,
    )

    customer = (
        db.query(Customer)
        .filter(
            Customer.id
            == order.customer_id
        )
        .first()
    )

    total_quantity = sum(
        _number(
            item.quantity
        )
        for item in items
    )

    total_amount = calculate_sales_order_total(
        db,
        order_id,
    )

    return {
        "id":
            order.id,

        "customer_id":
            order.customer_id,

        "customer":
            _get(
                customer,
                "name",
                "Unknown",
            ),

        "status":
            _status(order),

        "items":
            len(items),

        "quantity":
            total_quantity,

        "total":
            total_amount,

        "stock_reserved":
            bool(
                _get(
                    order,
                    "stock_reserved",
                    _get(
                        order,
                        "reserved",
                        False,
                    ),
                )
            ),
    }