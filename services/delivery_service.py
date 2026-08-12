"""
Esan ERP
Delivery Service

Handles delivery notes, delivery items, posting,
stock movement integration and reversal.

Nile Harvest Foods Ltd.
"""

from datetime import datetime

from models import (
    Delivery,
    DeliveryItem,
    Customer,
    Product,
    SalesOrder,
    SalesOrderItem,
)


# ==========================================================
# HELPERS
# ==========================================================

def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _status(delivery):
    return getattr(delivery, "status", None) or "Draft"


def _set_if_exists(obj, field, value):
    if hasattr(obj, field):
        setattr(obj, field, value)


# ==========================================================
# DELIVERY QUERIES
# ==========================================================

def get_all_deliveries(db):
    """Return all deliveries, newest first."""

    return (
        db.query(Delivery)
        .order_by(Delivery.id.desc())
        .all()
    )


def get_delivery(db, delivery_id):
    """Get one delivery."""

    return (
        db.query(Delivery)
        .filter(Delivery.id == delivery_id)
        .first()
    )


def get_customer_deliveries(db, customer_id):
    """Return deliveries for a customer."""

    return (
        db.query(Delivery)
        .filter(
            Delivery.customer_id == customer_id
        )
        .order_by(Delivery.id.desc())
        .all()
    )


def get_delivery_items(db, delivery_id):
    """Return delivery items."""

    return (
        db.query(DeliveryItem)
        .filter(
            DeliveryItem.delivery_id
            == delivery_id
        )
        .all()
    )


def get_delivery_item(db, item_id):
    """Get one delivery item."""

    return (
        db.query(DeliveryItem)
        .filter(
            DeliveryItem.id == item_id
        )
        .first()
    )


# ==========================================================
# CREATE DELIVERY
# ==========================================================

def create_delivery(
    db,
    customer_id,
    sales_order_id=None,
    delivery_date=None,
    notes=None,
):
    """
    Create a Draft delivery.
    """

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

    if sales_order_id:

        order = (
            db.query(SalesOrder)
            .filter(
                SalesOrder.id
                == sales_order_id
            )
            .first()
        )

        if not order:
            raise ValueError(
                "Sales Order not found."
            )

    delivery = Delivery(
        customer_id=customer_id,
    )

    _set_if_exists(
        delivery,
        "sales_order_id",
        sales_order_id,
    )

    _set_if_exists(
        delivery,
        "delivery_date",
        delivery_date or datetime.utcnow(),
    )

    _set_if_exists(
        delivery,
        "notes",
        notes,
    )

    _set_if_exists(
        delivery,
        "status",
        "Draft",
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    return delivery


# ==========================================================
# UPDATE DELIVERY
# ==========================================================

def update_delivery(
    db,
    delivery_id,
    customer_id=None,
    sales_order_id=None,
    delivery_date=None,
    notes=None,
):
    """Update a Draft delivery."""

    delivery = get_delivery(
        db,
        delivery_id,
    )

    if not delivery:
        return None

    if _status(delivery).lower() != "draft":
        raise ValueError(
            "Only Draft deliveries can be edited."
        )

    if customer_id is not None:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id
                == customer_id
            )
            .first()
        )

        if not customer:
            raise ValueError(
                "Customer not found."
            )

        delivery.customer_id = customer_id

    if sales_order_id is not None:

        order = (
            db.query(SalesOrder)
            .filter(
                SalesOrder.id
                == sales_order_id
            )
            .first()
        )

        if not order:
            raise ValueError(
                "Sales Order not found."
            )

        delivery.sales_order_id = sales_order_id

    _set_if_exists(
        delivery,
        "delivery_date",
        delivery_date,
    )

    _set_if_exists(
        delivery,
        "notes",
        notes,
    )

    db.commit()
    db.refresh(delivery)

    return delivery


# ==========================================================
# ADD DELIVERY ITEM
# ==========================================================

