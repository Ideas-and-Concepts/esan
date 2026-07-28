"""
Maintenance Dashboard
Esan ERP - Equipment & Machinery
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import SessionLocal
from models import Equipment

def get_db():
    return SessionLocal()

def maintenance_dashboard():
    st.title("🔧 Maintenance Management")
    tab1, tab2 = st.tabs(["Equipment", "Add Equipment"])
    with tab1:
        equipment_list()
    with tab2:
        add_equipment()

def equipment_list():
    db = get_db()
    try:
        equip = db.query(Equipment).all()
        if equip:
            data = [{
                'Name': e.name,
                'Type': e.equipment_type,
                'Serial': e.serial_number,
                'Last Maintenance': e.last_maintenance.strftime('%Y-%m-%d') if e.last_maintenance else '',
                'Next Due': e.next_maintenance.strftime('%Y-%m-%d') if e.next_maintenance else '',
                'Status': e.status
            } for e in equip]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No equipment registered.")
    finally:
        db.close()

def add_equipment():
    st.subheader("New Equipment")
    with st.form("add_equipment"):
        name = st.text_input("Equipment Name*")
        etype = st.selectbox("Type", ["Milling Machine", "Packaging Line", "Generator", "Vehicle", "Other"])
        serial = st.text_input("Serial Number")
        purchase = st.date_input("Purchase Date", datetime.now().date())
        last_maint = st.date_input("Last Maintenance", datetime.now().date())
        next_maint = st.date_input("Next Maintenance Due", datetime.now().date())
        status = st.selectbox("Status", ["Operational", "Under Maintenance", "Out of Service"])
        if st.form_submit_button("Save"):
            if not name:
                st.error("Name is required")
                return
            db = get_db()
            try:
                eq = Equipment(
                    name=name, equipment_type=etype, serial_number=serial,
                    purchase_date=purchase, last_maintenance=last_maint,
                    next_maintenance=next_maint, status=status,
                    created_at=datetime.utcnow()
                )
                db.add(eq)
                db.commit()
                st.success("Equipment added!")
                st.rerun()
            except Exception as e:
                db.rollback()
                st.error(f"Error: {e}")
            finally:
                db.close()