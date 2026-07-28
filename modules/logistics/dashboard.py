"""
Logistics Dashboard
Esan ERP - Vehicle & Delivery Management
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import SessionLocal
from models import Vehicle, MaintenanceRecord, Delivery

def get_db():
    return SessionLocal()

def logistics_dashboard():
    st.title("🚚 Logistics Dashboard")
    tab1, tab2, tab3 = st.tabs(["Vehicles", "Maintenance", "Active Deliveries"])
    with tab1:
        vehicle_list()
    with tab2:
        maintenance_list()
    with tab3:
        active_deliveries()

def vehicle_list():
    db = get_db()
    try:
        vehicles = db.query(Vehicle).all()
        if vehicles:
            data = [{
                'Number': v.vehicle_number,
                'Type': v.vehicle_type,
                'Make': v.make,
                'Model': v.model,
                'Capacity (T)': v.capacity,
                'Status': v.status
            } for v in vehicles]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No vehicles registered.")
        # Add vehicle form
        with st.expander("Add Vehicle"):
            with st.form("add_vehicle"):
                number = st.text_input("Plate Number*")
                v_type = st.selectbox("Type", ["Truck", "Van", "Bike", "Other"])
                make = st.text_input("Make")
                model = st.text_input("Model")
                capacity = st.number_input("Capacity (tons)", min_value=0.0)
                if st.form_submit_button("Save"):
                    if number:
                        db.add(Vehicle(
                            vehicle_number=number, vehicle_type=v_type,
                            make=make, model=model, capacity=capacity,
                            status="Available", created_at=datetime.utcnow()
                        ))
                        db.commit()
                        st.success("Vehicle added!")
                        st.rerun()
    finally:
        db.close()

def maintenance_list():
    db = get_db()
    try:
        records = db.query(MaintenanceRecord).order_by(MaintenanceRecord.maintenance_date.desc()).all()
        if records:
            data = []
            for r in records:
                vehicle = db.query(Vehicle).filter(Vehicle.id == r.vehicle_id).first()
                data.append({
                    'Vehicle': vehicle.vehicle_number if vehicle else 'N/A',
                    'Description': r.description,
                    'Cost': f"${r.cost:,.2f}",
                    'Date': r.maintenance_date.strftime('%Y-%m-%d') if r.maintenance_date else '',
                    'Next Due': r.next_due_date.strftime('%Y-%m-%d') if r.next_due_date else ''
                })
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No maintenance records.")
    finally:
        db.close()

def active_deliveries():
    db = get_db()
    try:
        deliveries = db.query(Delivery).filter(Delivery.status != "Delivered").all()
        if deliveries:
            data = [{
                'Delivery #': d.delivery_number,
                'Destination': d.destination,
                'Driver': d.driver,
                'Vehicle': d.vehicle,
                'Status': d.status
            } for d in deliveries]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("All deliveries completed.")
    finally:
        db.close()