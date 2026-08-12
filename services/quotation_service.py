"""
Esan ERP
Quotation Service

Handles quotation creation, editing, cancellation,
totals and conversion to Sales Orders.

Nile Harvest Foods Ltd.
"""

from datetime import datetime

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


def _set_if_exists(obj, field, value):
    """
    Set a model attribute only when the mapped model
    actually contains that attribute.
    """
    if hasattr(obj, field):
        setattr(obj, field, value)


# ==========================================================
# QUOTATIONS
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

    query = (
        db.query(Quotation)
        .filter(
            Quotation.customer_id == customer_id
        )
    )

    return query.order_by(
        Quotation.id.desc()
    ).all()


# ==========================================================
# ITEMS
# ==========================================================

def get_quotation_items(db, quotation_id):
    """Return all items belonging to a quotation."""

    return (
        db.query(QuotationItem)
        .filter(
            QuotationItem.quotation_id
            == quotation_id
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
    Create a quotation header.

    Items can subsequently be added using
    add_quotation_item().
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

    quotation = Quotation(
        customer_id=customer_id,
    )

    _set_if_exists(
        quotation,
        "quotation_date",
        quotation_date or datetime.utcnow(),
    )

    _set_if_exists(
        quotation,
        "valid_until",
        valid_until,
    )

    _set_if_exists(
        quotation,
        "notes",
        notes,
    )

    _set_if_exists(
        quotation,
        "status",
        "Draft",
    )

    _set_if_exists(
        quotation,
        "total_amount",
        0,
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

    _set_if_exists(
        quotation,
        "quotation_date",
        quotation_date,
    )

    _set_if_exists(
        quotation,
        "valid_until",
        valid_until,
    )

    _set_if_exists(
        quotation,
        "notes",
        notes,
    )

    db.commit()
    db.refresh(quotation)

    return quotation


# ==========================================================
# ADD ITEM
# ==========================================================

def add_quotation_item(
    db,
    quotation_id,
    product_id,
    quantity,
    unit_price,
):
    """Add a product to a quotation."""

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
        quantity=quantity,
        unit_price=unit_price,
    )

    _set_if_exists(
        item,
        "total",
        total,
    )

    _set_if_exists(
        item,
        "total_price",
        total,
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
# UPDATE ITEM
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

    if (
        _