"""
Esan ERP - Sales Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Central business logic for:
- Customers
- Quotations
- Quotation Items
- Sales Orders
- Sales Order Items
- Deliveries
- Invoices
- Payments

The service layer keeps database operations out of the
Streamlit UI modules.
"""

import logging
from datetime import datetime

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
# LOGGING
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

QUOTATION_STATUSES = [
    "Draft",
    "Sent",
    "Accepted",
    "Rejected",
    "Expired",
    "Cancelled",
]

SALES_ORDER_STATUSES = [
    "Draft",
    "Pending Approval",
    "Approved",
    "Processing",
    "Partially Delivered",
    "Delivered",
    "Cancelled",
]

DELIVERY_STATUSES = [
    "Pending",
    "Partially Delivered",
    "Delivered",
    "Cancelled",
]

INVOICE_STATUSES = [
    "Draft",
    "Issued",
    "Partially Paid",
    "Paid",
    "Overdue",
    "Cancelled",
]

PAYMENT_STATUSES = [
    "Pending",
    "Completed",
    "Failed",
    "Cancelled",
]


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """

    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _clean_string(value):
    """
    Safely clean a string value.
    """

    if value is None:
        return ""

    return str(value).strip()


def _get_model_field(model, field_name, default=None):
    """
    Safely retrieve an attribute from a model instance.
    """

    return getattr(
        model,
        field_name,
        default,
    )


def _set_if_exists(obj, field_name, value):
    """
    Set a model field only when that field exists.

    This makes the service more tolerant of small schema
    differences while the ERP database evolves.
    """

    if hasattr(obj, field_name):
        setattr(
            obj,
            field_name,
            value,
        )


# ============================================================
# CUSTOMER MANAGEMENT
# ============================================================

def get_all_customers(
    active_only=False,
    search=None,
):
    """
    Return all customers.

    Parameters:
        active_only:
            Return only active customers when True.

        search:
            Optional search term for name, phone or email.
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

        if search:

            search_term = (
                f"%{search.strip()}%"
            )

            filters = []

            if hasattr(Customer, "name"):
                filters.append(
                    Customer.name.ilike(
                        search_term
                    )
                )

            if hasattr(Customer, "phone"):
                filters.append(
                    Customer.phone.ilike(
                        search_term
                    )
                )

            if hasattr(Customer, "email"):
                filters.append(
                    Customer.email.ilike(
                        search_term
                    )
                )

            if filters:

                from sqlalchemy import or_

                query = query.filter(
                    or_(*filters)
                )

        if hasattr(Customer, "name"):

            query = query.order_by(
                Customer.name.asc()
            )

        return query.all()

    except Exception:

        logger.exception(
            "Failed to retrieve customers"
        )

        raise

    finally:

        db.close()


def get_customer(customer_id):
    """
    Return a customer by ID.
    """

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


def create_customer(
    name,
    phone=None,
    email=None,
    address=None,
    customer_type="Retail",
):
    """
    Create a new customer.
    """

    name = _clean_string(name)

    if not name:

        raise ValueError(
            "Customer name is required."
        )

    db = SessionLocal()

    try:

        existing = (
            db.query(Customer)
            .filter(
                Customer.name.ilike(name)
            )
            .first()
        )

        if existing:

            raise ValueError(
                "A customer with this name "
                "already exists."
            )

        customer = Customer(
            name=name,
            phone=_clean_string(phone) or None,
            email=_clean_string(email) or None,
            address=_clean_string(address) or None,
            customer_type=(
                _clean_string(customer_type)
                or "Retail"
            ),
        )

        db.add(customer)

        db.commit()

        db.refresh(customer)

        return customer

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to create customer"
        )

        raise

    finally:

        db.close()


