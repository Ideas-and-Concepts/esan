"""
Esan ERP
Quotation Total Regression Tests

Verifies:

1. Quotation.total_amount stores the quotation/header total.
2. QuotationItem.total stores each individual line total.
3. calculate_quotation_total() recalculates and persists both
   quotation and item totals consistently.
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
)
from services.quotation_service import (
    calculate_quotation_total,
)


# ============================================================
# ISOLATED DATABASE FIXTURE
# ============================================================

@pytest.fixture
def db():
    """
    Create an isolated in-memory SQLite database.

    StaticPool ensures every SQLAlchemy session operation uses
    the same SQLite connection, preventing the in-memory
    database from disappearing between operations.
    """

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )

    Base.metadata.create_all(engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


# ============================================================
# TEST DATA
# ============================================================

@pytest.fixture
def quotation_with_items(db):
    """
    Create one customer, two products, one quotation,
    and two quotation items.
    """

    customer = Customer(
        name="Test Customer",
        phone="0700000000",
        email="test@example.com",
    )

    product_1 = Product(
        name="Maize Flour 1kg",
        sku="TEST-MF-1KG",
        category="Finished Product",
        unit="Kg",
        quantity=1000.0,
        cost_price=2000.0,
        selling_price=3000.0,
    )

    product_2 = Product(
        name="Cassava Flour 1kg",
        sku="TEST-CF-1KG",
        category="Finished Product",
        unit="Kg",
        quantity=1000.0,
        cost_price=1500.0,
        selling_price=2500.0,
    )

    db.add_all(
        [
            customer,
            product_1,
            product_2,
        ]
    )

    db.flush()

    quotation = Quotation(
        quotation_number="Q-00001",
        customer_id=customer.id,
        status="Draft",
        total_amount=0.0,
    )

    db.add(quotation)
    db.flush()

    item_1 = QuotationItem(
        quotation_id=quotation.id,
        product_id=product_1.id,
        product_name=product_1.name,
        quantity=10.0,
        unit_price=3000.0,
        total=0.0,
    )

    item_2 = QuotationItem(
        quotation_id=quotation.id,
        product_id=product_2.id,
        product_name=product_2.name,
        quantity=5.0,
        unit_price=2500.0,
        total=0.0,
    )

    db.add_all(
        [
            item_1,
            item_2,
        ]
    )

    db.commit()

    db.refresh(quotation)
    db.refresh(item_1)
    db.refresh(item_2)

    return quotation, item_1, item_2


# ============================================================
# TEST 1
# ============================================================

def test_quotation_item_total_stores_line_total(
    db,
    quotation_with_items,
):
    """
    Each QuotationItem.total must contain its own
    quantity × unit_price value.
    """

    quotation, item_1, item_2 = quotation_with_items

    calculate_quotation_total(
        db,
        quotation.id,
    )

    db.refresh(item_1)
    db.refresh(item_2)

    assert item_1.total == pytest.approx(
        10.0 * 3000.0
    )

    assert item_2.total == pytest.approx(
        5.0 * 2500.0
    )


# ============================================================
# TEST 2
# ============================================================

def test_quotation_total_amount_stores_header_total(
    db,
    quotation_with_items,
):
    """
    Quotation.total_amount must equal the sum of all
    quotation item totals.
    """

    quotation, item_1, item_2 = quotation_with_items

    total = calculate_quotation_total(
        db,
        quotation.id,
    )

    db.refresh(quotation)

    expected_total = (
        (10.0 * 3000.0)
        + (5.0 * 2500.0)
    )

    assert total == pytest.approx(
        expected_total
    )

    assert quotation.total_amount == pytest.approx(
        expected_total
    )


# ============================================================
# TEST 3
# ============================================================

def test_calculate_quotation_total_updates_header_and_lines(
    db,
    quotation_with_items,
):
    """
    calculate_quotation_total() must update both:

        QuotationItem.total
        Quotation.total_amount
    """

    quotation, item_1, item_2 = quotation_with_items

    # Start with deliberately incorrect totals.
    item_1.total = 1.0
    item_2.total = 2.0
    quotation.total_amount = 3.0

    db.commit()

    calculated_total = calculate_quotation_total(
        db,
        quotation.id,
    )

    db.refresh(quotation)
    db.refresh(item_1)
    db.refresh(item_2)

    expected_item_1_total = (
        item_1.quantity
        * item_1.unit_price
    )

    expected_item_2_total = (
        item_2.quantity
        * item_2.unit_price
    )

    expected_header_total = (
        expected_item_1_total
        + expected_item_2_total
    )

    assert item_1.total == pytest.approx(
        expected_item_1_total
    )

    assert item_2.total == pytest.approx(
        expected_item_2_total
    )

    assert quotation.total_amount == pytest.approx(
        expected_header_total
    )

    assert calculated_total == pytest.approx(
        expected_header_total
    )


# ============================================================
# TEST 4
# ============================================================

def test_calculate_quotation_total_returns_persisted_header_total(
    db,
    quotation_with_items,
):
    """
    The function's return value must match the value persisted
    in Quotation.total_amount.
    """

    quotation, item_1, item_2 = quotation_with_items

    result = calculate_quotation_total(
        db,
        quotation.id,
    )

    db.refresh(quotation)

    assert result == pytest.approx(
        quotation.total_amount
    )


# ============================================================
# TEST 5
# ============================================================

def test_calculate_quotation_total_recalculates_after_quantity_change(
    db,
    quotation_with_items,
):
    """
    Changing an item's quantity and recalculating must update
    both that item's total and the quotation header total.
    """

    quotation, item_1, item_2 = quotation_with_items

    calculate_quotation_total(
        db,
        quotation.id,
    )

    # Change quantity after initial calculation.
    item_1.quantity = 20.0

    db.commit()

    calculate_quotation_total(
        db,
        quotation.id,
    )

    db.refresh(quotation)
    db.refresh(item_1)
    db.refresh(item_2)

    expected_item_1_total = (
        20.0 * 3000.0
    )

    expected_item_2_total = (
        5.0 * 2500.0
    )

    expected_header_total = (
        expected_item_1_total
        + expected_item_2_total
    )

    assert item_1.total == pytest.approx(
        expected_item_1_total
    )

    assert item_2.total == pytest.approx(
        expected_item_2_total
    )

    assert quotation.total_amount == pytest.approx(
        expected_header_total
    )