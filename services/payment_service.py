"""
Esan ERP - Payment Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Responsibilities:
- Create payments
- Edit payments
- Retrieve payments
- List payments
- Post payments
- Update invoice amount paid
- Update invoice balance due
- Create Cash/Bank -> Accounts Receivable journal entries
- Prevent duplicate posting
- Reverse posted payments
"""

import logging
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from models import (
    Payment,
    Invoice,
    Account,
    JournalEntry,
    JournalEntryLine,
)


logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

PAYMENT_DRAFT = "Draft"
PAYMENT_POSTED = "Posted"
PAYMENT_REVERSED = "Reversed"

AR_ACCOUNT_CODE = "1100"
CASH_ACCOUNT_CODE = "1000"
BANK_ACCOUNT_CODE = "1010"


# ============================================================
# HELPERS
# ============================================================

def _to_decimal(value):
    """
    Safely convert values to Decimal.
    """

    if value is None:
        return Decimal("0.00")

    return Decimal(str(value))


def _generate_payment_number(db: Session):
    """
    Generate a unique payment number.

    Example:
        PAY-000001
        PAY-000002
    """

    last_payment = (
        db.query(Payment)
        .order_by(Payment.id.desc())
        .first()
    )

    if not last_payment:
        next_number = 1
    else:
        next_number = last_payment.id + 1

    return f"PAY-{next_number:06d}"


def _generate_journal_number(db: Session):
    """
    Generate a unique journal number.

    Example:
        JE-000001
    """

    last_entry = (
        db.query(JournalEntry)
        .order_by(JournalEntry.id.desc())
        .first()
    )

    if not last_entry:
        next_number = 1
    else:
        next_number = last_entry.id + 1

    return f"JE-{next_number:06d}"


def _get_account(
    db: Session,
    code: str,
):
    """
    Retrieve an active accounting account.
    """

    account = (
        db.query(Account)
        .filter(
            Account.code == code,
            Account.active.is_(True),
        )
        .first()
    )

    if not account:
        raise ValueError(
            f"Accounting account {code} "
            f"does not exist or is inactive."
        )

    return account


def _cash_or_bank_account(
    db: Session,
    payment_method: str,
):
    """
    Select the accounting account according
    to the payment method.
    """

    method = (
        payment_method or "Cash"
    ).strip().lower()

    if method in {
        "bank",
        "bank transfer",
        "transfer",
        "mobile money",
        "mobile",
        "momo",
    }:
        return _get_account(
            db,
            BANK_ACCOUNT_CODE,
        )

    return _get_account(
        db,
        CASH_ACCOUNT_CODE,
    )


# ============================================================
# GET PAYMENT
# ============================================================

def get_payment(
    db: Session,
    payment_id: int,
):
    """
    Retrieve one payment.
    """

    return (
        db.query(Payment)
        .filter(
            Payment.id == payment_id
        )
        .first()
    )


# ============================================================
# GET PAYMENT BY NUMBER
# ============================================================

def get_payment_by_number(
    db: Session,
    payment_number: str,
):
    """
    Retrieve payment by payment number.
    """

    return (
        db.query(Payment)
        .filter(
            Payment.payment_number
            == payment_number
        )
        .first()
    )


# ============================================================
# LIST PAYMENTS
# ============================================================

def list_payments(
    db: Session,
    status=None,
    invoice_id=None,
):
    """
    Return payments with optional filters.
    """

    query = db.query(Payment)

    if status:
        query = query.filter(
            Payment.status == status
        )

    if invoice_id:
        query = query.filter(
            Payment.invoice_id
            == invoice_id
        )

    return (
        query
        .order_by(
            Payment.id.desc()
        )
        .all()
    )


# ============================================================
# CREATE PAYMENT
# ============================================================

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
    Create a payment in Draft status.

    Payment is not posted to Finance until
    post_payment() is called.
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

    if invoice.status != "Posted":
        raise ValueError(
            "Payment can only be created "
            "for a posted invoice."
        )

    payment_amount = _to_decimal(
        amount
    )

    if payment_amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    invoice_total = _to_decimal(
        invoice.total_amount
    )

    already_paid = _to_decimal(
        invoice.amount_paid
    )

    outstanding = (
        invoice_total - already_paid
    )

    if payment_amount > outstanding:
        raise ValueError(
            "Payment amount exceeds the "
            f"invoice balance of "
            f"{outstanding:,.2f}."
        )

    payment = Payment(
        payment_number=_generate_payment_number(
            db
        ),
        invoice_id=invoice_id,
        payment_date=(
            payment_date or date.today()
        ),
        amount=float(payment_amount),
        payment_method=(
            payment_method or "Cash"
        ),
        reference=reference,
        status=PAYMENT_DRAFT,
        notes=notes,
    )

    db.add(payment)

    db.commit()
    db.refresh(payment)

    logger.info(
        "Payment created: %s",
        payment.payment_number,
    )

    return payment


