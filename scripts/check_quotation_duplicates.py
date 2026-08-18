"""
Esan ERP
Quotation Duplicate Diagnostic

Checks for duplicate SalesOrder.quotation_id values before applying:

    uq_sales_orders_quotation_id

READ-ONLY:
    This script does NOT modify the database.

Usage:
    python scripts/check_quotation_duplicates.py
"""

from pathlib import Path
import sys

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT DATABASE CONFIGURATION
# ============================================================

try:
    from database import DATABASE_URL
except ImportError:
    try:
        from database import SQLALCHEMY_DATABASE_URL as DATABASE_URL
    except ImportError:
        print(
            "ERROR: Could not find DATABASE_URL or "
            "SQLALCHEMY_DATABASE_URL in database.py"
        )
        sys.exit(1)


# ============================================================
# IMPORT MODELS
# ============================================================

try:
    from models import SalesOrder
except ImportError as exc:
    print(f"ERROR: Could not import SalesOrder: {exc}")
    sys.exit(1)


# ============================================================
# ENGINE
# ============================================================

try:
    engine = create_engine(
        DATABASE_URL,
        future=True,
    )
except Exception as exc:
    print(f"ERROR: Could not create database engine: {exc}")
    sys.exit(1)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ============================================================
# DISPLAY DATABASE INFORMATION
# ============================================================

def print_database_info():
    print()
    print("=" * 70)
    print("ESAN ERP - SALES ORDER QUOTATION DUPLICATE SCAN")
    print("=" * 70)

    print()
    print("Database URL:")
    print(f"  {DATABASE_URL}")

    if DATABASE_URL.startswith("sqlite:///"):
        sqlite_path = DATABASE_URL.replace(
            "sqlite:///",
            "",
            1,
        )

        path = Path(sqlite_path)

        if not path.is_absolute():
            path = PROJECT_ROOT / path

        print()
        print("SQLite database file:")
        print(f"  {path.resolve()}")

        print()
        print("Database exists:")
        print(f"  {path.resolve().exists()}")

    print()


# ============================================================
# DUPLICATE SCAN
# ============================================================

def find_duplicates(db):
    """
    Find quotation IDs referenced by more than one SalesOrder.

    NULL quotation_id values are intentionally ignored because
    multiple NULL values are allowed by SQL UNIQUE constraints.
    """

    return (
        db.query(
            SalesOrder.quotation_id.label("quotation_id"),
            func.count(SalesOrder.id).label("sales_order_count"),
        )
        .filter(
            SalesOrder.quotation_id.isnot(None)
        )
        .group_by(
            SalesOrder.quotation_id
        )
        .having(
            func.count(SalesOrder.id) > 1
        )
        .order_by(
            SalesOrder.quotation_id.asc()
        )
        .all()
    )


# ============================================================
# SHOW AFFECTED SALES ORDERS
# ============================================================

def show_duplicate_orders(db, duplicate_rows):
    print("=" * 70)
    print("DUPLICATE QUOTATION REFERENCES")
    print("=" * 70)

    if not duplicate_rows:
        print()
        print("SUCCESS")
        print("No duplicate quotation_id values were found.")
        print()
        print(
            "The database contains no existing duplicate "
            "SalesOrder.quotation_id values."
        )
        print()
        return

    print()

    for duplicate in duplicate_rows:

        quotation_id = duplicate.quotation_id
        count = duplicate.sales_order_count

        print(
            f"Quotation ID {quotation_id} "
            f"is referenced by {count} Sales Orders:"
        )

        orders = (
            db.query(SalesOrder)
            .filter(
                SalesOrder.quotation_id == quotation_id
            )
            .order_by(
                SalesOrder.id.asc()
            )
            .all()
        )

        for order in orders:
            print(
                f"    ID={order.id}"
                f" | Order Number={order.order_number}"
                f" | Status={order.status}"
                f" | Date={order.order_date}"
                f" | Customer ID={order.customer_id}"
                f" | Total={order.total_amount}"
            )

        print()


# ============================================================
# SUMMARY
# ============================================================

def print_summary(duplicate_rows):
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if not duplicate_rows:
        print()
        print("Duplicate quotation_id groups : 0")
        print("Constraint status             : SAFE TO PROCEED")
        print()
        print(
            "No duplicate SalesOrder.quotation_id "
            "values need to be cleaned."
        )
        print()
        return

    total_groups = len(duplicate_rows)

    duplicate_order_count = sum(
        row.sales_order_count
        for row in duplicate_rows
    )

    print()
    print(
        f"Duplicate quotation_id groups : {total_groups}"
    )

    print(
        f"Sales Orders involved         : "
        f"{duplicate_order_count}"
    )

    print(
        "Constraint status             : "
        "NOT SAFE TO APPLY YET"
    )

    print()
    print(
        "Existing duplicates must be reviewed and "
        "resolved before adding:"
    )

    print()
    print(
        "    uq_sales_orders_quotation_id"
    )

    print()
    print(
        "IMPORTANT: This script has made NO database changes."
    )

    print()


# ============================================================
# MAIN
# ============================================================

def main():

    print_database_info()

    db = SessionLocal()

    try:

        duplicate_rows = find_duplicates(db)

        show_duplicate_orders(
            db,
            duplicate_rows,
        )

        print_summary(
            duplicate_rows,
        )

    except Exception as exc:

        print()
        print("=" * 70)
        print("ERROR DURING DUPLICATE SCAN")
        print("=" * 70)
        print()
        print(type(exc).__name__)
        print(str(exc))
        print()

        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()