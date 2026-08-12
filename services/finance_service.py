"""
Esan ERP
Finance Service

Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from models import (
    Account,
    JournalEntry,
    JournalEntryLine,
    Invoice,
    Payment,
)


# ==========================================================
# HELPERS
# ==========================================================

def _get(obj, field, default=None):
    """Safely read a model attribute."""
    return getattr(obj, field, default)


def _decimal(value):
    """Convert values safely to Decimal."""
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
# ACCOUNT TYPES
# ==========================================================

ASSET = "Asset"
LIABILITY = "Liability"
EQUITY = "Equity"
REVENUE = "Revenue"
EXPENSE = "Expense"


# ==========================================================
# DEFAULT CHART OF ACCOUNTS
# ==========================================================

DEFAULT_ACCOUNTS = [
    {
        "code": "1000",
        "name": "Cash",
        "account_type": ASSET,
    },
    {
        "code": "1010",
        "name": "Bank",
        "account_type": ASSET,
    },
    {
        "code": "1100",
        "name": "Accounts Receivable",
        "account_type": ASSET,
    },
    {
        "code": "1200",
        "name": "Inventory",
        "account_type": ASSET,
    },
    {
        "code": "2000",
        "name": "Accounts Payable",
        "account_type": LIABILITY,
    },
    {
        "code": "3000",
        "name": "Owner's Equity",
        "account_type": EQUITY,
    },
    {
        "code": "4000",
        "name": "Sales Revenue",
        "account_type": REVENUE,
    },
    {
        "code": "5000",
        "name": "Cost of Goods Sold",
        "account_type": EXPENSE,
    },
    {
        "code": "6000",
        "name": "Operating Expenses",
        "account_type": EXPENSE,
    },
]


# ==========================================================
# CHART OF ACCOUNTS
# ==========================================================

def get_all_accounts(
    db: Session,
    active_only=True,
):
    """
    Return accounts from the Chart of Accounts.
    """

    query = db.query(Account)

    if active_only and hasattr(Account, "active"):
        query = query.filter(
            Account.active.is_(True)
        )

    return (
        query
        .order_by(Account.code.asc())
        .all()
    )


def get_account(
    db: Session,
    account_id: int,
):
    """
    Get an account by ID.
    """

    return (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )


def get_account_by_code(
    db: Session,
    code: str,
):
    """
    Get an account by account code.
    """

    return (
        db.query(Account)
        .filter(Account.code == str(code))
        .first()
    )


def get_account_by_name(
    db: Session,
    name: str,
):
    """
    Get an account by name.
    """

    return (
        db.query(Account)
        .filter(Account.name == name)
        .first()
    )


def create_account(
    db: Session,
    code: str,
    name: str,
    account_type: str,
    description=None,
):
    """
    Create a Chart of Accounts entry.
    """

    if not code:
        raise ValueError(
            "Account code is required."
        )

    if not name:
        raise ValueError(
            "Account name is required."
        )

    existing = get_account_by_code(
        db,
        code,
    )

    if existing:
        raise ValueError(
            f"Account code {code} already exists."
        )

    account = Account(
        code=code,
        name=name,
        account_type=account_type,
    )

    if hasattr(
        account,
        "description",
    ):
        account.description = description

    if hasattr(
        account,
        "active",
    ):
        account.active = True

    db.add(account)

    try:
        _commit(db)
        db.refresh(account)
        return account

    except Exception:
        _rollback(db)
        raise


def seed_default_accounts(
    db: Session,
):
    """
    Create the standard Esan ERP accounts
    if they do not already exist.
    """

    created = []

    for data in DEFAULT_ACCOUNTS:

        existing = get_account_by_code(
            db,
            data["code"],
        )

        if existing:
            continue

        account = Account(
            code=data["code"],
            name=data["name"],
            account_type=data["account_type"],
        )

        if hasattr(
            account,
            "active",
        ):
            account.active = True

        db.add(account)
        created.append(account)

    try:
        _commit(db)

        for account in created:
            db.refresh(account)

        return created

    except Exception:
        _rollback(db)
        raise


# ==========================================================
# JOURNAL ENTRIES
# ==========================================================

def generate_journal_number(
    db: Session,
):
    """
    Generate a sequential journal number.
    """

    last_entry = (
        db.query(JournalEntry)
        .order_by(
            JournalEntry.id.desc()
        )
        .first()
    )

    next_id = (
        int(_get(last_entry, "id", 0) or 0)
        + 1
        if last_entry
        else 1
    )

    return f"JE-{next_id:06d}"


def get_journal_entries(
    db: Session,
):
    """
    Return journal entries, newest first.
    """

    return (
        db.query(JournalEntry)
        .order_by(
            JournalEntry.id.desc()
        )
        .all()
    )


def get_journal_entry(
    db: Session,
    entry_id: int,
):
    """
    Get one journal entry.
    """

    return (
        db.query(JournalEntry)
        .filter(
            JournalEntry.id == entry_id
        )
        .first()
    )


def get_journal_lines(
    db: Session,
    journal_entry_id: int,
):
    """
    Get all lines belonging to a journal entry.
    """

    return (
        db.query(JournalEntryLine)
        .filter(
            JournalEntryLine.journal_entry_id
            == journal_entry_id
        )
        .order_by(
            JournalEntryLine.id.asc()
        )
        .all()
    )


# ==========================================================
# CREATE JOURNAL ENTRY
# ==========================================================

def create_journal_entry(
    db: Session,
    description: str,
    lines: list,
    reference_type=None,
    reference_id=None,
    entry_date=None,
):
    """
    Create a balanced Draft journal entry.

    lines format:

    [
        {
            "account_id": 1,
            "debit": 1000,
            "credit": 0,
            "description": "..."
        },
        {
            "account_id": 2,
            "debit": 0,
            "credit": 1000,
            "description": "..."
        }
    ]
    """

    if not lines:
        raise ValueError(
            "Journal entry requires at least "
            "one line."
        )

    total_debit = Decimal("0")
    total_credit = Decimal("0")

    for line in lines:

        debit = _decimal(
            line.get("debit", 0)
        )

        credit = _decimal(
            line.get("credit", 0)
        )

        if debit < 0 or credit < 0:
            raise ValueError(
                "Debit and credit amounts "
                "cannot be negative."
            )

        if debit > 0 and credit > 0:
            raise ValueError(
                "A journal line cannot contain "
                "both debit and credit."
            )

        account_id = line.get(
            "account_id"
        )

        if not account_id:
            raise ValueError(
                "Every journal line requires "
                "an account."
            )

        account = get_account(
            db,
            account_id,
        )

        if not account:
            raise ValueError(
                f"Account {account_id} not found."
            )

        total_debit += debit
        total_credit += credit

    if total_debit != total_credit:
        raise ValueError(
            "Journal entry is not balanced. "
            f"Debit={total_debit}, "
            f"Credit={total_credit}"
        )

    if total_debit <= 0:
        raise ValueError(
            "Journal entry must contain "
            "a value greater than zero."
        )

    entry = JournalEntry(
        description=description,
    )

    if hasattr(
        entry,
        "entry_number",
    ):
        entry.entry_number = (
            generate_journal_number(db)
        )

    if hasattr(
        entry,
        "entry_date",
    ):
        entry.entry_date = (
            entry_date
            or datetime.utcnow()
        )

    if hasattr(
        entry,
        "reference_type",
    ):
        entry.reference_type = (
            reference_type
        )

    if hasattr(
        entry,
        "reference_id",
    ):
        entry.reference_id = (
            reference_id
        )

    if hasattr(
        entry,
        "status",
    ):
        entry.status = "Draft"

    db.add(entry)
    db.flush()

    for line in lines:

        journal_line = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=line["account_id"],
            debit=_decimal(
                line.get("debit", 0)
            ),
            credit=_decimal(
                line.get("credit", 0)
            ),
        )

        if hasattr(
            journal_line,
            "description",
        ):
            journal_line.description = (
                line.get(
                    "description"
                )
            )

        db.add(journal_line)

    try:

        _commit(db)
        db.refresh(entry)

        return entry

    except Exception:

        _rollback(db)
        raise


# ==========================================================
# POST JOURNAL ENTRY
# ==========================================================

def post_journal_entry(
    db: Session,
    entry_id: int,
):
    """
    Post a balanced journal entry.
    """

    entry = get_journal_entry(
        db,
        entry_id,
    )

    if not entry:
        raise ValueError(
            "Journal entry not found."
        )

    status = str(
        _get(
            entry,
            "status",
            "Draft",
        )
    ).lower()

    if status == "posted":
        raise ValueError(
            "Journal entry is already posted."
        )

    if status in (
        "reversed",
        "void",
        "voided",
    ):
        raise ValueError(
            "Journal entry cannot be posted."
        )

    lines = get_journal_lines(
        db,
        entry.id,
    )

    debit = sum(
        (
            _decimal(
                _get(
                    line,
                    "debit",
                    0,
                )
            )
            for line in lines
        ),
        Decimal("0"),
    )

    credit = sum(
        (
            _decimal(
                _get(
                    line,
                    "credit",
                    0,
                )
            )
            for line in lines
        ),
        Decimal("0"),
    )

    if debit != credit:
        raise ValueError(
            "Cannot post an unbalanced "
            "journal entry."
        )

    try:

        if hasattr(
            entry,
            "status",
        ):
            entry.status = "Posted"

        if hasattr(
            entry,
            "posted_at",
        ):
            entry.posted_at = (
                datetime.utcnow()
            )

        _commit(db)
        db.refresh(entry)

        return entry

    except Exception:

        _rollback(db)
        raise


# ==========================================================
# SALES INVOICE ACCOUNTING
# ==========================================================

def post_invoice_to_finance(
    db: Session,
    invoice_id: int,
):
    """
    Create and post accounting for a sales invoice.

    Accounting:

        DR Accounts Receivable
        CR Sales Revenue
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

    if invoice_status not in (
        "posted",
        "paid",
        "partially paid",
    ):
        raise ValueError(
            "Invoice must be posted before "
            "it can be integrated with Finance."
        )

    # Prevent duplicate posting.
    existing = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.reference_type
            == "Invoice"
        )
        .filter(
            JournalEntry.reference_id
            == invoice_id
        )
        .first()
    )

    if existing:
        return existing

    amount = _decimal(
        _get(
            invoice,
            "total",
            0,
        )
    )

    if amount <= 0:

        amount = _decimal(
            _get(
                invoice,
                "total_amount",
                0,
            )
        )

    if amount <= 0:
        raise ValueError(
            "Invoice total must be greater than zero."
        )

    ar = get_account_by_code(
        db,
        "1100",
    )

    revenue = get_account_by_code(
        db,
        "4000",
    )

    if not ar or not revenue:

        seed_default_accounts(db)

        ar = get_account_by_code(
            db,
            "1100",
        )

        revenue = get_account_by_code(
            db,
            "4000",
        )

    if not ar or not revenue:
        raise ValueError(
            "Required Accounts Receivable or "
            "Sales Revenue account is missing."
        )

    entry = create_journal_entry(
        db=db,
        description=(
            f"Sales Invoice #{invoice.id}"
        ),
        reference_type="Invoice",
        reference_id=invoice.id,
        lines=[
            {
                "account_id": ar.id,
                "debit": amount,
                "credit": 0,
                "description": (
                    "Accounts Receivable"
                ),
            },
            {
                "account_id": revenue.id,
                "debit": 0,
                "credit": amount,
                "description": (
                    "Sales Revenue"
                ),
            },
        ],
    )

    return post_journal_entry(
        db,
        entry.id,
    )


