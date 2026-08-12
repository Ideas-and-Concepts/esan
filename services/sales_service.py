"""
Esan ERP - Sales Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Responsibilities:
- Customers
- Products
- Quotations
- Sales Orders
- Quotation conversion
- Sales Order status management
- Sales Order editing
- Sales Order deletion
"""

from datetime import datetime

from sqlalchemy.orm import joinedload

from database import SessionLocal
from models import (
    Customer,
    Product,
    Quotation,
    QuotationItem,
    SalesOrder,
    SalesOrderItem,
)


# ============================================================
# SALES ORDER STATUSES
# ============================================================

SALES_ORDER_STATUSES = [
    "Draft",
    "Pending Approval",
    "Approved",
    "Confirmed",
    "Processing",
    "Partially Delivered",
    "Delivered",
    "Cancelled",
]


# ============================================================
# HELPERS
# ============================================================

def _generate_number(
    prefix,
    model,
    field_name,
    db,
):
    """
    Generate a sequential business document number.

    Example:
        SO-00001
        QT-00001
    """

    field = getattr(
        model,
        field_name,
    )

    last_record = (
        db.query(model)
        .order_by(model.id.desc())
        .first()
    )

    if not last_record:

        next_number = 1

    else:

        current_value = getattr(
            last_record,
            field_name,
            "",
        )

        try:

            number_part = (
                str(current_value)
                .split("-")[-1]
            )

            next_number = (
                int(number_part) + 1
            )

        except (
            ValueError,
            TypeError,
        ):

            next_number = (
                last_record.id + 1
            )

    return (
        f"{prefix}-{next_number:05d}"
    )


# ============================================================
# CUSTOMER SERVICES
# ============================================================

def get_all_customers(
    active_only=False,
):
    """
    Return all customers.

    active_only=True limits results to active customers
    when the Customer model contains an active field.
    """

    db = SessionLocal()

    try:

        query = db.query(Customer)

        if active_only and hasattr(
            Customer,
            "active",
        ):

            query = query.filter(
                Customer.active.is_(True)
            )

        return (
            query
            .order_by(Customer.name.asc())
            .all()
        )

    finally:

        db.close()


def get_customer(
    customer_id,
):
    """Return one customer."""

    db = SessionLocal()

    try:

        return (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
            .first()
        )

    finally:

        db.close()


# ============================================================
# PRODUCT SERVICES
# ============================================================

def get_all_products(
    active_only=False,
):
    """
    Return products.

    This function is used by the quotation module.
    """

    db = SessionLocal()

    try:

        query = db.query(Product)

        if active_only and hasattr(
            Product,
            "active",
        ):

            query = query.filter(
                Product.active.is_(True)
            )

        return (
            query
            .order_by(Product.name.asc())
            .all()
        )

    finally:

        db.close()


def get_sales_products(
    active_only=True,
):
    """
    Alias used by Sales Orders.
    """

    return get_all_products(
        active_only=active_only
    )


def get_product(
    product_id,
):
    """Return one product."""

    db = SessionLocal()

    try:

        return (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
            .first()
        )

    finally:

        db.close()


# ============================================================
# QUOTATION SERVICES
# ============================================================

def generate_quotation_number():

    db = SessionLocal()

    try:

        return _generate_number(
            prefix="QT",
            model=Quotation,
            field_name="quotation_number",
            db=db,
        )

    finally:

        db.close()


def get_all_quotations(
    status=None,
):
    """Return quotations with customer and items loaded."""

    db = SessionLocal()

    try:

        query = (
            db.query(Quotation)
            .options(
                joinedload(
                    Quotation.customer
                ),
                joinedload(
                    Quotation.items
                ),
            )
        )

        if status:

            query = query.filter(
                Quotation.status == status
            )

        return (
            query
            .order_by(
                Quotation.id.desc()
            )
            .all()
        )

    finally:

        db.close()


def get_quotation(
    quotation_id,
):
    """Return one quotation with its items."""

    db = SessionLocal()

    try:

        return (
            db.query(Quotation)
            .options(
                joinedload(
                    Quotation.customer
                ),
                joinedload(
                    Quotation.items
                ),
            )
            .filter(
                Quotation.id == quotation_id
            )
            .first()
        )

    finally:

        db.close()


