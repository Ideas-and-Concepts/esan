"""
Esan ERP
Payment Service

Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from models import (
    Payment,
    Invoice,
    Customer,
)

from services.finance_service import (
    post_payment_to_finance,
    reverse_payment_finance,
)


# ==========================================================
# HELPERS
# ==========================================================

def _decimal(value):
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")


def _get(obj, field, default=None):
    return getattr(
        obj,
        field,
        default,
    )


# ==========================================================
# GET PAYMENTS
# ==========================================================

def get_payments(
    db: Session,
):
    """
    Return all payments.
    """

    return (
        db.query(Payment)
        .order_by(
            Payment.id.desc()
        )
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
            Payment.invoice_id
            == invoice_id
        )
        .order_by(
            Payment.id.desc()
        )
        .all()
    )


def get_customer_payments(
    db: Session,
    customer_id: int,
):
    """
    Return payments made by a customer.
    """

    return (
        db.query(Payment)
        .filter(
            Payment.customer_id
            == customer_id
        )
        .order_by(
            Payment.id.desc()
        )
        .all()
    )


# ==========================================================
# CREATE PAYMENT
# ==========================================================

def create_payment(
    db: Session,
    invoice_id: int,
    amount,
    payment_method="Cash",
    payment_date=None,
    reference=None,
    notes=None,
):
    """
    Create a Draft payment.

    The payment does not affect Finance until
    it is posted.
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
        "draft",
        "void",
        "voided",
    ):
        raise ValueError(
            "Payment cannot be created for "
            "this invoice."
        )

    amount = _decimal(amount)

    if amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    payment = Payment(
        invoice_id=invoice_id,
        amount=amount,
    )

    # Copy customer where supported.
    customer_id = _get(
        invoice,
        "customer_id",
    )

    if customer_id is not None and hasattr(
        payment,
        "customer_id",
    ):
        payment.customer_id = customer_id

    if hasattr(
        payment,
        "payment_method",
    ):
        payment.payment_method = (
            payment_method
        )

    if hasattr(
        payment,
        "payment_date",
    ):
        payment.payment_date = (
            payment_date
            or datetime.utcnow()
        )

    if hasattr(
        payment,
        "reference",
    ):
        payment.reference = reference

    if hasattr(
        payment,
        "notes",
    ):
        payment.notes = notes

    if hasattr(
        payment,
        "status",
    ):
        payment.status = "Draft"

    db.add(payment)

    try:

        db.commit()
        db.refresh(payment)

        return payment

    except Exception:

        db.rollback()
        raise


# ==========================================================
# EDIT PAYMENT
# ==========================================================

