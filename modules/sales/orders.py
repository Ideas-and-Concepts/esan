"""
Esan ERP Sales Orders Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging ERP

Handles:
- Create Sales Orders
- View Orders
- Update Order Status
- Create Delivery from Order
"""

import streamlit as st
import pandas as pd

from services.sales_service import (
    get_all_sales_orders,
    create_sales_order,
    update_order_status,
    get_all_customers
)

from services.delivery_service import (
    create_delivery
)



# ==================================================
# MAIN PAGE
# ==================================================

def sales_orders_page():

    st.title("📋 Sales Orders")


    tabs = st.tabs(
        [
            "Create Order",
            "View Orders",
            "Order Workflow"
        ]
    )


    with tabs[0]:

        create_order()



    with tabs[1]:

        view_orders()



    with tabs[2]:

        order_workflow()



# ==================================================
# CREATE ORDER
# ==================================================

def create_order():

    st.subheader(
        "Create New Sales Order"
    )


    customers = get_all_customers()


    if not customers:

        st.warning(
            "No customers available."
        )

        return



    customer_map = {

        c.name: c.id

        for c in customers

    }


    selected_customer = st.selectbox(

        "Customer",

        list(customer_map.keys())

    )


    status = st.selectbox(

        "Initial Status",

        [
            "Pending",
            "Confirmed",
            "Processing"
        ]

    )


    if "order_items" not in st.session_state:

        st.session_state.order_items = []



    st.markdown(
        "### Order Items"
    )


    with st.form(
        "order_item_form"
    ):


        col1, col2, col3 = st.columns(3)


        product = col1.text_input(
            "Product"
        )


        quantity = col2.number_input(
            "Quantity",
            min_value=0.0,
            step=1.0
        )


        price = col3.number_input(
            "Unit Price",
            min_value=0.0,
            step=100.0
        )



        add_item = st.form_submit_button(
            "Add Item"
        )


        if add_item:

            if product and quantity > 0:

                st.session_state.order_items.append(

                    {
                        "product_name": product,
                        "quantity": quantity,
                        "unit_price": price
                    }

                )


                st.success(
                    "Item added"
                )



    if st.session_state.order_items:


        df = pd.DataFrame(
            st.session_state.order_items
        )


        st.dataframe(
            df,
            use_container_width=True
        )


        total = sum(

            item["quantity"] *
            item["unit_price"]

            for item in
            st.session_state.order_items

        )


        st.metric(
            "Order Total",
            f"{total:,.2f}"
        )



        if st.button(
            "Clear Items"
        ):

            st.session_state.order_items = []

            st.rerun()



    if st.button(
        "Create Sales Order",
        type="primary"
    ):


        if not st.session_state.order_items:

            st.error(
                "Add at least one item"
            )

            return



        try:


            order = create_sales_order(

                customer_map[selected_customer],

                st.session_state.order_items,

                status

            )


            st.success(

                f"Order {order.order_number} created"

            )


            st.session_state.order_items = []


            st.rerun()



        except Exception as e:


            st.error(
                f"Order creation failed: {e}"
            )



# ==================================================
# VIEW ORDERS
# ==================================================

def view_orders():


    st.subheader(
        "Sales Orders"
    )


    orders = get_all_sales_orders()



    if not orders:

        st.info(
            "No sales orders found"
        )

        return



    data=[]


    for order in orders:


        data.append(

            {

                "Order Number":
                    order.order_number,

                "Customer ID":
                    order.customer_id,

                "Status":
                    order.status,

                "Amount":
                    order.total_amount,

                "Date":
                    order.created_at.strftime(
                        "%Y-%m-%d"
                    )

            }

        )


    st.dataframe(

        pd.DataFrame(data),

        use_container_width=True

    )



# ==================================================
# ORDER WORKFLOW
# ==================================================

def order_workflow():


    st.subheader(
        "🚚 Order Fulfillment Workflow"
    )


    orders = get_all_sales_orders()



    if not orders:


        st.info(
            "No orders available"
        )

        return



    order_map = {

        o.order_number:o

        for o in orders

    }



    selected = st.selectbox(

        "Select Order",

        list(order_map.keys())

    )


    order = order_map[selected]



    st.write(
        f"Customer ID: {order.customer_id}"
    )


    st.write(
        f"Current Status: {order.status}"
    )



    st.divider()



    new_status = st.selectbox(

        "Update Status",

        [
            "Pending",
            "Confirmed",
            "Processing",
            "Ready",
            "Dispatched",
            "Delivered",
            "Cancelled"
        ]

    )



    if st.button(
        "Update Order Status"
    ):


        update_order_status(

            order.id,

            new_status

        )


        st.success(
            "Order status updated"
        )


        st.rerun()



    st.divider()



    st.subheader(
        "Create Delivery"
    )



    destination = st.text_input(

        "Destination"

    )


    driver = st.text_input(

        "Driver"

    )


    vehicle = st.text_input(

        "Vehicle"

    )



    if st.button(
        "Create Delivery",
        type="primary"
    ):



        if not destination:


            st.error(
                "Destination is required"
            )

            return



        try:


            delivery = create_delivery(

                order_id=order.id,

                destination=destination,

                driver=driver,

                vehicle=vehicle

            )



            st.success(

                f"Delivery {delivery.delivery_number} created"

            )


            st.rerun()



        except Exception as e:


            st.error(

                f"Delivery failed: {e}"

            )