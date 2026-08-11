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
    create_supplier,
)


# ==================================================
# SUPPLIER PAGE
# ==================================================

def suppliers_page():
    """
    Main Supplier Management page.
    """

    st.title("👨‍🌾 Supplier Management")
    st.caption(
        "Register and manage agricultural suppliers."
    )

    tab1, tab2 = st.tabs(
        [
            "➕ Add Supplier",
            "📋 Suppliers List",
        ]
    )

    with tab1:
        add_supplier()

    with tab2:
        view_suppliers()


# ==================================================
# ADD SUPPLIER
# ==================================================

def add_supplier():
    """
    Register a new supplier.
    """

    st.subheader("Register New Supplier")

    with st.form("supplier_form", clear_on_submit=True):

        name = st.text_input(
            "Supplier Name *"
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
            "Country",
            value="Uganda"
        )

        address = st.text_area(
            "Address"
        )

        supplier_type = st.selectbox(
            "Supplier Type",
            [
                "Agricultural Supplier",
                "Farmer",
                "Farmer Group",
                "Cooperative",
                "Distributor",
                "Other",
            ],
        )

        submitted = st.form_submit_button(
            "💾 Save Supplier",
            use_container_width=True,
        )

        if submitted:

            # ------------------------------------------
            # VALIDATION
            # ------------------------------------------

            if not name.strip():
                st.error(
                    "Supplier name is required."
                )
                return

            # ------------------------------------------
            # SAVE
            # ------------------------------------------

            try:

                supplier = create_supplier(
                    name=name.strip(),
                    phone=phone.strip() or None,
                    email=email.strip() or None,
                    address=address.strip() or None,
                    supplier_type=supplier_type,
                    location=location.strip() or None,
                    country=country.strip() or None,
                    contact_person=contact_person.strip() or None,
                )

                st.success(
                    f"Supplier '{supplier.name}' "
                    "was added successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "Unable to save supplier."
                )

                with st.expander(
                    "Technical information"
                ):
                    st.exception(e)


# ==================================================
# VIEW SUPPLIERS
# ==================================================

def view_suppliers():
    """
    Display all registered suppliers.
    """

    st.subheader("Registered Suppliers")

    try:
        suppliers = get_all_suppliers()

    except Exception as e:

        st.error(
            "Unable to load suppliers."
        )

        with st.expander(
            "Technical information"
        ):
            st.exception(e)

        return

    if not suppliers:

        st.info(
            "No suppliers have been registered yet."
        )

        return

    data = []

    for supplier in suppliers:

        created_date = ""

        if supplier.created_at:
            created_date = (
                supplier.created_at.strftime(
                    "%Y-%m-%d"
                )
            )

        data.append(
            {
                "ID": supplier.id,
                "Name": supplier.name or "",
                "Contact Person":
                    supplier.contact_person or "",
                "Phone":
                    supplier.phone or "",
                "Email":
                    supplier.email or "",
                "Location":
                    supplier.location or "",
                "Country":
                    supplier.country or "",
                "Type":
                    supplier.supplier_type or "",
                "Created":
                    created_date,
            }
        )

    df = pd.DataFrame(data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        f"Total suppliers: {len(suppliers)}"
    )