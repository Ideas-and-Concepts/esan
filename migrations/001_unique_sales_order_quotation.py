"""
Migration:
Enforce one SalesOrder per Quotation.

Adds a UNIQUE constraint to sales_orders.quotation_id.
"""

from sqlalchemy import text

from database import engine


def migrate():
    with engine.begin() as connection:

        # ----------------------------------------------------
        # Check whether the unique index already exists.
        # ----------------------------------------------------

        result = connection.execute(
            text(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                  AND name = 'uq_sales_orders_quotation_id'
                """
            )
        )

        if result.fetchone():

            print(
                "Migration already applied: "
                "uq_sales_orders_quotation_id"
            )

            return

        # ----------------------------------------------------
        # Find duplicate quotation references before applying
        # the constraint.
        # ----------------------------------------------------

        duplicates = connection.execute(
            text(
                """
                SELECT quotation_id, COUNT(*) AS count
                FROM sales_orders
                WHERE quotation_id IS NOT NULL
                GROUP BY quotation_id
                HAVING COUNT(*) > 1
                """
            )
        ).fetchall()

        if duplicates:

            raise RuntimeError(
                "Migration aborted. Duplicate quotation_id "
                "values already exist in sales_orders: "
                f"{duplicates}"
            )

        # ----------------------------------------------------
        # SQLite supports a unique index directly.
        # ----------------------------------------------------

        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX
                uq_sales_orders_quotation_id
                ON sales_orders (quotation_id)
                """
            )
        )

        print(
            "Migration successful: "
            "sales_orders.quotation_id is now unique."
        )


if __name__ == "__main__":
    migrate()