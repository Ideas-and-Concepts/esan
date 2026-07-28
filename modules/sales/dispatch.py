"""
Dispatch Module
Esan ERP - Dispatch Notes
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import SessionLocal
from models import SalesOrder, Delivery, Customer

def get_db():
    return SessionLocal()

def dispatch_page():
    st.title("📦 Dispatch Management")
    tab1, tab2 = st.tabs(["Pending Dispatch", "Dispatch History"])
    with tab1:
        pending_dispatch()
    with tab2:
        dispatch_history()

def pending_dispatch():
    db = get_db()
    try:
        # Orders that are confirmed but not yet dispatched
        orders = db.query(SalesOrder).filter(SalesOrder.status == "Confirmed").all()
        if not orders:
            st.info("No orders awaiting dispatch.")
            return
        data = []
        for order in orders:
            customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
            data.append({
                'Order #': order.order_number,
                'Customer': customer.name if customer else 'N/A',
                'Total': f"${order.total_amount:,.2f}",
                'Status': order.status
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        # Dispatch action
        selected_order_num = st.selectbox("Select Order to Dispatch", [o.order_number for o in orders])
        if st.button("Mark as Dispatched"):
            order = db.query(SalesOrder).filter(SalesOrder.order_number == selected_order_num).first()
            if order:
                order.status = "Dispatched"
                # Optionally create a delivery record
                db.commit()
                st.success(f"Order {selected_order_num} dispatched!")
                st.rerun()
    finally:
        db.close()

def dispatch_history():
    db = get_db()
    try:
        orders = db.query(SalesOrder).filter(SalesOrder.status.in_(["Dispatched", "Delivered"])).all()
        if orders:
            data = []
            for order in orders:
                customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
                data.append({
                    'Order #': order.order_number,
                    'Customer': customer.name if customer else 'N/A',
                    'Total': f"${order.total_amount:,.2f}",
                    'Status': order.status,
                    'Date': order.created_at.strftime('%Y-%m-%d') if order.created_at else ''
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No dispatch history.")
    finally:
        db.close()