# ==========================================================
# PAYMENT ACCOUNTING
# ==========================================================

def post_payment_to_finance(
    db: Session,
    payment_id: int,
):
    """
    Create and post accounting for a customer payment.

    Accounting:

        DR Cash/Bank
        CR Accounts Receivable
    """

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id
        )
        .first()
    )

    if not payment:
        raise ValueError(
            "Payment not found."
        )

    payment_status = str(
        _get(
            payment,
            "status",
            "Draft",
        )
    ).lower()

    if payment_status != "posted":
        raise ValueError(
            "Payment must be posted before "
            "Finance integration."
        )

    existing = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.reference_type
            == "Payment"
        )
        .filter(
            JournalEntry.reference_id
            == payment_id
        )
        .first()
    )

    if existing:
        return existing

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

    method = str(
        _get(
            payment,
            "payment_method",
            "Cash",
        )
    ).lower()

    if "bank" in method:
        account_code = "1010"
    else:
        account_code = "1000"

    cash_bank = get_account_by_code(
        db,
        account_code,
    )

    ar = get_account_by_code(
        db,
        "1100",
    )

    if not cash_bank or not ar:

        seed_default_accounts(db)

        cash_bank = get_account_by_code(
            db,
            account_code,
        )

        ar = get_account_by_code(
            db,
            "1100",
        )

    if not cash_bank or not ar:
        raise ValueError(
            "Required Cash/Bank or "
            "Accounts Receivable account is missing."
        )

    entry = create_journal_entry(
        db=db,
        description=(
            f"Customer Payment #{payment.id}"
        ),
        reference_type="Payment",
        reference_id=payment.id,
        lines=[
            {
                "account_id": cash_bank.id,
                "debit": amount,
                "credit": 0,
                "description": (
                    "Cash / Bank received"
                ),
            },
            {
                "account_id": ar.id,
                "debit": 0,
                "credit": amount,
                "description": (
                    "Accounts Receivable"
                ),
            },
        ],
    )

    return post_journal_entry(
        db,
        entry.id,
    )


