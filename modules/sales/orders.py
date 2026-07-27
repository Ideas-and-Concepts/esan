"""
Esan ERP Sales Order Management
Nile Harvest Foods Ltd.
Version 1.2.0 Alpha
"""


import streamlit as st
from datetime import datetime

from database import SessionLocal
from models import SalesOrder



def sales_orders_page():

    st.header(
        "🧾 Sales Orders"
    )


    db = SessionLocal()


    try:

        st.subheader(
            "Create Sales Order"
        )


        customer = st.text_input(
            "Customer Name"
        )


        product = st.text_input(
            "Product"
        )


        quantity = st.number_input(
            "Quantity",
            min_value=1
        )


        price = st.number_input(
            "Unit Price",
            min_value=0.0
        )


        if st.button(
            "Create Order"
        ):


            total = quantity * price


            order = SalesOrder(

                customer_name=customer,

                product_name=product,

                quantity=quantity,

                unit_price=price,

                total_amount=total,

                status="Pending",

                created_at=datetime.utcnow()

            )


            db.add(order)

            db.commit()


            st.success(
                "Sales Order created successfully."
            )


        st.divider()


        st.subheader(
            "Sales Order Records"
        )


        orders = (
            db.query(SalesOrder)
            .order_by(
                SalesOrder.id.desc()
            )
            .all()
        )


        if orders:


            for order in orders:

                st.write(
                    f"""
                    **Order #{order.id}**

                    Customer: {order.customer_name}

                    Product: {order.product_name}

                    Quantity: {order.quantity}

                    Total: {order.total_amount}

                    Status: {order.status}

                    ---
                    """
                )


        else:

            st.info(
                "No sales orders available."
            )


    except Exception as e:

        st.error(
            "Sales Order module error"
        )

        st.exception(e)


    finally:

        db.close()