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
    return (
        db.query(Quotation)
        .filter(Quotation.customer_id == customer_id)
        .order_by(Quotation.id.desc())
        .all()
    )


# ==========================================================
# ITEMS
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
        .filter(QuotationItem.id == item_id)
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
    """Create a quotation header."""

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        raise ValueError("Customer not found.")

    quotation = Quotation(
        customer_id=customer_id,
    )

    _set_if_exists(
        quotation,
        "quotation_date",
        quotation_date or date.today(),
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
        0.0,
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
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            raise ValueError(
                "Customer not found."
            )

        quotation.customer_id = customer_id

    if quotation_date is not None:
        _set_if_exists(
            quotation,
            "quotation_date",
            quotation_date,
        )

    if valid_until is not None:
        _set_if_exists(
            quotation,
            "valid_until",
            valid_until,
        )

    if notes is not None:
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

    if _quotation_status(
        quotation
    ).lower() != "draft":
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
        product_name=getattr(
            product,
            "name",
            "Product",
        ),
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

    total = quantity * unit_price

    item.quantity = quantity
    item.unit_price = unit_price

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

    db.flush()

    recalculate_quotation_total(
        db,
        quotation.id,
        commit=False,
    )

    db.commit()
    db.refresh(item)

    return item


# ==========================================================
# DELETE ITEM
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

    if _quotation_status(
        quotation
    ).lower() != "draft":
        raise ValueError(
            "Only Draft quotations can be edited."
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
# RECALCULATE TOTAL
# ==========================================================

def recalculate_quotation_total(
    db,
    quotation_id,
    commit=True,
):
    """Recalculate quotation total from its items."""

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        return None

    items = get_quotation_items(
        db,
        quotation_id,
    )

    total = 0.0

    for item in items:

        item_total = getattr(
            item,
            "total",
            None,
        )

        if item_total is None:
            item_total = (
                _to_float(
                    getattr(
                        item,
                        "quantity",
                        0,
                    )
                )
                *
                _to_float(
                    getattr(
                        item,
                        "unit_price",
                        0,
                    )
                )
            )

            _set_if_exists(
                item,
                "total",
                item_total,
            )

        total += _to_float(
            item_total
        )

    _set_if_exists(
        quotation,
        "total_amount",
        total,
    )

    if commit:
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
    """Approve a Draft quotation."""

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

    recalculate_quotation_total(
        db,
        quotation_id,
        commit=False,
    )

    _set_if_exists(
        quotation,
        "status",
        "Approved",
    )

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

    _set_if_exists(
        quotation,
        "status",
        "Cancelled",
    )

    db.commit()
    db.refresh(quotation)

    return quotation


# ==========================================================
# CONVERT TO SALES ORDER
# ==========================================================

def convert_quotation_to_sales_order(
    db,
    quotation_id,
):
    """
    Convert an approved quotation into a Sales Order.

    The quotation remains linked to the resulting order.
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

    recalculate_quotation_total(
        db,
        quotation_id,
        commit=False,
    )

    items = get_quotation_items(
        db,
        quotation_id,
    )

    if not items:
        raise ValueError(
            "Quotation has no items."
        )

    order_number = (
        f"SO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )

    sales_order = SalesOrder(
        order_number=order_number,
        customer_id=quotation.customer_id,
        quotation_id=quotation.id,
    )

    _set_if_exists(
        sales_order,
        "order_date",
        date.today(),
    )

    _set_if_exists(
        sales_order,
        "status",
        "Draft",
    )

    _set_if_exists(
        sales_order,
        "total_amount",
        _to_float(
            getattr(
                quotation,
                "total_amount",
                0,
            )
        ),
    )

    _set_if_exists(
        sales_order,
        "notes",
        getattr(
            quotation,
            "notes",
            None,
        ),
    )

    db.add(sales_order)
    db.flush()

    for item in items:

        quantity = _to_float(
            getattr(
                item,
                "quantity",
                0,
            )
        )

        unit_price = _to_float(
            getattr(
                item,
                "unit_price",
                0,
            )
        )

        sales_item = SalesOrderItem(
            sales_order_id=sales_order.id,
            product_id=getattr(
                item,
                "product_id",
                None,
            ),
            product_name=getattr(
                item,
                "product_name",
                None,
            ) or "Product",
            quantity=quantity,
            unit_price=unit_price,
        )

        _set_if_exists(
            sales_item,
            "total",
            quantity * unit_price,
        )

        _set_if_exists(
            sales_item,
            "reserved_quantity",
            0,
        )

        _set_if_exists(
            sales_item,
            "delivered_quantity",
            0,
        )

        db.add(sales_item)

    _set_if_exists(
        quotation,
        "status",
        "Converted",
    )

    db.commit()
    db.refresh(sales_order)

    return sales_order


# ==========================================================
# SEARCH
# ==========================================================

def search_quotations(
    db,
    search_term,
):
    """Search quotations by quotation number or customer."""

    term = str(
        search_term or ""
    ).strip()

    if not term:
        return get_all_quotations(db)

    quotations = get_all_quotations(db)

    term_lower = term.lower()

    results = []

    for quotation in quotations:

        quotation_number = str(
            getattr(
                quotation,
                "quotation_number",
                "",
            ) or ""
        )

        customer = getattr(
            quotation,
            "customer",
            None,
        )

        customer_name = str(
            getattr(
                customer,
                "name",
                "",
            ) or ""
        )

        if (
            term_lower in quotation_number.lower()
            or term_lower in customer_name.lower()
        ):
            results.append(
                quotation
            )

    return results