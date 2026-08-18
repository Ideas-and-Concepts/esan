# tests/test_quotation_conversion.py

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import (
    Base,
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
    Regression test for quotation -> sales order conversion.

    Verifies:

    1. A quotation containing N items creates exactly N SalesOrderItems.
    2. Each SalesOrderItem belongs to the newly created SalesOrder.
    3. Product, quantity and price are copied correctly.
    4. The quotation status becomes Converted.
    """

    # ------------------------------------------------------
    # TEST DATABASE
    # ------------------------------------------------------

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )

    Base.metadata.create_all(engine)

    db = TestingSessionLocal()

    try:

        # --------------------------------------------------
        # CUSTOMER
        # --------------------------------------------------

        customer = Customer(
            name="Test Customer",
            phone="0700000000",
            email="test@example.com",
        )

        db.add(customer)
        db.flush()

        # --------------------------------------------------
        # PRODUCTS
        # --------------------------------------------------

        product_1 = Product(
            name="Maize Flour 1kg",
            category="Flour",
            unit="Bag",
            quantity=100,
            cost_price=3000,
            selling_price=5000,
        )

        product_2 = Product(
            name="Cassava Flour 1kg",
            category="Flour",
            unit="Bag",
            quantity=100,
            cost_price=2500,
            selling_price=4500,
        )

        db.add_all(
            [
                product_1,
                product_2,
            ]
        )

        db.flush()

        # --------------------------------------------------
        # QUOTATION
        # --------------------------------------------------

        quotation = Quotation(
            quotation_number="Q-00001",
            customer_id=customer.id,
            quotation_date=date.today(),
            valid_until=date.today(),
            status="Draft",
            total_amount=0,
            notes="Conversion test",
        )

        db.add(quotation)
        db.flush()

        # --------------------------------------------------
        # QUOTATION ITEMS
        # --------------------------------------------------

        quotation_item_1 = QuotationItem(
            quotation_id=quotation.id,
            product_id=product_1.id,
            product_name=product_1.name,
            quantity=10,
            unit_price=5000,
            total=50000,
        )

        quotation_item_2 = QuotationItem(
            quotation_id=quotation.id,
            product_id=product_2.id,
            product_name=product_2.name,
            quantity=20,
            unit_price=4500,
            total=90000,
        )

        db.add_all(
            [
                quotation_item_1,
                quotation_item_2,
            ]
        )

        db.commit()

        # --------------------------------------------------
        # CONVERT
        # --------------------------------------------------

        sales_order = convert_quotation_to_sales_order(
            db,
            quotation.id,
        )

        # --------------------------------------------------
        # VERIFY SALES ORDER
        # --------------------------------------------------

        assert sales_order is not None
        assert sales_order.id is not None

        assert sales_order.order_number == (
            f"SO-{sales_order.id:05d}"
        )

        assert sales_order.customer_id == customer.id

        assert sales_order.quotation_id == quotation.id

        # --------------------------------------------------
        # VERIFY QUOTATION STATUS
        # --------------------------------------------------

        db.refresh(quotation)

        assert quotation.status == "Converted"

        # --------------------------------------------------
        # VERIFY EXACT ITEM COUNT
        # --------------------------------------------------

        source_items = (
            db.query(QuotationItem)
            .filter(
                QuotationItem.quotation_id
                == quotation.id
            )
            .all()
        )

        sales_order_items = (
            db.query(SalesOrderItem)
            .filter(
                SalesOrderItem.sales_order_id
                == sales_order.id
            )
            .all()
        )

        assert len(source_items) == 2

        # Critical regression assertion:
        assert len(sales_order_items) == len(
            source_items
        )

        assert len(sales_order_items) == 2

        # --------------------------------------------------
        # VERIFY EACH ITEM
        # --------------------------------------------------

        items_by_product = {
            item.product_id: item
            for item in sales_order_items
        }

        converted_item_1 = items_by_product[
            product_1.id
        ]

        converted_item_2 = items_by_product[
            product_2.id
        ]

        assert converted_item_1.product_name == (
            product_1.name
        )

        assert converted_item_1.quantity == 10

        assert converted_item_1.unit_price == 5000

        assert converted_item_1.total == 50000

        assert converted_item_2.product_name == (
            product_2.name
        )

        assert converted_item_2.quantity == 20

        assert converted_item_2.unit_price == 4500

        assert converted_item_2.total == 90000

        # --------------------------------------------------
        # VERIFY NO DUPLICATE ITEMS
        # --------------------------------------------------

        product_ids = [
            item.product_id
            for item in sales_order_items
        ]

        assert len(product_ids) == len(
            set(product_ids)
        )

    finally:

        db.close()
        Base.metadata.drop_all(engine)