def create_quotation(
    customer_id,
    items,
    valid_until=None,
    status="Draft",
    notes=None,
):
    """
    Create a quotation.

    items format:

    [
        {
            "product_id": 1,
            "product_name": "Maize Flour 25Kg",
            "quantity": 10,
            "unit_price": 50000,
        }
    ]
    """

    db = SessionLocal()

    try:

        quotation_number = _generate_number(
            prefix="QT",
            model=Quotation,
            field_name="quotation_number",
            db=db,
        )

        quotation = Quotation(
            quotation_number=quotation_number,
            customer_id=customer_id,
            status=status,
            total_amount=0,
            notes=notes,
        )

        if hasattr(
            Quotation,
            "valid_until",
        ):

            quotation.valid_until = (
                valid_until
            )

        db.add(quotation)

        db.flush()

        total_amount = 0.0

        for item_data in items:

            quantity = float(
                item_data.get(
                    "quantity",
                    0,
                )
            )

            unit_price = float(
                item_data.get(
                    "unit_price",
                    0,
                )
            )

            item_total = (
                quantity * unit_price
            )

            quotation_item = QuotationItem(
                quotation_id=quotation.id,
                product_name=item_data.get(
                    "product_name",
                    "",
                ),
                quantity=quantity,
                unit_price=unit_price,
                total=item_total,
            )

            if hasattr(
                QuotationItem,
                "product_id",
            ):

                quotation_item.product_id = (
                    item_data.get(
                        "product_id"
                    )
                )

            db.add(
                quotation_item
            )

            total_amount += item_total

        quotation.total_amount = (
            total_amount
        )

        db.commit()

        db.refresh(quotation)

        return quotation

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def update_quotation(
    quotation_id,
    customer_id=None,
    items=None,
    valid_until=None,
    status=None,
    notes=None,
):
    """Update an existing quotation."""

    db = SessionLocal()

    try:

        quotation = (
            db.query(Quotation)
            .filter(
                Quotation.id == quotation_id
            )
            .first()
        )

        if not quotation:

            return None

        if customer_id is not None:

            quotation.customer_id = (
                customer_id
            )

        if status is not None:

            quotation.status = status

        if notes is not None:

            quotation.notes = notes

        if (
            valid_until is not None
            and hasattr(
                Quotation,
                "valid_until",
            )
        ):

            quotation.valid_until = (
                valid_until
            )

        if items is not None:

            quotation.items.clear()

            db.flush()

            total_amount = 0.0

            for item_data in items:

                quantity = float(
                    item_data.get(
                        "quantity",
                        0,
                    )
                )

                unit_price = float(
                    item_data.get(
                        "unit_price",
                        0,
                    )
                )

                item_total = (
                    quantity * unit_price
                )

                quotation_item = QuotationItem(
                    quotation_id=quotation.id,
                    product_name=item_data.get(
                        "product_name",
                        "",
                    ),
                    quantity=quantity,
                    unit_price=unit_price,
                    total=item_total,
                )

                if hasattr(
                    QuotationItem,
                    "product_id",
                ):

                    quotation_item.product_id = (
                        item_data.get(
                            "product_id"
                        )
                    )

                db.add(
                    quotation_item
                )

                total_amount += (
                    item_total
                )

            quotation.total_amount = (
                total_amount
            )

        db.commit()

        db.refresh(quotation)

        return quotation

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def delete_quotation(
    quotation_id,
):
    """Delete a quotation and its items."""

    db = SessionLocal()

    try:

        quotation = (
            db.query(Quotation)
            .filter(
                Quotation.id == quotation_id
            )
            .first()
        )

        if not quotation:

            return False

        db.delete(
            quotation
        )

        db.commit()

        return True

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def set_quotation_status(
    quotation_id,
    status,
):
    """Change quotation status."""

    db = SessionLocal()

    try:

        quotation = (
            db.query(Quotation)
            .filter(
                Quotation.id == quotation_id
            )
            .first()
        )

        if not quotation:

            return None

        quotation.status = status

        db.commit()

        db.refresh(quotation)

        return quotation

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# SALES ORDER SERVICES
# ============================================================

def generate_sales_order_number():

    db = SessionLocal()

    try:

        return _generate_number(
            prefix="SO",
            model=SalesOrder,
            field_name="order_number",
            db=db,
        )

    finally:

        db.close()


def get_all_sales_orders():
    """Return all Sales Orders."""

    db = SessionLocal()

    try:

        return (
            db.query(SalesOrder)
            .options(
                joinedload(
                    SalesOrder.customer
                ),
                joinedload(
                    SalesOrder.items
                ),
            )
            .order_by(
                SalesOrder.id.desc()
            )
            .all()
        )

    finally:

        db.close()


def get_sales_order(
    order_id,
):
    """Return one Sales Order."""

    db = SessionLocal()

    try:

        return (
            db.query(SalesOrder)
            .options(
                joinedload(
                    SalesOrder.customer
                ),
                joinedload(
                    SalesOrder.items
                ),
            )
            .filter(
                SalesOrder.id == order_id
            )
            .first()
        )

    finally:

        db.close()


