"""
Esan ERP
Quotation -> Sales Order Conversion Regression Test

Verifies that:
- One SalesOrder is created.
- Exactly one SalesOrderItem is created per QuotationItem.
- Quotation status becomes "Converted".
- Product name, quantity, unit price and total are preserved.
- A valid order_number is generated.

Run:
    pytest -q tests/test_quotation_conversion.py
"""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
# TEST DATABASE
# ============================================================

@pytest.fixture()
def db():
    """
    Create a completely isolated in-memory SQLite database.
    """

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


# ============================================================
# TEST CONVERSION
# ============================================================

def test_convert_quotation_creates_sales_order_items(
    db,
):
    """
    A quotation with N items must create:

        1 SalesOrder
        N SalesOrderItems

    and the quotation must become Converted.
    """

    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    customer = Customer(
        name="Test Customer",
        phone="0700000000",
        email="test@example.com",
        address="Kampala",
        customer_type="Wholesale",
        active=True,
    )

    db.add(customer)
    db.flush()

    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    product_1 = Product(
        name="Maize Flour 25kg",
        sku="MF-25",
        category="Finished Product",
        product_type="Finished Product",
        unit="Bag",
        quantity=100,
        cost_price=25000,
        selling_price=35000,
        minimum_stock=10,
        active=True,
    )

    product_2 = Product(
        name="Maize Flour 50kg",
        sku="MF-50",
        category="Finished Product",
        product_type="Finished Product",
        unit="Bag",
        quantity=100,
        cost_price=45000,
        selling_price=60000,
        minimum_stock=10,
        active=True,
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
        quotation_number="Q-00001",
        customer_id=customer.id,
        quotation_date=date.today(),
        status="Draft",
        total_amount=155000,
        notes="Conversion regression test",
    )

    db.add(quotation)
    db.flush()

    # --------------------------------------------------------
    # QUOTATION ITEMS
    # --------------------------------------------------------

    item_1 = QuotationItem(
        quotation_id=quotation.id,
        product_id=product_1.id,
        product_name=product_1.name,
        quantity=2,
        unit_price=35000,
        total=70000,
    )

    item_2 = QuotationItem(
        quotation_id=quotation.id,
        product_id=product_2.id,
        product_name=product_2.name,
        quantity=1,
        unit_price=60000,
        total=60000,
    )

    item_3 = QuotationItem(
        quotation_id=quotation.id,
        product_id=product_1.id,
        product_name=product_1.name,
        quantity=1,
        unit_price=25000,
        total=25000,
    )

    db.add_all(
        [
            item_1,
            item_2,
            item_3,
        ]
    )

    db.commit()

    # --------------------------------------------------------
    # VERIFY INITIAL STATE
    # --------------------------------------------------------

    quotation_before = (
        db.query(Quotation)
        .filter(
            Quotation.id == quotation.id
        )
        .one()
    )

    quotation_items_before = (
        db.query(QuotationItem)
        .filter(
            QuotationItem.quotation_id
            == quotation.id
        )
        .all()
    )

    assert quotation_before.status == "Draft"

    assert len(quotation_items_before) == 3

    # --------------------------------------------------------
    # CONVERT
    # --------------------------------------------------------

    sales_order = convert_quotation_to_sales_order(
        db,
        quotation.id,
    )

    # --------------------------------------------------------
    # BASIC SALES ORDER ASSERTIONS
    # --------------------------------------------------------

    assert sales_order is not None

    assert isinstance(
        sales_order,
        SalesOrder,
    )

    assert sales_order.id is not None

    assert sales_order.order_number is not None

    assert sales_order.order_number != ""

    assert sales_order.customer_id == customer.id

    assert sales_order.quotation_id == quotation.id

    # --------------------------------------------------------
    # VERIFY SALES ORDER WAS SAVED
    # --------------------------------------------------------

    saved_order = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.id == sales_order.id
        )
        .one()
    )

    assert saved_order.order_number == (
        sales_order.order_number
    )

    # --------------------------------------------------------
    # VERIFY EXACT NUMBER OF SALES ORDER ITEMS
    # --------------------------------------------------------

    sales_order_items = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == sales_order.id
        )
        .order_by(
            SalesOrderItem.id
        )
        .all()
    )

    assert len(sales_order_items) == (
        len(quotation_items_before)
    )

    assert len(sales_order_items) == 3

    # --------------------------------------------------------
    # VERIFY EACH ITEM
    # --------------------------------------------------------

    for quotation_item, sales_item in zip(
        quotation_items_before,
        sales_order_items,
    ):

        assert (
            sales_item.sales_order_id
            == sales_order.id
        )

        assert (
            sales_item.product_id
            == quotation_item.product_id
        )

        assert (
            sales_item.product_name
            == quotation_item.product_name
        )

        assert (
            float(sales_item.quantity)
            == float(quotation_item.quantity)
        )

        assert (
            float(sales_item.unit_price)
            == float(quotation_item.unit_price)
        )

        assert (
            float(sales_item.total)
            == float(quotation_item.total)
        )

    # --------------------------------------------------------
    # VERIFY SPECIFIC ITEM VALUES
    # --------------------------------------------------------

    assert sales_order_items[0].product_name == (
        "Maize Flour 25kg"
    )

    assert float(
        sales_order_items[0].quantity
    ) == 2.0

    assert float(
        sales_order_items[0].unit_price
    ) == 35000.0

    assert float(
        sales_order_items[0].total
    ) == 70000.0

    assert sales_order_items[1].product_name == (
        "Maize Flour 50kg"
    )

    assert float(
        sales_order_items[1].quantity
    ) == 1.0

    assert float(
        sales_order_items[1].unit_price
    ) == 60000.0

    assert float(
        sales_order_items[1].total
    ) == 60000.0

    # --------------------------------------------------------
    # VERIFY QUOTATION STATUS
    # --------------------------------------------------------

    db.refresh(quotation)

    assert quotation.status == "Converted"

    # --------------------------------------------------------
    # VERIFY EXACTLY ONE SALES ORDER EXISTS
    # --------------------------------------------------------

    sales_orders = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.quotation_id
            == quotation.id
        )
        .all()
    )

    assert len(sales_orders) == 1

    # --------------------------------------------------------
    # VERIFY EXACTLY THREE SALES ORDER ITEMS EXIST
    # --------------------------------------------------------

    all_converted_items = (
        db.query(SalesOrderItem)
        .join(
            SalesOrder,
            SalesOrder.id
            == SalesOrderItem.sales_order_id,
        )
        .filter(
            SalesOrder.quotation_id
            == quotation.id
        )
        .all()
    )

    assert len(all_converted_items) == 3