# ==========================================================
# PAYMENT REVERSAL
# ==========================================================

def reverse_payment_finance(
    db: Session,
    payment_id: int,
    reason=None,
):
    """
    Reverse the Finance transaction created
    by a posted payment.

    Accounting:

        DR Accounts Receivable
        CR Cash/Bank
    """

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id
        )
        .first()
    )

    if not payment:
        raise ValueError(
            "Payment not found."
        )

    original_entry = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.reference_type
            == "Payment"
        )
        .filter(
            JournalEntry.reference_id
            == payment_id
        )
        .first()
    )

    if not original_entry:
        raise ValueError(
            "No Finance entry exists for this payment."
        )

    existing_reversal = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.reference_type
            == "Payment Reversal"
        )
        .filter(
            JournalEntry.reference_id
            == payment_id
        )
        .first()
    )

    if existing_reversal:
        return existing_reversal

    amount = _decimal(
        _get(
            payment,
            "amount",
            0,
        )
    )

    method = str(
        _get(
            payment,
            "payment_method",
            "Cash",
        )
    ).lower()

    if "bank" in method:
        account_code = "1010"
    else:
        account_code = "1000"

    cash_bank = get_account_by_code(
        db,
        account_code,
    )

    ar = get_account_by_code(
        db,
        "1100",
    )

    if not cash_bank or not ar:
        raise ValueError(
            "Required Finance accounts are missing."
        )

    description = (
        f"Reversal of Payment #{payment.id}"
    )

    if reason:
        description += f" - {reason}"

    entry = create_journal_entry(
        db=db,
        description=description,
        reference_type="Payment Reversal",
        reference_id=payment.id,
        lines=[
            {
                "account_id": ar.id,
                "debit": amount,
                "credit": 0,
                "description": (
                    "Restore Accounts Receivable"
                ),
            },
            {
                "account_id": cash_bank.id,
                "debit": 0,
                "credit": amount,
                "description": (
                    "Reverse Cash / Bank"
                ),
            },
        ],
    )

    return post_journal_entry(
        db,
        entry.id,
    )


