# tests/test_duplicate_quotation_conversion.py

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models import (
    Customer,
    Product,
    Quotation,
    SalesOrder,
    SalesOrderItem,
)

from services.quotation_service import (
    create_quotation,
    add_quotation_item,
    convert_quotation_to_sales_order,
)


# ==========================================================
# ISOLATED DATABASE FIXTURE
# ==========================================================

@pytest.fixture
def db():
    """
    Create a completely isolated in-memory SQLite database
    for each test.
    """

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
    )

    # Create every table defined by the Esan SQLAlchemy models.
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        # Roll back anything left open.
        session.rollback()

        # Close the test session.
        session.close()

        # Drop all tables before disposing the engine.
        Base.metadata.drop_all(bind=engine)

        # Release the in-memory database connection.
        engine.dispose()


# ==========================================================
# TEST
# ==========================================================

def test_converting_same_quotation_twice_creates_no_duplicates(
    db,
):
    """
    Verify that:

    1. The first conversion succeeds.
    2. The quotation becomes Converted.
    3. Exactly one SalesOrder is created.
    4. Exactly one SalesOrderItem is created for one QuotationItem.
    5. A second conversion raises ValueError.
    6. The second attempt creates no additional
       SalesOrder or SalesOrderItem.
    """

    # ------------------------------------------------------
    # ARRANGE
    # ------------------------------------------------------

    customer = Customer(
        name="Test Customer",
        phone="0700000000",
    )

    product = Product(
        name="Test Product",
        category="Test",
        unit="kg",
        quantity=100,
        cost_price=1000,
        selling_price=1500,
    )

    db.add_all([
        customer,
        product,
    ])

    db.commit()

    # ------------------------------------------------------
    # CREATE QUOTATION
    # ------------------------------------------------------

    quotation = create_quotation(
        db=db,
        customer_id=customer.id,
    )

    add_quotation_item(
        db=db,
        quotation_id=quotation.id,
        product_id=product.id,
        quantity=10,
        unit_price=1500,
    )

    # Confirm there is exactly one quotation item.
    quotation_items = (
        db.query(Quotation)
        .filter(
            Quotation.id == quotation.id
        )
        .one()
    )

    # ------------------------------------------------------
    # FIRST CONVERSION
    # ------------------------------------------------------

    sales_order = convert_quotation_to_sales_order(
        db=db,
        quotation_id=quotation.id,
    )

    # ------------------------------------------------------
    # VERIFY FIRST CONVERSION
    # ------------------------------------------------------

    converted_quotation = (
        db.query(Quotation)
        .filter(
            Quotation.id == quotation.id
        )
        .one()
    )

    assert converted_quotation.status == "Converted"

    orders = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.quotation_id
            == quotation.id
        )
        .all()
    )

    assert len(orders) == 1
    assert orders[0].id == sales_order.id

    quotation_item_count = (
        db.query(QuotationItem)
        .filter(
            QuotationItem.quotation_id
            == quotation.id
        )
        .count()
    )

    sales_order_item_count = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == sales_order.id
        )
        .count()
    )

    assert quotation_item_count == 1
    assert sales_order_item_count == quotation_item_count

    # ------------------------------------------------------
    # SECOND CONVERSION
    # ------------------------------------------------------

    with pytest.raises(
        ValueError,
        match="already been converted",
    ):
        convert_quotation_to_sales_order(
            db=db,
            quotation_id=quotation.id,
        )

    # ------------------------------------------------------
    # VERIFY NO DUPLICATES
    # ------------------------------------------------------

    orders_after_second_attempt = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.quotation_id
            == quotation.id
        )
        .all()
    )

    assert len(orders_after_second_attempt) == 1

    assert (
        orders_after_second_attempt[0].id
        == sales_order.id
    )

    items_after_second_attempt = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == sales_order.id
        )
        .all()
    )

    assert len(items_after_second_attempt) == 1

    final_quotation = (
        db.query(Quotation)
        .filter(
            Quotation.id == quotation.id
        )
        .one()
    )

    assert final_quotation.status == "Converted"