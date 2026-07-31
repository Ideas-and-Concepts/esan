"""
Customers Module – uses sales_service
"""

import streamlit as st
import pandas as pd
from services.sales_service import get_all_customers, create_customer
from datetime import datetime

def customers_page():
    st.title("👥 Customer Management")
    tab1, tab2 = st.tabs(["Customer List", "Add Customer"])
    with tab1:
        view_customers()
    with tab2:
        add_customer()

def view_customers():
    customers = get_all_customers()
    if customers:
        data = [{
            'Name': c.name,
            'Type': c.customer_type,
            'Phone': c.phone,
            'Email': c.email,
            'Location': c.location,
            'Country': c.country,
            'Contact': c.contact_person
        } for c in customers]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No customers found.")

def add_customer():
    st.subheader("New Customer")
    with st.form("add_customer_form"):
        name = st.text_input("Company Name *")
        c_type = st.selectbox("Customer Type", ["Wholesale", "Retail", "Distributor", "Export"])
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        address = st.text_input("Address")
        location = st.text_input("Location/City")
        country = st.text_input("Country")
        contact_person = st.text_input("Contact Person")
        if st.form_submit_button("Save Customer"):
            if not name:
                st.error("Name is required")
                return
            try:
                create_customer(
                    name=name,
                    customer_type=c_type,
                    phone=phone,
                    email=email,
                    address=address,
                    location=location,
                    country=country,
                    contact_person=contact_person
                )
                st.success(f"Customer '{name}' added!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