# ==========================================================
# ACCOUNTS RECEIVABLE
# ==========================================================

def get_accounts_receivable(
    db: Session,
):
    """
    Calculate Accounts Receivable from
    posted journal entries.

    AR account = 1100.
    """

    ar = get_account_by_code(
        db,
        "1100",
    )

    if not ar:
        return Decimal("0")

    entries = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.status
            == "Posted"
        )
        .all()
    )

    balance = Decimal("0")

    for entry in entries:

        lines = get_journal_lines(
            db,
            entry.id,
        )

        for line in lines:

            if (
                _get(
                    line,
                    "account_id",
                )
                != ar.id
            ):
                continue

            balance += (
                _decimal(
                    _get(
                        line,
                        "debit",
                        0,
                    )
                )
                - _decimal(
                    _get(
                        line,
                        "credit",
                        0,
                    )
                )
            )

    return balance


# ==========================================================
# CUSTOMER RECEIVABLE
# ==========================================================

def get_customer_balance(
    db: Session,
    customer_id: int,
):
    """
    Calculate outstanding invoice balance
    for one customer.

    This is based directly on invoices and
    posted payments.
    """

    invoices = (
        db.query(Invoice)
        .filter(
            Invoice.customer_id
            == customer_id
        )
        .all()
    )

    balance = Decimal("0")

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
            "draft",
        ):
            continue

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
                for p in payments
            ),
            Decimal("0"),
        )

        outstanding = (
            invoice_total - paid
        )

        if outstanding > 0:
            balance += outstanding

    return balance


