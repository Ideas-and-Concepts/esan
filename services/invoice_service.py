"""
Esan ERP
Invoice Service

Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from models import Invoice, InvoiceItem, Customer
from services.finance_service import post_invoice_to_finance


# ==========================================================
# HELPERS
# ==========================================================

def _decimal(value):
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")


def _get(obj, field, default=None):
    return getattr(obj, field, default)


# ==========================================================
# GET INVOICES
# ==========================================================

def get_invoices(db: Session):
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
    Return one invoice.
    """

    return (
        db.query(Invoice)
        .filter(
            Invoice.id == invoice_id
        )
        .first()
    )


def get_customer_invoices(
    db: Session,
    customer_id: int,
):
    """
    Return invoices belonging to a customer.
    """

    return (
        db.query(Invoice)
        .filter(
            Invoice.customer_id == customer_id
        )
        .order_by(
            Invoice.id.desc()
        )
        .all()
    )


# ==========================================================
# CALCULATE TOTAL
# ==========================================================

def calculate_invoice_total(
    items,
):
    """
    Calculate invoice total from line items.
    """

    total = Decimal("0")

    for item in items:

        quantity = _decimal(
            item.get("quantity", 0)
        )

        unit_price = _decimal(
            item.get("unit_price", 0)
        )

        total += quantity * unit_price

    return total


# ==========================================================
# CREATE INVOICE
# ==========================================================

def create_invoice(
    db: Session,
    customer_id: int,
    items: list,
    invoice_date=None,
    due_date=None,
    notes=None,
):
    """
    Create a Draft invoice.

    Example:

    items = [
        {
            "product_id": 1,
            "description": "Maize Flour 25kg",
            "quantity": 10,
            "unit_price": 45000,
        }
    ]
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

    if not items:
        raise ValueError(
            "Invoice must contain at least "
            "one item."
        )

    total = calculate_invoice_total(
        items
    )

    if total <= 0:
        raise ValueError(
            "Invoice total must be greater than zero."
        )

    invoice = Invoice(
        customer_id=customer_id,
    )

    if hasattr(
        invoice,
        "invoice_date",
    ):
        invoice.invoice_date = (
            invoice_date
            or datetime.utcnow()
        )

    if hasattr(
        invoice,
        "due_date",
    ):
        invoice.due_date = due_date

    if hasattr(
        invoice,
        "notes",
    ):
        invoice.notes = notes

    if hasattr(
        invoice,
        "status",
    ):
        invoice.status = "Draft"

    if hasattr(
        invoice,
        "total",
    ):
        invoice.total = total

    elif hasattr(
        invoice,
        "total_amount",
    ):
        invoice.total_amount = total

    db.add(invoice)
    db.flush()

    for item in items:

        quantity = _decimal(
            item.get("quantity", 0)
        )

        unit_price = _decimal(
            item.get("unit_price", 0)
        )

        line_total = (
            quantity * unit_price
        )

        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=item.get(
                "product_id"
            ),
            quantity=quantity,
            unit_price=unit_price,
        )

        if hasattr(
            invoice_item,
            "description",
        ):
            invoice_item.description = (
                item.get("description")
            )

        if hasattr(
            invoice_item,
            "total",
        ):
            invoice_item.total = line_total

        elif hasattr(
            invoice_item,
            "line_total",
        ):
            invoice_item.line_total = (
                line_total
            )

        db.add(invoice_item)

    try:

        db.commit()
        db.refresh(invoice)

        return invoice

    except Exception:

        db.rollback()
        raise


# ==========================================================
# EDIT INVOICE
# ==========================================================

def update_invoice(
    db: Session,
    invoice_id: int,
    customer_id=None,
    items=None,
    invoice_date=None,
    due_date=None,
    notes=None,
):
    """
    Edit a Draft invoice.

    Posted invoices should not be edited.
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
        _get(
            invoice,
            "status",
            "Draft",
        )
    ).lower()

    if status not in (
        "draft",
        "pending",
    ):
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

    if invoice_date is not None and hasattr(
        invoice,
        "invoice_date",
    ):
        invoice.invoice_date = invoice_date

    if due_date is not None and hasattr(
        invoice,
        "due_date",
    ):
        invoice.due_date = due_date

    if notes is not None and hasattr(
        invoice,
        "notes",
    ):
        invoice.notes = notes

    if items is not None:

        if not items:
            raise ValueError(
                "Invoice must contain at least "
                "one item."
            )

        db.query(InvoiceItem).filter(
            InvoiceItem.invoice_id
            == invoice.id
        ).delete(
            synchronize_session=False
        )

        total = calculate_invoice_total(
            items
        )

        for item in items:

            quantity = _decimal(
                item.get("quantity", 0)
            )

            unit_price = _decimal(
                item.get("unit_price", 0)
            )

            line_total = (
                quantity * unit_price
            )

            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=item.get(
                    "product_id"
                ),
                quantity=quantity,
                unit_price=unit_price,
            )

            if hasattr(
                invoice_item,
                "description",
            ):
                invoice_item.description = (
                    item.get("description")
                )

            if hasattr(
                invoice_item,
                "total",
            ):
                invoice_item.total = line_total

            elif hasattr(
                invoice_item,
                "line_total",
            ):
                invoice_item.line_total = (
                    line_total
                )

            db.add(invoice_item)

        if hasattr(
            invoice,
            "total",
        ):
            invoice.total = total

        elif hasattr(
            invoice,
            "total_amount",
        ):
            invoice.total_amount = total

    try:

        db.commit()
        db.refresh(invoice)

        return invoice

    except Exception:

        db.rollback()
        raise