def update_payment(
    db: Session,
    payment_id: int,
    amount=None,
    payment_method=None,
    payment_date=None,
    reference=None,
    notes=None,
):
    """
    Edit a Draft payment.

    Posted payments cannot be edited.
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

    if status not in (
        "draft",
        "pending",
    ):
        raise ValueError(
            "Only Draft payments can be edited."
        )

    if amount is not None:

        amount = _decimal(amount)

        if amount <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        payment.amount = amount

    if payment_method is not None and hasattr(
        payment,
        "payment_method",
    ):
        payment.payment_method = (
            payment_method
        )

    if payment_date is not None and hasattr(
        payment,
        "payment_date",
    ):
        payment.payment_date = payment_date

    if reference is not None and hasattr(
        payment,
        "reference",
    ):
        payment.reference = reference

    if notes is not None and hasattr(
        payment,
        "notes",
    ):
        payment.notes = notes

    try:

        db.commit()
        db.refresh(payment)

        return payment

    except Exception:

        db.rollback()
        raise


# ==========================================================
# POST PAYMENT
# ==========================================================

def post_payment(
    db: Session,
    payment_id: int,
):
    """
    Post a payment and integrate it with Finance.

    Accounting:

        DR Cash / Bank
        CR Accounts Receivable
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
            "This payment cannot be posted."
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
            "Associated invoice not found."
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
        "draft",
    ):
        raise ValueError(
            "Payment cannot be posted against "
            "this invoice."
        )

    # ------------------------------------------------------
    # Prevent overpayment
    # ------------------------------------------------------

    invoice_total = _decimal(
        _get(
            invoice,
            "total",
            0,
        )
    )

    if invoice_total <= 0:

        invoice_total = _decimal(
            _get(
                invoice,
                "total_amount",
                0,
            )
        )

    posted_payments = (
        db.query(Payment)
        .filter(
            Payment.invoice_id
            == invoice.id
        )
        .filter(
            Payment.status
            == "Posted"
        )
        .filter(
            Payment.id != payment.id
        )
        .all()
    )

    already_paid = sum(
        (
            _decimal(
                _get(
                    p,
                    "amount",
                    0,
                )
            )
            for p in posted_payments
        ),
        Decimal("0"),
    )

    outstanding = (
        invoice_total
        - already_paid
    )

    if amount > outstanding:
        raise ValueError(
            "Payment exceeds the outstanding "
            f"invoice balance of {outstanding}."
        )

    try:

        # --------------------------------------------------
        # Operational posting
        # --------------------------------------------------

        if hasattr(
            payment,
            "status",
        ):
            payment.status = "Posted"

        if hasattr(
            payment,
            "posted_at",
        ):
            payment.posted_at = (
                datetime.utcnow()
            )

        db.flush()

        # --------------------------------------------------
        # Finance posting
        # --------------------------------------------------

        finance_entry = (
            post_payment_to_finance(
                db,
                payment.id,
            )
        )

        # --------------------------------------------------
        # Update invoice status
        # --------------------------------------------------

        new_paid = (
            already_paid + amount
        )

        if new_paid >= invoice_total:

            if hasattr(
                invoice,
                "status",
            ):
                invoice.status = "Paid"

        else:

            if hasattr(
                invoice,
                "status",
            ):
                invoice.status = (
                    "Partially Paid"
                )

        db.commit()

        db.refresh(payment)
        db.refresh(invoice)

        return payment

    except Exception:

        db.rollback()
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

    Finance creates:

        DR Accounts Receivable
        CR Cash / Bank
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

    if status != "posted":
        raise ValueError(
            "Only posted payments can be reversed."
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
            "Associated invoice not found."
        )

    try:

        # --------------------------------------------------
        # Finance reversal
        # --------------------------------------------------

        finance_entry = (
            reverse_payment_finance(
                db,
                payment.id,
                reason,
            )
        )

        # --------------------------------------------------
        # Operational reversal
        # --------------------------------------------------

        if hasattr(
            payment,
            "status",
        ):
            payment.status = "Reversed"

        if hasattr(
            payment,
            "reversed_at",
        ):
            payment.reversed_at = (
                datetime.utcnow()
            )

        if reason and hasattr(
            payment,
            "notes",
        ):

            current_notes = (
                payment.notes or ""
            )

            payment.notes = (
                f"{current_notes}\n"
                f"Reversal reason: {reason}"
            ).strip()

        # --------------------------------------------------
        # Recalculate invoice balance
        # --------------------------------------------------

        posted_payments = (
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
                        p,
                        "amount",
                        0,
                    )
                )
                for p in posted_payments
            ),
            Decimal("0"),
        )

        invoice_total = _decimal(
            _get(
                invoice,
                "total",
                0,
            )
        )

        if invoice_total <= 0:
            invoice_total = _decimal(
                _get(
                    invoice,
                    "total_amount",
                    0,
                )
            )

        if paid >= invoice_total:

            if hasattr(
                invoice,
                "status",
            ):
                invoice.status = "Paid"

        elif paid > 0:

            if hasattr(
                invoice,
                "status",
            ):
                invoice.status = (
                    "Partially Paid"
                )

        else:

            if hasattr(
                invoice,
                "status",
            ):
                invoice.status = "Posted"

        db.commit()

        db.refresh(payment)
        db.refresh(invoice)

        return payment

    except Exception:

        db.rollback()
        raise


# ==========================================================
# DELETE DRAFT PAYMENT
# ==========================================================

def delete_payment(
    db: Session,
    payment_id: int,
):
    """
    Delete only a Draft payment.
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

    if status not in (
        "draft",
        "pending",
    ):
        raise ValueError(
            "Only Draft payments can be deleted."
        )

    try:

        db.delete(payment)
        db.commit()

        return True

    except Exception:

        db.rollback()
        raise


# ==========================================================
# PAYMENT SUMMARY
# ==========================================================

def get_payment_summary(
    db: Session,
    invoice_id: int,
):
    """
    Return payment totals for an invoice.
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

    invoice_total = _decimal(
        _get(
            invoice,
            "total",
            0,
        )
    )

    if invoice_total <= 0:
        invoice_total = _decimal(
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
            == invoice_id
        )
        .all()
    )

    posted = sum(
        (
            _decimal(
                _get(
                    p,
                    "amount",
                    0,
                )
            )
            for p in payments
            if str(
                _get(
                    p,
                    "status",
                    "",
                )
            ).lower()
            == "posted"
        ),
        Decimal("0"),
    )

    reversed_amount = sum(
        (
            _decimal(
                _get(
                    p,
                    "amount",
                    0,
                )
            )
            for p in payments
            if str(
                _get(
                    p,
                    "status",
                    "",
                )
            ).lower()
            == "reversed"
        ),
        Decimal("0"),
    )

    outstanding = max(
        invoice_total - posted,
        Decimal("0"),
    )

    return {
        "invoice_total": invoice_total,
        "posted_payments": posted,
        "reversed_payments": reversed_amount,
        "outstanding": outstanding,
    }