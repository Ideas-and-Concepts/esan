"""
Esan ERP
Finance Seed Data

Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
"""

import logging

from database import SessionLocal
from models import Account


logger = logging.getLogger(__name__)


# ==========================================================
# INITIAL CHART OF ACCOUNTS
# ==========================================================

FINANCE_ACCOUNTS = [
    {
        "code": "1000",
        "name": "Cash",
        "account_type": "Asset",
        "description": "Cash on hand",
    },
    {
        "code": "1010",
        "name": "Bank",
        "account_type": "Asset",
        "description": "Company bank accounts",
    },
    {
        "code": "1100",
        "name": "Accounts Receivable",
        "account_type": "Asset",
        "description": "Amounts owed by customers",
    },
    {
        "code": "1200",
        "name": "Inventory",
        "account_type": "Asset",
        "description": "General inventory",
    },
    {
        "code": "1300",
        "name": "Raw Materials Inventory",
        "account_type": "Asset",
        "description": "Maize, cassava and other raw materials",
    },
    {
        "code": "1400",
        "name": "Finished Goods Inventory",
        "account_type": "Asset",
        "description": "Finished and packaged products",
    },
    {
        "code": "2000",
        "name": "Accounts Payable",
        "account_type": "Liability",
        "description": "Amounts owed to suppliers",
    },
    {
        "code": "3000",
        "name": "Share Capital",
        "account_type": "Equity",
        "description": "Owner/shareholder capital",
    },
    {
        "code": "4000",
        "name": "Sales Revenue",
        "account_type": "Revenue",
        "description": "Revenue from product sales",
    },
    {
        "code": "5000",
        "name": "Cost of Goods Sold",
        "account_type": "Expense",
        "description": "Cost of products sold",
    },
    {
        "code": "5100",
        "name": "Operating Expenses",
        "account_type": "Expense",
        "description": "General operating expenses",
    },
    {
        "code": "5200",
        "name": "Transport & Distribution",
        "account_type": "Expense",
        "description": "Transportation and distribution costs",
    },
    {
        "code": "5300",
        "name": "Utilities",
        "account_type": "Expense",
        "description": "Electricity, water and other utilities",
    },
    {
        "code": "5400",
        "name": "Salaries & Wages",
        "account_type": "Expense",
        "description": "Employee salaries and wages",
    },
]


# ==========================================================
# SEED FINANCE ACCOUNTS
# ==========================================================

def seed_finance_accounts(db=None):
    """
    Create the initial Chart of Accounts.

    Existing accounts are preserved.

    Returns:
        {
            "created": int,
            "existing": int,
            "errors": int
        }
    """

    own_session = False

    if db is None:
        db = SessionLocal()
        own_session = True

    created = 0
    existing = 0
    errors = 0

    try:

        for account_data in FINANCE_ACCOUNTS:

            code = account_data["code"]

            existing_account = (
                db.query(Account)
                .filter(
                    Account.code == code
                )
                .first()
            )

            if existing_account:

                existing += 1

                # Fill missing optional fields
                # without overwriting user changes.

                if (
                    hasattr(
                        existing_account,
                        "description",
                    )
                    and not existing_account.description
                ):
                    existing_account.description = (
                        account_data["description"]
                    )

                if (
                    hasattr(
                        existing_account,
                        "active",
                    )
                    and existing_account.active is None
                ):
                    existing_account.active = True

                continue

            account_kwargs = {
                "code": code,
                "name": account_data["name"],
                "account_type": account_data[
                    "account_type"
                ],
            }

            # Optional fields
            if hasattr(
                Account,
                "description",
            ):
                account_kwargs["description"] = (
                    account_data["description"]
                )

            if hasattr(
                Account,
                "active",
            ):
                account_kwargs["active"] = True

            account = Account(
                **account_kwargs
            )

            db.add(account)
            created += 1

        db.commit()

        logger.info(
            "Finance seed completed: "
            "%s created, %s existing",
            created,
            existing,
        )

        return {
            "created": created,
            "existing": existing,
            "errors": errors,
        }

    except Exception:

        db.rollback()

        logger.exception(
            "Finance seed failed"
        )

        raise

    finally:

        if own_session:
            db.close()


# ==========================================================
# LOAD SEED DATA
# ==========================================================

def load_finance_seed():
    """
    Standalone loader used when running this file directly.
    """

    result = seed_finance_accounts()

    print(
        "Finance seed completed."
    )

    print(
        f"Created: {result['created']}"
    )

    print(
        f"Already existed: {result['existing']}"
    )

    return result


# ==========================================================
# COMPATIBILITY ALIAS
# ==========================================================

def load_seed_data():
    """
    Compatibility function.

    Allows the Finance seed to be called using the
    same convention as other Esan seed modules.
    """

    return load_finance_seed()


# ==========================================================
# DIRECT EXECUTION
# ==========================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s - "
            "%(levelname)s - "
            "%(message)s"
        ),
    )

    load_finance_seed()