def update_customer(
    customer_id,
    name,
    phone=None,
    email=None,
    address=None,
    customer_type="Retail",
):
    """
    Update an existing customer.
    """

    name = _clean_string(name)

    if not name:

        raise ValueError(
            "Customer name is required."
        )

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
            .first()
        )

        if not customer:

            return None

        customer.name = name

        _set_if_exists(
            customer,
            "phone",
            _clean_string(phone) or None,
        )

        _set_if_exists(
            customer,
            "email",
            _clean_string(email) or None,
        )

        _set_if_exists(
            customer,
            "address",
            _clean_string(address) or None,
        )

        _set_if_exists(
            customer,
            "customer_type",
            _clean_string(
                customer_type
            ) or "Retail",
        )

        db.commit()

        db.refresh(customer)

        return customer

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to update customer"
        )

        raise

    finally:

        db.close()


def update_customer_status(
    customer_id,
    active,
):
    """
    Activate or deactivate a customer.
    """

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
            .first()
        )

        if not customer:

            return None

        if not hasattr(
            customer,
            "active",
        ):

            raise AttributeError(
                "Customer model does not contain "
                "an active field."
            )

        customer.active = bool(active)

        db.commit()

        db.refresh(customer)

        return customer

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def delete_customer(customer_id):
    """
    Delete a customer.

    In normal ERP operation, deactivation is preferable
    to deletion once transactions exist.
    """

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
            .first()
        )

        if not customer:

            return False

        db.delete(customer)

        db.commit()

        return True

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to delete customer"
        )

        raise

    finally:

        db.close()


# ============================================================
# PRODUCT LOOKUP
# ============================================================