# ==========================================================
# POST INVOICE
# ==========================================================

def post_invoice(
    db: Session,
    invoice_id: int,
):
    """
    Post invoice and integrate it with Finance.

    Accounting:

        DR Accounts Receivable
        CR Sales Revenue
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
        _get(
            invoice,
            "status",
            "Draft",
        )
    ).lower()

    if status in (
        "void",
        "voided",
    ):
        raise ValueError(
            "A voided invoice cannot be posted."
        )

    if status == "posted":
        raise ValueError(
            "Invoice is already posted."
        )

    if status == "paid":
        raise ValueError(
            "Invoice is already paid."
        )

    # Ensure total exists.
    total = _decimal(
        _get(
            invoice,
            "total",
            0,
        )
    )

    if total <= 0:

        total = _decimal(
            _get(
                invoice,
                "total_amount",
                0,
            )
        )

    if total <= 0:
        raise ValueError(
            "Invoice total must be greater than zero."
        )

    try:

        # Set operational status first.
        if hasattr(
            invoice,
            "status",
        ):
            invoice.status = "Posted"

        if hasattr(
            invoice,
            "posted_at",
        ):
            invoice.posted_at = (
                datetime.utcnow()
            )

        db.flush()

        # Create Finance journal entry.
        finance_entry = (
            post_invoice_to_finance(
                db,
                invoice.id,
            )
        )

        db.commit()
        db.refresh(invoice)

        return invoice

    except Exception:

        db.rollback()
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

    A posted invoice is not physically deleted.
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
        _get(
            invoice,
            "status",
            "Draft",
        )
    ).lower()

    if status == "void":
        raise ValueError(
            "Invoice is already voided."
        )

    if status == "paid":
        raise ValueError(
            "A paid invoice cannot be voided."
        )

    if hasattr(
        invoice,
        "status",
    ):
        invoice.status = "Void"

    if reason and hasattr(
        invoice,
        "notes",
    ):
        current_notes = (
            invoice.notes or ""
        )

        invoice.notes = (
            f"{current_notes}\n"
            f"Void reason: {reason}"
        ).strip()

    try:

        db.commit()
        db.refresh(invoice)

        return invoice

    except Exception:

        db.rollback()
        raise


# ==========================================================
# DELETE DRAFT INVOICE
# ==========================================================

def delete_invoice(
    db: Session,
    invoice_id: int,
):
    """
    Delete an invoice only when it is still Draft.
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
        _get(
            invoice,
            "status",
            "Draft",
        )
    ).lower()

    if status not in (
        "draft",
        "pending",
    ):
        raise ValueError(
            "Only Draft invoices can be deleted."
        )

    try:

        db.delete(invoice)
        db.commit()

        return True

    except Exception:

        db.rollback()
        raise


# ==========================================================
# INVOICE BALANCE
# ==========================================================

def get_invoice_balance(
    db: Session,
    invoice_id: int,
):
    """
    Calculate outstanding balance on an invoice.
    """

    from models import Payment

    invoice = get_invoice(
        db,
        invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    total = _decimal(
        _get(
            invoice,
            "total",
            0,
        )
    )

    if total <= 0:
        total = _decimal(
            _get(
                invoice,
                "total_amount",
                0,
            )
        )

    payments = (
        db.query(Payment)
        .filter(
            Payment.invoice_id
            == invoice.id
        )
        .filter(
            Payment.status
            == "Posted"
        )
        .all()
    )

    paid = sum(
        (
            _decimal(
                _get(
                    payment,
                    "amount",
                    0,
                )
            )
            for payment in payments
        ),
        Decimal("0"),
    )

    return max(
        total - paid,
        Decimal("0"),
    )