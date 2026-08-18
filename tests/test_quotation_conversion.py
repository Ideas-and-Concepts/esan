"""
Regression test for quotation -> Sales Order conversion.

Verifies:
1. Every quotation item produces exactly one SalesOrderItem.
2. No duplicate SalesOrderItem records are created.
3. The quotation is marked as Converted.
4. The generated Sales Order has the expected item count.
"""

from datetime import date

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


def test_convert_quotation_creates_exactly_one_sales_order_item_per_quotation_item():
    """
    Regression test for duplicate SalesOrderItem creation.
    """

    # ------------------------------------------------------
    # In-memory test database
    # ------------------------------------------------------

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
    )

    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )

    db = TestingSessionLocal()

    try:

        # --------------------------------------------------
        # Create customer
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Create products
        # --------------------------------------------------

        product_1 = Product(
            name="Maize Flour 10Kg",
            sku="TEST-MF-10",
            category="Finished Product",
            product_type="Finished Product",
            unit="Bag",
            quantity=100,
            cost_price=25000,
            selling_price=30000,
            minimum_stock=10,
            active=True,
        )

        product_2 = Product(
            name="Cassava Flour 10Kg",
            sku="TEST-CF-10",
            category="Finished Product",
            product_type="Finished Product",
            unit="Bag",
            quantity=100,
            cost_price=22000,
            selling_price=28000,
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

        # --------------------------------------------------
        # Create quotation
        # --------------------------------------------------

        quotation = Quotation(
            quotation_number="Q-TEST-00001",
            customer_id=customer.id,
            quotation_date=date.today(),
            valid_until=date.today(),
            status="Draft",
            total_amount=0.0,
            notes="Regression test quotation",
        )

        db.add(quotation)
        db.flush()

        # --------------------------------------------------
        # Create quotation items
        # --------------------------------------------------

        quotation_item_1 = QuotationItem(
            quotation_id=quotation.id,
            product_id=product_1.id,
            product_name=product_1.name,
            quantity=5,
            unit_price=30000,
            total=150000,
        )

        quotation_item_2 = QuotationItem(
            quotation_id=quotation.id,
            product_id=product_2.id,
            product_name=product_2.name,
            quantity=3,
            unit_price=28000,
            total=84000,
        )

        db.add_all(
            [
                quotation_item_1,
                quotation_item_2,
            ]
        )

        db.commit()

        # --------------------------------------------------
        # Confirm source quotation has exactly two items
        # --------------------------------------------------

        quotation_items = (
            db.query(QuotationItem)
            .filter(
                QuotationItem.quotation_id
                == quotation.id
            )
            .all()
        )

        assert len(quotation_items) == 2

        # --------------------------------------------------
        # Convert quotation
        # --------------------------------------------------

        sales_order = convert_quotation_to_sales_order(
            db,
            quotation.id,
        )

        # --------------------------------------------------
        # Verify Sales Order was created
        # --------------------------------------------------

        assert sales_order is not None
        assert sales_order.id is not None

        assert sales_order.order_number.startswith(
            "SO-"
        )

        assert sales_order.customer_id == customer.id
        assert sales_order.quotation_id == quotation.id

        # --------------------------------------------------
        # Verify exactly one SalesOrderItem per
        # quotation item
        # --------------------------------------------------

        sales_order_items = (
            db.query(SalesOrderItem)
            .filter(
                SalesOrderItem.sales_order_id
                == sales_order.id
            )
            .all()
        )

        assert len(sales_order_items) == len(
            quotation_items
        )

        assert len(sales_order_items) == 2

        # --------------------------------------------------
        # Verify there are no duplicate products
        # --------------------------------------------------

        product_ids = [
            item.product_id
            for item in sales_order_items
        ]

        assert product_ids.count(product_1.id) == 1
        assert product_ids.count(product_2.id) == 1

        # --------------------------------------------------
        # Verify copied quantities and prices
        # --------------------------------------------------

        item_by_product = {
            item.product_id: item
            for item in sales_order_items
        }

        order_item_1 = item_by_product[
            product_1.id
        ]

        assert order_item_1.product_name == product_1.name
        assert order_item_1.quantity == 5
        assert order_item_1.unit_price == 30000
        assert order_item_1.total == 150000

        order_item_2 = item_by_product[
            product_2.id
        ]

        assert order_item_2.product_name == product_2.name
        assert order_item_2.quantity == 3
        assert order_item_2.unit_price == 28000
        assert order_item_2.total == 84000

        # --------------------------------------------------
        # Verify quotation status
        # --------------------------------------------------

        db.refresh(quotation)

        assert quotation.status == "Converted"

        # --------------------------------------------------
        # Verify only one SalesOrder exists for this
        # quotation
        # --------------------------------------------------

        sales_orders = (
            db.query(SalesOrder)
            .filter(
                SalesOrder.quotation_id
                == quotation.id
            )
            .all()
        )

        assert len(sales_orders) == 1

    finally:

        db.close()
        Base.metadata.drop_all(engine)