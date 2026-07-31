"""
Maintenance Dashboard – uses maintenance_service
"""

import streamlit as st
import pandas as pd
from services.maintenance_service import get_all_equipment, create_equipment
from datetime import datetime

def maintenance_dashboard():
    st.title("🔧 Maintenance")
    tab1, tab2 = st.tabs(["Equipment", "Add Equipment"])
    with tab1:
        equip = get_all_equipment()
        if equip:
            data = [{
                "Name": e.name,
                "Type": e.equipment_type,
                "Serial": e.serial_number,
                "Last Maint.": e.last_maintenance.strftime('%Y-%m-%d') if e.last_maintenance else '',
                "Next Due": e.next_maintenance.strftime('%Y-%m-%d') if e.next_maintenance else '',
                "Status": e.status
            } for e in equip]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No equipment.")
    with tab2:
        with st.form("add_equipment"):
            name = st.text_input("Name *")
            etype = st.selectbox("Type", ["Milling Machine", "Packaging Line", "Generator", "Vehicle", "Other"])
            serial = st.text_input("Serial Number")
            purchase = st.date_input("Purchase Date", datetime.now().date())
            last_maint = st.date_input("Last Maintenance")
            next_maint = st.date_input("Next Due")
            status = st.selectbox("Status", ["Operational", "Under Maintenance", "Out of Service"])
            if st.form_submit_button("Save"):
                if name:
                    create_equipment(name, etype, serial, purchase, last_maint, next_maint, status)
                    st.success("Equipment added")
                    st.rerun()
