"""
Esan ERP Procurement - Suppliers Module

Nile Harvest Foods Ltd.

Functions:
- Register suppliers
- View suppliers
- Manage agricultural suppliers
"""

import streamlit as st
import pandas as pd

from services.procurement_service import (
    get_all_suppliers,
    create_supplier
)



# =====================================
# SUPPLIER PAGE
# =====================================

def suppliers_page():

    st.title("👨‍🌾 Supplier Management")


    tab1, tab2 = st.tabs(
        [
            "➕ Add Supplier",
            "📋 Suppliers List"
        ]
    )


    with tab1:

        add_supplier()



    with tab2:

        view_suppliers()




# =====================================
# ADD SUPPLIER
# =====================================

def add_supplier():

    st.subheader(
        "Register New Supplier"
    )


    with st.form(
        "supplier_form"
    ):


        name = st.text_input(
            "Supplier Name"
        )


        contact_person = st.text_input(
            "Contact Person"
        )


        phone = st.text_input(
            "Phone Number"
        )


        email = st.text_input(
            "Email"
        )


        location = st.text_input(
            "Location"
        )


        country = st.text_input(
            "Country"
        )


        address = st.text_area(
            "Address"
        )


        submitted = st.form_submit_button(
            "Save Supplier"
        )



        if submitted:


            if not name:

                st.error(
                    "Supplier name is required"
                )

                return



            try:


                supplier = create_supplier(

                    name=name,

                    phone=phone,

                    email=email,

                    address=address,

                    location=location,

                    country=country

                )


                st.success(

                    f"Supplier {supplier.name} added successfully"

                )


                st.rerun()



            except Exception as e:

                st.error(
                    f"Error: {e}"
                )




# =====================================
# VIEW SUPPLIERS
# =====================================

def view_suppliers():

    suppliers = get_all_suppliers()


    if not suppliers:

        st.info(
            "No suppliers registered."
        )

        return



    data = []


    for supplier in suppliers:


        data.append({

            "Name":
                supplier.name,

            "Phone":
                supplier.phone,

            "Email":
                supplier.email,

            "Location":
                supplier.location,

            "Country":
                supplier.country,

            "Created":
                supplier.created_at.strftime(
                    "%Y-%m-%d"
                )

        })



    df = pd.DataFrame(data)


    st.dataframe(

        df,

        use_container_width=True

    )