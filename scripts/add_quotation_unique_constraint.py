"""
Esan ERP
PostgreSQL-safe migration:
Enforce one SalesOrder per Quotation.

Creates:

    uq_sales_orders_quotation_id

on:

    sales_orders(quotation_id)

The migration is:

- Read-only until validation succeeds
- Safe against existing duplicate quotation_id values
- Idempotent
- Safe to run repeatedly
- Detects an existing unique constraint
- Detects an existing unique index
- Uses PostgreSQL's transactional DDL
- Does not modify duplicate records

Usage:

    python scripts/add_quotation_unique_constraint.py
"""

from sqlalchemy import inspect, text

from database import engine


TABLE_NAME = "sales_orders"
COLUMN_NAME = "quotation_id"
CONSTRAINT_NAME = "uq_sales_orders_quotation_id"


# ============================================================
# DUPLICATE CHECK
# ============================================================

def get_duplicate_quotation_ids(connection):
    """
    Return quotation_id values referenced by more than one
    Sales Order.

    NULL quotation_id values are intentionally ignored.
    """

    result = connection.execute(
        text(
            """
            SELECT
                quotation_id,
                COUNT(*) AS order_count
            FROM sales_orders
            WHERE quotation_id IS NOT NULL
            GROUP BY quotation_id
            HAVING COUNT(*) > 1
            ORDER BY quotation_id
            """
        )
    )

    return result.fetchall()


# ============================================================
# CONSTRAINT DETECTION
# ============================================================

def get_unique_constraint(connection):
    """
    Return an existing unique constraint with our expected
    name, if present.
    """

    inspector = inspect(connection)

    constraints = inspector.get_unique_constraints(
        TABLE_NAME
    )

    for constraint in constraints:

        if constraint.get("name") == CONSTRAINT_NAME:

            columns = constraint.get(
                "column_names",
                [],
            )

            if columns == [COLUMN_NAME]:
                return constraint

    return None


# ============================================================
# INDEX DETECTION
# ============================================================

def get_unique_index(connection):
    """
    Return an existing unique index with our expected name,
    if present.
    """

    inspector = inspect(connection)

    indexes = inspector.get_indexes(
        TABLE_NAME
    )

    for index in indexes:

        if index.get("name") != CONSTRAINT_NAME:
            continue

        columns = index.get(
            "column_names",
            [],
        )

        if (
            index.get("unique") is True
            and columns == [COLUMN_NAME]
        ):
            return index

    return None


# ============================================================
# POSTGRESQL CATALOG CHECK
# ============================================================

def get_postgres_unique_object(connection):
    """
    Direct PostgreSQL catalog check.

    This catches unique indexes/constraints even when SQLAlchemy's
    inspector representation differs from expectations.
    """

    result = connection.execute(
        text(
            """
            SELECT
                c.relname AS object_name,
                i.indisunique AS is_unique,
                pg_get_indexdef(i.indexrelid) AS index_definition
            FROM pg_index i
            JOIN pg_class c
                ON c.oid = i.indexrelid
            JOIN pg_class t
                ON t.oid = i.indrelid
            JOIN pg_namespace n
                ON n.oid = t.relnamespace
            WHERE t.relname = :table_name
              AND n.nspname = current_schema()
              AND c.relname = :object_name
            """
        ),
        {
            "table_name": TABLE_NAME,
            "object_name": CONSTRAINT_NAME,
        },
    )

    return result.first()


# ============================================================
# CREATE UNIQUE INDEX
# ============================================================

