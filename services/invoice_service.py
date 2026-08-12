"""
Esan ERP - Invoice Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Responsibilities:
- Create invoices
- Calculate invoice totals
- Edit draft invoices
- Retrieve invoices
- List invoices
- Post invoices
- Create Accounts Receivable journal entries
- Create Sales Revenue journal entries
- Prevent duplicate posting
- Void posted invoices
- Reverse accounting entries
"""

import logging
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from models import (
    Invoice,
    InvoiceItem,
    Customer,
    SalesOrder,
    Account,
    JournalEntry,
    JournalEntryLine,
)


logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

AR_ACCOUNT_CODE = "1100"
SALES_REVENUE_ACCOUNT_CODE = "4000"

INVOICE_DRAFT = "Draft"
INVOICE_POSTED = "Posted"
INVOICE_VOID = "Void"


# ============================================================
# HELPERS
# ============================================================

def _to_decimal(value):
    """
    Safely convert a number to Decimal.
    """

    if value is None:
        return Decimal("0.00")

    return Decimal(str(value))


def _generate_invoice_number(db: Session):
    """
    Generate the next invoice number.

    Example:
        INV-000001
        INV-000002
    """

    last_invoice = (
        db.query(Invoice)
        .order_by(Invoice.id.desc())
        .first()
    )

    if not last_invoice:
        next_number = 1
    else:
        next_number = last_invoice.id + 1

    return f"INV-{next_number:06d}"


