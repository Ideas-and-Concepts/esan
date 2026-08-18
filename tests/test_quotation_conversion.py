import pytest

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
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


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(
        engine
    )

    Session = sessionmaker(
        bind=engine
    )

    session = Session()

    try:
        yield session
    finally:
        session.close()

        Base.metadata.drop_all(
            engine
        )

        engine.dispose()


def create_test_quotation(db):
    customer = Customer(
        name="Test Customer",
        phone="0700000000",
    )

    product_one = Product(
        name="Maize Flour",
        sku="TEST-MAIZE",
        category="Flour",
        unit="Kg",
        quantity=1000,
        selling_price=2500,
    )

    product_two = Product(
        name="Cassava Flour",
        sku="TEST-CASSAVA",
        category="Flour",
        unit="Kg",
        quantity=1000,
        selling_price=3000,
    )

    db.add_all(
        [
            customer,
            product_one,
            product_two,
        ]
    )

    db.flush()

    quotation = Quotation(
        quotation_number="Q-00001",
        customer_id=customer.id,
        status="Draft",
        total_amount=0,
    )

    db.add(quotation)

    db.flush()

    item_one = QuotationItem(
        quotation_id=quotation.id,
        product_id=product_one.id,
        product_name=product_one.name,
        quantity=10,
        unit_price=2500,
        total=25000,
    )

    item_two = QuotationItem(
        quotation_id=quotation.id,
        product_id=product_two.id,
        product_name=product_two.name,
        quantity=20,
        unit_price=3000,
        total=60000,
    )

    db.add_all(
        [
            item_one,
            item_two,
        ]
    )

    db.commit()

    return quotation.id


def test_conversion_creates_exactly_one_sales_order_item_per_quotation_item(
    db,
):
    quotation_id = create_test_quotation(
        db
    )

    quotation_items_before = (
        db.query(QuotationItem)
        .filter(
            QuotationItem.quotation_id
            == quotation_id
        )
        .count()
    )

    assert quotation_items_before == 2

    sales_order = (
        convert_quotation_to_sales_order(
            db,
            quotation_id,
        )
    )

    db.expire_all()

    quotation = (
        db.query(Quotation)
        .filter(
            Quotation.id == quotation_id
        )
        .one()
    )

    sales_order_items = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == sales_order.id
        )
        .all()
    )

    assert sales_order.id is not None

    assert (
        sales_order.order_number
        == f"SO-{sales_order.id:05d}"
    )

    assert quotation.status == "Converted"

    assert (
        len(sales_order_items)
        == quotation_items_before
    )


def test_converting_same_quotation_twice_does_not_create_duplicate_order(
    db,
):
    quotation_id = create_test_quotation(
        db
    )

    first_order = (
        convert_quotation_to_sales_order(
            db,
            quotation_id,
        )
    )

    first_item_count = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == first_order.id
        )
        .count()
    )

    assert first_item_count == 2

    with pytest.raises(
        ValueError,
        match="already been converted",
    ):
        convert_quotation_to_sales_order(
            db,
            quotation_id,
        )

    total_orders = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.quotation_id
            == quotation_id
        )
        .count()
    )

    total_items = (
        db.query(SalesOrderItem)
        .join(
            SalesOrder,
            SalesOrder.id
            == SalesOrderItem.sales_order_id,
        )
        .filter(
            SalesOrder.quotation_id
            == quotation_id
        )
        .count()
    )

    quotation = (
        db.query(Quotation)
        .filter(
            Quotation.id
            == quotation_id
        )
        .one()
    )

    assert total_orders == 1

    assert total_items == 2

    assert quotation.status == "Converted"