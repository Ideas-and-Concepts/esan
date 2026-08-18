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


# ==========================================================
# HELPERS
# ==========================================================

def _to_float(value, default=0.0):
    """
    Safely convert a value to float.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _status(value):
    """
    Return a normalized status.
    """
    return str(value or "Draft").strip().lower()


def _quotation_number(quotation_id):
    """
    Generate canonical quotation number.

    Example:
        1 -> Q-00001
    """
    return f"Q-{int(quotation_id):05d}"


def _order_number(order_id):
    """
    Generate canonical sales order number.

    Example:
        1 -> SO-00001
    """
    return f"SO-{int(order_id):05d}"


def _recalculate_item_total(item):
    """
    Calculate and update a quotation item's total.
    """
    quantity = _to_float(
        getattr(item, "quantity", 0)
    )

    unit_price = _to_float(
        getattr(item, "unit_price", 0)
    )

    total = quantity * unit_price

    item.total = total

    return total


# ==========================================================
# QUOTATIONS
# ==========================================================

def get_all_quotations(db):
    """
    Return all quotations, newest first.
    """
    return (
        db.query(Quotation)
        .order_by(
            Quotation.id.desc()
        )
        .all()
    )


def get_quotation(db, quotation_id):
    """
    Return one quotation by ID.
    """
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
    """
    Return quotations belonging to a customer.
    """
    return (
        db.query(Quotation)
        .filter(
            Quotation.customer_id
            == customer_id
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
    """
    Return all items belonging to a quotation.
    """
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
    """
    Return one quotation item.
    """
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

    The database first assigns the quotation ID.
    The canonical quotation number is then generated:

        Q-00001
        Q-00002
        Q-00003
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

    # Obtain database-generated ID.
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
    """
    Update quotation header information.
    """

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
    """
    Add a product to a Draft quotation.
    """

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

    total = (
        quantity * unit_price
    )

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
    """
    Update an existing quotation item.
    """

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
    """
    Delete an item from a Draft quotation.
    """

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
# CALCULATE QUOTATION TOTAL
# ==========================================================

def calculate_quotation_total(
    db,
    quotation_id,
    commit=True,
):
    """
    Calculate the quotation total from its items.

    Updates:

        Quotation.total_amount

    and each:

        QuotationItem.total
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

        item_total = (
            _recalculate_item_total(
                item
            )
        )

        total += item_total

    quotation.total_amount = total

    if commit:

        db.commit()

        db.refresh(
            quotation
        )

    else:

        db.flush()

    return total


# ==========================================================
# CANCEL QUOTATION
# ==========================================================

def cancel_quotation(
    db,
    quotation_id,
):
    """
    Cancel a quotation.
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
    Convert a quotation into exactly one Sales Order.

    Rules:

    1. Quotation must exist.
    2. Quotation cannot be cancelled.
    3. Quotation cannot already be converted.
    4. Quotation must contain at least one item.
    5. Only one SalesOrder may reference the quotation.
    6. Exactly one SalesOrderItem is created for every
       QuotationItem.
    7. Quotation status becomes Converted.
    8. Database IntegrityError is handled safely.
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

    # ------------------------------------------------------
    # Status protection
    # ------------------------------------------------------

    if current_status == "cancelled":

        raise ValueError(
            "Cancelled quotations cannot be converted."
        )

    if current_status == "converted":

        raise ValueError(
            "This quotation has already been converted."
        )

    # ------------------------------------------------------
    # Application-level duplicate protection
    # ------------------------------------------------------

    existing_order = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.quotation_id
            == quotation.id
        )
        .first()
    )

    if existing_order:

        # Synchronize the quotation state if necessary.
        quotation.status = "Converted"

        db.commit()

        raise ValueError(
            "This quotation has already been converted "
            f"to Sales Order "
            f"{existing_order.order_number}."
        )

    # ------------------------------------------------------
    # Load quotation items
    # ------------------------------------------------------

    items = get_quotation_items(
        db,
        quotation_id,
    )

    if not items:

        raise ValueError(
            "Cannot convert a quotation with no items."
        )

    # ------------------------------------------------------
    # Verify customer
    # ------------------------------------------------------

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

    try:

        # --------------------------------------------------
        # Ensure quotation total is current.
        # --------------------------------------------------

        quotation_total = (
            calculate_quotation_total(
                db,
                quotation_id,
                commit=False,
            )
        )

        # --------------------------------------------------
        # CREATE ONE SALES ORDER
        # --------------------------------------------------

        sales_order = SalesOrder(
            order_number="TEMP",
            customer_id=quotation.customer_id,
            quotation_id=quotation.id,
            order_date=date.today(),
            status="Draft",
            total_amount=quotation_total,
            notes=quotation.notes,
        )

        db.add(
            sales_order
        )

        # Generate database ID.
        db.flush()

        # Generate canonical order number.
        sales_order.order_number = (
            _order_number(
                sales_order.id
            )
        )

        # --------------------------------------------------
        # CREATE EXACTLY ONE SALES ORDER ITEM
        # PER QUOTATION ITEM
        # --------------------------------------------------

        for quotation_item in items:

            product = None

            if (
                quotation_item.product_id
                is not None
            ):

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
                if quotation_item.product_name
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

            total = (
                quantity
                * unit_price
            )

            sales_order_item = SalesOrderItem(
                sales_order_id=sales_order.id,
                product_id=(
                    quotation_item.product_id
                ),
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total=total,
                reserved_quantity=0.0,
                delivered_quantity=0.0,
            )

            db.add(
                sales_order_item
            )

        # --------------------------------------------------
        # Mark quotation as Converted
        # --------------------------------------------------

        quotation.status = "Converted"

        # --------------------------------------------------
        # Commit everything as one transaction
        # --------------------------------------------------

        db.commit()

        db.refresh(
            sales_order
        )

        db.refresh(
            quotation
        )

        return sales_order

    except IntegrityError as exc:

        # --------------------------------------------------
        # ALWAYS rollback a failed transaction before
        # using the SQLAlchemy session again.
        # --------------------------------------------------

        db.rollback()

        # --------------------------------------------------
        # Check whether another SalesOrder already exists
        # for this quotation.
        # --------------------------------------------------

        existing_order = (
            db.query(SalesOrder)
            .filter(
                SalesOrder.quotation_id
                == quotation.id
            )
            .first()
        )

        if existing_order:

            # The database has confirmed that this
            # quotation already has a Sales Order.

            quotation = get_quotation(
                db,
                quotation_id,
            )

            if quotation:

                quotation.status = "Converted"

                db.commit()

            raise ValueError(
                "This quotation has already been "
                "converted to Sales Order "
                f"{existing_order.order_number}."
            ) from exc

        # --------------------------------------------------
        # An unrelated database constraint failed.
        # Do not hide the original IntegrityError.
        # --------------------------------------------------

        raise