def create_unique_index(connection):
    """
    Create the unique index.

    PostgreSQL's normal CREATE UNIQUE INDEX is transactional
    when executed inside the SQLAlchemy transaction used here.
    """

    connection.execute(
        text(
            f"""
            CREATE UNIQUE INDEX {CONSTRAINT_NAME}
            ON {TABLE_NAME} ({COLUMN_NAME})
            """
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "Esan ERP - PostgreSQL Sales Order Quotation Migration"
    )
    print("=" * 70)

    print()
    print("Database URL:")
    print(engine.url)

    print()
    print("Database dialect:")
    print(engine.dialect.name)

    if engine.dialect.name != "postgresql":

        raise RuntimeError(
            "This migration is intended for PostgreSQL. "
            f"Detected: {engine.dialect.name}"
        )

    # --------------------------------------------------------
    # Begin transactional migration
    # --------------------------------------------------------

    with engine.begin() as connection:

        # ----------------------------------------------------
        # Verify table
        # ----------------------------------------------------

        inspector = inspect(connection)

        tables = inspector.get_table_names()

        if TABLE_NAME not in tables:

            raise RuntimeError(
                f"Table '{TABLE_NAME}' does not exist."
            )

        print()
        print(
            f"✓ Table '{TABLE_NAME}' exists."
        )

        # ----------------------------------------------------
        # Detect existing named unique constraint
        # ----------------------------------------------------

        existing_constraint = get_unique_constraint(
            connection
        )

        if existing_constraint:

            print()
            print(
                f"✓ Unique constraint '{CONSTRAINT_NAME}' "
                "already exists."
            )

            print()
            print(
                "No migration required."
            )

            return

        # ----------------------------------------------------
        # Detect existing named unique index
        # ----------------------------------------------------

        existing_index = get_unique_index(
            connection
        )

        if existing_index:

            print()
            print(
                f"✓ Unique index '{CONSTRAINT_NAME}' "
                "already exists."
            )

            print()
            print(
                "No migration required."
            )

            return

        # ----------------------------------------------------
        # PostgreSQL catalog verification
        # ----------------------------------------------------

        catalog_object = get_postgres_unique_object(
            connection
        )

        if catalog_object:

            object_name = catalog_object.object_name
            is_unique = catalog_object.is_unique

            print()
            print(
                f"Found existing PostgreSQL object: "
                f"{object_name}"
            )

            if is_unique:

                print(
                    "✓ Existing object is unique."
                )

                print()
                print(
                    "No migration required."
                )

                return

            raise RuntimeError(
                f"An object named '{CONSTRAINT_NAME}' "
                "already exists but is not unique. "
                "Migration stopped to avoid modifying it."
            )

        # ----------------------------------------------------
        # Duplicate scan
        # ----------------------------------------------------

        print()
        print(
            "Scanning for duplicate quotation_id values..."
        )

        duplicates = get_duplicate_quotation_ids(
            connection
        )

        if duplicates:

            print()
            print("!" * 70)
            print("MIGRATION ABORTED")
            print("!" * 70)

            print()
            print(
                "Duplicate quotation_id values were found:"
            )

            print()
            print(
                f"{'quotation_id':<20}"
                f"{'sales_orders':>15}"
            )

            print("-" * 35)

            for quotation_id, order_count in duplicates:

                print(
                    f"{str(quotation_id):<20}"
                    f"{order_count:>15}"
                )

            print()
            print(
                "Resolve the duplicate Sales Orders before "
                "running this migration again."
            )

            print()
            print(
                "No database changes were made."
            )

            return

        print()
        print(
            "✓ Duplicate check passed."
        )

        # ----------------------------------------------------
        # Create unique index
        # ----------------------------------------------------

        print()
        print(
            f"Creating unique index '{CONSTRAINT_NAME}'..."
        )

        create_unique_index(
            connection
        )

        print(
            "✓ Unique index created."
        )

        # ----------------------------------------------------
        # Verify creation
        # ----------------------------------------------------

        print()
        print(
            "Verifying PostgreSQL catalog..."
        )

        verified = get_postgres_unique_object(
            connection
        )

        if not verified:

            raise RuntimeError(
                "Migration verification failed. "
                f"'{CONSTRAINT_NAME}' was not found."
            )

        if not verified.is_unique:

            raise RuntimeError(
                f"'{CONSTRAINT_NAME}' exists but is not unique."
            )

        print(
            "✓ PostgreSQL reports the object as UNIQUE."
        )

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)

    print()
    print(
        f"Unique enforcement:"
    )

    print(
        f"  {TABLE_NAME}.{COLUMN_NAME}"
    )

    print()
    print(
        f"Object:"
    )

    print(
        f"  {CONSTRAINT_NAME}"
    )

    print()
    print(
        "One non-NULL quotation_id can now reference "
        "only one Sales Order."
    )

    print()
    print(
        "Multiple NULL quotation_id values remain allowed."
    )

    print()


if __name__ == "__main__":
    main()