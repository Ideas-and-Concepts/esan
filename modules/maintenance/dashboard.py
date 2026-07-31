"""
Maintenance Dashboard
Esan ERP - Equipment & Machinery
"""

import streamlit as st
import pandas as pd
from services.maintenance_service import get_all_equipment, create_equipment
from datetime import datetime

def maintenance_dashboard():
    st.title("🔧 Maintenance")
    tab1, tab2 = st.tabs(["Equipment List", "Add Equipment"])

    with tab1:
        equipment = get_all_equipment()
        if equipment:
            data = [{
                "Name": e.name,
                "Type": e.equipment_type,
                "Serial": e.serial_number,
                "Last Maintenance": e.last_maintenance.strftime('%Y-%m-%d') if e.last_maintenance else "",
                "Next Due": e.next_maintenance.strftime('%Y-%m-%d') if e.next_maintenance else "",
                "Status": e.status
            } for e in equipment]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No equipment registered.")

    with tab2:
        st.subheader("➕ Add Equipment")
        with st.form("add_equipment_form"):
            name = st.text_input("Equipment Name *")
            etype = st.selectbox("Type", ["Milling Machine", "Packaging Line", "Generator", "Vehicle", "Other"])
            serial = st.text_input("Serial Number")
            purchase = st.date_input("Purchase Date", datetime.today())
            last_maint = st.date_input("Last Maintenance Date", datetime.today())
            next_maint = st.date_input("Next Maintenance Due", datetime.today())
            status = st.selectbox("Status", ["Operational", "Under Maintenance", "Out of Service"])
            if st.form_submit_button("Save Equipment"):
                if not name:
                    st.error("Name is required.")
                else:
                    create_equipment(name, etype, serial, purchase, last_maint, next_maint, status)
                    st.success("Equipment added successfully.")
                    st.rerun()