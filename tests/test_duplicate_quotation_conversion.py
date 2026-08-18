# tests/test_duplicate_quotation_conversion.py

import pytest

from models import (
    Customer,
    Product,
    Quotation,
    QuotationItem,
    SalesOrder,
    SalesOrderItem,
)

from services.quotation_service import (
    create_quotation,
    add_quotation_item,
    convert_quotation_to_sales_order,
)


def test_converting_same_quotation_twice_creates_no_duplicates(db):
    """
    A quotation may only be converted once.

    The second conversion must:
      1. raise ValueError
      2. create no second SalesOrder
      3. create no duplicate SalesOrderItems
      4. leave the quotation status as Converted
    """

    # ------------------------------------------------------
    # Arrange
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

    db.add(customer)
    db.add(product)
    db.commit()

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

    # ------------------------------------------------------
    # First conversion
    # ------------------------------------------------------

    sales_order = convert_quotation_to_sales_order(
        db=db,
        quotation_id=quotation.id,
    )

    db.expire_all()

    # ------------------------------------------------------
    # Verify first conversion
    # ------------------------------------------------------

    converted_quotation = (
        db.query(Quotation)
        .filter(Quotation.id == quotation.id)
        .one()
    )

    assert converted_quotation.status == "Converted"

    orders = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.quotation_id == quotation.id
        )
        .all()
    )

    assert len(orders) == 1
    assert orders[0].id == sales_order.id

    items = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.sales_order_id
            == sales_order.id
        )
        .all()
    )

    assert len(items) == 1

    # ------------------------------------------------------
    # Second conversion must fail
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
    # Verify no duplicates were created
    # ------------------------------------------------------

    db.expire_all()

    orders_after_second_attempt = (
        db.query(SalesOrder)
        .filter(
            SalesOrder.quotation_id == quotation.id
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
        .filter(Quotation.id == quotation.id)
        .one()
    )

    assert final_quotation.status == "Converted"