# ============================================================
# UPDATE PAYMENT
# ============================================================

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
    Update a Draft payment.

    Posted and Reversed payments cannot be edited.
    """

    payment = get_payment(
        db,
        payment_id,
    )

    if not payment:
        raise ValueError(
            "Payment not found."
        )

    if payment.status != PAYMENT_DRAFT:
        raise ValueError(
            "Only Draft payments can be edited."
        )

    invoice = payment.invoice

    if not invoice:
        raise ValueError(
            "Payment invoice could not be found."
        )

    if amount is not None:

        payment_amount = _to_decimal(
            amount
        )

        if payment_amount <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        invoice_total = _to_decimal(
            invoice.total_amount
        )

        # Existing draft payment has not yet
        # been added to amount_paid.
        outstanding = (
            invoice_total
            - _to_decimal(
                invoice.amount_paid
            )
        )

        if payment_amount > outstanding:
            raise ValueError(
                "Payment amount exceeds "
                "the invoice balance."
            )

        payment.amount = float(
            payment_amount
        )

    if payment_method is not None:
        payment.payment_method = (
            payment_method
        )

    if payment_date is not None:
        payment.payment_date = (
            payment_date
        )

    if reference is not None:
        payment.reference = reference

    if notes is not None:
        payment.notes = notes

    db.commit()
    db.refresh(payment)

    logger.info(
        "Payment updated: %s",
        payment.payment_number,
    )

    return payment


# ============================================================
# CREATE PAYMENT JOURNAL
# ============================================================

def _create_payment_journal(
    db: Session,
    payment: Payment,
):
    """
    Create accounting entry for a payment.

    Cash/Bank       Dr
        Accounts Receivable   Cr
    """

    existing = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.reference_type
            == "Payment",
            JournalEntry.reference_id
            == payment.id,
            JournalEntry.status
            == "Posted",
        )
        .first()
    )

    if existing:
        raise ValueError(
            "This payment already has "
            "a posted journal entry."
        )

    invoice = payment.invoice

    if not invoice:
        raise ValueError(
            "Payment invoice could not be found."
        )

    amount = _to_decimal(
        payment.amount
    )

    if amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    cash_bank_account = (
        _cash_or_bank_account(
            db,
            payment.payment_method,
        )
    )

    ar_account = _get_account(
        db,
        AR_ACCOUNT_CODE,
    )

    journal = JournalEntry(
        entry_number=_generate_journal_number(
            db
        ),
        entry_date=datetime.utcnow(),
        description=(
            f"Payment {payment.payment_number} "
            f"for invoice "
            f"{invoice.invoice_number}"
        ),
        reference_type="Payment",
        reference_id=payment.id,
        status="Posted",
        posted_at=datetime.utcnow(),
    )

    db.add(journal)

    db.flush()

    debit_line = JournalEntryLine(
        journal_entry_id=journal.id,
        account_id=cash_bank_account.id,
        debit=amount,
        credit=Decimal("0.00"),
        description=(
            f"Payment received - "
            f"{payment.payment_number}"
        ),
    )

    credit_line = JournalEntryLine(
        journal_entry_id=journal.id,
        account_id=ar_account.id,
        debit=Decimal("0.00"),
        credit=amount,
        description=(
            f"Receivable settlement - "
            f"{invoice.invoice_number}"
        ),
    )

    db.add(debit_line)
    db.add(credit_line)

    return journal


# ============================================================
# POST PAYMENT
# ============================================================

def post_payment(
    db: Session,
    payment_id: int,
):
    """
    Post payment.

    This will:

    1. Create the Finance journal.
    2. Increase invoice.amount_paid.
    3. Reduce invoice.balance_due.
    4. Mark payment as Posted.

    All operations occur in one transaction.
    """

    payment = get_payment(
        db,
        payment_id,
    )

    if not payment:
        raise ValueError(
            "Payment not found."
        )

    if payment.status == PAYMENT_POSTED:
        raise ValueError(
            "Payment is already posted."
        )

    if payment.status == PAYMENT_REVERSED:
        raise ValueError(
            "A reversed payment cannot be posted."
        )

    if payment.status != PAYMENT_DRAFT:
        raise ValueError(
            f"Payment status "
            f"'{payment.status}' cannot be posted."
        )

    invoice = payment.invoice

    if not invoice:
        raise ValueError(
            "Payment invoice could not be found."
        )

    if invoice.status != "Posted":
        raise ValueError(
            "Payment can only be posted "
            "against a posted invoice."
        )

    amount = _to_decimal(
        payment.amount
    )

    if amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    current_paid = _to_decimal(
        invoice.amount_paid
    )

    total = _to_decimal(
        invoice.total_amount
    )

    current_balance = (
        total - current_paid
    )

    if amount > current_balance:
        raise ValueError(
            "Payment exceeds the "
            f"remaining invoice balance "
            f"of {current_balance:,.2f}."
        )

    try:

        journal = _create_payment_journal(
            db,
            payment,
        )

        invoice.amount_paid = float(
            current_paid + amount
        )

        new_balance = (
            total
            - _to_decimal(
                invoice.amount_paid
            )
        )

        invoice.balance_due = float(
            max(
                Decimal("0.00"),
                new_balance,
            )
        )

        payment.status = PAYMENT_POSTED

        # Automatically mark invoice as paid
        # when balance reaches zero.
        if invoice.balance_due <= 0:
            invoice.status = "Paid"

        db.commit()

        db.refresh(payment)

        logger.info(
            "Payment posted: %s | Journal: %s",
            payment.payment_number,
            journal.entry_number,
        )

        return payment

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to post payment %s",
            payment_id,
        )

        raise


# ============================================================
# GET PAYMENT JOURNAL
# ============================================================

def get_payment_journal(
    db: Session,
    payment_id: int,
):
    """
    Retrieve the posted journal associated
    with a payment.
    """

    return (
        db.query(JournalEntry)
        .filter(
            JournalEntry.reference_type
            == "Payment",
            JournalEntry.reference_id
            == payment_id,
            JournalEntry.status
            == "Posted",
        )
        .first()
    )


# ============================================================
# REVERSE PAYMENT
# ============================================================

def reverse_payment(
    db: Session,
    payment_id: int,
):
    """
    Reverse a posted payment.

    Accounting:

        Accounts Receivable   Dr
            Cash / Bank            Cr

    The invoice's amount_paid is reduced
    and its balance_due is restored.
    """

    payment = get_payment(
        db,
        payment_id,
    )

    if not payment:
        raise ValueError(
            "Payment not found."
        )

    if payment.status == PAYMENT_REVERSED:
        raise ValueError(
            "Payment is already reversed."
        )

    if payment.status != PAYMENT_POSTED:
        raise ValueError(
            "Only posted payments can be reversed."
        )

    invoice = payment.invoice

    if not invoice:
        raise ValueError(
            "Payment invoice could not be found."
        )

    original_journal = get_payment_journal(
        db,
        payment.id,
    )

    if not original_journal:
        raise ValueError(
            "Posted payment has no accounting "
            "journal to reverse."
        )

    amount = _to_decimal(
        payment.amount
    )

    if amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    try:

        cash_bank_account = (
            _cash_or_bank_account(
                db,
                payment.payment_method,
            )
        )

        ar_account = _get_account(
            db,
            AR_ACCOUNT_CODE,
        )

        reversal = JournalEntry(
            entry_number=_generate_journal_number(
                db
            ),
            entry_date=datetime.utcnow(),
            description=(
                f"Reversal of payment "
                f"{payment.payment_number}"
            ),
            reference_type="PaymentReverse",
            reference_id=payment.id,
            status="Posted",
            posted_at=datetime.utcnow(),
        )

        db.add(reversal)

        db.flush()

        # Reverse original debit to Cash/Bank.
        db.add(
            JournalEntryLine(
                journal_entry_id=reversal.id,
                account_id=cash_bank_account.id,
                debit=Decimal("0.00"),
                credit=amount,
                description=(
                    f"Reverse cash/bank receipt - "
                    f"{payment.payment_number}"
                ),
            )
        )

        # Restore Accounts Receivable.
        db.add(
            JournalEntryLine(
                journal_entry_id=reversal.id,
                account_id=ar_account.id,
                debit=amount,
                credit=Decimal("0.00"),
                description=(
                    f"Restore receivable - "
                    f"{invoice.invoice_number}"
                ),
            )
        )

        current_paid = _to_decimal(
            invoice.amount_paid
        )

        new_paid = (
            current_paid - amount
        )

        if new_paid < 0:
            new_paid = Decimal("0.00")

        invoice.amount_paid = float(
            new_paid
        )

        invoice.balance_due = float(
            _to_decimal(
                invoice.total_amount
            )
            - new_paid
        )

        # Restore invoice to Posted status.
        # It remains an issued invoice with
        # an outstanding receivable.
        if invoice.status == "Paid":
            invoice.status = "Posted"

        payment.status = PAYMENT_REVERSED

        db.commit()

        db.refresh(payment)

        logger.info(
            "Payment reversed: %s | Reversal journal: %s",
            payment.payment_number,
            reversal.entry_number,
        )

        return payment

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to reverse payment %s",
            payment_id,
        )

        raise


# ============================================================
# CUSTOMER PAYMENT SUMMARY
# ============================================================

def get_invoice_payment_summary(
    db: Session,
    invoice_id: int,
):
    """
    Return payment information for an invoice.
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

    payments = list_payments(
        db,
        invoice_id=invoice_id,
    )

    posted_payments = [
        payment
        for payment in payments
        if payment.status == PAYMENT_POSTED
    ]

    total_paid = sum(
        (
            _to_decimal(
                payment.amount
            )
            for payment in posted_payments
        ),
        Decimal("0.00"),
    )

    balance = (
        _to_decimal(
            invoice.total_amount
        )
        - total_paid
    )

    return {
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "invoice_total": float(
            invoice.total_amount
        ),
        "total_paid": float(
            total_paid
        ),
        "balance_due": float(
            max(
                Decimal("0.00"),
                balance,
            )
        ),
        "payments": posted_payments,
    }