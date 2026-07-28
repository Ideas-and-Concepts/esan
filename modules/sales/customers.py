"""
Customers Module
Esan ERP - Customer Management
"""

import streamlit as st
import pandas as pd
from database import SessionLocal
from models import Customer
from datetime import datetime

def get_db():
    return SessionLocal()

def customers_page():
    st.title("👥 Customer Management")
    tab1, tab2 = st.tabs(["Customer List", "Add Customer"])
    with tab1:
        view_customers()
    with tab2:
        add_customer()

def view_customers():
    db = get_db()
    try:
        customers = db.query(Customer).order_by(Customer.name).all()
        if customers:
            data = [{
                'ID': c.id,
                'Name': c.name,
                'Type': c.customer_type,
                'Phone': c.phone,
                'Email': c.email,
                'Location': c.location,
                'Country': c.country,
                'Contact': c.contact_person
            } for c in customers]
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No customers found.")
    finally:
        db.close()

def add_customer():
    st.subheader("New Customer")
    with st.form("add_customer"):
        name = st.text_input("Company Name*")
        c_type = st.selectbox("Customer Type", ["Wholesale", "Retail", "Distributor", "Export"])
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        address = st.text_input("Address")
        location = st.text_input("Location/City")
        country = st.text_input("Country")
        contact = st.text_input("Contact Person")
        if st.form_submit_button("Save Customer"):
            if not name:
                st.error("Name is required")
                return
            db = get_db()
            try:
                cust = Customer(
                    name=name, customer_type=c_type, phone=phone, email=email,
                    address=address, location=location, country=country,
                    contact_person=contact, created_at=datetime.utcnow()
                )
                db.add(cust)
                db.commit()
                st.success(f"Customer '{name}' added!")
                st.rerun()
            except Exception as e:
                db.rollback()
                st.error(f"Error: {e}")
            finally:
                db.close()
