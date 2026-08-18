"""
Esan ERP
Safe migration: enforce one SalesOrder per Quotation.

Adds:
    uq_sales_orders_quotation_id

Before adding the constraint, the script checks for duplicate
non-NULL quotation_id values and aborts safely if any exist.

Works with SQLite and SQLAlchemy.
"""

from sqlalchemy import inspect, text

from database import engine


CONSTRAINT_NAME = "uq_sales_orders_quotation_id"
TABLE_NAME = "sales_orders"
COLUMN_NAME = "quotation_id"


def get_duplicate_quotation_ids(connection):
    """Return quotation IDs that occur more than once."""

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


def constraint_exists(connection):
    """Check whether the unique constraint already exists."""

    inspector = inspect(connection)

    # SQLite exposes unique constraints through get_unique_constraints().
    constraints = inspector.get_unique_constraints(TABLE_NAME)

    return any(
        constraint.get("name") == CONSTRAINT_NAME
        for constraint in constraints
    )


def sqlite_table_has_unique_index(connection):
    """
    SQLite may represent a unique constraint/index differently
    depending on how the database was created.

    Check indexes as a second safety measure.
    """

    inspector = inspect(connection)

    indexes = inspector.get_indexes(TABLE_NAME)

    for index in indexes:
        if index.get("name") == CONSTRAINT_NAME:
            if index.get("unique"):
                return True

    return False


def add_sqlite_unique_constraint(connection):
    """
    SQLite does not support:

        ALTER TABLE ... ADD CONSTRAINT ...

    Therefore create a unique index with the required name.
    """

    connection.execute(
        text(
            f"""
            CREATE UNIQUE INDEX {CONSTRAINT_NAME}
            ON {TABLE_NAME} ({COLUMN_NAME})
            """
        )
    )


def add_generic_unique_constraint(connection):
    """
    Generic SQLAlchemy-compatible migration for databases that
    support ALTER TABLE ADD CONSTRAINT.
    """

    connection.execute(
        text(
            f"""
            ALTER TABLE {TABLE_NAME}
            ADD CONSTRAINT {CONSTRAINT_NAME}
            UNIQUE ({COLUMN_NAME})
            """
        )
    )


def main():
    print("=" * 70)
    print("Esan ERP - Sales Order Quotation Constraint Migration")
    print("=" * 70)

    print()
    print("Database URL:")
    print(engine.url)

    with engine.begin() as connection:

        dialect = connection.dialect.name

        print()
        print(f"Database dialect: {dialect}")

        # ------------------------------------------------------
        # Verify table exists
        # ------------------------------------------------------

        inspector = inspect(connection)

        tables = inspector.get_table_names()

        if TABLE_NAME not in tables:
            raise RuntimeError(
                f"Table '{TABLE_NAME}' does not exist."
            )

        print(
            f"✓ Table '{TABLE_NAME}' exists."
        )

        # ------------------------------------------------------
        # Check whether constraint/index already exists
        # ------------------------------------------------------

        if constraint_exists(connection):
            print()
            print(
                f"✓ Constraint '{CONSTRAINT_NAME}' already exists."
            )
            print("Nothing to migrate.")
            return

        if dialect == "sqlite" and sqlite_table_has_unique_index(
            connection
        ):
            print()
            print(
                f"✓ Unique index '{CONSTRAINT_NAME}' already exists."
            )
            print("Nothing to migrate.")
            return

        # ------------------------------------------------------
        # Duplicate detection
        # ------------------------------------------------------

        print()
        print("Scanning for duplicate quotation_id values...")

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
                "Duplicate quotation_id values were found."
            )

            print()
            print(
                f"{'quotation_id':<20} {'sales_orders':>15}"
            )
            print("-" * 40)

            for quotation_id, order_count in duplicates:
                print(
                    f"{str(quotation_id):<20} "
                    f"{order_count:>15}"
                )

            print()
            print(
                "Clean these duplicates before running this "
                "migration again."
            )

            print()
            print(
                "No database changes were made."
            )

            return

        print("✓ No duplicate quotation_id values found.")

        # ------------------------------------------------------
        # Apply constraint
        # ------------------------------------------------------

        print()
        print(
            f"Adding '{CONSTRAINT_NAME}'..."
        )

        if dialect == "sqlite":
            add_sqlite_unique_constraint(
                connection
            )
        else:
            add_generic_unique_constraint(
                connection
            )

        print(
            f"✓ '{CONSTRAINT_NAME}' added successfully."
        )

    # ----------------------------------------------------------
    # Final verification
    # ----------------------------------------------------------

    print()
    print("Verifying migration...")

    with engine.connect() as connection:

        if dialect == "sqlite":
            verified = sqlite_table_has_unique_index(
                connection
            )
        else:
            verified = constraint_exists(
                connection
            )

    if not verified:
        raise RuntimeError(
            f"Migration verification failed: "
            f"{CONSTRAINT_NAME} was not detected."
        )

    print(
        f"✓ Verified: {CONSTRAINT_NAME}"
    )

    print()
    print("=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    print()
    print(
        "The database now prevents more than one SalesOrder "
        "from referencing the same quotation."
    )


if __name__ == "__main__":
    main()