"""
Esan ERP
Quotation Service

Quotation creation, editing, cancellation, totals,
and conversion to Sales Orders.

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

from datetime import date

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


def _status(value):
    """Return a normalized status."""
    return str(value or "Draft").strip().lower()


def _quotation_number(quotation_id):
    """Generate the canonical quotation number."""
    return f"Q-{int(quotation_id):05d}"


def _order_number(order_id):
    """Generate the canonical sales-order number."""
    return f"SO-{int(order_id):05d}"


def _recalculate_item_total(item):
    """Calculate and update an item's total."""
    quantity = _to_float(
        getattr(item, "quantity", 0)
    )

    unit_price = _to_float(
        getattr(item, "unit_price", 0)
    )

    item.total = quantity * unit_price

    return item.total


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
        .filter(
            Quotation.id == quotation_id
        )
        .first()
    )


def get_customer_quotations(
    db,
    customer_id,
):
    """Return quotations belonging to a customer."""

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

def get_quotation_items(
    db,
    quotation_id,
):
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


def get_quotation_item(
    db,
    item_id,
):
    """Return one quotation item."""

    return (
        db.query(QuotationItem)
        .filter(
            QuotationItem.id == item_id
        )
        .first()
    )


# ==========================================================
# CALCULATE QUOTATION TOTAL
# ==========================================================

def calculate_quotation_total(
    db,
    quotation_id,
    commit=True,
):
    """
    Calculate the quotation total from its items.

    Updates quotation.total_amount and returns
    the calculated total.
    """

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        return 0.0

    items = get_quotation_items(
        db,
        quotation_id,
    )

    total = 0.0

    for item in items:
        total += _recalculate_item_total(
            item
        )

    quotation.total_amount = total

    if commit:
        db.commit()
        db.refresh(quotation)
    else:
        db.flush()

    return total


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

    quotation_number is generated after the database
    assigns the quotation ID.
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
        quotation_number="TEMP",
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

    db.flush()

    quotation.quotation_number = (
        _quotation_number(
            quotation.id
        )
    )

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

    if _status(
        quotation.status
    ) in {
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
                Customer.id
                == customer_id
            )
            .first()
        )

        if not customer:
            raise ValueError(
                "Customer not found."
            )

        quotation.customer_id = (
            customer_id
        )

    if quotation_date is not None:
        quotation.quotation_date = (
            quotation_date
        )

    if valid_until is not None:
        quotation.valid_until = (
            valid_until
        )

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
    """Add a product to a draft quotation."""

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        raise ValueError(
            "Quotation not found."
        )

    if _status(
        quotation.status
    ) != "draft":
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

    quantity = _to_float(
        quantity
    )

    unit_price = _to_float(
        unit_price
    )

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    if unit_price < 0:
        raise ValueError(
            "Unit price cannot be negative."
        )

    item = QuotationItem(
        quotation_id=quotation_id,
        product_id=product_id,
        product_name=product.name,
        quantity=quantity,
        unit_price=unit_price,
        total=quantity * unit_price,
    )

    db.add(item)

    db.flush()

    calculate_quotation_total(
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
    """Update an existing quotation item."""

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

    if _status(
        quotation.status
    ) != "draft":
        raise ValueError(
            "Items can only be edited on Draft quotations."
        )

    quantity = _to_float(
        quantity
    )

    unit_price = _to_float(
        unit_price
    )

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

    item.total = (
        quantity * unit_price
    )

    db.flush()

    calculate_quotation_total(
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
    """Delete an item from a draft quotation."""

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

    if _status(
        quotation.status
    ) != "draft":
        raise ValueError(
            "Items can only be deleted from Draft quotations."
        )

    quotation_id = quotation.id

    db.delete(item)

    db.flush()

    calculate_quotation_total(
        db,
        quotation_id,
        commit=False,
    )

    db.commit()

    return True


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
        raise ValueError(
            "Quotation not found."
        )

    current_status = _status(
        quotation.status
    )

    if current_status == "converted":
        raise ValueError(
            "A converted quotation cannot be cancelled."
        )

    if current_status == "cancelled":
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
    Convert a quotation into a Sales Order.

    A quotation can only be converted once.

    Every QuotationItem produces exactly one
    SalesOrderItem.
    """

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        raise ValueError(
            "Quotation not found."
        )

    current_status = _status(
        quotation.status
    )

    if current_status == "cancelled":
        raise ValueError(
            "Cancelled quotations cannot be converted."
        )

    if current_status == "converted":
        raise ValueError(
            "This quotation has already been converted."
        )

    items = get_quotation_items(
        db,
        quotation_id,
    )

    if not items:
        raise ValueError(
            "Cannot convert a quotation with no items."
        )

    customer = (
        db.query(Customer)
        .filter(
            Customer.id
            == quotation.customer_id
        )
        .first()
    )

    if not customer:
        raise ValueError(
            "Customer associated with quotation "
            "was not found."
        )

    # Ensure quotation total is current.
    quotation_total = (
        calculate_quotation_total(
            db,
            quotation_id,
            commit=False,
        )
    )

    # ------------------------------------------------------
    # CREATE SALES ORDER
    # ------------------------------------------------------

    sales_order = SalesOrder(
        order_number="TEMP",
        customer_id=quotation.customer_id,
        quotation_id=quotation.id,
        order_date=date.today(),
        status="Draft",
        total_amount=quotation_total,
        notes=quotation.notes,
    )

    db.add(sales_order)

    db.flush()

    sales_order.order_number = (
        _order_number(
            sales_order.id
        )
    )

    # ------------------------------------------------------
    # COPY QUOTATION ITEMS
    # ------------------------------------------------------

    for quotation_item in items:

        product = None

        if quotation_item.product_id is not None:

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
            if getattr(
                quotation_item,
                "product_name",
                None,
            )
            else (
                product.name
                if product
                else "Unknown Product"
            )
        )

        quantity = _to_float(
            quotation_item.quantity
        )

        unit_price = _to_float(
            quotation_item.unit_price
        )

        sales_order_item = SalesOrderItem(
            sales_order=sales_order,
            product_id=quotation_item.product_id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            total=quantity * unit_price,
            reserved_quantity=0.0,
            delivered_quantity=0.0,
        )

        db.add(sales_order_item)

    # ------------------------------------------------------
    # MARK QUOTATION CONVERTED
    # ------------------------------------------------------

    quotation.status = "Converted"

    db.flush()

    db.commit()

    db.refresh(sales_order)

    db.refresh(quotation)

    return sales_order