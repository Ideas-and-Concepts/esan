"""
Esan ERP
Database Target Inspection

Prints:
- SQLAlchemy engine URL
- Database driver
- Resolved SQLite database path
- Proposed backup target

This script does NOT modify the database.
"""

from pathlib import Path

from sqlalchemy.engine import make_url

from database import engine


def main():
    print("=" * 60)
    print("ESAN ERP DATABASE TARGET CHECK")
    print("=" * 60)

    engine_url = str(engine.url)
    url = make_url(engine_url)

    print()
    print("SQLAlchemy engine URL:")
    print(engine_url)

    print()
    print("Database driver:")
    print(url.drivername)

    print()
    if url.drivername.startswith("sqlite") and url.database:
        database_path = Path(url.database).resolve()
        backup_path = Path(
            f"{database_path}.bak"
        ).resolve()

        print("SQLite database:")
        print(database_path)

        print()
        print("Database exists:")
        print(database_path.exists())

        print()
        print("Proposed backup target:")
        print(backup_path)

        print()
        print("Backup target already exists:")
        print(backup_path.exists())

        if database_path.exists():
            print()
            print("Database size:")
            print(f"{database_path.stat().st_size:,} bytes")

    else:
        print()
        print("SQLite database:")
        print("N/A")

        print()
        print("Backup target:")
        print("N/A")

        print()
        print(
            "This database is not using SQLite. "
            "Use the database server's native backup procedure."
        )

    print()
    print("=" * 60)
    print("NO DATABASE CHANGES WERE MADE")
    print("=" * 60)


if __name__ == "__main__":
    main()