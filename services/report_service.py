"""
Esan ERP
Report Service

Data aggregation for Reports module.

Nile Harvest Foods Ltd.
"""

from collections import defaultdict

from database import SessionLocal

from models import (
    Invoice,
    Payment,
    Customer,
    Product,
    SalesOrder,
    Account,
    JournalEntry,
    JournalEntryLine,
)


# ==========================================================
# REVENUE BY CUSTOMER
# ==========================================================

def revenue_by_customer():
    """
    Return completed payment revenue grouped by customer.
    """

    db = SessionLocal()

    try:

        payments = (
            db.query(Payment)
            .all()
        )

        result = defaultdict(float)

        for payment in payments:

            invoice = (
                db.query(Invoice)
                .filter(
                    Invoice.id
                    == payment.invoice_id
                )
                .first()
            )

            if not invoice:
                continue

            customer = (
                db.query(Customer)
                .filter(
                    Customer.id
                    == invoice.customer_id
                )
                .first()
            )

            if customer:
                name = customer.name
            else:
                name = (
                    f"Invoice "
                    f"{invoice.invoice_number}"
                )

            result[name] += float(
                payment.amount or 0
            )

        return dict(result)

    except Exception:
        return {}

    finally:
        db.close()


# ==========================================================
# MONTHLY REVENUE
# ==========================================================

def monthly_revenue():
    """
    Return payment revenue grouped by YYYY-MM.
    """

    db = SessionLocal()

    try:

        payments = (
            db.query(Payment)
            .all()
        )

        monthly = defaultdict(float)

        for payment in payments:

            payment_date = (
                getattr(
                    payment,
                    "payment_date",
                    None,
                )
                or getattr(
                    payment,
                    "created_at",
                    None,
                )
            )

            if not payment_date:
                continue

            month = payment_date.strftime(
                "%Y-%m"
            )

            monthly[month] += float(
                payment.amount or 0
            )

        return dict(
            sorted(
                monthly.items()
            )
        )

    except Exception:
        return {}

    finally:
        db.close()


# ==========================================================
# INVENTORY LEVELS
# ==========================================================

def inventory_levels():
    """
    Return current product inventory levels.
    """

    db = SessionLocal()

    try:

        products = (
            db.query(Product)
            .all()
        )

        return [
            {
                "name": getattr(
                    product,
                    "name",
                    "Unknown",
                ),
                "quantity": float(
                    getattr(
                        product,
                        "quantity",
                        0,
                    )
                    or 0
                ),
                "category": getattr(
                    product,
                    "category",
                    None,
                ) or "Uncategorized",
            }
            for product in products
        ]

    except Exception:
        return []

    finally:
        db.close()


# ==========================================================
# EXPENSE CATEGORIES
# ==========================================================

def expense_categories():
    """
    Return expenses grouped by account.

    Esan no longer depends on FinanceTransaction.
    Expenses are derived from posted journal entries
    and debit lines belonging to expense accounts.
    """

    db = SessionLocal()

    try:

        expense_accounts = (
            db.query(Account)
            .filter(
                Account.account_type.ilike(
                    "Expense"
                )
            )
            .all()
        )

        if not expense_accounts:
            return {}

        account_map = {
            account.id: account.name
            for account in expense_accounts
        }

        account_ids = list(
            account_map.keys()
        )

        lines = (
            db.query(JournalEntryLine)
            .filter(
                JournalEntryLine.account_id.in_(
                    account_ids
                )
            )
            .all()
        )

        result = defaultdict(float)

        for line in lines:

            journal_entry = (
                db.query(JournalEntry)
                .filter(
                    JournalEntry.id
                    == line.journal_entry_id
                )
                .first()
            )

            if journal_entry:

                status = (
                    getattr(
                        journal_entry,
                        "status",
                        "",
                    )
                    or ""
                ).lower()

                if status not in {
                    "posted",
                    "approved",
                }:
                    continue

            category = account_map.get(
                line.account_id,
                "Other",
            )

            result[category] += float(
                line.debit or 0
            )

        return dict(result)

    except Exception:
        return {}

    finally:
        db.close()


# ==========================================================
# ORDER STATUS SUMMARY
# ==========================================================

def order_status_summary():
    """
    Return sales orders grouped by status.
    """

    db = SessionLocal()

    try:

        orders = (
            db.query(SalesOrder)
            .all()
        )

        result = defaultdict(int)

        for order in orders:

            status = (
                getattr(
                    order,
                    "status",
                    None,
                )
                or "Unknown"
            )

            result[status] += 1

        return dict(result)

    except Exception:
        return {}

    finally:
        db.close()


# ==========================================================
# REPORT SUMMARY
# ==========================================================

def get_report_summary():
    """
    Return all report data in one structure.
    """

    return {
        "revenue_by_customer":
            revenue_by_customer(),

        "monthly_revenue":
            monthly_revenue(),

        "inventory_levels":
            inventory_levels(),

        "expense_categories":
            expense_categories(),

        "order_status_summary":
            order_status_summary(),
    }