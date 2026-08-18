"""
Esan ERP
Quotation Service

Quotation creation, editing, cancellation, totals,
and conversion to Sales Orders.

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

from datetime import date

from sqlalchemy.exc import IntegrityError

from models import (
    Quotation,
    QuotationItem,
    Customer,
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
    """Return a normalized lowercase status."""

    return str(value or "Draft").strip().lower()


def _quotation_number(quotation_id):
    """Generate canonical quotation number."""

    return f"Q-{int(quotation_id):05d}"


def _order_number(order_id):
    """Generate canonical sales order number."""

    return f"SO-{int(order_id):05d}"


def _recalculate_item_total(item):
    """
    Recalculate a quotation item's line total.

    QuotationItem.total is always:

        quantity × unit_price
    """

    quantity = _to_float(
        getattr(item, "quantity", 0)
    )

    unit_price = _to_float(
        getattr(item, "unit_price", 0)
    )

    item.total = quantity * unit_price

    return item.total


# ============================================================
# QUOTATIONS
# ============================================================

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
        .order_by(Quotation.id.desc())
        .all()
    )


# ============================================================
# QUOTATION ITEMS
# ============================================================

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


# ============================================================
# CREATE QUOTATION
# ============================================================

def create_quotation(
    db,
    customer_id,
    quotation_date=None,
    valid_until=None,
    notes=None,
):
    """
    Create a quotation.

    The quotation number is generated after the database
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

    try:

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

    except Exception:
        db.rollback()
        raise


