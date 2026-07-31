"""
Logistics Dashboard
Esan ERP - Vehicle & Delivery Overview
"""

import streamlit as st
import pandas as pd
from services.logistics_service import (
    get_all_vehicles, create_vehicle,
    get_all_maintenance_records, create_maintenance_record
)
from services.delivery_service import get_all_deliveries, get_pending_deliveries

def logistics_dashboard():
    st.title("🚚 Logistics")
    tab1, tab2, tab3 = st.tabs(["Vehicles", "Maintenance", "Deliveries"])

    with tab1:
        vehicles_tab()
    with tab2:
        maintenance_tab()
    with tab3:
        deliveries_tab()

def vehicles_tab():
    st.subheader("🚛 Vehicle Fleet")
    vehicles = get_all_vehicles()
    if vehicles:
        data = [{
            "Plate Number": v.vehicle_number,
            "Type": v.vehicle_type,
            "Make": v.make,
            "Model": v.model,
            "Capacity (tons)": v.capacity,
            "Status": v.status
        } for v in vehicles]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No vehicles registered.")

    with st.expander("➕ Add Vehicle"):
        with st.form("add_vehicle_form"):
            plate = st.text_input("Plate Number *")
            vtype = st.selectbox("Type", ["Truck", "Van", "Bike"])
            make = st.text_input("Make")
            model = st.text_input("Model")
            capacity = st.number_input("Capacity (tons)", min_value=0.0, step=0.1)
            if st.form_submit_button("Save Vehicle"):
                if not plate:
                    st.error("Plate number is required.")
                else:
                    create_vehicle(plate, vtype, make, model, capacity)
                    st.success(f"Vehicle {plate} added.")
                    st.rerun()

def maintenance_tab():
    st.subheader("🔧 Maintenance Records")
    records = get_all_maintenance_records()
    if records:
        data = [{
            "Vehicle ID": r.vehicle_id,
            "Description": r.description,
            "Cost": f"${r.cost:,.2f}",
            "Date": r.maintenance_date.strftime('%Y-%m-%d') if r.maintenance_date else "",
            "Next Due": r.next_due_date.strftime('%Y-%m-%d') if r.next_due_date else ""
        } for r in records]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No maintenance records yet.")

    with st.expander("📝 Add Record"):
        vehicles = get_all_vehicles()
        voptions = {v.vehicle_number: v.id for v in vehicles}
        if voptions:
            with st.form("add_maintenance_form"):
                selected = st.selectbox("Vehicle", list(voptions.keys()))
                desc = st.text_area("Description")
                cost = st.number_input("Cost", min_value=0.0)
                date = st.date_input("Maintenance Date")
                next_due = st.date_input("Next Due (optional)")
                if st.form_submit_button("Save Record"):
                    if not desc:
                        st.error("Description is required.")
                    else:
                        create_maintenance_record(voptions[selected], desc, cost, date, next_due)
                        st.success("Maintenance record saved.")
                        st.rerun()
        else:
            st.warning("Add a vehicle first.")

def deliveries_tab():
    st.subheader("📦 Delivery Status")
    tab1, tab2 = st.tabs(["All Deliveries", "Pending"])
    with tab1:
        deliveries = get_all_deliveries()
        if deliveries:
            data = [{
                "Delivery #": d.delivery_number,
                "Order ID": d.order_id,
                "Destination": d.destination,
                "Driver": d.driver,
                "Vehicle": d.vehicle,
                "Status": d.status
            } for d in deliveries]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No deliveries.")
    with tab2:
        pending = get_pending_deliveries()
        if pending:
            data = [{
                "Delivery #": d.delivery_number,
                "Order ID": d.order_id,
                "Destination": d.destination,
                "Driver": d.driver,
                "Status": d.status
            } for d in pending]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.success("All deliveries completed.")