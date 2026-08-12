"""
Esan ERP
Central Seed Data Loader

Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
"""

import logging

from database import SessionLocal

from seed.finance_seed import seed_finance_accounts


logger = logging.getLogger(__name__)


# ==========================================================
# OPTIONAL EXISTING SEEDS
# ==========================================================

def seed_customers(db):
    """
    Existing customer seed logic can remain here.
    """

    # ------------------------------------------------------
    # IMPORTANT:
    # Keep your existing customer seed code here.
    # ------------------------------------------------------

    return 0


def seed_products(db):
    """
    Existing product seed logic can remain here.
    """

    # ------------------------------------------------------
    # Keep your existing product seed code here.
    # ------------------------------------------------------

    return 0


def seed_suppliers(db):
    """
    Existing supplier seed logic can remain here.
    """

    # ------------------------------------------------------
    # Keep your existing supplier seed code here.
    # ------------------------------------------------------

    return 0


# ==========================================================
# CENTRAL SEED LOADER
# ==========================================================

def load_seed_data():
    """
    Load all Esan ERP seed data.

    This function is called by streamlit_app.py
    during application initialization.
    """

    db = SessionLocal()

    results = {
        "customers": 0,
        "products": 0,
        "suppliers": 0,
        "finance_accounts": 0,
    }

    try:

        # --------------------------------------------------
        # CUSTOMERS
        # --------------------------------------------------

        try:

            results["customers"] = (
                seed_customers(db)
                or 0
            )

        except Exception as e:

            logger.exception(
                "Customer seed failed: %s",
                e,
            )

        # --------------------------------------------------
        # PRODUCTS
        # --------------------------------------------------

        try:

            results["products"] = (
                seed_products(db)
                or 0
            )

        except Exception as e:

            logger.exception(
                "Product seed failed: %s",
                e,
            )

        # --------------------------------------------------
        # SUPPLIERS
        # --------------------------------------------------

        try:

            results["suppliers"] = (
                seed_suppliers(db)
                or 0
            )

        except Exception as e:

            logger.exception(
                "Supplier seed failed: %s",
                e,
            )

        # --------------------------------------------------
        # FINANCE
        # --------------------------------------------------

        try:

            finance_result = (
                seed_finance_accounts(db)
            )

            if finance_result:

                results[
                    "finance_accounts"
                ] = finance_result.get(
                    "created",
                    0,
                )

        except Exception as e:

            logger.exception(
                "Finance seed failed: %s",
                e,
            )

        logger.info(
            "Esan ERP seed process completed."
        )

        return results

    finally:

        db.close()


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

    result = load_seed_data()

    print(
        "\nEsan ERP seed process completed."
    )

    print(
        f"Customers: "
        f"{result['customers']}"
    )

    print(
        f"Products: "
        f"{result['products']}"
    )

    print(
        f"Suppliers: "
        f"{result['suppliers']}"
    )

    print(
        f"Finance accounts created: "
        f"{result['finance_accounts']}"
    )