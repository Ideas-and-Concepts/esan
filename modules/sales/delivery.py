"""
Delivery Management Module
Nile Harvest Foods Ltd.
Esan ERP - Delivery Tracking
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import SessionLocal
from models import Delivery, SalesOrder

def get_db():
    return SessionLocal()

def generate_delivery_number():
    db = get_db()
    count = db.query(Delivery).count()
    db.close()
    return f"DEL-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"

def delivery_page():
    st.title("🚛 Delivery Management")
    tab1, tab2, tab3 = st.tabs(["Schedule Delivery", "Track Deliveries", "Update Status"])
    with tab1:
        schedule_delivery()
    with tab2:
        track_deliveries()
    with tab3:
        update_delivery_status()

def schedule_delivery():
    st.subheader("Schedule New Delivery")
    db = get_db()
    try:
        orders = db.query(SalesOrder).filter(SalesOrder.status.in_(["Confirmed", "Processing"])).all()
        if not orders:
            st.warning("No orders available for delivery.")
            return
        order_options = {f"{o.order_number}": o.id for o in orders}
        with st.form("delivery_form"):
            selected_order = st.selectbox("Sales Order", list(order_options.keys()))
            col1, col2 = st.columns(2)
            with col1:
                destination = st.text_input("Delivery Destination")
                driver = st.text_input("Driver Name")
            with col2:
                vehicle = st.text_input("Vehicle Number/Type")
                delivery_date = st.date_input("Scheduled Delivery Date")
            if st.form_submit_button("Schedule Delivery"):
                if destination and driver and vehicle:
                    delivery_number = generate_delivery_number()
                    new_delivery = Delivery(
                        delivery_number=delivery_number,
                        order_id=order_options[selected_order],
                        destination=destination,
                        driver=driver,
                        vehicle=vehicle,
                        status="Scheduled",
                        created_at=datetime.utcnow()
                    )
                    db.add(new_delivery)
                    db.commit()
                    st.success(f"Delivery {delivery_number} scheduled!")
                    st.rerun()
                else:
                    st.error("Please fill all fields.")
    finally:
        db.close()

def track_deliveries():
    st.subheader("Delivery Tracking")
    db = get_db()
    try:
        deliveries = db.query(Delivery).order_by(Delivery.created_at.desc()).all()
        if deliveries:
            data = []
            for d in deliveries:
                order = db.query(SalesOrder).filter(SalesOrder.id == d.order_id).first()
                data.append({
                    'Delivery #': d.delivery_number,
                    'Order #': order.order_number if order else 'N/A',
                    'Destination': d.destination,
                    'Driver': d.driver,
                    'Vehicle': d.vehicle,
                    'Status': d.status,
                    'Date': d.created_at.strftime('%Y-%m-%d') if d.created_at else 'N/A'
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

            st.markdown("---")
            st.subheader("Delivery Summary")
            status_counts = df['Status'].value_counts()
            cols = st.columns(len(status_counts))
            for i, (status, count) in enumerate(status_counts.items()):
                with cols[i]:
                    st.metric(status, count)
        else:
            st.info("No deliveries found.")
    finally:
        db.close()

def update_delivery_status():
    st.subheader("Update Delivery Status")
    db = get_db()
    try:
        deliveries = db.query(Delivery).filter(Delivery.status != "Delivered").all()
        if deliveries:
            delivery_options = {d.delivery_number: d.id for d in deliveries}
            col1, col2 = st.columns(2)
            with col1:
                selected = st.selectbox("Select Delivery", list(delivery_options.keys()))
            with col2:
                new_status = st.selectbox("New Status", ["Scheduled", "In Transit", "Out for Delivery", "Delivered", "Failed"])
            if st.button("Update Status", type="primary"):
                delivery = db.query(Delivery).filter(Delivery.id == delivery_options[selected]).first()
                if delivery:
                    delivery.status = new_status
                    if new_status == "Delivered":
                        delivery.delivered_date = datetime.utcnow()
                    db.commit()
                    st.success(f"Status updated to {new_status}")
                    st.rerun()
        else:
            st.info("All deliveries completed.")
    finally:
        db.close()