# ============================================================
# UPDATE QUOTATION
# ============================================================

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

    if _status(quotation.status) in {
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

    quotation.notes = notes

    try:

        db.commit()
        db.refresh(quotation)

        return quotation

    except Exception:
        db.rollback()
        raise


# ============================================================
# ADD QUOTATION ITEM
# ============================================================

def add_quotation_item(
    db,
    quotation_id,
    product_id,
    quantity,
    unit_price,
):
    """Add a product to a Draft quotation."""

    quotation = get_quotation(
        db,
        quotation_id,
    )

    if not quotation:
        raise ValueError(
            "Quotation not found."
        )

    if _status(quotation.status) != "draft":
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

    item = QuotationItem(
        quotation_id=quotation_id,
        product_id=product_id,
        product_name=product.name,
        quantity=quantity,
        unit_price=unit_price,
        total=quantity * unit_price,
    )

    try:

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

    except Exception:
        db.rollback()
        raise


# ============================================================
# UPDATE QUOTATION ITEM
# ============================================================

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

    if _status(quotation.status) != "draft":
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

    _recalculate_item_total(item)

    try:

        db.flush()

        calculate_quotation_total(
            db,
            quotation.id,
            commit=False,
        )

        db.commit()
        db.refresh(item)

        return item

    except Exception:
        db.rollback()
        raise


# ============================================================
# DELETE QUOTATION ITEM
# ============================================================

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

    if _status(quotation.status) != "draft":
        raise ValueError(
            "Items can only be deleted from Draft quotations."
        )

    quotation_id = quotation.id

    try:

        db.delete(item)
        db.flush()

        calculate_quotation_total(
            db,
            quotation_id,
            commit=False,
        )

        db.commit()

        return True

    except Exception:
        db.rollback()
        raise


# ============================================================
# CALCULATE QUOTATION TOTAL
# ============================================================

def calculate_quotation_total(
    db,
    quotation_id,
    commit=True,
):
    """
    Recalculate every quotation line and the quotation header.

    QuotationItem.total:
        quantity × unit_price

    Quotation.total_amount:
        sum of all QuotationItem.total values

    Returns:
        float
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

        try:

            db.commit()
            db.refresh(quotation)

        except Exception:
            db.rollback()
            raise

    else:
        db.flush()

    return total


# ============================================================
# CANCEL QUOTATION
# ============================================================

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

    try:

        db.commit()
        db.refresh(quotation)

        return quotation

    except Exception:
        db.rollback()
        raise


# ============================================================
# EXISTING SALES ORDER FOR QUOTATION
# ============================================================

def get_sales_order_for_quotation(
    db,
    quotation_id,
):
    """
    Return the Sales Order associated with a quotation.

    Because quotation_id is unique at the database level,
    there can be at most one.
    """

    return (
        db.query(SalesOrder)
        .filter(
            SalesOrder.quotation_id
            == quotation_id
        )
        .first()
    )


# ============================================================
# CONVERT QUOTATION TO SALES ORDER
# ============================================================

def convert_quotation_to_sales_order(
    db,
    quotation_id,
):
    """
    Convert a quotation into exactly one Sales Order.

    Rules:

    - quotation must exist
    - quotation must contain items
    - cancelled quotation cannot convert
    - already-converted quotation cannot convert again
    - only one SalesOrder is created
    - exactly one SalesOrderItem is created per QuotationItem
    - quotation status becomes Converted
    - IntegrityError from the unique quotation_id constraint
      is handled safely
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

        existing_order = (
            get_sales_order_for_quotation(
                db,
                quotation_id,
            )
        )

        if existing_order:
            raise ValueError(
                "This quotation has already been "
                f"converted to Sales Order "
                f"{existing_order.order_number}."
            )

        raise ValueError(
            "This quotation has already been converted."
        )

    # --------------------------------------------------------
    # Check whether a Sales Order already exists.
    #
    # This protects against duplicate conversion attempts
    # before the database constraint is reached.
    # --------------------------------------------------------

    existing_order = (
        get_sales_order_for_quotation(
            db,
            quotation_id,
        )
    )

    if existing_order:

        quotation.status = "Converted"

        try:
            db.commit()
            db.refresh(quotation)
        except Exception:
            db.rollback()
            raise

        raise ValueError(
            "A Sales Order already exists for this quotation: "
            f"{existing_order.order_number}."
        )

    # --------------------------------------------------------
    # Load quotation items
    # --------------------------------------------------------

    items = get_quotation_items(
        db,
        quotation_id,
    )

    if not items:
        raise ValueError(
            "Cannot convert a quotation with no items."
        )

    # --------------------------------------------------------
    # Verify customer
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Recalculate quotation totals before conversion
    # --------------------------------------------------------

    quotation_total = (
        calculate_quotation_total(
            db,
            quotation_id,
            commit=False,
        )
    )

    # --------------------------------------------------------
    # Create Sales Order
    # --------------------------------------------------------

    sales_order = SalesOrder(
        order_number="TEMP",
        customer_id=quotation.customer_id,
        quotation_id=quotation.id,
        order_date=date.today(),
        status="Draft",
        total_amount=quotation_total,
        notes=quotation.notes,
    )

    try:

        db.add(sales_order)

        # Obtain SalesOrder.id before generating order number.
        db.flush()

        sales_order.order_number = (
            _order_number(
                sales_order.id
            )
        )

        # ----------------------------------------------------
        # Create EXACTLY ONE SalesOrderItem per QuotationItem
        # ----------------------------------------------------

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

            line_total = (
                quantity * unit_price
            )

            sales_order_item = SalesOrderItem(
                sales_order_id=sales_order.id,
                product_id=quotation_item.product_id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total=line_total,
                reserved_quantity=0.0,
                delivered_quantity=0.0,
            )

            db.add(
                sales_order_item
            )

        # ----------------------------------------------------
        # Mark quotation converted
        # ----------------------------------------------------

        quotation.status = "Converted"

        # ----------------------------------------------------
        # Flush everything before commit.
        #
        # This is important because the unique quotation_id
        # constraint can raise IntegrityError here.
        # ----------------------------------------------------

        db.flush()

        db.commit()

        db.refresh(sales_order)
        db.refresh(quotation)

        return sales_order

    except IntegrityError as exc:

        # ----------------------------------------------------
        # Roll back EVERYTHING from this conversion attempt.
        #
        # This prevents:
        #
        # SalesOrder without items
        # SalesOrderItems without successful conversion
        # Quotation marked Converted prematurely
        # ----------------------------------------------------

        db.rollback()

        # Check whether another transaction has already created
        # the Sales Order for this quotation.
        existing_order = (
            get_sales_order_for_quotation(
                db,
                quotation_id,
            )
        )

        if existing_order:

            raise ValueError(
                "This quotation has already been "
                "converted to Sales Order "
                f"{existing_order.order_number}."
            ) from exc

        raise ValueError(
            "The quotation could not be converted because "
            "another Sales Order already references it."
        ) from exc

    except Exception:

        # ----------------------------------------------------
        # Any other failure must roll back the entire
        # conversion transaction.
        # ----------------------------------------------------

        db.rollback()
        raise