"""
Sales Orders Module
Nile Harvest Foods Ltd.
Esan ERP

Sales Order Workflow:
Quotation → Sales Order → Approval → Stock Reservation → Delivery → Invoice → Payment
"""

import streamlit as st
import pandas as pd


from services.sales_service import (
    get_all_sales_orders,
    create_sales_order,
    update_order_status,
    get_all_customers
)


# Optional service connections

try:
    from services.inventory_service import reserve_stock
except Exception:
    reserve_stock = None


try:
    from services.delivery_service import create_delivery
except Exception:
    create_delivery = None


try:
    from services.invoice_service import create_invoice
except Exception:
    create_invoice = None


try:
    from services.payment_service import get_payment_status
except Exception:
    get_payment_status = None



# =====================================
# MAIN PAGE
# =====================================

def sales_orders_page():

    st.title("🚚 Sales Order Management")


    orders = get_all_sales_orders()


    # KPI SECTION

    total_orders = len(orders)

    pending = len(
        [
            o for o in orders
            if o.status in ["Pending", "Draft"]
        ]
    )


    completed = len(
        [
            o for o in orders
            if o.status == "Delivered"
        ]
    )


    revenue = sum(
        o.total_amount or 0
        for o in orders
    )


    col1, col2, col3, col4 = st.columns(4)


    col1.metric(
        "📋 Total Orders",
        total_orders
    )


    col2.metric(
        "⏳ Pending",
        pending
    )


    col3.metric(
        "🚚 Delivered",
        completed
    )


    col4.metric(
        "💰 Sales Value",
        f"UGX {revenue:,.0f}"
    )


    st.divider()


    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "➕ Create Order",
            "📋 Orders",
            "✅ Approval",
            "🔄 Workflow"
        ]
    )


    with tab1:
        create_order()


    with tab2:
        view_orders()


    with tab3:
        approve_orders()


    with tab4:
        order_workflow()



# =====================================
# CREATE ORDER
# =====================================

def create_order():


    st.subheader(
        "Create Sales Order"
    )


    customers = get_all_customers()


    if not customers:

        st.warning(
            "No customers available. Create customers first."
        )

        return



    customer_map = {
        c.name: c.id
        for c in customers
    }



    customer = st.selectbox(
        "Customer",
        list(customer_map.keys())
    )


    if "order_items" not in st.session_state:

        st.session_state.order_items = []



    st.markdown(
        "### Order Items"
    )


    with st.form(
        "item_form"
    ):


        col1, col2, col3 = st.columns(3)


        product = col1.text_input(
            "Product"
        )


        quantity = col2.number_input(
            "Quantity",
            min_value=0.0
        )


        price = col3.number_input(
            "Unit Price",
            min_value=0.0
        )



        add = st.form_submit_button(
            "Add Item"
        )



        if add:

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
            i["quantity"] * i["unit_price"]
            for i in st.session_state.order_items
        )


        st.info(
            f"Order Total: UGX {total:,.0f}"
        )



        if st.button(
            "Create Sales Order",
            type="primary"
        ):


            try:

                order = create_sales_order(
                    customer_map[customer],
                    st.session_state.order_items,
                    "Pending"
                )


                st.success(
                    f"Created Order {order.order_number}"
                )


                st.session_state.order_items = []


                st.rerun()


            except Exception as e:

                st.error(
                    str(e)
                )




# =====================================
# VIEW ORDERS
# =====================================

def view_orders():


    st.subheader(
        "Sales Orders"
    )


    orders = get_all_sales_orders()



    if not orders:

        st.info(
            "No sales orders found."
        )

        return



    rows = []


    for order in orders:

        rows.append(
            {
                "Order": order.order_number,
                "Customer": order.customer_id,
                "Status": order.status,
                "Amount": order.total_amount,
                "Date": order.created_at.strftime("%Y-%m-%d")
            }
        )



    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True
    )





# =====================================
# APPROVAL
# =====================================

def approve_orders():


    st.subheader(
        "Approve Sales Orders"
    )


    orders = get_all_sales_orders()


    pending_orders = [
        o for o in orders
        if o.status == "Pending"
    ]


    if not pending_orders:

        st.info(
            "No pending approvals."
        )

        return



    order_map = {
        o.order_number:o.id
        for o in pending_orders
    }



    selected = st.selectbox(
        "Select Order",
        list(order_map.keys())
    )



    if st.button(
        "Approve Order"
    ):


        update_order_status(
            order_map[selected],
            "Approved"
        )


        st.success(
            "Order approved"
        )


        st.rerun()




# =====================================
# WORKFLOW
# =====================================

def order_workflow():


    st.subheader(
        "Order Processing Workflow"
    )


    orders = get_all_sales_orders()



    if not orders:

        st.info(
            "No orders available."
        )

        return



    selected = st.selectbox(
        "Order",
        [
            o.order_number
            for o in orders
        ]
    )



    order = next(
        o for o in orders
        if o.order_number == selected
    )



    st.write(
        f"Current Status: **{order.status}**"
    )



    col1, col2, col3 = st.columns(3)



    with col1:

        if st.button(
            "📦 Reserve Stock"
        ):


            if reserve_stock:

                reserve_stock(order.id)

                st.success(
                    "Stock reserved"
                )

            else:

                st.warning(
                    "Inventory service not connected yet."
                )



    with col2:

        if st.button(
        if st.button(
    "🚚 Create Delivery"
):

    if create_delivery:

        destination = st.text_input(
            "Delivery Destination",
            key=f"destination_{order.id}"
        )

        driver = st.text_input(
            "Driver Name",
            key=f"driver_{order.id}"
        )

        vehicle = st.text_input(
            "Vehicle Number",
            key=f"vehicle_{order.id}"
        )


        if st.button(
            "Confirm Delivery",
            key=f"confirm_delivery_{order.id}"
        ):

            try:

                delivery = create_delivery(
                    order.id,
                    destination,
                    driver,
                    vehicle
                )


                st.success(
                    f"Delivery {delivery.delivery_number} created"
                )


                st.rerun()


            except Exception as e:

                st.error(
                    f"Delivery error: {e}"
                )

    else:

        st.warning(
            "Delivery service not connected."
)

            else:

                st.warning(
                    "Delivery service not connected."
                )



    with col3:

        if st.button(
            "🧾 Generate Invoice"
        ):


            if create_invoice:

                create_invoice(order.id)

                st.success(
                    "Invoice generated"
                )

            else:

                st.warning(
                    "Invoice service not connected."
                )
