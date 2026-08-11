"""
Esan ERP - Procurement Suppliers Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:
- Add suppliers
- Edit suppliers
- Delete suppliers
- View suppliers
- Manage agricultural suppliers
"""

import streamlit as st
import pandas as pd

from services.procurement_service import (
    get_all_suppliers,
    create_supplier,
    update_supplier,
    delete_supplier,
)


# ==================================================
# MAIN SUPPLIER PAGE
# ==================================================

def suppliers_page():

    st.title("👨‍🌾 Supplier Management")

    tab1, tab2, tab3 = st.tabs(
        [
            "➕ Add Supplier",
            "📋 Suppliers List",
            "⚙️ Manage Suppliers",
        ]
    )

    with tab1:
        add_supplier()

    with tab2:
        view_suppliers()

    with tab3:
        manage_suppliers()


# ==================================================
# ADD SUPPLIER
# ==================================================

def add_supplier():

    st.subheader("Register New Supplier")

    with st.form("supplier_add_form"):

        name = st.text_input(
            "Supplier Name",
            placeholder="e.g. Nile Grain Suppliers",
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

        supplier_type = st.selectbox(
            "Supplier Type",
            [
                "Agricultural Supplier",
                "Raw Material Supplier",
                "Packaging Supplier",
                "Equipment Supplier",
                "Service Provider",
                "Other",
            ],
        )

        col1, col2 = st.columns(2)

        with col1:
            location = st.text_input(
                "Location"
            )

        with col2:
            country = st.text_input(
                "Country",
                value="Uganda",
            )

        address = st.text_area(
            "Address"
        )

        submitted = st.form_submit_button(
            "💾 Save Supplier",
            use_container_width=True,
        )

        if submitted:

            if not name.strip():

                st.error(
                    "Supplier name is required."
                )

                return

            try:

                supplier = create_supplier(
                    name=name,
                    phone=phone,
                    email=email,
                    address=address,
                    supplier_type=supplier_type,
                    location=location,
                    country=country,
                    contact_person=contact_person,
                )

                st.success(
                    f"Supplier '{supplier.name}' "
                    "added successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Unable to add supplier: {e}"
                )


# ==================================================
# VIEW SUPPLIERS
# ==================================================

def view_suppliers():

    st.subheader("📋 Registered Suppliers")

    suppliers = get_all_suppliers()

    if not suppliers:

        st.info(
            "No suppliers have been registered yet."
        )

        return

    data = []

    for supplier in suppliers:

        data.append(
            {
                "ID": supplier.id,
                "Supplier": supplier.name,
                "Contact Person":
                    supplier.contact_person or "",
                "Phone":
                    supplier.phone or "",
                "Email":
                    supplier.email or "",
                "Type":
                    supplier.supplier_type or "",
                "Location":
                    supplier.location or "",
                "Country":
                    supplier.country or "",
                "Created":
                    (
                        supplier.created_at.strftime(
                            "%Y-%m-%d"
                        )
                        if supplier.created_at
                        else ""
                    ),
            }
        )

    df = pd.DataFrame(data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


# ==================================================
# MANAGE SUPPLIERS
# ==================================================

def manage_suppliers():

    st.subheader("⚙️ Manage Suppliers")

    suppliers = get_all_suppliers()

    if not suppliers:

        st.info(
            "No suppliers available to manage."
        )

        return

    supplier_options = {
        f"{supplier.name} | "
        f"{supplier.phone or 'No phone'}":
            supplier.id
        for supplier in suppliers
    }

    selected_supplier = st.selectbox(
        "Select Supplier",
        list(supplier_options.keys()),
    )

    supplier_id = supplier_options[
        selected_supplier
    ]

    current_supplier = next(
        (
            supplier
            for supplier in suppliers
            if supplier.id == supplier_id
        ),
        None,
    )

    if not current_supplier:
        st.error("Supplier could not be found.")
        return

    action = st.radio(
        "Action",
        [
            "Edit Supplier",
            "Delete Supplier",
        ],
        horizontal=True,
    )

    if action == "Edit Supplier":

        with st.form(
            "edit_supplier_form"
        ):

            name = st.text_input(
                "Supplier Name",
                value=current_supplier.name or "",
            )

            contact_person = st.text_input(
                "Contact Person",
                value=current_supplier.contact_person or "",
            )

            phone = st.text_input(
                "Phone",
                value=current_supplier.phone or "",
            )

            email = st.text_input(
                "Email",
                value=current_supplier.email or "",
            )

            supplier_types = [
                "Agricultural Supplier",
                "Raw Material Supplier",
                "Packaging Supplier",
                "Equipment Supplier",
                "Service Provider",
                "Other",
            ]

            current_type = (
                current_supplier.supplier_type
                if current_supplier.supplier_type
                in supplier_types
                else "Other"
            )

            supplier_type = st.selectbox(
                "Supplier Type",
                supplier_types,
                index=supplier_types.index(
                    current_type
                ),
            )

            col1, col2 = st.columns(2)

            with col1:
                location = st.text_input(
                    "Location",
                    value=current_supplier.location or "",
                )

            with col2:
                country = st.text_input(
                    "Country",
                    value=current_supplier.country or "",
                )

            address = st.text_area(
                "Address",
                value=current_supplier.address or "",
            )

            save = st.form_submit_button(
                "💾 Save Changes",
                use_container_width=True,
            )

            if save:

                if not name.strip():

                    st.error(
                        "Supplier name is required."
                    )

                    return

                try:

                    updated = update_supplier(
                        supplier_id=supplier_id,
                        name=name,
                        phone=phone,
                        email=email,
                        address=address,
                        supplier_type=supplier_type,
                        location=location,
                        country=country,
                        contact_person=contact_person,
                    )

                    if updated:

                        st.success(
                            "Supplier updated successfully."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Supplier was not found."
                        )

                except Exception as e:

                    st.error(
                        f"Unable to update supplier: {e}"
                    )

    else:

        st.warning(
            "⚠️ Deleting a supplier is permanent."
        )

        st.write(
            f"Supplier selected: **{current_supplier.name}**"
        )

        confirm = st.checkbox(
            "I understand that this action cannot be undone."
        )

        if st.button(
            "🗑️ Delete Supplier",
            type="primary",
            disabled=not confirm,
            use_container_width=True,
        ):

            try:

                success, message = delete_supplier(
                    supplier_id
                )

                if success:

                    st.success(message)
                    st.rerun()

                else:

                    st.error(message)

            except Exception as e:

                st.error(
                    f"Unable to delete supplier: {e}"
                )


# ==================================================
# STANDALONE EXECUTION
# ==================================================

if __name__ == "__main__":
    suppliers_page()