def _generate_journal_number(db: Session):
    """
    Generate a unique journal entry number.

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


def _calculate_items_total(items):
    """
    Calculate invoice subtotal from item data.

    Expected item format:

        {
            "product_id": 1,
            "product_name": "Maize Flour",
            "quantity": 10,
            "unit_price": 5000
        }
    """

    subtotal = Decimal("0.00")

    for item in items:

        quantity = _to_decimal(
            item.get("quantity", 0)
        )

        unit_price = _to_decimal(
            item.get("unit_price", 0)
        )

        if quantity < 0:
            raise ValueError(
                "Invoice quantity cannot be negative."
            )

        if unit_price < 0:
            raise ValueError(
                "Invoice unit price cannot be negative."
            )

        total = quantity * unit_price

        subtotal += total

    return subtotal


# ============================================================
# CREATE INVOICE
# ============================================================

def create_invoice(
    db: Session,
    customer_id: int,
    items,
    invoice_date=None,
    due_date=None,
    sales_order_id=None,
    tax_amount=0,
    notes=None,
):
    """
    Create a new Draft invoice.

    The invoice remains editable until posted.
    """

    if not customer_id:
        raise ValueError(
            "Customer is required."
        )

    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.active.is_(True),
        )
        .first()
    )

    if not customer:
        raise ValueError(
            "Customer does not exist or is inactive."
        )

    if not items:
        raise ValueError(
            "Invoice must contain at least one item."
        )

    if sales_order_id:

        sales_order = (
            db.query(SalesOrder)
            .filter(
                SalesOrder.id == sales_order_id
            )
            .first()
        )

        if not sales_order:
            raise ValueError(
                "Sales order does not exist."
            )

    subtotal = _calculate_items_total(items)

    tax = _to_decimal(tax_amount)

    if tax < 0:
        raise ValueError(
            "Tax amount cannot be negative."
        )

    total = subtotal + tax

    invoice = Invoice(
        invoice_number=_generate_invoice_number(db),
        customer_id=customer_id,
        sales_order_id=sales_order_id,
        invoice_date=(
            invoice_date or date.today()
        ),
        due_date=due_date,
        status=INVOICE_DRAFT,
        subtotal=float(subtotal),
        tax_amount=float(tax),
        total_amount=float(total),
        amount_paid=0.0,
        balance_due=float(total),
        notes=notes,
    )

    db.add(invoice)

    # Flush so invoice.id becomes available.
    db.flush()

    for item in items:

        quantity = _to_decimal(
            item.get("quantity", 0)
        )

        unit_price = _to_decimal(
            item.get("unit_price", 0)
        )

        item_total = (
            quantity * unit_price
        )

        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=item.get(
                "product_id"
            ),
            product_name=item.get(
                "product_name",
                "Unknown Product",
            ),
            quantity=float(quantity),
            unit_price=float(unit_price),
            total=float(item_total),
        )

        db.add(invoice_item)

    db.commit()
    db.refresh(invoice)

    logger.info(
        "Invoice created: %s",
        invoice.invoice_number,
    )

    return invoice


# ============================================================
# GET INVOICE
# ============================================================

def get_invoice(
    db: Session,
    invoice_id: int,
):
    """
    Retrieve a single invoice.
    """

    return (
        db.query(Invoice)
        .filter(
            Invoice.id == invoice_id
        )
        .first()
    )


# ============================================================
# GET INVOICE BY NUMBER
# ============================================================

def get_invoice_by_number(
    db: Session,
    invoice_number: str,
):
    """
    Retrieve invoice by invoice number.
    """

    return (
        db.query(Invoice)
        .filter(
            Invoice.invoice_number
            == invoice_number
        )
        .first()
    )


# ============================================================
# LIST INVOICES
# ============================================================

def list_invoices(
    db: Session,
    status=None,
    customer_id=None,
):
    """
    Return invoices with optional filters.
    """

    query = db.query(Invoice)

    if status:
        query = query.filter(
            Invoice.status == status
        )

    if customer_id:
        query = query.filter(
            Invoice.customer_id
            == customer_id
        )

    return (
        query
        .order_by(
            Invoice.id.desc()
        )
        .all()
    )


# ============================================================
# UPDATE DRAFT INVOICE
# ============================================================

def update_invoice(
    db: Session,
    invoice_id: int,
    customer_id=None,
    items=None,
    invoice_date=None,
    due_date=None,
    tax_amount=None,
    notes=None,
):
    """
    Update a Draft invoice.

    Posted and Void invoices cannot be edited.
    """

    invoice = get_invoice(
        db,
        invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    if invoice.status != INVOICE_DRAFT:
        raise ValueError(
            "Only Draft invoices can be edited."
        )

    if customer_id is not None:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id,
                Customer.active.is_(True),
            )
            .first()
        )

        if not customer:
            raise ValueError(
                "Customer does not exist "
                "or is inactive."
            )

        invoice.customer_id = customer_id

    if invoice_date is not None:
        invoice.invoice_date = invoice_date

    if due_date is not None:
        invoice.due_date = due_date

    if notes is not None:
        invoice.notes = notes

    if items is not None:

        if not items:
            raise ValueError(
                "Invoice must contain at least one item."
            )

        subtotal = (
            _calculate_items_total(items)
        )

        # Remove existing lines.
        invoice.items.clear()

        for item in items:

            quantity = _to_decimal(
                item.get("quantity", 0)
            )

            unit_price = _to_decimal(
                item.get("unit_price", 0)
            )

            item_total = (
                quantity * unit_price
            )

            invoice.items.append(
                InvoiceItem(
                    product_id=item.get(
                        "product_id"
                    ),
                    product_name=item.get(
                        "product_name",
                        "Unknown Product",
                    ),
                    quantity=float(quantity),
                    unit_price=float(unit_price),
                    total=float(item_total),
                )
            )

        invoice.subtotal = float(
            subtotal
        )

    if tax_amount is not None:

        tax = _to_decimal(
            tax_amount
        )

        if tax < 0:
            raise ValueError(
                "Tax amount cannot be negative."
            )

        invoice.tax_amount = float(
            tax
        )

    subtotal = _to_decimal(
        invoice.subtotal
    )

    tax = _to_decimal(
        invoice.tax_amount
    )

    total = subtotal + tax

    invoice.total_amount = float(
        total
    )

    invoice.balance_due = float(
        total
        - _to_decimal(
            invoice.amount_paid
        )
    )

    db.commit()
    db.refresh(invoice)

    logger.info(
        "Invoice updated: %s",
        invoice.invoice_number,
    )

    return invoice


# ============================================================
# CREATE INVOICE JOURNAL
# ============================================================

def _create_invoice_journal(
    db: Session,
    invoice: Invoice,
):
    """
    Create the accounting entry for a posted invoice.

    Debit:
        Accounts Receivable

    Credit:
        Sales Revenue
    """

    # Prevent duplicate accounting entries.
    existing = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.reference_type
            == "Invoice",
            JournalEntry.reference_id
            == invoice.id,
            JournalEntry.status
            == "Posted",
        )
        .first()
    )

    if existing:
        raise ValueError(
            "This invoice already has "
            "a posted journal entry."
        )

    ar_account = _get_account(
        db,
        AR_ACCOUNT_CODE,
    )

    revenue_account = _get_account(
        db,
        SALES_REVENUE_ACCOUNT_CODE,
    )

    amount = _to_decimal(
        invoice.total_amount
    )

    if amount <= 0:
        raise ValueError(
            "Invoice total must be greater than zero."
        )

    journal = JournalEntry(
        entry_number=_generate_journal_number(
            db
        ),
        entry_date=datetime.utcnow(),
        description=(
            f"Invoice {invoice.invoice_number} "
            f"- Sales to "
            f"{invoice.customer.name}"
        ),
        reference_type="Invoice",
        reference_id=invoice.id,
        status="Posted",
        posted_at=datetime.utcnow(),
    )

    db.add(journal)
    db.flush()

    debit_line = JournalEntryLine(
        journal_entry_id=journal.id,
        account_id=ar_account.id,
        debit=amount,
        credit=Decimal("0.00"),
        description=(
            f"Accounts receivable - "
            f"{invoice.invoice_number}"
        ),
    )

    credit_line = JournalEntryLine(
        journal_entry_id=journal.id,
        account_id=revenue_account.id,
        debit=Decimal("0.00"),
        credit=amount,
        description=(
            f"Sales revenue - "
            f"{invoice.invoice_number}"
        ),
    )

    db.add(debit_line)
    db.add(credit_line)

    return journal


# ============================================================
# POST INVOICE
# ============================================================

def post_invoice(
    db: Session,
    invoice_id: int,
):
    """
    Post an invoice and create its accounting entry.
    """

    invoice = get_invoice(
        db,
        invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    if invoice.status == INVOICE_POSTED:
        raise ValueError(
            "Invoice is already posted."
        )

    if invoice.status == INVOICE_VOID:
        raise ValueError(
            "A void invoice cannot be posted."
        )

    if invoice.status != INVOICE_DRAFT:
        raise ValueError(
            f"Invoice status '{invoice.status}' "
            f"cannot be posted."
        )

    if not invoice.items:
        raise ValueError(
            "Invoice cannot be posted "
            "without invoice items."
        )

    if invoice.total_amount <= 0:
        raise ValueError(
            "Invoice total must be greater than zero."
        )

    try:

        journal = _create_invoice_journal(
            db,
            invoice,
        )

        invoice.status = INVOICE_POSTED

        invoice.balance_due = float(
            _to_decimal(
                invoice.total_amount
            )
            - _to_decimal(
                invoice.amount_paid
            )
        )

        db.commit()
        db.refresh(invoice)

        logger.info(
            "Invoice posted: %s | Journal: %s",
            invoice.invoice_number,
            journal.entry_number,
        )

        return invoice

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to post invoice %s",
            invoice_id,
        )

        raise


# ============================================================
# FIND INVOICE JOURNAL
# ============================================================

def get_invoice_journal(
    db: Session,
    invoice_id: int,
):
    """
    Retrieve the posted journal associated
    with an invoice.
    """

    return (
        db.query(JournalEntry)
        .filter(
            JournalEntry.reference_type
            == "Invoice",
            JournalEntry.reference_id
            == invoice_id,
            JournalEntry.status
            == "Posted",
        )
        .first()
    )


# ============================================================
# VOID INVOICE
# ============================================================

def void_invoice(
    db: Session,
    invoice_id: int,
):
    """
    Void an invoice.

    A posted invoice is reversed by creating
    a reversal journal entry.

    Draft invoices can simply be marked Void.
    """

    invoice = get_invoice(
        db,
        invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    if invoice.status == INVOICE_VOID:
        raise ValueError(
            "Invoice is already void."
        )

    journal = get_invoice_journal(
        db,
        invoice_id,
    )

    try:

        if journal:

            ar_account = _get_account(
                db,
                AR_ACCOUNT_CODE,
            )

            revenue_account = _get_account(
                db,
                SALES_REVENUE_ACCOUNT_CODE,
            )

            amount = _to_decimal(
                invoice.total_amount
            )

            reversal = JournalEntry(
                entry_number=(
                    _generate_journal_number(db)
                ),
                entry_date=datetime.utcnow(),
                description=(
                    f"Reversal of invoice "
                    f"{invoice.invoice_number}"
                ),
                reference_type="InvoiceVoid",
                reference_id=invoice.id,
                status="Posted",
                posted_at=datetime.utcnow(),
            )

            db.add(reversal)
            db.flush()

            db.add(
                JournalEntryLine(
                    journal_entry_id=reversal.id,
                    account_id=revenue_account.id,
                    debit=amount,
                    credit=Decimal("0.00"),
                    description=(
                        f"Reverse sales revenue - "
                        f"{invoice.invoice_number}"
                    ),
                )
            )

            db.add(
                JournalEntryLine(
                    journal_entry_id=reversal.id,
                    account_id=ar_account.id,
                    debit=Decimal("0.00"),
                    credit=amount,
                    description=(
                        f"Reverse receivable - "
                        f"{invoice.invoice_number}"
                    ),
                )
            )

        invoice.status = INVOICE_VOID

        db.commit()
        db.refresh(invoice)

        logger.info(
            "Invoice voided: %s",
            invoice.invoice_number,
        )

        return invoice

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to void invoice %s",
            invoice_id,
        )

        raise


# ============================================================
# OUTSTANDING BALANCE
# ============================================================

def get_invoice_balance(
    db: Session,
    invoice_id: int,
):
    """
    Return current invoice balance.
    """

    invoice = get_invoice(
        db,
        invoice_id,
    )

    if not invoice:
        raise ValueError(
            "Invoice not found."
        )

    return max(
        0.0,
        float(
            _to_decimal(
                invoice.total_amount
            )
            - _to_decimal(
                invoice.amount_paid
            )
        ),
    )