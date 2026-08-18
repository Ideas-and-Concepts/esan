"""
Esan ERP
Quotation -> Sales Order Conversion Tests

Verifies that every QuotationItem produces exactly one
SalesOrderItem with matching product, quantity, unit price,
and line total.
"""

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from models import (
    Customer,
    Product,
    Quotation,
    QuotationItem,
    SalesOrder,
    SalesOrderItem,
)
from services.quotation_service import (
    convert_quotation_to_sales_order,
)


# ============================================================
# DATABASE FIXTURE
# ============================================================

@pytest.fixture
def db():
    """
    Isolated in-memory SQLite database.

    StaticPool ensures every SQLAlchemy session operation
    uses the same SQLite connection.
    """

    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


# ============================================================
# TEST
# ============================================================

def test_conversion_creates_one_sales_order_item_per_quotation_item(
    db,
):
    """
    Each QuotationItem must create exactly one SalesOrderItem.

    The converted SalesOrderItem must preserve:

    - product_id
    - product_name
    - quantity
    - unit_price
    - total
    """

    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    customer = Customer(
        name="Test Customer",
        phone="0700000000",
        email="test@example.com",
    )

    db.add(customer)
    db.flush()

    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    product_1 = Product(
        name="Maize Flour 1Kg",
        sku="TEST-MF-001",
        category="Finished Product",
        unit="Bag",
        quantity=1000.0,
        cost_price=2000.0,
        selling_price=3000.0,
    )

    product_2 = Product(
        name="Cassava Flour 1Kg",
        sku="TEST-CF-001",
        category="Finished Product",
        unit="Bag",
        quantity=1000.0,
        cost_price=1800.0,
        selling_price=2800.0,
    )

    db.add_all(
        [
            product_1,
            product_2,
        ]
    )

    db.flush()

    # --------------------------------------------------------
    # QUOTATION
    # --------------------------------------------------------

    quotation = Quotation(
        quotation_number="Q-TEST-00001",
        customer_id=customer.id,
        status="Draft",
        total_amount=0.0,
    )

    db.add(quotation)
    db.flush()

    # --------------------------------------------------------
    # QUOTATION ITEMS
    # --------------------------------------------------------

    quotation_item_1 = QuotationItem(
        quotation_id=quotation.id,
        product_id=product_1.id,
        product_name=product_1.name,
        quantity=10.0,
        unit_price=3000.0,
        total=30000.0,
    )

    quotation_item_2 = QuotationItem(
        quotation_id=quotation.id,
        product_id=product_2.id,
        product_name=product_2.name,
        quantity=25.0,
        unit_price=2800.0,
        total=70000.0,
    )

    db.add_all(
        [
            quotation_item_1,
            quotation_item_2,
        ]
    )

    db.flush()

    quotation.total_amount = (
        quotation_item_1.total
        + quotation_item_2.total
    )

    db.commit()

    # --------------------------------------------------------
    # CONVERT
    # --------------------------------------------------------

    sales_order = convert_quotation_to_sales_order(
        db,
        quotation.id,
    )

    # --------------------------------------------------------
    # VERIFY SALES ORDER
    # --------------------------------------------------------

    assert sales_order is not None

    assert sales_order.quotation_id == quotation.id
    assert sales_order.customer_id == customer.id

    # --------------------------------------------------------
    # LOAD QUOTATION ITEMS
    # --------------------------------------------------------

    quotation_items = (
        db.query(QuotationItem)
        .filter(
            QuotationItem.quotation_id
            == quotation.id
        )
        .order_by(QuotationItem.id.asc())
        .all()
    )

    # --------------------------------------------------------
    # LOAD SALES ORDER ITEMS
    # --------------------------------------------------------

    sales_order_items = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == sales_order.id
        )
        .order_by(SalesOrderItem.id.asc())
        .all()
    )

    # --------------------------------------------------------
    # EXACT ONE-TO-ONE COUNT
    # --------------------------------------------------------

    assert len(sales_order_items) == len(
        quotation_items
    )

    assert len(quotation_items) == 2
    assert len(sales_order_items) == 2

    # --------------------------------------------------------
    # VERIFY EACH LINE
    # --------------------------------------------------------

    for quotation_item in quotation_items:

        matching_items = [
            item
            for item in sales_order_items
            if item.product_id
            == quotation_item.product_id
        ]

        assert len(matching_items) == 1

        sales_order_item = matching_items[0]

        # Product
        assert (
            sales_order_item.product_id
            == quotation_item.product_id
        )

        assert (
            sales_order_item.product_name
            == quotation_item.product_name
        )

        # Quantity
        assert (
            sales_order_item.quantity
            == quotation_item.quantity
        )

        # Unit price
        assert (
            sales_order_item.unit_price
            == quotation_item.unit_price
        )

        # Line total
        assert (
            sales_order_item.total
            == quotation_item.total
        )

    # --------------------------------------------------------
    # VERIFY QUOTATION STATUS
    # --------------------------------------------------------

    db.refresh(quotation)

    assert quotation.status == "Converted"

    # --------------------------------------------------------
    # VERIFY SALES ORDER TOTAL
    # --------------------------------------------------------

    expected_total = sum(
        item.total
        for item in quotation_items
    )

    assert (
        sales_order.total_amount
        == expected_total
    )


