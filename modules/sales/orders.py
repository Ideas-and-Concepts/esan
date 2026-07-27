"""
Sales Orders Module
Nile Harvest Foods Ltd.
Esan ERP - Sales Order Management
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import SessionLocal
from models import SalesOrder, SalesOrderItem, Customer

def get_db():
    return SessionLocal()

def generate_order_number():
    db = get_db()
    count = db.query(SalesOrder).count()
    db.close()
    return f"SO-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"

def sales_orders_page():
    st.title("📋 Sales Orders")
    tab1, tab2, tab3 = st.tabs(["Create Order", "View Orders", "Order Details"])
    with tab1:
        create_sales_order()
    with tab2:
        view_sales_orders()
    with tab3:
        view_order_details()

def create_sales_order():
    st.subheader("Create New Sales Order")
    db = get_db()
    try:
        customers = db.query(Customer).all()
        if not customers:
            st.warning("No customers available.")
            return
        customer_options = {c.name: c.id for c in customers}
        col1, col2 = st.columns(2)
        with col1:
            selected_customer = st.selectbox("Customer", list(customer_options.keys()))
            order_date = st.date_input("Order Date", datetime.now().date())
        with col2:
            status = st.selectbox("Status", ["Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"])
            delivery_date = st.date_input("Expected Delivery Date", datetime.now().date())
        st.markdown("---")
        st.subheader("Order Items")
        if 'order_items' not in st.session_state:
            st.session_state.order_items = []
        with st.form("add_item_form", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                product_name = st.text_input("Product Name")
            with col2:
                quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
            with col3:
                unit_price = st.number_input("Unit Price", min_value=0.0, step=0.01)
            with col4:
                total = quantity * unit_price
                st.text(f"Total: {total:.2f}")
            if st.form_submit_button("Add Item"):
                if product_name and quantity > 0 and unit_price > 0:
                    st.session_state.order_items.append({
                        'product_name': product_name,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total': total
                    })
                    st.success("Item added!")
        if st.session_state.order_items:
            st.markdown("**Current Items:**")
            items_df = pd.DataFrame(st.session_state.order_items)
            st.dataframe(items_df, use_container_width=True)
            total_amount = sum(item['total'] for item in st.session_state.order_items)
            st.markdown(f"**Total Amount: ${total_amount:,.2f}**")
            if st.button("Clear All Items"):
                st.session_state.order_items = []
                st.rerun()
        st.markdown("---")
        if st.button("Create Sales Order", type="primary", use_container_width=True):
            if not st.session_state.order_items:
                st.error("Please add at least one item.")
                return
            try:
                order_number = generate_order_number()
                new_order = SalesOrder(
                    order_number=order_number,
                    customer_id=customer_options[selected_customer],
                    status=status,
                    total_amount=total_amount,
                    created_at=datetime.utcnow()
                )
                db.add(new_order)
                db.flush()
                for item in st.session_state.order_items:
                    order_item = SalesOrderItem(
                        order_id=new_order.id,
                        product_name=item['product_name'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        total=item['total']
                    )
                    db.add(order_item)
                db.commit()
                st.success(f"Sales Order {order_number} created!")
                st.session_state.order_items = []
                st.rerun()
            except Exception as e:
                db.rollback()
                st.error(f"Error: {str(e)}")
    finally:
        db.close()

def view_sales_orders():
    st.subheader("All Sales Orders")
    db = get_db()
    try:
        orders = db.query(SalesOrder).order_by(SalesOrder.created_at.desc()).all()
        if orders:
            data = []
            for order in orders:
                customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
                data.append({
                    'Order #': order.order_number,
                    'Customer': customer.name if customer else 'N/A',
                    'Status': order.status,
                    'Total': f"${order.total_amount:,.2f}",
                    'Date': order.created_at.strftime('%Y-%m-%d') if order.created_at else 'N/A'
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No sales orders found.")
    finally:
        db.close()

def view_order_details():
    st.subheader("Order Details")
    db = get_db()
    try:
        orders = db.query(SalesOrder).order_by(SalesOrder.created_at.desc()).all()
        if orders:
            order_options = {o.order_number: o.id for o in orders}
            selected_order_num = st.selectbox("Select Order", list(order_options.keys()))
            if selected_order_num:
                order = db.query(SalesOrder).filter(SalesOrder.id == order_options[selected_order_num]).first()
                customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Order Number", order.order_number)
                with col2:
                    st.metric("Customer", customer.name if customer else 'N/A')
                with col3:
                    st.metric("Status", order.status)
                st.markdown("---")
                st.markdown("**Order Items:**")
                items = db.query(SalesOrderItem).filter(SalesOrderItem.order_id == order.id).all()
                if items:
                    items_data = []
                    for item in items:
                        items_data.append({
                            'Product': item.product_name,
                            'Quantity': item.quantity,
                            'Unit Price': f"${item.unit_price:,.2f}",
                            'Total': f"${item.total:,.2f}"
                        })
                    st.dataframe(pd.DataFrame(items_data), use_container_width=True)
                    st.markdown(f"**Total Amount: ${order.total_amount:,.2f}**")
        else:
            st.info("No orders available.")
    finally:
        db.close()
