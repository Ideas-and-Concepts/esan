"""
Esan ERP
Invoice Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from models import (
    Invoice,
    InvoiceItem,
    Customer,
    Product,
    SalesOrder,
    SalesOrderItem,
    Delivery,
)


# ==========================================================
# HELPERS
# ==========================================================

def _get(obj, field, default=None):
    return getattr(obj, field, default)


def _decimal(value):
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")


def _commit(db):
    db.commit()


def _rollback(db):
    try:
        db.rollback()
    except Exception:
        pass


# ==========================================================
# GET INVOICES
# ==========================================================

def get_all_invoices(db: Session):
    """
    Return all invoices, newest first.
    """
    return (
        db.query(Invoice)
        .order_by(Invoice.id.desc())
        .all()
    )


def get_invoice(
    db: Session,
    invoice_id: int,
):
    """
    Return one invoice by ID.
    """
    return (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id)
        .first()
    )


def get_invoice_items(
    db: Session,
    invoice_id: int,
):
    """
    Return invoice line items.
    """
    return (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.invoice_id == invoice_id
        )
        .order_by(InvoiceItem.id)
        .all()
    )


# ==========================================================
# TOTAL
# ==========================================================

def calculate_invoice_total(
    db: Session,
    invoice_id: int,
):
    """
    Calculate invoice total from invoice items.
    """

    items = get_invoice_items(
        db,
        invoice_id,
    )

    total = Decimal("0")

    for item in items:

        quantity = _decimal(
            _get(item, "quantity", 0)
        )

        unit_price = _decimal(
            _get(item, "unit_price", 0)
        )

        total += quantity * unit_price

    return total


# ==========================================================
# CREATE INVOICE
# ==========================================================

def create_invoice(
    db: Session,
    customer_id: int,
    sales_order_id=None,
    delivery_id=None,
    invoice_date=None,
    due_date=None,
    notes=None,
):
    """
    Create a draft invoice.
    """

    if not customer_id:
        raise ValueError(
            "Customer is required."
        )

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        raise ValueError(
            "Customer not found."
        )

    invoice = Invoice(
        customer_id=customer_id,
        sales_order_id=sales_order_id,
        delivery_id=delivery_id,
        invoice_date=invoice_date or datetime.utcnow(),
        due_date=due_date,
        notes=notes,
        status="Draft",
        total=0,
    )

    db.add(invoice)

    try:
        _commit(db)
        db.refresh(invoice)
        return invoice

    except Exception:
        _rollback(db)
        raise


# ==========================================================
# CREATE FROM SALES ORDER
# ==========================================================

def create_invoice_from_sales_order(
    db: Session,
    sales_order_id: int,
    due_date=None,
    notes=None,
):
    """
    Create a draft invoice using the Sales Order lines.
    """

    order = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.id == sales_order_id
        )
        .first()
    )

    if not order:
        raise ValueError(
            "Sales Order not found."
        )

    customer_id = _get(
        order,
        "customer_id",
    )

    if not customer_id:
        raise ValueError(
            "Sales Order has no customer."
        )

    existing = (
        db.query(Invoice)
        .filter(
            Invoice.sales_order_id
            == sales_order_id,
            Invoice.status != "Void",
        )
        .first()
    )

    if existing:
        raise ValueError(
            f"Invoice #{existing.id} already exists "
            "for this Sales Order."
        )

    invoice = create_invoice(
        db=db,
        customer_id=customer_id,
        sales_order_id=sales_order_id,
        due_date=due_date,
        notes=notes,
    )

    order_items = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == sales_order_id
        )
        .all()
    )

    if not order_items:
        raise ValueError(
            "Sales Order contains no items."
        )

    try:

        for order_item in order_items:

            quantity = _decimal(
                _get(
                    order_item,
                    "quantity",
                    0,
                )
            )

            unit_price = _decimal(
                _get(
                    order_item,
                    "unit_price",
                    _get(
                        order_item,
                        "price",
                        0,
                    ),
                )
            )

            item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=order_item.product_id,
                description=_get(
                    order_item,
                    "description",
                    None,
                ),
                quantity=quantity,
                unit_price=unit_price,
                total=quantity * unit_price,
            )

            db.add(item)

        db.flush()

        invoice.total = calculate_invoice_total(
            db,
            invoice.id,
        )

        db.commit()
        db.refresh(invoice)

        return invoice

    except Exception:
        _rollback(db)

        # Remove partially created invoice if necessary.
        try:
            if invoice.id:
                db.delete(invoice)
                db.commit()
        except Exception:
            _rollback(db)

        raise


# ==========================================================
# CREATE FROM DELIVERY
# ==========================================================

def create_invoice_from_delivery(
    db: Session,
    delivery_id: int,
    due_date=None,
    notes=None,
):
    """
    Create a draft invoice from a delivery.

    This function is intentionally defensive because
    different versions of the Delivery model may use
    different Sales Order relationship fields.
    """

    delivery = (
        db.query(Delivery)
        .filter(
            Delivery.id == delivery_id
        )
        .first()
    )

    if not delivery:
        raise ValueError(
            "Delivery not found."
        )

    sales_order_id = _get(
        delivery,
        "sales_order_id",
        _get(
            delivery,
            "order_id",
            None,
        ),
    )

    customer_id = _get(
        delivery,
        "customer_id",
    )

    if not customer_id and sales_order_id:

        order = (
            db.query(SalesOrder)
            .filter(
                SalesOrder.id
                == sales_order_id
            )
            .first()
        )

        if order:
            customer_id = order.customer_id

    if not customer_id:
        raise ValueError(
            "Could not determine the customer "
            "for this delivery."
        )

    existing = (
        db.query(Invoice)
        .filter(
            Invoice.delivery_id == delivery_id,
            Invoice.status != "Void",
        )
        .first()
    )

    if existing:
        raise ValueError(
            f"Invoice #{existing.id} already exists "
            "for this delivery."
        )

    if sales_order_id:

        return create_invoice_from_sales_order(
            db=db,
            sales_order_id=sales_order_id,
            due_date=due_date,
            notes=notes,
        )

    return create_invoice(
        db=db,
        customer_id=customer_id,
        delivery_id=delivery_id,
        due_date=due_date,
        notes=notes,
    )


# ==========================================================
# UPDATE INVOICE
# ==========================================================

def update_invoice(
    db: Session,
    invoice_id: int,
    customer_id=None,
    invoice_date=None,
    due_date=None,
    notes=None,
):
    """
    Update a Draft invoice only.
    """

    invoice = get_invoice(
        db,
        invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    status = _get(
        invoice,
        "status",
        "Draft",
    )

    if str(status).lower() != "draft":
        raise ValueError(
            "Only Draft invoices can be edited."
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

        invoice.customer_id = customer_id

    if invoice_date is not None:
        invoice.invoice_date = invoice_date

    if due_date is not None:
        invoice.due_date = due_date

    if notes is not None:
        invoice.notes = notes

    try:

        invoice.total = calculate_invoice_total(
            db,
            invoice.id,
        )

        _commit(db)
        db.refresh(invoice)

        return invoice

    except Exception:
        _rollback(db)
        raise


# ==========================================================
# ADD ITEM
# ==========================================================

def add_invoice_item(
    db: Session,
    invoice_id: int,
    product_id: int,
    quantity,
    unit_price,
    description=None,
):
    """
    Add an item to a Draft invoice.
    """

    invoice = get_invoice(
        db,
        invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    if str(
        _get(invoice, "status", "Draft")
    ).lower() != "draft":
        raise ValueError(
            "Only Draft invoices can be edited."
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

    quantity = _decimal(quantity)
    unit_price = _decimal(unit_price)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    if unit_price < 0:
        raise ValueError(
            "Unit price cannot be negative."
        )

    item = InvoiceItem(
        invoice_id=invoice_id,
        product_id=product_id,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        total=quantity * unit_price,
    )

    db.add(item)

    try:

        db.flush()

        invoice.total = calculate_invoice_total(
            db,
            invoice_id,
        )

        _commit(db)

        db.refresh(item)

        return item

    except Exception:
        _rollback(db)
        raise


# ==========================================================
# UPDATE ITEM
# ==========================================================

def update_invoice_item(
    db: Session,
    item_id: int,
    quantity,
    unit_price,
    description=None,
):
    """
    Update a Draft invoice item.
    """

    item = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.id == item_id
        )
        .first()
    )

    if not item:
        raise ValueError(
            "Invoice item not found."
        )

    invoice = get_invoice(
        db,
        item.invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    if str(
        _get(invoice, "status", "Draft")
    ).lower() != "draft":
        raise ValueError(
            "Only Draft invoices can be edited."
        )

    quantity = _decimal(quantity)
    unit_price = _decimal(unit_price)

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

    if description is not None:
        item.description = description

    try:

        db.flush()

        invoice.total = calculate_invoice_total(
            db,
            invoice.id,
        )

        _commit(db)

        return item

    except Exception:
        _rollback(db)
        raise


# ==========================================================
# DELETE ITEM
# ==========================================================

def delete_invoice_item(
    db: Session,
    item_id: int,
):
    """
    Delete a Draft invoice item.
    """

    item = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.id == item_id
        )
        .first()
    )

    if not item:
        raise ValueError(
            "Invoice item not found."
        )

    invoice = get_invoice(
        db,
        item.invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    if str(
        _get(invoice, "status", "Draft")
    ).lower() != "draft":
        raise ValueError(
            "Only Draft invoices can be edited."
        )

    try:

        db.delete(item)
        db.flush()

        invoice.total = calculate_invoice_total(
            db,
            invoice.id,
        )

        _commit(db)

    except Exception:
        _rollback(db)
        raise


# ==========================================================
# POST INVOICE
# ==========================================================

def post_invoice(
    db: Session,
    invoice_id: int,
):
    """
    Post an invoice.

    Posted invoices become read-only and form
    the Accounts Receivable balance.
    """

    invoice = get_invoice(
        db,
        invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    status = str(
        _get(invoice, "status", "Draft")
    ).lower()

    if status == "posted":
        raise ValueError(
            "Invoice is already posted."
        )

    if status in (
        "void",
        "voided",
        "cancelled",
        "canceled",
    ):
        raise ValueError(
            "A void or cancelled invoice cannot be posted."
        )

    items = get_invoice_items(
        db,
        invoice_id,
    )

    if not items:
        raise ValueError(
            "Cannot post an invoice with no items."
        )

    total = calculate_invoice_total(
        db,
        invoice_id,
    )

    if total <= 0:
        raise ValueError(
            "Invoice total must be greater than zero."
        )

    try:

        invoice.total = total
        invoice.status = "Posted"

        if hasattr(
            invoice,
            "posted_at",
        ):
            invoice.posted_at = datetime.utcnow()

        _commit(db)
        db.refresh(invoice)

        return invoice

    except Exception:
        _rollback(db)
        raise


# ==========================================================
# VOID INVOICE
# ==========================================================

def void_invoice(
    db: Session,
    invoice_id: int,
    reason=None,
):
    """
    Void an invoice.

    A posted invoice is never deleted. It is voided
    so that the accounting trail remains intact.
    """

    invoice = get_invoice(
        db,
        invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    status = str(
        _get(invoice, "status", "Draft")
    ).lower()

    if status in (
        "void",
        "voided",
    ):
        raise ValueError(
            "Invoice is already void."
        )

    if status == "draft":
        invoice.status = "Void"

    else:

        invoice.status = "Void"

        if hasattr(
            invoice,
            "voided_at",
        ):
            invoice.voided_at = datetime.utcnow()

        if reason and hasattr(
            invoice,
            "void_reason",
        ):
            invoice.void_reason = reason

    try:

        _commit(db)
        db.refresh(invoice)

        return invoice

    except Exception:
        _rollback(db)
        raise


# ==========================================================
# ACCOUNTS RECEIVABLE
# ==========================================================

def get_invoice_balance(
    db: Session,
    invoice_id: int,
):
    """
    Return invoice balance.

    This function is intentionally payment-service
    independent. Once payments are connected, the
    payment service can supply the collected amount.
    """

    invoice = get_invoice(
        db,
        invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    total = calculate_invoice_total(
        db,
        invoice_id,
    )

    paid = _decimal(
        _get(
            invoice,
            "paid_amount",
            0,
        )
    )

    balance = total - paid

    if balance < 0:
        balance = Decimal("0")

    return {
        "total": total,
        "paid": paid,
        "balance": balance,
    }