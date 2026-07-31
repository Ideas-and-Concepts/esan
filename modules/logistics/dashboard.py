"""
Logistics Dashboard – uses logistics_service & delivery_service
"""

import streamlit as st
import pandas as pd
from services.logistics_service import (
    get_all_vehicles, create_vehicle,
    get_all_maintenance_records, create_maintenance_record
)
from services.delivery_service import get_all_deliveries

def logistics_dashboard():
    st.title("🚚 Logistics")
    tab1, tab2, tab3 = st.tabs(["Vehicles", "Maintenance", "Deliveries"])
    with tab1:
        vehicles_view()
    with tab2:
        maintenance_view()
    with tab3:
        deliveries_view()

def vehicles_view():
    vehicles = get_all_vehicles()
    if vehicles:
        data = [{
            "Number": v.vehicle_number,
            "Type": v.vehicle_type,
            "Make": v.make,
            "Model": v.model,
            "Capacity": v.capacity,
            "Status": v.status
        } for v in vehicles]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No vehicles.")
    with st.expander("Add Vehicle"):
        with st.form("add_vehicle"):
            number = st.text_input("Plate Number *")
            vtype = st.selectbox("Type", ["Truck", "Van", "Bike"])
            make = st.text_input("Make")
            model = st.text_input("Model")
            capacity = st.number_input("Capacity (tons)", min_value=0.0)
            if st.form_submit_button("Save"):
                if number:
                    create_vehicle(number, vtype, make, model, capacity)
                    st.success("Vehicle added")
                    st.rerun()

def maintenance_view():
    records = get_all_maintenance_records()
    if records:
        data = [{
            "Vehicle ID": r.vehicle_id,
            "Description": r.description,
            "Cost": f"${r.cost:,.2f}",
            "Date": r.maintenance_date.strftime('%Y-%m-%d') if r.maintenance_date else '',
            "Next Due": r.next_due_date.strftime('%Y-%m-%d') if r.next_due_date else ''
        } for r in records]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No records.")
    with st.expander("Add Maintenance Record"):
        vehicles = get_all_vehicles()
        v_options = {v.vehicle_number: v.id for v in vehicles}
        with st.form("add_maintenance"):
            selected_vehicle = st.selectbox("Vehicle", list(v_options.keys())) if v_options else None
            desc = st.text_area("Description")
            cost = st.number_input("Cost", min_value=0.0)
            date = st.date_input("Date")
            next_due = st.date_input("Next Due (optional)")
            if st.form_submit_button("Save") and selected_vehicle:
                create_maintenance_record(v_options[selected_vehicle], desc, cost, date, next_due)
                st.success("Recorded")
                st.rerun()

def deliveries_view():
    deliveries = get_all_deliveries()
    if deliveries:
        data = [{
            "Delivery #": d.delivery_number,
            "Order ID": d.order_id,
            "Destination": d.destination,
            "Driver": d.driver,
            "Status": d.status
        } for d in deliveries]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No deliveries.")
