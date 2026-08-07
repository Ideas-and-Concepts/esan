"""
Esan ERP Sales Service
Nile Harvest Foods Ltd.

Handles:
- Customers
- Sales Orders
- Sales Order Items
- Order Status Updates
"""

from datetime import datetime

from database import SessionLocal

from models import (
    Customer,
    SalesOrder,
    SalesOrderItem
)



# =====================================
# CUSTOMERS
# =====================================

def get_all_customers():

    db = SessionLocal()

    try:

        return db.query(Customer).all()

    finally:

        db.close()



# =====================================
# SALES ORDERS
# =====================================

def get_all_sales_orders():

    db = SessionLocal()

    try:

        return (
            db.query(SalesOrder)
            .order_by(
                SalesOrder.created_at.desc()
            )
            .all()
        )

    finally:

        db.close()



def create_sales_order(
        customer_id,
        items,
        status="Pending"
):

    db = SessionLocal()


    try:

        order_number = (
            "SO-"
            +
            datetime.now()
            .strftime("%Y%m%d%H%M%S")
        )


        total_amount = sum(
            item["quantity"] *
            item["unit_price"]
            for item in items
        )


        order = SalesOrder(

            order_number=order_number,

            customer_id=customer_id,

            status=status,

            total_amount=total_amount

        )


        db.add(order)

        db.flush()



        for item in items:


            order_item = SalesOrderItem(

                order_id=order.id,

                product_name=item["product_name"],

                quantity=item["quantity"],

                unit_price=item["unit_price"],

                total=
                item["quantity"]
                *
                item["unit_price"]

            )


            db.add(order_item)



        db.commit()

        db.refresh(order)


        return order



    except Exception:

        db.rollback()

        raise


    finally:

        db.close()




# =====================================
# UPDATE STATUS
# =====================================

def update_order_status(
        order_id,
        new_status
):

    db = SessionLocal()


    try:

        order = (
            db.query(SalesOrder)
            .filter(
                SalesOrder.id == order_id
            )
            .first()
        )


        if not order:

            return None



        order.status = new_status


        db.commit()

        db.refresh(order)


        return order



    finally:

        db.close()




# =====================================
# GET SINGLE ORDER
# =====================================

def get_sales_order(order_id):

    db = SessionLocal()

    try:

        return (
            db.query(SalesOrder)
            .filter(
                SalesOrder.id == order_id
            )
            .first()
        )

    finally:

        db.close()