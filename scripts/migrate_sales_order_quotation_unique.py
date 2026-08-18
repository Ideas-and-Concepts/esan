"""
Esan ERP
Migration: Unique SalesOrder.quotation_id

Adds database-level protection so that one quotation can create
at most one Sales Order.

Constraint/index name:

    uq_sales_orders_quotation_id

IMPORTANT:
    This migration is intentionally defensive.

    It WILL NOT modify the database if duplicate quotation_id
    values already exist.

Usage:

    python scripts/migrate_sales_order_quotation_unique.py
"""

from pathlib import Path
import shutil
import sys
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

try:
    from database import DATABASE_URL
except ImportError:
    try:
        from database import SQLALCHEMY_DATABASE_URL as DATABASE_URL
    except ImportError:
        print(
            "ERROR: database.py must define either "
            "DATABASE_URL or SQLALCHEMY_DATABASE_URL."
        )
        sys.exit(1)


# ============================================================
# CONSTANTS
# ============================================================

INDEX_NAME = "uq_sales_orders_quotation_id"
TABLE_NAME = "sales_orders"
COLUMN_NAME = "quotation_id"


# ============================================================
# DATABASE ENGINE
# ============================================================

try:
    engine = create_engine(
        DATABASE_URL,
        future=True,
    )
except Exception as exc:
    print(f"ERROR: Could not create database engine: {exc}")
    sys.exit(1)


# ============================================================
# DATABASE INFORMATION
# ============================================================

def get_database_path():

    url = make_url(str(engine.url))

    if url.get_backend_name() != "sqlite":
        return None

    if not url.database:
        return None

    if url.database == ":memory:":
        return None

    path = Path(url.database).expanduser()

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path.resolve()


# ============================================================
# BACKUP
# ============================================================

def backup_sqlite_database():

    database_path = get_database_path()

    if database_path is None:
        print(
            "SQLite file backup skipped because the database "
            "is not a file-based SQLite database."
        )
        return None

    if not database_path.exists():
        raise RuntimeError(
            f"SQLite database does not exist: {database_path}"
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = database_path.with_name(
        f"{database_path.stem}"
        f"_before_quotation_unique_"
        f"{timestamp}"
        f"{database_path.suffix}"
    )

    shutil.copy2(
        database_path,
        backup_path,
    )

    print()
    print("SQLite backup created:")
    print(f"  {backup_path}")

    return backup_path


# ============================================================
# CHECK DUPLICATES
# ============================================================

def find_duplicates(connection):

    result = connection.execute(
        text(
            f"""
            SELECT
                {COLUMN_NAME},
                COUNT(*) AS sales_order_count
            FROM {TABLE_NAME}
            WHERE {COLUMN_NAME} IS NOT NULL
            GROUP BY {COLUMN_NAME}
            HAVING COUNT(*) > 1
            ORDER BY {COLUMN_NAME}
            """
        )
    )

    return result.fetchall()


# ============================================================
# CHECK EXISTING INDEX
# ============================================================

def index_exists(connection):

    dialect = connection.dialect.name

    if dialect == "sqlite":

        result = connection.execute(
            text(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'index'
                  AND name = :index_name
                """
            ),
            {
                "index_name": INDEX_NAME,
            },
        )

        return result.first() is not None

    if dialect == "postgresql":

        result = connection.execute(
            text(
                """
                SELECT 1
                FROM pg_indexes
                WHERE indexname = :index_name
                """
            ),
            {
                "index_name": INDEX_NAME,
            },
        )

        return result.first() is not None

    return False


# ============================================================
# CREATE UNIQUE INDEX
# ============================================================

def create_unique_index(connection):

    dialect = connection.dialect.name

    if dialect == "sqlite":

        connection.execute(
            text(
                f"""
                CREATE UNIQUE INDEX {INDEX_NAME}
                ON {TABLE_NAME} ({COLUMN_NAME})
                """
            )
        )

        return

    if dialect == "postgresql":

        connection.execute(
            text(
                f"""
                CREATE UNIQUE INDEX {INDEX_NAME}
                ON {TABLE_NAME} ({COLUMN_NAME})
                """
            )
        )

        return

    raise RuntimeError(
        f"Unsupported database dialect: {dialect}"
    )


# ============================================================
# VERIFY UNIQUE INDEX
# ============================================================

def verify_index(connection):

    if not index_exists(connection):
        raise RuntimeError(
            f"Could not verify {INDEX_NAME}."
        )


# ============================================================
# MAIN MIGRATION
# ============================================================

def main():

    print("=" * 70)
    print("ESAN ERP")
    print("Sales Order Quotation Uniqueness Migration")
    print("=" * 70)

    print()
    print("Database URL:")
    print(f"  {engine.url}")

    print()
    print("Database dialect:")
    print(f"  {engine.dialect.name}")

    database_path = get_database_path()

    if database_path:
        print()
        print("SQLite database:")
        print(f"  {database_path}")

    # --------------------------------------------------------
    # BACKUP
    # --------------------------------------------------------

    backup_sqlite_database()

    # --------------------------------------------------------
    # TRANSACTION
    # --------------------------------------------------------

    with engine.begin() as connection:

        print()
        print("Checking for duplicate quotation_id values...")

        duplicates = find_duplicates(
            connection
        )

        # ----------------------------------------------------
        # REFUSE MIGRATION IF DUPLICATES EXIST
        # ----------------------------------------------------

        if duplicates:

            print()
            print(
                "MIGRATION ABORTED"
            )

            print()
            print(
                "Duplicate quotation_id values were found:"
            )

            for quotation_id, count in duplicates:

                print(
                    f"  quotation_id={quotation_id}"
                    f" | sales_orders={count}"
                )

            print()
            print(
                "Resolve these duplicates before running "
                "the migration again."
            )

            print()
            print(
                "NO UNIQUE INDEX WAS CREATED."
            )

            return

        print()
        print(
            "Duplicate check passed."
        )

        # ----------------------------------------------------
        # EXISTING INDEX
        # ----------------------------------------------------

        if index_exists(connection):

            print()
            print(
                f"{INDEX_NAME} already exists."
            )

            print(
                "No migration is required."
            )

            return

        # ----------------------------------------------------
        # CREATE UNIQUE INDEX
        # ----------------------------------------------------

        print()
        print(
            f"Creating unique index: {INDEX_NAME}"
        )

        create_unique_index(
            connection
        )

        # ----------------------------------------------------
        # VERIFY
        # ----------------------------------------------------

        verify_index(
            connection
        )

        print()
        print(
            "Unique index successfully created."
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    print()
    print("=" * 70)
    print("MIGRATION SUCCESSFUL")
    print("=" * 70)

    print()
    print(
        f"Database protection added:"
    )

    print(
        f"  {INDEX_NAME}"
    )

    print()
    print(
        "One non-NULL quotation_id can now reference "
        "only one Sales Order."
    )

    print()
    print(
        "Existing NULL quotation_id values remain allowed."
    )

    print()


if __name__ == "__main__":
    main()