"""
Esan ERP
Sales Orders Module
Nile Harvest Foods Ltd.
"""

import streamlit as st

from database import SessionLocal

from models import (
    Customer,
    SalesOrder
)



def sales_orders_page():


    st.header(
        "📋 Sales Orders"
    )


    db = SessionLocal()



    # =====================================
    # CREATE SALES ORDER
    # =====================================

    st.subheader(
        "➕ Create New Sales Order"
    )


    customers = (

        db.query(Customer)

        .order_by(
            Customer.name
        )

        .all()

    )


    if not customers:

        st.warning(
            "Please add customers first."
        )

        db.close()

        return



    customer_list = {

        customer.name: customer.id

        for customer in customers

    }


    with st.form(
        "sales_order_form"
    ):


        customer_name = st.selectbox(

            "Customer",

            list(customer_list.keys())

        )


        product = st.selectbox(

            "Product",

            [

                "Maize Flour 5kg",

                "Maize Flour 10kg",

                "Maize Flour 25kg",

                "Cassava Flour"

            ]

        )


        quantity = st.number_input(

            "Quantity (Bags)",

            min_value=1.0,

            step=1.0

        )


        unit_price = st.number_input(

            "Unit Price (UGX)",

            min_value=0.0,

            step=1000.0

        )


        status = st.selectbox(

            "Order Status",

            [

                "Pending",

                "Approved",

                "Processing",

                "Completed",

                "Cancelled"

            ]

        )


        submit = st.form_submit_button(

            "💾 Save Order"

        )


        if submit:


            total = quantity * unit_price


            order = SalesOrder(

                customer_id=

                customer_list[customer_name],

                product=product,

                quantity=quantity,

                unit_price=unit_price,

                total_amount=total,

                status=status

            )


            db.add(order)

            db.commit()


            st.success(

                "Sales order created successfully."

            )


            st.rerun()



    st.divider()



    # =====================================
    # ORDER LIST
    # =====================================


    st.subheader(

        "📦 Existing Orders"

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


            customer = (

                db.query(Customer)

                .filter(

                    Customer.id == order.customer_id

                )

                .first()

            )


            with st.expander(

                f"Order #{order.id} | {customer.name}"

            ):


                st.write(

                    f"""
                    **Product:** {order.product}

                    **Quantity:** {order.quantity} bags

                    **Unit Price:** UGX {order.unit_price:,.0f}

                    **Total:** UGX {order.total_amount:,.0f}

                    **Status:** {order.status}
                    """

                )


    else:

        st.info(

            "No sales orders available."

        )


    db.close()