def get_sales_products(
    active_only=False,
    search=None,
):
    """
    Retrieve products available for sales.
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

        if search and hasattr(
            Product,
            "name",
        ):

            query = query.filter(
                Product.name.ilike(
                    f"%{search.strip()}%"
                )
            )

        if hasattr(Product, "name"):

            query = query.order_by(
                Product.name.asc()
            )

        return query.all()

    finally:

        db.close()


def get_product(product_id):
    """
    Retrieve a product by ID.
    """

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
# QUOTATION NUMBER
# ============================================================

def generate_quotation_number(db=None):
    """
    Generate the next quotation number.

    Format:
        QT-00001
    """

    close_session = False

    if db is None:

        db = SessionLocal()

        close_session = True

    try:

        last = (
            db.query(Quotation)
            .order_by(
                Quotation.id.desc()
            )
            .first()
        )

        if not last:

            return "QT-00001"

        previous_number = _get_model_field(
            last,
            "quotation_number",
            "",
        )

        try:

            number = int(
                str(previous_number)
                .replace("QT-", "")
            )

            return f"QT-{number + 1:05d}"

        except (ValueError, TypeError):

            return (
                f"QT-{last.id + 1:05d}"
            )

    finally:

        if close_session:

            db.close()


# ============================================================
# QUOTATION MANAGEMENT
# ============================================================

def get_all_quotations(
    status=None,
    customer_id=None,
    search=None,
):
    """
    Retrieve quotations with optional filtering.
    """

    db = SessionLocal()

    try:

        query = db.query(Quotation)

        if status:

            query = query.filter(
                Quotation.status == status
            )

        if customer_id:

            query = query.filter(
                Quotation.customer_id
                == customer_id
            )

        if search:

            search_term = (
                f"%{search.strip()}%"
            )

            filters = []

            if hasattr(
                Quotation,
                "quotation_number",
            ):

                filters.append(
                    Quotation.quotation_number.ilike(
                        search_term
                    )
                )

            if filters:

                from sqlalchemy import or_

                query = query.filter(
                    or_(*filters)
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


def get_quotation(quotation_id):
    """
    Retrieve one quotation.
    """

    db = SessionLocal()

    try:

        return (
            db.query(Quotation)
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
    status="Draft",
    valid_until=None,
    notes=None,
):
    """
    Create quotation and quotation items.

    items format:

    [
        {
            "product_name": "Maize Flour",
            "quantity": 100,
            "unit_price": 5000
        }
    ]
    """

    if not items:

        raise ValueError(
            "Quotation must contain at least "
            "one item."
        )

    if status not in QUOTATION_STATUSES:

        raise ValueError(
            f"Invalid quotation status: {status}"
        )

    db = SessionLocal()

    try:

        quotation_number = (
            generate_quotation_number(db)
        )

        quotation = Quotation(
            quotation_number=quotation_number,
            customer_id=customer_id,
            status=status,
            total_amount=0.0,
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

        db.add(quotation)

        db.flush()

        total_amount = 0.0

        for item_data in items:

            product_name = _clean_string(
                item_data.get(
                    "product_name"
                )
            )

            quantity = _safe_float(
                item_data.get(
                    "quantity"
                )
            )

            unit_price = _safe_float(
                item_data.get(
                    "unit_price"
                )
            )

            if not product_name:

                raise ValueError(
                    "Product name is required."
                )

            if quantity <= 0:

                raise ValueError(
                    f"Quantity for "
                    f"{product_name} must be "
                    "greater than zero."
                )

            if unit_price < 0:

                raise ValueError(
                    f"Unit price for "
                    f"{product_name} cannot "
                    "be negative."
                )

            item_total = (
                quantity * unit_price
            )

            quotation_item = QuotationItem(
                quotation_id=quotation.id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total=item_total,
            )

            db.add(quotation_item)

            total_amount += item_total

        quotation.total_amount = total_amount

        db.commit()

        db.refresh(quotation)

        return quotation

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to create quotation"
        )

        raise

    finally:

        db.close()


def update_quotation(
    quotation_id,
    customer_id,
    items,
    status="Draft",
    valid_until=None,
    notes=None,
):
    """
    Update quotation and replace its items.
    """

    if not items:

        raise ValueError(
            "Quotation must contain at least "
            "one item."
        )

    if status not in QUOTATION_STATUSES:

        raise ValueError(
            f"Invalid quotation status: {status}"
        )

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

        quotation.customer_id = customer_id
        quotation.status = status
        quotation.total_amount = 0.0

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

        # Remove old items.
        for old_item in list(
            quotation.items
        ):

            db.delete(old_item)

        db.flush()

        total_amount = 0.0

        for item_data in items:

            product_name = _clean_string(
                item_data.get(
                    "product_name"
                )
            )

            quantity = _safe_float(
                item_data.get(
                    "quantity"
                )
            )

            unit_price = _safe_float(
                item_data.get(
                    "unit_price"
                )
            )

            if not product_name:

                raise ValueError(
                    "Product name is required."
                )

            if quantity <= 0:

                raise ValueError(
                    f"Quantity for "
                    f"{product_name} must be "
                    "greater than zero."
                )

            item_total = (
                quantity * unit_price
            )

            quotation_item = QuotationItem(
                quotation_id=quotation.id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total=item_total,
            )

            db.add(quotation_item)

            total_amount += item_total

        quotation.total_amount = total_amount

        db.commit()

        db.refresh(quotation)

        return quotation

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def update_quotation_status(
    quotation_id,
    status,
):
    """
    Change quotation status.
    """

    if status not in QUOTATION_STATUSES:

        raise ValueError(
            f"Invalid quotation status: {status}"
        )

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

    finally:

        db.close()


def delete_quotation(
    quotation_id,
):
    """
    Delete quotation and associated items.
    """

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

        db.delete(quotation)

        db.commit()

        return True

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# SALES ORDER NUMBER
# ============================================================

def generate_sales_order_number(
    db=None,
):
    """
    Generate the next sales order number.

    Format:
        SO-00001
    """

    close_session = False

    if db is None:

        db = SessionLocal()

        close_session = True

    try:

        last = (
            db.query(SalesOrder)
            .order_by(
                SalesOrder.id.desc()
            )
            .first()
        )

        if not last:

            return "SO-00001"

        previous_number = _get_model_field(
            last,
            "order_number",
            "",
        )

        if not previous_number:

            previous_number = _get_model_field(
                last,
                "so_number",
                "",
            )

        try:

            number = int(
                str(previous_number)
                .replace("SO-", "")
            )

            return f"SO-{number + 1:05d}"

        except (ValueError, TypeError):

            return (
                f"SO-{last.id + 1:05d}"
            )

    finally:

        if close_session:

            db.close()


# ============================================================
# SALES ORDER MANAGEMENT
# ============================================================

def get_all_sales_orders(
    status=None,
    customer_id=None,
    search=None,
):
    """
    Retrieve sales orders.
    """

    db = SessionLocal()

    try:

        query = db.query(SalesOrder)

        if status:

            query = query.filter(
                SalesOrder.status == status
            )

        if customer_id:

            query = query.filter(
                SalesOrder.customer_id
                == customer_id
            )

        if search:

            search_term = (
                f"%{search.strip()}%"
            )

            filters = []

            if hasattr(
                SalesOrder,
                "order_number",
            ):

                filters.append(
                    SalesOrder.order_number.ilike(
                        search_term
                    )
                )

            if hasattr(
                SalesOrder,
                "so_number",
            ):

                filters.append(
                    SalesOrder.so_number.ilike(
                        search_term
                    )
                )

            if filters:

                from sqlalchemy import or_

                query = query.filter(
                    or_(*filters)
                )

        return (
            query
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
    """
    Retrieve one sales order.
    """

    db = SessionLocal()

    try:

        return (
            db.query(SalesOrder)
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
    quotation_id=None,
    notes=None,
):
    """
    Create a sales order.

    Items format:

    [
        {
            "product_name": "Maize Flour",
            "quantity": 100,
            "unit_price": 5000
        }
    ]
    """

    if not items:

        raise ValueError(
            "Sales order must contain at least "
            "one item."
        )

    if status not in SALES_ORDER_STATUSES:

        raise ValueError(
            f"Invalid sales order status: {status}"
        )

    db = SessionLocal()

    try:

        order_number = (
            generate_sales_order_number(db)
        )

        order_kwargs = {
            "customer_id": customer_id,
            "status": status,
            "total_amount": 0.0,
        }

        # Support common model naming.
        if hasattr(
            SalesOrder,
            "order_number",
        ):

            order_kwargs[
                "order_number"
            ] = order_number

        elif hasattr(
            SalesOrder,
            "so_number",
        ):

            order_kwargs[
                "so_number"
            ] = order_number

        if hasattr(
            SalesOrder,
            "quotation_id",
        ):

            order_kwargs[
                "quotation_id"
            ] = quotation_id

        order = SalesOrder(
            **order_kwargs
        )

        _set_if_exists(
            order,
            "notes",
            notes,
        )

        db.add(order)

        db.flush()

        total_amount = 0.0

        for item_data in items:

            product_name = _clean_string(
                item_data.get(
                    "product_name"
                )
            )

            quantity = _safe_float(
                item_data.get(
                    "quantity"
                )
            )

            unit_price = _safe_float(
                item_data.get(
                    "unit_price"
                )
            )

            if not product_name:

                raise ValueError(
                    "Product name is required."
                )

            if quantity <= 0:

                raise ValueError(
                    f"Quantity for "
                    f"{product_name} must be "
                    "greater than zero."
                )

            if unit_price < 0:

                raise ValueError(
                    f"Unit price for "
                    f"{product_name} cannot "
                    "be negative."
                )

            item_total = (
                quantity * unit_price
            )

            item_kwargs = {
                "sales_order_id": order.id,
                "product_name": product_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "total": item_total,
            }

            sales_order_item = SalesOrderItem(
                **item_kwargs
            )

            db.add(
                sales_order_item
            )

            total_amount += item_total

        order.total_amount = total_amount

        db.commit()

        db.refresh(order)

        return order

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to create sales order"
        )

        raise

    finally:

        db.close()


def update_sales_order_status(
    order_id,
    status,
):
    """
    Change sales order status.
    """

    if status not in SALES_ORDER_STATUSES:

        raise ValueError(
            f"Invalid sales order status: {status}"
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
    """
    Delete a sales order.
    """

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


# ============================================================
# SALES ORDER FROM QUOTATION
# ============================================================

def create_sales_order_from_quotation(
    quotation_id,
    status="Draft",
):
    """
    Convert an accepted quotation into a sales order.
    """

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

            raise ValueError(
                "Quotation not found."
            )

        if quotation.status != "Accepted":

            raise ValueError(
                "Only an accepted quotation "
                "can be converted into a "
                "sales order."
            )

        existing_orders = []

        if hasattr(
            quotation,
            "sales_orders",
        ):

            existing_orders = (
                quotation.sales_orders
                or []
            )

        if existing_orders:

            raise ValueError(
                "This quotation has already "
                "been converted into a "
                "sales order."
            )

        order_number = (
            generate_sales_order_number(db)
        )

        order_kwargs = {
            "customer_id":
                quotation.customer_id,

            "status":
                status,

            "total_amount":
                quotation.total_amount or 0.0,
        }

        if hasattr(
            SalesOrder,
            "order_number",
        ):

            order_kwargs[
                "order_number"
            ] = order_number

        elif hasattr(
            SalesOrder,
            "so_number",
        ):

            order_kwargs[
                "so_number"
            ] = order_number

        if hasattr(
            SalesOrder,
            "quotation_id",
        ):

            order_kwargs[
                "quotation_id"
            ] = quotation.id

        order = SalesOrder(
            **order_kwargs
        )

        _set_if_exists(
            order,
            "notes",
            (
                f"Created from "
                f"{quotation.quotation_number}"
            ),
        )

        db.add(order)

        db.flush()

        for quotation_item in quotation.items:

            sales_order_item = SalesOrderItem(
                sales_order_id=order.id,
                product_name=quotation_item.product_name,
                quantity=quotation_item.quantity,
                unit_price=quotation_item.unit_price,
                total=quotation_item.total,
            )

            db.add(
                sales_order_item
            )

        db.commit()

        db.refresh(order)

        return order

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# SALES SUMMARY
# ============================================================

def get_sales_summary():
    """
    Return high-level sales statistics.
    """

    db = SessionLocal()

    try:

        customers_count = (
            db.query(Customer)
            .count()
        )

        quotations_count = (
            db.query(Quotation)
            .count()
        )

        sales_orders_count = (
            db.query(SalesOrder)
            .count()
        )

        quotation_value = sum(
            _safe_float(
                quotation.total_amount
            )
            for quotation
            in db.query(Quotation).all()
        )

        sales_order_value = sum(
            _safe_float(
                order.total_amount
            )
            for order
            in db.query(SalesOrder).all()
        )

        return {
            "customers":
                customers_count,

            "quotations":
                quotations_count,

            "sales_orders":
                sales_orders_count,

            "quotation_value":
                quotation_value,

            "sales_order_value":
                sales_order_value,
        }

    finally:

        db.close()


# ============================================================
# SALES DASHBOARD METRICS
# ============================================================

def get_sales_dashboard_metrics():
    """
    Return metrics suitable for the Sales dashboard.
    """

    summary = get_sales_summary()

    return {
        "customers":
            summary["customers"],

        "quotations":
            summary["quotations"],

        "sales_orders":
            summary["sales_orders"],

        "quotation_value":
            summary["quotation_value"],

        "sales_order_value":
            summary["sales_order_value"],
    }


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    # Customers
    "get_all_customers",
    "get_customer",
    "create_customer",
    "update_customer",
    "update_customer_status",
    "delete_customer",

    # Products
    "get_sales_products",
    "get_product",

    # Quotations
    "generate_quotation_number",
    "get_all_quotations",
    "get_quotation",
    "create_quotation",
    "update_quotation",
    "update_quotation_status",
    "delete_quotation",

    # Sales Orders
    "generate_sales_order_number",
    "get_all_sales_orders",
    "get_sales_order",
    "create_sales_order",
    "update_sales_order_status",
    "delete_sales_order",
    "create_sales_order_from_quotation",

    # Dashboard
    "get_sales_summary",
    "get_sales_dashboard_metrics",
]