def create_sales_order(
    customer_id,
    items,
    status="Draft",
    notes=None,
):
    """
    Create a Sales Order.

    items format:

    [
        {
            "product_name": "Maize Flour 25Kg",
            "quantity": 10,
            "unit_price": 50000,
        }
    ]
    """

    db = SessionLocal()

    try:

        order_number = _generate_number(
            prefix="SO",
            model=SalesOrder,
            field_name="order_number",
            db=db,
        )

        order = SalesOrder(
            order_number=order_number,
            customer_id=customer_id,
            status=status,
            total_amount=0,
            notes=notes,
        )

        db.add(order)

        db.flush()

        total_amount = 0.0

        for item_data in items:

            quantity = float(
                item_data.get(
                    "quantity",
                    0,
                )
            )

            unit_price = float(
                item_data.get(
                    "unit_price",
                    0,
                )
            )

            item_total = (
                quantity * unit_price
            )

            order_item = SalesOrderItem(
                sales_order_id=order.id,
                product_name=item_data.get(
                    "product_name",
                    "",
                ),
                quantity=quantity,
                unit_price=unit_price,
                total=item_total,
            )

            if hasattr(
                SalesOrderItem,
                "product_id",
            ):

                order_item.product_id = (
                    item_data.get(
                        "product_id"
                    )
                )

            db.add(
                order_item
            )

            total_amount += item_total

        order.total_amount = (
            total_amount
        )

        db.commit()

        db.refresh(order)

        return order

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def create_sales_order_from_quotation(
    quotation_id,
    status="Draft",
):
    """
    Convert an accepted quotation
    into a Sales Order.
    """

    db = SessionLocal()

    try:

        quotation = (
            db.query(Quotation)
            .options(
                joinedload(
                    Quotation.items
                )
            )
            .filter(
                Quotation.id
                == quotation_id
            )
            .first()
        )

        if not quotation:

            raise ValueError(
                "Quotation not found."
            )

        if quotation.status != "Accepted":

            raise ValueError(
                "Only accepted quotations "
                "can be converted to Sales Orders."
            )

        order_number = _generate_number(
            prefix="SO",
            model=SalesOrder,
            field_name="order_number",
            db=db,
        )

        order = SalesOrder(
            order_number=order_number,
            customer_id=quotation.customer_id,
            status=status,
            total_amount=0,
            notes=quotation.notes,
        )

        db.add(order)

        db.flush()

        total_amount = 0.0

        for quotation_item in (
            quotation.items
        ):

            item_total = (
                float(
                    quotation_item.quantity
                    or 0
                )
                *
                float(
                    quotation_item.unit_price
                    or 0
                )
            )

            order_item = SalesOrderItem(
                sales_order_id=order.id,
                product_name=(
                    quotation_item.product_name
                ),
                quantity=(
                    quotation_item.quantity
                ),
                unit_price=(
                    quotation_item.unit_price
                ),
                total=item_total,
            )

            if (
                hasattr(
                    SalesOrderItem,
                    "product_id",
                )
                and hasattr(
                    quotation_item,
                    "product_id",
                )
            ):

                order_item.product_id = (
                    quotation_item.product_id
                )

            db.add(
                order_item
            )

            total_amount += item_total

        order.total_amount = (
            total_amount
        )

        # Keep the quotation history.
        # We do not delete the quotation.

        db.commit()

        db.refresh(order)

        return order

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def update_sales_order(
    order_id,
    customer_id=None,
    items=None,
    status=None,
    notes=None,
):
    """Update an existing Sales Order."""

    db = SessionLocal()

    try:

        order = (
            db.query(SalesOrder)
            .options(
                joinedload(
                    SalesOrder.items
                )
            )
            .filter(
                SalesOrder.id == order_id
            )
            .first()
        )

        if not order:

            return None

        if customer_id is not None:

            order.customer_id = (
                customer_id
            )

        if status is not None:

            order.status = status

        if notes is not None:

            order.notes = notes

        if items is not None:

            # Remove existing items.
            for item in list(
                order.items
            ):

                db.delete(item)

            db.flush()

            total_amount = 0.0

            for item_data in items:

                quantity = float(
                    item_data.get(
                        "quantity",
                        0,
                    )
                )

                unit_price = float(
                    item_data.get(
                        "unit_price",
                        0,
                    )
                )

                item_total = (
                    quantity
                    * unit_price
                )

                order_item = SalesOrderItem(
                    sales_order_id=order.id,
                    product_name=item_data.get(
                        "product_name",
                        "",
                    ),
                    quantity=quantity,
                    unit_price=unit_price,
                    total=item_total,
                )

                if hasattr(
                    SalesOrderItem,
                    "product_id",
                ):

                    order_item.product_id = (
                        item_data.get(
                            "product_id"
                        )
                    )

                db.add(
                    order_item
                )

                total_amount += (
                    item_total
                )

            order.total_amount = (
                total_amount
            )

        db.commit()

        db.refresh(order)

        return order

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def update_sales_order_status(
    order_id,
    status,
):
    """Update only the Sales Order status."""

    if status not in SALES_ORDER_STATUSES:

        raise ValueError(
            f"Invalid Sales Order status: "
            f"{status}"
        )

    db = SessionLocal()

    try:

        order = (
            db.query(SalesOrder)
            .filter(
                SalesOrder.id == order_id
            )
            .first()
        )

        if not order:

            return None

        order.status = status

        db.commit()

        db.refresh(order)

        return order

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def delete_sales_order(
    order_id,
):
    """Delete a Sales Order and its items."""

    db = SessionLocal()

    try:

        order = (
            db.query(SalesOrder)
            .filter(
                SalesOrder.id == order_id
            )
            .first()
        )

        if not order:

            return False

        db.delete(order)

        db.commit()

        return True

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()