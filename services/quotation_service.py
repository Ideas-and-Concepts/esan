"""
Esan ERP
Quotation Service

Handles quotation creation, editing, cancellation,
totals and conversion to Sales Orders.

Nile Harvest Foods Ltd.
"""

from datetime import datetime, date

from models import (
    Quotation,
    QuotationItem,
    Customer,
    Product,
    SalesOrder,
    SalesOrderItem,
)


# ==========================================================
# HELPERS
# ==========================================================

def _to_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _quotation_status(quotation):
    """Return quotation status safely."""
    return getattr(quotation, "status", None) or "Draft"


def generate_quotation_number(db):
    """
    Generate the next quotation number.

    Example:
        QT-000001
        QT-000002
    """

    last_quotation = (
        db.query(Quotation)
        .order_by(Quotation.id.desc())
        .first()
    )

    if last_quotation and last_quotation.id:
        next_id = last_quotation.id + 1
    else:
        next_id = 1

    return f"QT-{next_id:06d}"


def generate_order_number(db):
    """
    Generate the next sales order number.

    Example:
        SO-000001
        SO-000002
    """

    last_order = (
        db.query(SalesOrder)
        .order_by(SalesOrder.id.desc())
        .first()
    )

    if last_order and last_order.id:
        next_id = last_order.id + 1
    else:
        next_id = 1

    return f"SO-{next_id:06d}"


# ==========================================================
# QUOTATION QUERIES
# ==========================================================

def get_all_quotations(db):
    """Return all quotations, newest first."""

    return (
        db.query(Quotation)
        .order_by(Quotation.id.desc())
        .all()
    )


def get_quotation(db, quotation_id):
    """Return one quotation by ID."""

    return (
        db.query(Quotation)
        .filter(Quotation.id == quotation_id)
        .first()
    )


def get_customer_quotations(db, customer_id):
    """Return quotations belonging to a customer."""

    return (
        db.query(Quotation)
        .filter(
            Quotation.customer_id == customer_id
        )
        .order_by(Quotation.id.desc())
        .all()
    )


# ==========================================================
# QUOTATION ITEMS
# ==========================================================

def get_quotation_items(db, quotation_id):
    """Return all items belonging to a quotation."""

    return (
        db.query(QuotationItem)
        .filter(
            QuotationItem.quotation_id == quotation_id
        )
        .all()
    )


def get_quotation_item(db, item_id):
    """Return one quotation item."""

    return (
        db.query(QuotationItem)
        .filter(
            QuotationItem.id == item_id
        )
        .first()
    )


# ==========================================================
# CREATE QUOTATION
# ==========================================================

def create_quotation(
    db,
    customer_id,
    quotation_date=None,
    valid_until=None,
    notes=None,
):
    """
    Create a quotation header using the canonical
    Quotation model fields.
    """

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        raise ValueError("Customer not found.")

    quotation_number = generate_quotation_number(db)

    quotation = Quotation(
        quotation_number=quotation_number,
        customer_id=customer_id,
        quotation_date=quotation_date or date.today(),
        valid_until=valid_until,
        status="Draft",
        total_amount=0.0,
        notes=notes,
    )

    db.add(quotation)
    db.commit()
    db.refresh(quotation)

    return quotation


# ==========================================================
# UPDATE QUOTATION
# ==========================================================

