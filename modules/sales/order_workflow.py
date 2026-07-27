"""
Esan ERP Sales Order Workflow
"""


import streamlit as st

from database import SessionLocal

from models import (
    SalesOrder,
    Product,
    StockReservation,
    Delivery,
    Invoice,
    Payment,
    FinanceTransaction
)



def approve_order(order_id):


    db = SessionLocal()


    try:


        order = (

            db.query(SalesOrder)

            .filter(
                SalesOrder.id == order_id
            )

            .first()

        )


        if order:

            order.status = "Approved"

            db.commit()


    finally:

        db.close()




def reserve_stock(order_id):


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

            return False



        for item in order.items:


            product = (

                db.query(Product)

                .filter(
                    Product.name ==
                    item.product_name
                )

                .first()

            )


            if product and product.quantity >= item.quantity:


                product.quantity -= item.quantity



                reservation = StockReservation(

                    sales_order_id=order.id,

                    product_id=product.id,

                    quantity=item.quantity,

                    status="Reserved"

                )


                db.add(reservation)



            else:

                st.error(
                    f"Insufficient stock for {item.product_name}"
                )

                return False



        order.status = "Stock Reserved"


        db.commit()


        return True



    finally:

        db.close()