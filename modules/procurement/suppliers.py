"""
Esan ERP Procurement - Suppliers Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:

- Register suppliers
- View suppliers
- Manage agricultural suppliers
  """

import logging

import pandas as pd
import streamlit as st

from services.procurement_service import (
get_all_suppliers,
create_supplier,
)

logger = logging.getLogger(name)

==================================================

SUPPLIER PAGE

==================================================

def suppliers_page():

st.title("👨‍🌾 Supplier Management")

st.caption(
    "Manage agricultural suppliers, contact information "
    "and procurement partners."
)

st.divider()

tab1, tab2 = st.tabs(
    [
        "➕ Add Supplier",
        "📋 Suppliers List",
    ]
)

# ==================================================
# ADD SUPPLIER
# ==================================================

with tab1:
    add_supplier()

# ==================================================
# SUPPLIER LIST
# ==================================================

with tab2:
    view_suppliers()

==================================================

ADD SUPPLIER

==================================================

def add_supplier():

st.subheader("Register New Supplier")

with st.form("supplier_form", clear_on_submit=True):

    col1, col2 = st.columns(2)

    with col1:

        name = st.text_input(
            "Supplier Name *",
            placeholder="e.g. Nile Grain Suppliers Ltd."
        )

        contact_person = st.text_input(
            "Contact Person",
            placeholder="Full name"
        )

        phone = st.text_input(
            "Phone Number",
            placeholder="+256..."
        )

        email = st.text_input(
            "Email",
            placeholder="supplier@example.com"
        )

    with col2:

        supplier_type = st.selectbox(
            "Supplier Type",
            [
                "Agricultural Supplier",
                "Farmer",
                "Farmer Cooperative",
                "Grain Trader",
                "Cassava Supplier",
                "Maize Supplier",
                "Packaging Supplier",
                "Other",
            ],
        )

        location = st.text_input(
            "Location",
            placeholder="District / Town"
        )

        country = st.text_input(
            "Country",
            value="Uganda"
        )

        address = st.text_area(
            "Address",
            placeholder="Physical or postal address"
        )

    submitted = st.form_submit_button(
        "💾 Save Supplier",
        use_container_width=True,
    )

    if submitted:

        # ------------------------------------------
        # VALIDATION
        # ------------------------------------------

        name = name.strip()
        contact_person = contact_person.strip()
        phone = phone.strip()
        email = email.strip()
        location = location.strip()
        country = country.strip()
        address = address.strip()

        if not name:

            st.error(
                "Supplier name is required."
            )

            return

        # ------------------------------------------
        # CREATE SUPPLIER
        # ------------------------------------------

        try:

            supplier = create_supplier(
                name=name,
                phone=phone or None,
                email=email or None,
                address=address or None,
                supplier_type=supplier_type,
                location=location or None,
                country=country or None,
                contact_person=contact_person or None,
            )

            if supplier:

                st.success(
                    f"Supplier '{supplier.name}' "
                    "was added successfully."
                )

                st.rerun()

            else:

                st.error(
                    "Supplier could not be created."
                )

        except Exception as e:

            logger.exception(
                "Failed to create supplier: %s",
                e
            )

            st.error(
                "Unable to save supplier. "
                "Please check the database or "
                "procurement service."
            )

            with st.expander(
                "Technical Error Details"
            ):
                st.code(str(e))

==================================================

VIEW SUPPLIERS

==================================================

def view_suppliers():

st.subheader("Registered Suppliers")

# ----------------------------------------------
# LOAD SUPPLIERS
# ----------------------------------------------

try:

    suppliers = get_all_suppliers()

except Exception as e:

    logger.exception(
        "Failed to load suppliers: %s",
        e
    )

    st.error(
        "Unable to load suppliers."
    )

    with st.expander(
        "Technical Error Details"
    ):
        st.code(str(e))

    return

# ----------------------------------------------
# EMPTY STATE
# ----------------------------------------------

if not suppliers:

    st.info(
        "No suppliers registered yet."
    )

    return

# ----------------------------------------------
# BUILD TABLE
# ----------------------------------------------

data = []

for supplier in suppliers:

    created = getattr(
        supplier,
        "created_at",
        None
    )

    created_text = (
        created.strftime("%Y-%m-%d")
        if created
        else ""
    )

    data.append(
        {
            "ID": supplier.id,
            "Supplier Name": supplier.name or "",
            "Type": (
                supplier.supplier_type
                or "Agricultural Supplier"
            ),
            "Contact Person": (
                supplier.contact_person
                or ""
            ),
            "Phone": supplier.phone or "",
            "Email": supplier.email or "",
            "Location": supplier.location or "",
            "Country": supplier.country or "",
            "Created": created_text,
        }
    )

# ----------------------------------------------
# DATAFRAME
# ----------------------------------------------

df = pd.DataFrame(data)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
)

st.caption(
    f"Total suppliers: {len(data)}"
)