def update_quotation(
    db,
    quotation_id,
    customer_id=None,
    quotation_date=None,
    valid_until=None,
    notes=None,
):
    """Update quotation header information."""

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        return None

    status = _quotation_status(
        quotation
    ).lower()

    if status in {
        "cancelled",
        "converted",
        "approved",
    }:
        raise ValueError(
            "This quotation can no longer be edited."
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

        quotation.customer_id = customer_id

    if quotation_date is not None:
        quotation.quotation_date = quotation_date

    if valid_until is not None:
        quotation.valid_until = valid_until

    if notes is not None:
        quotation.notes = notes

    db.commit()
    db.refresh(quotation)

    return quotation


# ==========================================================
# ADD QUOTATION ITEM
# ==========================================================

def add_quotation_item(
    db,
    quotation_id,
    product_id,
    quantity,
    unit_price,
):
    """
    Add a product to a quotation using the canonical
    QuotationItem fields.
    """

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        raise ValueError(
            "Quotation not found."
        )

    status = _quotation_status(
        quotation
    ).lower()

    if status != "draft":
        raise ValueError(
            "Items can only be added to Draft quotations."
        )

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise ValueError(
            "Product not found."
        )

    quantity = _to_float(quantity)
    unit_price = _to_float(unit_price)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    if unit_price < 0:
        raise ValueError(
            "Unit price cannot be negative."
        )

    total = quantity * unit_price

    item = QuotationItem(
        quotation_id=quotation_id,
        product_id=product_id,
        product_name=product.name,
        quantity=quantity,
        unit_price=unit_price,
        total=total,
    )

    db.add(item)
    db.flush()

    recalculate_quotation_total(
        db,
        quotation_id,
        commit=False,
    )

    db.commit()
    db.refresh(item)

    return item


# ==========================================================
# UPDATE QUOTATION ITEM
# ==========================================================

def update_quotation_item(
    db,
    item_id,
    quantity,
    unit_price,
):
    """Update a quotation item."""

    item = get_quotation_item(
        db,
        item_id,
    )

    if not item:
        return None

    quotation = get_quotation(
        db,
        item.quotation_id,
    )

    if not quotation:
        raise ValueError(
            "Quotation not found."
        )

    status = _quotation_status(
        quotation
    ).lower()

    if status != "draft":
        raise ValueError(
            "Items can only be edited on Draft quotations."
        )

    quantity = _to_float(quantity)
    unit_price = _to_float(unit_price)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    if unit_price < 0:
        raise ValueError(
            "Unit price cannot be negative."
        )

    item.quantity = quantity
    item.unit_price = unit_price
    item.total = quantity * unit_price

    recalculate_quotation_total(
        db,
        quotation.id,
        commit=False,
    )

    db.commit()
    db.refresh(item)

    return item


# ==========================================================
# DELETE QUOTATION ITEM
# ==========================================================

def delete_quotation_item(
    db,
    item_id,
):
    """Delete a quotation item."""

    item = get_quotation_item(
        db,
        item_id,
    )

    if not item:
        return False

    quotation = get_quotation(
        db,
        item.quotation_id,
    )

    if not quotation:
        raise ValueError(
            "Quotation not found."
        )

    status = _quotation_status(
        quotation
    ).lower()

    if status != "draft":
        raise ValueError(
            "Items can only be deleted from Draft quotations."
        )

    quotation_id = item.quotation_id

    db.delete(item)
    db.flush()

    recalculate_quotation_total(
        db,
        quotation_id,
        commit=False,
    )

    db.commit()

    return True


# ==========================================================
# RECALCULATE QUOTATION TOTAL
# ==========================================================

def recalculate_quotation_total(
    db,
    quotation_id,
    commit=True,
):
    """
    Recalculate the quotation total from its items.
    """

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        raise ValueError(
            "Quotation not found."
        )

    items = get_quotation_items(
        db,
        quotation_id,
    )

    total = 0.0

    for item in items:
        item_total = _to_float(
            item.total
        )

        total += item_total

    quotation.total_amount = total

    if commit:
        db.commit()
        db.refresh(quotation)

    return quotation


# ==========================================================
# CANCEL QUOTATION
# ==========================================================

def cancel_quotation(
    db,
    quotation_id,
):
    """Cancel a quotation."""

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        return None

    status = _quotation_status(
        quotation
    ).lower()

    if status == "converted":
        raise ValueError(
            "Converted quotations cannot be cancelled."
        )

    quotation.status = "Cancelled"

    db.commit()
    db.refresh(quotation)

    return quotation


# ==========================================================
# APPROVE QUOTATION
# ==========================================================

def approve_quotation(
    db,
    quotation_id,
):
    """Approve a draft quotation."""

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        return None

    status = _quotation_status(
        quotation
    ).lower()

    if status != "draft":
        raise ValueError(
            "Only Draft quotations can be approved."
        )

    quotation.status = "Approved"

    db.commit()
    db.refresh(quotation)

    return quotation


# ==========================================================
# CONVERT QUOTATION TO SALES ORDER
# ==========================================================

def convert_quotation_to_sales_order(
    db,
    quotation_id,
):
    """
    Convert an approved quotation into a Sales Order.

    Canonical SalesOrder fields:
        order_number
        customer_id
        quotation_id
        order_date
        status
        total_amount
        notes

    Canonical SalesOrderItem fields:
        sales_order_id
        product_id
        product_name
        quantity
        unit_price
        total
        reserved_quantity
        delivered_quantity
    """

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        raise ValueError(
            "Quotation not found."
        )

    status = _quotation_status(
        quotation
    ).lower()

    if status == "cancelled":
        raise ValueError(
            "Cancelled quotations cannot be converted."
        )

    if status == "converted":
        raise ValueError(
            "Quotation has already been converted."
        )

    if status not in {
        "approved",
        "draft",
    }:
        raise ValueError(
            "Only Draft or Approved quotations can be converted."
        )

    items = get_quotation_items(
        db,
        quotation_id,
    )

    if not items:
        raise ValueError(
            "Cannot convert a quotation without items."
        )

    order_number = generate_order_number(db)

    sales_order = SalesOrder(
        order_number=order_number,
        customer_id=quotation.customer_id,
        quotation_id=quotation.id,
        order_date=date.today(),
        status="Draft",
        total_amount=0.0,
        notes=quotation.notes,
    )

    db.add(sales_order)
    db.flush()

    order_total = 0.0

    for quotation_item in items:

        quantity = _to_float(
            quotation_item.quantity
        )

        unit_price = _to_float(
            quotation_item.unit_price
        )

        total = _to_float(
            quotation_item.total
        )

        if total == 0.0:
            total = quantity * unit_price

        sales_order_item = SalesOrderItem(
            sales_order_id=sales_order.id,
            product_id=quotation_item.product_id,
            product_name=quotation_item.product_name,
            quantity=quantity,
            unit_price=unit_price,
            total=total,
            reserved_quantity=0.0,
            delivered_quantity=0.0,
        )

        db.add(sales_order_item)

        order_total += total

    sales_order.total_amount = order_total

    quotation.status = "Converted"

    db.commit()
    db.refresh(sales_order)

    return sales_order