# ==========================================================
# FINANCE SUMMARY
# ==========================================================

def get_financial_summary(
    db: Session,
):
    """
    Return high-level Finance KPIs.
    """

    ar = get_accounts_receivable(
        db
    )

    posted_entries = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.status
            == "Posted"
        )
        .all()
    )

    revenue = Decimal("0")
    expenses = Decimal("0")
    cash = Decimal("0")
    bank = Decimal("0")

    for entry in posted_entries:

        lines = get_journal_lines(
            db,
            entry.id,
        )

        for line in lines:

            account = get_account(
                db,
                _get(
                    line,
                    "account_id",
                ),
            )

            if not account:
                continue

            account_type = str(
                _get(
                    account,
                    "account_type",
                    "",
                )
            ).lower()

            code = str(
                _get(
                    account,
                    "code",
                    "",
                )
            )

            debit = _decimal(
                _get(
                    line,
                    "debit",
                    0,
                )
            )

            credit = _decimal(
                _get(
                    line,
                    "credit",
                    0,
                )
            )

            if account_type == "revenue":
                revenue += (
                    credit - debit
                )

            elif account_type == "expense":
                expenses += (
                    debit - credit
                )

            elif code == "1000":
                cash += (
                    debit - credit
                )

            elif code == "1010":
                bank += (
                    debit - credit
                )

    return {
        "accounts_receivable": ar,
        "revenue": revenue,
        "expenses": expenses,
        "cash": cash,
        "bank": bank,
        "net_profit": (
            revenue - expenses
        ),
        "journal_entries": len(
            posted_entries
        ),
    }


# ==========================================================
# FINANCE INTEGRATION
# ==========================================================

def integrate_invoice(
    db: Session,
    invoice_id: int,
):
    """
    Public integration helper for Invoice posting.
    """

    return post_invoice_to_finance(
        db,
        invoice_id,
    )


def integrate_payment(
    db: Session,
    payment_id: int,
):
    """
    Public integration helper for Payment posting.
    """

    return post_payment_to_finance(
        db,
        payment_id,
    )


def integrate_payment_reversal(
    db: Session,
    payment_id: int,
    reason=None,
):
    """
    Public integration helper for Payment reversal.
    """

    return reverse_payment_finance(
        db,
        payment_id,
        reason,
    )