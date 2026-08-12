"""
Esan ERP
Payment Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from models import Payment, Invoice, Customer


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
# PAYMENT NUMBER
# ==========================================================

def generate_payment_number(db: Session):
    """
    Generate a simple sequential payment number.

    Example:
        PAY-00001
        PAY-00002
    """

    last_payment = (
        db.query(Payment)
        .order_by(Payment.id.desc())
        .first()
    )

    if not last_payment:
        next_id = 1
    else:
        next_id = int(
            _get(last_payment, "id", 0) or 0
        ) + 1

    return f"PAY-{next_id:05d}"


# ==========================================================
# GET PAYMENTS
# ==========================================================

def get_all_payments(db: Session):
    """
    Return all payments, newest first.
    """

    return (
        db.query(Payment)
        .order_by(Payment.id.desc())
        .all()
    )


def get_payment(
    db: Session,
    payment_id: int,
):
    """
    Return one payment.
    """

    return (
        db.query(Payment)
        .filter(
            Payment.id == payment_id
        )
        .first()
    )


def get_invoice_payments(
    db: Session,
    invoice_id: int,
):
    """
    Return payments belonging to an invoice.
    """

    return (
        db.query(Payment)
        .filter(
            Payment.invoice_id == invoice_id
        )
        .order_by(Payment.id.desc())
        .all()
    )


def get_customer_payments(
    db: Session,
    customer_id: int,
):
    """
    Return payments belonging to a customer.
    """

    return (
        db.query(Payment)
        .filter(
            Payment.customer_id == customer_id
        )
        .order_by(Payment.id.desc())
        .all()
    )


# ==========================================================
# INVOICE BALANCE
# ==========================================================

def calculate_invoice_paid_amount(
    db: Session,
    invoice_id: int,
):
    """
    Calculate total successfully posted payments
    against an invoice.
    """

    payments = get_invoice_payments(
        db,
        invoice_id,
    )

    total = Decimal("0")

    for payment in payments:

        status = str(
            _get(
                payment,
                "status",
                "Draft",
            )
        ).lower()

        if status != "posted":
            continue

        total += _decimal(
            _get(
                payment,
                "amount",
                0,
            )
        )

    return total


def calculate_invoice_total(
    db: Session,
    invoice_id: int,
):
    """
    Calculate invoice total from InvoiceItem records.

    Uses a local import to avoid unnecessary model
    dependency issues.
    """

    try:

        from models import InvoiceItem

        items = (
            db.query(InvoiceItem)
            .filter(
                InvoiceItem.invoice_id
                == invoice_id
            )
            .all()
        )

        total = Decimal("0")

        for item in items:

            quantity = _decimal(
                _get(
                    item,
                    "quantity",
                    0,
                )
            )

            unit_price = _decimal(
                _get(
                    item,
                    "unit_price",
                    0,
                )
            )

            item_total = _get(
                item,
                "total",
                None,
            )

            if item_total is not None:
                total += _decimal(item_total)
            else:
                total += (
                    quantity * unit_price
                )

        return total

    except Exception:

        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.id == invoice_id
            )
            .first()
        )

        if invoice:
            return _decimal(
                _get(
                    invoice,
                    "total",
                    0,
                )
            )

        return Decimal("0")


def get_invoice_balance(
    db: Session,
    invoice_id: int,
):
    """
    Return:

        invoice total
        amount paid
        outstanding balance
    """

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.id == invoice_id
        )
        .first()
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    invoice_total = calculate_invoice_total(
        db,
        invoice_id,
    )

    paid_amount = calculate_invoice_paid_amount(
        db,
        invoice_id,
    )

    balance = (
        invoice_total - paid_amount
    )

    if balance < 0:
        balance = Decimal("0")

    return {
        "invoice_total": invoice_total,
        "paid_amount": paid_amount,
        "balance": balance,
    }


# ==========================================================
# CREATE PAYMENT
# ==========================================================

def create_payment(
    db: Session,
    invoice_id: int,
    amount,
    payment_date=None,
    payment_method="Cash",
    reference=None,
    notes=None,
):
    """
    Create a Draft payment against an invoice.
    """

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.id == invoice_id
        )
        .first()
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    invoice_status = str(
        _get(
            invoice,
            "status",
            "Draft",
        )
    ).lower()

    if invoice_status in (
        "void",
        "voided",
    ):
        raise ValueError(
            "Cannot receive payment against "
            "a void invoice."
        )

    amount = _decimal(amount)

    if amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    balance = get_invoice_balance(
        db,
        invoice_id,
    )

    if amount > balance["balance"]:
        raise ValueError(
            "Payment amount cannot exceed "
            f"the outstanding balance of "
            f"{balance['balance']}."
        )

    customer_id = _get(
        invoice,
        "customer_id",
        None,
    )

    if not customer_id:
        raise ValueError(
            "Invoice does not have a customer."
        )

    payment = Payment(
        invoice_id=invoice_id,
        customer_id=customer_id,
        amount=amount,
        payment_date=(
            payment_date
            or datetime.utcnow()
        ),
        payment_method=payment_method,
        reference=reference,
        notes=notes,
        status="Draft",
    )

    # Support models that contain payment_number.
    if hasattr(
        Payment,
        "payment_number",
    ):
        payment.payment_number = (
            generate_payment_number(db)
        )

    db.add(payment)

    try:

        _commit(db)
        db.refresh(payment)

        return payment

    except Exception:

        _rollback(db)
        raise


# ==========================================================
# UPDATE PAYMENT
# ==========================================================

def update_payment(
    db: Session,
    payment_id: int,
    amount=None,
    payment_date=None,
    payment_method=None,
    reference=None,
    notes=None,
):
    """
    Edit a Draft payment.
    """

    payment = get_payment(
        db,
        payment_id,
    )

    if not payment:
        raise ValueError(
            "Payment not found."
        )

    status = str(
        _get(
            payment,
            "status",
            "Draft",
        )
    ).lower()

    if status != "draft":
        raise ValueError(
            "Only Draft payments can be edited."
        )

    if amount is not None:

        amount = _decimal(amount)

        if amount <= 0:
            raise ValueError(
                "Payment amount must be "
                "greater than zero."
            )

        balance = get_invoice_balance(
            db,
            payment.invoice_id,
        )

        # Exclude the current payment from the
        # outstanding calculation if it is somehow
        # already included.
        existing_amount = _decimal(
            _get(
                payment,
                "amount",
                0,
            )
        )

        available_balance = (
            balance["balance"]
            + existing_amount
        )

        if amount > available_balance:
            raise ValueError(
                "Payment amount exceeds "
                "the invoice balance."
            )

        payment.amount = amount

    if payment_date is not None:
        payment.payment_date = payment_date

    if payment_method is not None:
        payment.payment_method = (
            payment_method
        )

    if reference is not None:
        payment.reference = reference

    if notes is not None:
        payment.notes = notes

    try:

        _commit(db)
        db.refresh(payment)

        return payment

    except Exception:

        _rollback(db)
        raise


# ==========================================================
# POST PAYMENT
# ==========================================================

def post_payment(
    db: Session,
    payment_id: int,
):
    """
    Post a payment.

    Posting the payment reduces the outstanding
    Accounts Receivable balance.
    """

    payment = get_payment(
        db,
        payment_id,
    )

    if not payment:
        raise ValueError(
            "Payment not found."
        )

    status = str(
        _get(
            payment,
            "status",
            "Draft",
        )
    ).lower()

    if status == "posted":
        raise ValueError(
            "Payment is already posted."
        )

    if status in (
        "reversed",
        "void",
        "voided",
    ):
        raise ValueError(
            "A reversed or void payment "
            "cannot be posted."
        )

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.id
            == payment.invoice_id
        )
        .first()
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    invoice_status = str(
        _get(
            invoice,
            "status",
            "Draft",
        )
    ).lower()

    if invoice_status in (
        "void",
        "voided",
    ):
        raise ValueError(
            "Cannot post payment against "
            "a void invoice."
        )

    amount = _decimal(
        _get(
            payment,
            "amount",
            0,
        )
    )

    if amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    balance = get_invoice_balance(
        db,
        payment.invoice_id,
    )

    if amount > balance["balance"]:
        raise ValueError(
            "Payment exceeds the remaining "
            "invoice balance."
        )

    try:

        payment.status = "Posted"

        if hasattr(
            payment,
            "posted_at",
        ):
            payment.posted_at = (
                datetime.utcnow()
            )

        _commit(db)
        db.refresh(payment)

        # Update invoice payment fields when
        # those fields exist in the current model.
        paid_amount = calculate_invoice_paid_amount(
            db,
            payment.invoice_id,
        )

        if hasattr(
            invoice,
            "paid_amount",
        ):
            invoice.paid_amount = paid_amount

        invoice_total = calculate_invoice_total(
            db,
            invoice.id,
        )

        if (
            paid_amount >= invoice_total
            and invoice_total > 0
        ):

            if hasattr(
                invoice,
                "payment_status",
            ):
                invoice.payment_status = "Paid"

        else:

            if hasattr(
                invoice,
                "payment_status",
            ):
                invoice.payment_status = "Partially Paid"

        _commit(db)
        db.refresh(payment)

        return payment

    except Exception:

        _rollback(db)
        raise


# ==========================================================
# REVERSE PAYMENT
# ==========================================================

def reverse_payment(
    db: Session,
    payment_id: int,
    reason=None,
):
    """
    Reverse a posted payment.

    The original payment remains in the database.
    Its status becomes Reversed.

    This restores the outstanding invoice balance.
    """

    payment = get_payment(
        db,
        payment_id,
    )

    if not payment:
        raise ValueError(
            "Payment not found."
        )

    status = str(
        _get(
            payment,
            "status",
            "Draft",
        )
    ).lower()

    if status == "reversed":
        raise ValueError(
            "Payment has already been reversed."
        )

    if status != "posted":
        raise ValueError(
            "Only Posted payments can be reversed."
        )

    try:

        payment.status = "Reversed"

        if reason and hasattr(
            payment,
            "reversal_reason",
        ):
            payment.reversal_reason = reason

        if hasattr(
            payment,
            "reversed_at",
        ):
            payment.reversed_at = (
                datetime.utcnow()
            )

        _commit(db)

        # Recalculate invoice payment status.
        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.id
                == payment.invoice_id
            )
            .first()
        )

        if invoice:

            paid_amount = (
                calculate_invoice_paid_amount(
                    db,
                    invoice.id,
                )
            )

            if hasattr(
                invoice,
                "paid_amount",
            ):
                invoice.paid_amount = paid_amount

            invoice_total = (
                calculate_invoice_total(
                    db,
                    invoice.id,
                )
            )

            if hasattr(
                invoice,
                "payment_status",
            ):

                if paid_amount <= 0:
                    invoice.payment_status = (
                        "Unpaid"
                    )

                elif paid_amount < invoice_total:
                    invoice.payment_status = (
                        "Partially Paid"
                    )

                else:
                    invoice.payment_status = (
                        "Paid"
                    )

            _commit(db)

        db.refresh(payment)

        return payment

    except Exception:

        _rollback(db)
        raise


# ==========================================================
# CUSTOMER BALANCE
# ==========================================================

def get_customer_outstanding_balance(
    db: Session,
    customer_id: int,
):
    """
    Calculate total outstanding receivables
    for a customer.
    """

    invoices = (
        db.query(Invoice)
        .filter(
            Invoice.customer_id
            == customer_id
        )
        .all()
    )

    total_outstanding = Decimal("0")

    for invoice in invoices:

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
            continue

        balance = get_invoice_balance(
            db,
            invoice.id,
        )

        total_outstanding += balance[
            "balance"
        ]

    return total_outstanding


# ==========================================================
# PAYMENT SUMMARY
# ==========================================================

def get_payment_summary(
    db: Session,
):
    """
    Return basic payment statistics.
    """

    payments = get_all_payments(db)

    total_posted = Decimal("0")
    total_draft = Decimal("0")
    total_reversed = Decimal("0")

    for payment in payments:

        amount = _decimal(
            _get(
                payment,
                "amount",
                0,
            )
        )

        status = str(
            _get(
                payment,
                "status",
                "Draft",
            )
        ).lower()

        if status == "posted":
            total_posted += amount

        elif status == "draft":
            total_draft += amount

        elif status == "reversed":
            total_reversed += amount

    return {
        "total_posted": total_posted,
        "total_draft": total_draft,
        "total_reversed": total_reversed,
        "payment_count": len(payments),
    }