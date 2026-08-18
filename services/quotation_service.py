"""
Esan ERP
Quotation Service

Handles:
- Quotation creation
- Quotation retrieval
- Quotation editing
- Quotation item management
- Quotation totals
- Quotation approval
- Quotation cancellation
- Conversion to Sales Orders

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

from datetime import date, datetime

from models import (
    Customer,
    Product,
    Quotation,
    QuotationItem,
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
    return (
        getattr(quotation, "status", None)
        or "Draft"
    ).strip()


def _generate_quotation_number(db):
    """Generate a unique quotation number."""
    prefix = "QT"

    last = (
        db.query(Quotation)
        .order_by(Quotation.id.desc())
        .first()
    )

    if last and getattr(last, "quotation_number", None):
        try:
            last_number = int(
                str(last.quotation_number)
                .replace(prefix, "")
                .replace("-", "")
            )
            next_number = last_number + 1
        except (TypeError, ValueError):
            next_number = (
                getattr(last, "id", 0) or 0
            ) + 1
    else:
        next_number = 1

    return f"{prefix}-{next_number:05d}"


def _generate_order_number(db):
    """Generate a unique sales order number."""
    prefix = "SO"

    last = (
        db.query(SalesOrder)
        .order_by(SalesOrder.id.desc())
        .first()
    )

    if last and getattr(last, "order_number", None):
        try:
            last_number = int(
                str(last.order_number)
                .replace(prefix, "")
                .replace("-", "")
            )
            next_number = last_number + 1
        except (TypeError, ValueError):
            next_number = (
                getattr(last, "id", 0) or 0
            ) + 1
    else:
        next_number = 1

    return f"{prefix}-{next_number:05d}"


# ==========================================================
# QUOTATION RETRIEVAL
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
        .filter(
            Quotation.id == quotation_id
        )
        .first()
    )


def get_customer_quotations(db, customer_id):
    """Return all quotations for a customer."""

    return (
        db.query(Quotation)
        .filter(
            Quotation.customer_id == customer_id
        )
        .order_by(
            Quotation.id.desc()
        )
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
            QuotationItem.quotation_id
            == quotation_id
        )
        .order_by(
            QuotationItem.id.asc()
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
    Create a new quotation.

    Canonical model fields:
    - quotation_number
    - customer_id
    - quotation_date
    - valid_until
    - status
    - total_amount
    - notes
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

    quotation = Quotation(
        quotation_number=_generate_quotation_number(db),
        customer_id=customer_id,
        quotation_date=(
            quotation_date
            or date.today()
        ),
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
    """Add a product item to a quotation."""

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        raise ValueError(
            "Quotation not found."
        )

    if _quotation_status(
        quotation
    ).lower() != "draft":
        raise ValueError(
            "Items can only be added to Draft quotations."
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

    calculate_quotation_total(
        db,
        quotation_id,
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
    """Update quantity and price of a quotation item."""

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

    if _quotation_status(
        quotation
    ).lower() != "draft":
        raise ValueError(
            "Only Draft quotations can be edited."
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

    calculate_quotation_total(
        db,
        quotation.id,
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
    """Delete an item from a Draft quotation."""

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

    if _quotation_status(
        quotation
    ).lower() != "draft":
        raise ValueError(
            "Only Draft quotations can be edited."
        )

    quotation_id = quotation.id

    db.delete(item)
    db.flush()

    calculate_quotation_total(
        db,
        quotation_id,
    )

    db.commit()

    return True


# ==========================================================
# CALCULATE QUOTATION TOTAL
# ==========================================================

def calculate_quotation_total(
    db,
    quotation_id,
):
    """
    Calculate and update quotation total.

    Returns the calculated total.
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
        quantity = _to_float(
            item.quantity
        )

        unit_price = _to_float(
            item.unit_price
        )

        item_total = (
            quantity * unit_price
        )

        item.total = item_total
        total += item_total

    quotation.total_amount = total

    return total


# ==========================================================
# BACKWARD-COMPATIBLE ALIAS
# ==========================================================

def recalculate_quotation_total(
    db,
    quotation_id,
    commit=True,
):
    """
    Backward-compatible wrapper.

    Existing quotation modules may still call
    recalculate_quotation_total().
    """

    total = calculate_quotation_total(
        db,
        quotation_id,
    )

    if commit:
        db.commit()

    return total


# ==========================================================
# APPROVE QUOTATION
# ==========================================================

def approve_quotation(
    db,
    quotation_id,
):
    """Approve a Draft quotation."""

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
            "Only Draft quotations can be approved."
        )

    calculate_quotation_total(
        db,
        quotation_id,
    )

    if quotation.total_amount <= 0:
        raise ValueError(
            "Quotation must contain items before approval."
        )

    quotation.status = "Approved"

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
            "A converted quotation cannot be cancelled."
        )

    if status == "cancelled":
        return quotation

    quotation.status = "Cancelled"

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

    The quotation remains in the database and is marked
    as Converted after successful order creation.
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

    if status == "converted":
        raise ValueError(
            "Quotation has already been converted."
        )

    if status == "cancelled":
        raise ValueError(
            "Cancelled quotations cannot be converted."
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
            "Quotation has no items."
        )

    calculate_quotation_total(
        db,
        quotation_id,
    )

    order = SalesOrder(
        order_number=_generate_order_number(db),
        customer_id=quotation.customer_id,
        quotation_id=quotation.id,
        order_date=date.today(),
        status="Draft",
        total_amount=quotation.total_amount,
        notes=quotation.notes,
    )

    db.add(order)
    db.flush()

    for quotation_item in items:

        product = None

        if quotation_item.product_id:
            product = (
                db.query(Product)
                .filter(
                    Product.id
                    == quotation_item.product_id
                )
                .first()
            )

        product_name = (
            quotation_item.product_name
            or (
                product.name
                if product
                else "Product"
            )
        )

        order_item = SalesOrderItem(
            sales_order_id=order.id,
            product_id=quotation_item.product_id,
            product_name=product_name,
            quantity=_to_float(
                quotation_item.quantity
            ),
            unit_price=_to_float(
                quotation_item.unit_price
            ),
            total=_to_float(
                quotation_item.total
            ),
            reserved_quantity=0.0,
            delivered_quantity=0.0,
        )

        db.add(order_item)

    quotation.status = "Converted"

    db.commit()
    db.refresh(order)
    db.refresh(quotation)

    return order


# ==========================================================
# LEGACY FUNCTION NAME
# ==========================================================

def convert_to_sales_order(
    db,
    quotation_id,
):
    """
    Backward-compatible alias used by older
    Sales & Distribution code.
    """

    return convert_quotation_to_sales_order(
        db,
        quotation_id,
    )