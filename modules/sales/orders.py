l"""
Sales Orders Module – uses sales_service
"""

import streamlit as st
import pandas as pd
from services.sales_service import (
    get_all_sales_orders,
    create_sales_order,
    update_order_status,
    get_all_customers
)

def sales_orders_page():
    st.title("📋 Sales Orders")
    tab1, tab2, tab3 = st.tabs(["Create Order", "View Orders", "Update Status"])
    with tab1:
        create_order()
    with tab2:
        view_orders()
    with tab3:
        update_status()

def create_order():
    st.subheader("New Sales Order")
    customers = get_all_customers()
    if not customers:
        st.warning("No customers available.")
        return
    customer_options = {c.name: c.id for c in customers}
    selected_customer = st.selectbox("Customer", list(customer_options.keys()))
    status = st.selectbox("Status", ["Pending", "Confirmed", "Processing"])

    # dynamic items
    st.markdown("### Order Items")
    if 'order_items' not in st.session_state:
        st.session_state.order_items = []
    with st.form("add_item", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        product_name = col1.text_input("Product")
        quantity = col2.number_input("Quantity", min_value=0.0, step=1.0)
        unit_price = col3.number_input("Unit Price", min_value=0.0, step=0.01)
        if st.form_submit_button("Add Item"):
            if product_name and quantity > 0 and unit_price > 0:
                st.session_state.order_items.append({
                    'product_name': product_name,
                    'quantity': quantity,
                    'unit_price': unit_price
                })
                st.success("Item added")

    if st.session_state.order_items:
        df = pd.DataFrame(st.session_state.order_items)
        st.dataframe(df, use_container_width=True)
        total = sum(it['quantity']*it['unit_price'] for it in st.session_state.order_items)
        st.markdown(f"**Total:** ${total:,.2f}")
        if st.button("Clear Items"):
            st.session_state.order_items = []
            st.rerun()

    if st.button("Create Order", type="primary"):
        if not st.session_state.order_items:
            st.error("Add at least one item.")
            return
        try:
            order = create_sales_order(customer_options[selected_customer], st.session_state.order_items, status)
            st.success(f"Order {order.order_number} created!")
            st.session_state.order_items = []
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

def view_orders():
    orders = get_all_sales_orders()
    if orders:
        data = []
        for o in orders:
            data.append({
                'Order #': o.order_number,
                'Customer ID': o.customer_id,
                'Status': o.status,
                'Total': f"${o.total_amount:,.2f}",
                'Date': o.created_at.strftime('%Y-%m-%d')
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No orders.")

def update_status():
    orders = get_all_sales_orders()
    if orders:
        order_nums = [o.order_number for o in orders]
        selected = st.selectbox("Order", order_nums)
        new_status = st.selectbox("New Status", ["Pending", "Confirmed", "Processing", "Dispatched", "Delivered", "Cancelled"])
        if st.button("Update"):
            order_id = next(o.id for o in orders if o.order_number == selected)
            update_order_status(order_id, new_status)
            st.success("Status updated")
            st.rerun()
    else:
        st.info("No orders.")