# ============================================================
# OPTIONAL STRONGER DUPLICATE-LINE CHECK
# ============================================================

def test_conversion_preserves_duplicate_product_lines_separately(
    db,
):
    """
    If a quotation contains two separate lines for the same
    product, conversion must still create exactly two
    SalesOrderItems, not collapse them into one.
    """

    customer = Customer(
        name="Duplicate Line Customer",
    )

    product = Product(
        name="Maize Flour 1Kg",
        sku="TEST-DUP-001",
        quantity=1000.0,
        selling_price=3000.0,
    )

    db.add_all(
        [
            customer,
            product,
        ]
    )

    db.flush()

    quotation = Quotation(
        quotation_number="Q-TEST-DUP-001",
        customer_id=customer.id,
        status="Draft",
        total_amount=0.0,
    )

    db.add(quotation)
    db.flush()

    item_1 = QuotationItem(
        quotation_id=quotation.id,
        product_id=product.id,
        product_name=product.name,
        quantity=10.0,
        unit_price=3000.0,
        total=30000.0,
    )

    item_2 = QuotationItem(
        quotation_id=quotation.id,
        product_id=product.id,
        product_name=product.name,
        quantity=5.0,
        unit_price=2900.0,
        total=14500.0,
    )

    db.add_all(
        [
            item_1,
            item_2,
        ]
    )

    db.flush()

    quotation.total_amount = (
        item_1.total
        + item_2.total
    )

    db.commit()

    # --------------------------------------------------------
    # CONVERT
    # --------------------------------------------------------

    sales_order = convert_quotation_to_sales_order(
        db,
        quotation.id,
    )

    # --------------------------------------------------------
    # VERIFY BOTH LINES SURVIVED
    # --------------------------------------------------------

    sales_order_items = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == sales_order.id
        )
        .order_by(SalesOrderItem.id.asc())
        .all()
    )

    assert len(sales_order_items) == 2

    assert (
        sales_order_items[0].product_id
        == product.id
    )

    assert (
        sales_order_items[1].product_id
        == product.id
    )

    assert (
        sales_order_items[0].quantity
        == 10.0
    )

    assert (
        sales_order_items[1].quantity
        == 5.0
    )

    assert (
        sales_order_items[0].unit_price
        == 3000.0
    )

    assert (
        sales_order_items[1].unit_price
        == 2900.0
    )

    assert (
        sales_order_items[0].total
        == 30000.0
    )

    assert (
        sales_order_items[1].total
        == 14500.0
    )

    # The quotation must be converted exactly once.
    db.refresh(quotation)

    assert quotation.status == "Converted"