def add_delivery_item(
    db,
    delivery_id,
    product_id,
    quantity,
):
    """Add product quantity to a delivery."""

    delivery = get_delivery(
        db,
        delivery_id,
    )

    if not delivery:
        raise ValueError(
            "Delivery not found."
        )

    if _status(delivery).lower() != "draft":
        raise ValueError(
            "Items can only be added to Draft deliveries."
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

    quantity = _to_float(quantity)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    item = DeliveryItem(
        delivery_id=delivery_id,
        product_id=product_id,
        quantity=quantity,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


# ==========================================================
# UPDATE DELIVERY ITEM
# ==========================================================

def update_delivery_item(
    db,
    item_id,
    quantity,
):
    """Edit a delivery item."""

    item = get_delivery_item(
        db,
        item_id,
    )

    if not item:
        return None

    delivery = get_delivery(
        db,
        item.delivery_id,
    )

    if not delivery:
        raise ValueError(
            "Delivery not found."
        )

    if _status(delivery).lower() != "draft":
        raise ValueError(
            "Only Draft delivery items can be edited."
        )

    quantity = _to_float(quantity)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    item.quantity = quantity

    db.commit()
    db.refresh(item)

    return item


# ==========================================================
# DELETE DELIVERY ITEM
# ==========================================================

def delete_delivery_item(
    db,
    item_id,
):
    """Delete a delivery item."""

    item = get_delivery_item(
        db,
        item_id,
    )

    if not item:
        return False

    delivery = get_delivery(
        db,
        item.delivery_id,
    )

    if delivery and _status(delivery).lower() != "draft":
        raise ValueError(
            "Only Draft delivery items can be deleted."
        )

    db.delete(item)
    db.commit()

    return True


# ==========================================================
# STOCK CHECK
# ==========================================================

def check_delivery_stock(
    db,
    delivery_id,
):
    """
    Check whether sufficient stock exists
    for every delivery item.

    Returns:

        {
            "available": True/False,
            "items": [...]
        }
    """

    delivery = get_delivery(
        db,
        delivery_id,
    )

    if not delivery:
        raise ValueError(
            "Delivery not found."
        )

    items = get_delivery_items(
        db,
        delivery_id,
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

        stock = _to_float(
            getattr(
                product,
                "quantity",
                0,
            )
        )

        requested = _to_float(
            item.quantity
        )

        available = stock >= requested

        if not available:
            all_available = False

        results.append(
            {
                "product_id":
                    item.product_id,
                "product":
                    getattr(
                        product,
                        "name",
                        "Unknown",
                    ),
                "requested":
                    requested,
                "available_stock":
                    stock,
                "available":
                    available,
            }
        )

    return {
        "available":
            all_available,
        "items":
            results,
    }


# ==========================================================
# POST DELIVERY
# ==========================================================

def post_delivery(
    db,
    delivery_id,
):
    """
    Post a delivery.

    Posting:
        1. Checks stock.
        2. Reduces Product.quantity.
        3. Creates StockMovement when supported.
        4. Changes delivery status to Posted.
    """

    delivery = get_delivery(
        db,
        delivery_id,
    )

    if not delivery:
        raise ValueError(
            "Delivery not found."
        )

    if _status(delivery).lower() != "draft":
        raise ValueError(
            "Only Draft deliveries can be posted."
        )

    items = get_delivery_items(
        db,
        delivery_id,
    )

    if not items:
        raise ValueError(
            "A delivery must contain at least one item."
        )

    stock_check = check_delivery_stock(
        db,
        delivery_id,
    )

    if not stock_check["available"]:

        shortages = [
            item
            for item in stock_check["items"]
            if not item["available"]
        ]

        message = "; ".join(
            f"{item['product']}: "
            f"requested {item['requested']}, "
            f"available {item['available_stock']}"
            for item in shortages
        )

        raise ValueError(
            f"Insufficient stock: {message}"
        )

    # ------------------------------------------------------
    # Import stock service only when posting.
    # This prevents warehouse-service import problems
    # from breaking the whole Sales module.
    # ------------------------------------------------------

    stock_service = None

    try:

        from services import warehouse_service

        stock_service = warehouse_service

    except Exception:
        stock_service = None

    # ------------------------------------------------------
    # Reduce stock
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

        if not product:
            raise ValueError(
                f"Product {item.product_id} not found."
            )

        quantity = _to_float(
            item.quantity
        )

        current_stock = _to_float(
            getattr(
                product,
                "quantity",
                0,
            )
        )

        product.quantity = (
            current_stock - quantity
        )

        # ----------------------------------------------
        # StockMovement integration
        # ----------------------------------------------

        if stock_service:

            try:

                if hasattr(
                    stock_service,
                    "create_stock_movement",
                ):

                    stock_service.create_stock_movement(
                        db=db,
                        product_id=product.id,
                        quantity=-quantity,
                        movement_type="Delivery",
                        reference_id=delivery.id,
                    )

            except TypeError:

                # Compatibility with older service
                # signatures.
                try:

                    stock_service.create_stock_movement(
                        db,
                        product.id,
                        -quantity,
                        "Delivery",
                    )

                except Exception:
                    pass

            except Exception:
                pass

    # ------------------------------------------------------
    # Update delivery
    # ------------------------------------------------------

    _set_if_exists(
        delivery,
        "status",
        "Posted",
    )

    _set_if_exists(
        delivery,
        "posted_at",
        datetime.utcnow(),
    )

    db.commit()
    db.refresh(delivery)

    return delivery


# ==========================================================
# CANCEL DELIVERY
# ==========================================================

def cancel_delivery(
    db,
    delivery_id,
):
    """
    Cancel a Draft delivery.

    Posted deliveries must be reversed instead.
    """

    delivery = get_delivery(
        db,
        delivery_id,
    )

    if not delivery:
        return None

    status = _status(
        delivery
    ).lower()

    if status == "posted":
        raise ValueError(
            "Posted deliveries must be reversed, "
            "not cancelled."
        )

    if status == "cancelled":
        raise ValueError(
            "Delivery is already cancelled."
        )

    _set_if_exists(
        delivery,
        "status",
        "Cancelled",
    )

    _set_if_exists(
        delivery,
        "cancelled_at",
        datetime.utcnow(),
    )

    db.commit()
    db.refresh(delivery)

    return delivery


# ==========================================================
# REVERSE DELIVERY
# ==========================================================

def reverse_delivery(
    db,
    delivery_id,
):
    """
    Reverse a Posted delivery.

    Stock quantities are returned to inventory.
    """

    delivery = get_delivery(
        db,
        delivery_id,
    )

    if not delivery:
        raise ValueError(
            "Delivery not found."
        )

    if _status(delivery).lower() != "posted":
        raise ValueError(
            "Only Posted deliveries can be reversed."
        )

    items = get_delivery_items(
        db,
        delivery_id,
    )

    stock_service = None

    try:

        from services import warehouse_service

        stock_service = warehouse_service

    except Exception:
        stock_service = None

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
            raise ValueError(
                f"Product {item.product_id} not found."
            )

        quantity = _to_float(
            item.quantity
        )

        current_stock = _to_float(
            getattr(
                product,
                "quantity",
                0,
            )
        )

        product.quantity = (
            current_stock + quantity
        )

        if stock_service:

            try:

                if hasattr(
                    stock_service,
                    "create_stock_movement",
                ):

                    stock_service.create_stock_movement(
                        db=db,
                        product_id=product.id,
                        quantity=quantity,
                        movement_type="Delivery Reversal",
                        reference_id=delivery.id,
                    )

            except Exception:
                pass

    _set_if_exists(
        delivery,
        "status",
        "Reversed",
    )

    _set_if_exists(
        delivery,
        "reversed_at",
        datetime.utcnow(),
    )

    db.commit()
    db.refresh(delivery)

    return delivery