# ============================================================
# DUPLICATION PROTECTION TEST
# ============================================================

def test_converted_quotation_cannot_be_converted_twice(
    db,
):
    """
    Once a quotation is Converted, a second conversion
    must not create another SalesOrder.
    """

    customer = Customer(
        name="Conversion Test Customer",
        customer_type="Wholesale",
        active=True,
    )

    product = Product(
        name="Test Maize Flour",
        sku="TEST-MF-001",
        category="Finished Product",
        product_type="Finished Product",
        unit="Bag",
        quantity=100,
        cost_price=20000,
        selling_price=30000,
        minimum_stock=10,
        active=True,
    )

    db.add_all(
        [
            customer,
            product,
        ]
    )

    db.flush()

    quotation = Quotation(
        quotation_number="Q-00002",
        customer_id=customer.id,
        quotation_date=date.today(),
        status="Draft",
        total_amount=30000,
    )

    db.add(quotation)
    db.flush()

    item = QuotationItem(
        quotation_id=quotation.id,
        product_id=product.id,
        product_name=product.name,
        quantity=1,
        unit_price=30000,
        total=30000,
    )

    db.add(item)

    db.commit()

    # First conversion must succeed.
    first_order = convert_quotation_to_sales_order(
        db,
        quotation.id,
    )

    assert first_order is not None

    assert quotation.status == "Converted"

    # Second conversion must fail safely.
    with pytest.raises(
        (ValueError, RuntimeError)
    ):
        convert_quotation_to_sales_order(
            db,
            quotation.id,
        )

    # Only one SalesOrder should exist.
    orders = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.quotation_id
            == quotation.id
        )
        .all()
    )

    assert len(orders) == 1

    # Only one SalesOrderItem should exist.
    items = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == first_order.id
        )
        .all()
    )

    assert len(items) == 1