"""
Esan ERP - Procurement Suppliers Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:
- Register suppliers
- View suppliers
- Search suppliers
- Edit suppliers
- Delete suppliers
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
# MAIN SUPPLIERS PAGE
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

    with st.form("supplier_form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:

            name = st.text_input(
                "Supplier Name *",
                placeholder="e.g. Nile Grain Suppliers Ltd."
            )

            contact_person = st.text_input(
                "Contact Person",
                placeholder="Contact person's name"
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
                    "Grain Supplier",
                    "Cassava Supplier",
                    "Packaging Supplier",
                    "Equipment Supplier",
                    "Transport Supplier",
                    "Other",
                ]
            )

            location = st.text_input(
                "Location",
                placeholder="District / City"
            )

            country = st.text_input(
                "Country",
                value="Uganda"
            )

            address = st.text_area(
                "Address",
                placeholder="Physical address"
            )

        submitted = st.form_submit_button(
            "💾 Save Supplier",
            type="primary",
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
                f"Unable to create supplier: {e}"
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

    # --------------------------------------------------
    # SEARCH
    # --------------------------------------------------

    search = st.text_input(
        "🔎 Search Suppliers",
        placeholder="Search by name, phone, location or country..."
    )

    if search.strip():

        search_text = search.lower().strip()

        suppliers = [
            supplier
            for supplier in suppliers
            if (
                search_text in (supplier.name or "").lower()
                or search_text in (supplier.phone or "").lower()
                or search_text in (supplier.email or "").lower()
                or search_text in (supplier.location or "").lower()
                or search_text in (supplier.country or "").lower()
                or search_text in (supplier.contact_person or "").lower()
            )
        ]

    if not suppliers:

        st.info(
            "No suppliers match your search."
        )

        return

    # --------------------------------------------------
    # SUPPLIER TABLE
    # --------------------------------------------------

    data = []

    for supplier in suppliers:

        data.append(
            {
                "ID": supplier.id,
                "Supplier": supplier.name,
                "Contact Person": supplier.contact_person or "",
                "Phone": supplier.phone or "",
                "Email": supplier.email or "",
                "Type": supplier.supplier_type or "",
                "Location": supplier.location or "",
                "Country": supplier.country or "",
                "Created": (
                    supplier.created_at.strftime("%Y-%m-%d")
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

    st.caption(
        f"Showing {len(suppliers)} supplier(s)"
    )


# ==================================================
# MANAGE SUPPLIERS
# ==================================================

def manage_suppliers():

    st.subheader("⚙️ Manage Suppliers")

    suppliers = get_all_suppliers()

    if not suppliers:

        st.info(
            "There are no suppliers to manage."
        )

        return

    supplier_options = {
        f"{supplier.name} | "
        f"{supplier.phone or 'No phone'}":
            supplier.id
        for supplier in suppliers
    }

    selected_supplier_label = st.selectbox(
        "Select Supplier",
        options=list(supplier_options.keys()),
    )

    selected_supplier_id = supplier_options[
        selected_supplier_label
    ]

    selected_supplier = next(
        (
            supplier
            for supplier in suppliers
            if supplier.id == selected_supplier_id
        ),
        None,
    )

    if not selected_supplier:
        st.error("Supplier could not be found.")
        return

    st.divider()

    edit_tab, delete_tab = st.tabs(
        [
            "✏️ Edit Supplier",
            "🗑️ Delete Supplier",
        ]
    )

    # ==================================================
    # EDIT SUPPLIER
    # ==================================================

    with edit_tab:

        st.markdown(
            f"### Edit: {selected_supplier.name}"
        )

        with st.form(
            f"edit_supplier_{selected_supplier.id}"
        ):

            col1, col2 = st.columns(2)

            with col1:

                name = st.text_input(
                    "Supplier Name *",
                    value=selected_supplier.name or "",
                )

                contact_person = st.text_input(
                    "Contact Person",
                    value=selected_supplier.contact_person or "",
                )

                phone = st.text_input(
                    "Phone Number",
                    value=selected_supplier.phone or "",
                )

                email = st.text_input(
                    "Email",
                    value=selected_supplier.email or "",
                )

            with col2:

                supplier_types = [
                    "Agricultural Supplier",
                    "Farmer",
                    "Farmer Cooperative",
                    "Grain Supplier",
                    "Cassava Supplier",
                    "Packaging Supplier",
                    "Equipment Supplier",
                    "Transport Supplier",
                    "Other",
                ]

                current_type = (
                    selected_supplier.supplier_type
                    or "Agricultural Supplier"
                )

                if current_type not in supplier_types:
                    supplier_types.append(current_type)

                supplier_type = st.selectbox(
                    "Supplier Type",
                    supplier_types,
                    index=supplier_types.index(current_type),
                )

                location = st.text_input(
                    "Location",
                    value=selected_supplier.location or "",
                )

                country = st.text_input(
                    "Country",
                    value=selected_supplier.country or "",
                )

                address = st.text_area(
                    "Address",
                    value=selected_supplier.address or "",
                )

            save_changes = st.form_submit_button(
                "💾 Save Changes",
                type="primary",
                use_container_width=True,
            )

        if save_changes:

            if not name.strip():

                st.error(
                    "Supplier name is required."
                )

                return

            try:

                updated_supplier = update_supplier(
                    supplier_id=selected_supplier.id,
                    name=name.strip(),
                    phone=phone.strip() or None,
                    email=email.strip() or None,
                    address=address.strip() or None,
                    supplier_type=supplier_type,
                    location=location.strip() or None,
                    country=country.strip() or None,
                    contact_person=contact_person.strip() or None,
                )

                if updated_supplier:

                    st.success(
                        f"Supplier '{updated_supplier.name}' "
                        "updated successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Supplier could not be found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to update supplier: {e}"
                )

    # ==================================================
    # DELETE SUPPLIER
    # ==================================================

    with delete_tab:

        st.warning(
            "⚠️ Deleting a supplier is permanent."
        )

        st.write(
            f"Supplier: **{selected_supplier.name}**"
        )

        st.write(
            f"Phone: **{selected_supplier.phone or 'Not provided'}**"
        )

        st.write(
            f"Location: **{selected_supplier.location or 'Not provided'}**"
        )

        st.divider()

        confirm_delete = st.checkbox(
            "I understand that deleting this supplier cannot be undone."
        )

        if confirm_delete:

            if st.button(
                "🗑️ Delete Supplier",
                type="primary",
                use_container_width=True,
            ):

                try:

                    result = delete_supplier(
                        selected_supplier.id
                    )

                    if result:

                        st.success(
                            f"Supplier '{selected_supplier.name}' "
                            "deleted successfully."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Supplier could not be found."
                        )

                except Exception as e:

                    st.error(
                        f"Unable to delete supplier: {e}"
                    )


# ==================================================
# STANDALONE EXECUTION
# ==================================================

if __name__ == "__main__":
    suppliers_page()