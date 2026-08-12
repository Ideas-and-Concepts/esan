"""
Esan ERP Sales - Customer Management

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:
- Add customers
- Edit customers
- Delete customers
- Activate/deactivate customers
- Search customers
- View customer records
"""

import streamlit as st
import pandas as pd

from services.sales_service import (
    get_all_customers,
    search_customers,
    create_customer,
    update_customer,
    delete_customer,
    set_customer_status,
)


# ==================================================
# MAIN CUSTOMER PAGE
# ==================================================

def customers_page():

    st.title("👥 Customer Management")

    tab1, tab2, tab3 = st.tabs(
        [
            "➕ Add Customer",
            "📋 Customers",
            "✏️ Manage Customer",
        ]
    )

    with tab1:
        add_customer()

    with tab2:
        view_customers()

    with tab3:
        manage_customer()


# ==================================================
# ADD CUSTOMER
# ==================================================

def add_customer():

    st.subheader("Register New Customer")

    with st.form("customer_form"):

        col1, col2 = st.columns(2)

        with col1:

            name = st.text_input(
                "Customer Name *"
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

        with col2:

            customer_type = st.selectbox(
                "Customer Type",
                [
                    "Retail",
                    "Wholesale",
                    "Distributor",
                    "Corporate",
                    "Institution",
                    "Export",
                    "Other",
                ],
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
            "💾 Save Customer",
            use_container_width=True,
        )

    if submitted:

        if not name.strip():

            st.error(
                "Customer name is required."
            )

            return

        try:

            customer = create_customer(
                name=name,
                phone=phone,
                email=email,
                address=address,
                customer_type=customer_type,
                location=location,
                country=country,
                contact_person=contact_person,
            )

            st.success(
                f"Customer '{customer.name}' "
                "created successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to create customer: {e}"
            )


# ==================================================
# VIEW CUSTOMERS
# ==================================================

def view_customers():

    st.subheader("Customer Directory")

    search_term = st.text_input(
        "🔎 Search customers",
        placeholder=(
            "Search by name, phone, email or address"
        ),
    )

    try:

        if search_term.strip():

            customers = search_customers(
                search_term
            )

        else:

            customers = get_all_customers()

    except Exception as e:

        st.error(
            f"Unable to load customers: {e}"
        )

        return

    if not customers:

        st.info(
            "No customers found."
        )

        return

    data = []

    for customer in customers:

        active = getattr(
            customer,
            "active",
            True,
        )

        data.append(
            {
                "ID": customer.id,
                "Customer": customer.name,
                "Contact Person": getattr(
                    customer,
                    "contact_person",
                    "",
                ),
                "Phone": customer.phone or "",
                "Email": customer.email or "",
                "Type": getattr(
                    customer,
                    "customer_type",
                    "",
                ),
                "Location": getattr(
                    customer,
                    "location",
                    "",
                ),
                "Country": getattr(
                    customer,
                    "country",
                    "",
                ),
                "Status": (
                    "Active"
                    if active
                    else "Inactive"
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
        f"Total customers: {len(customers)}"
    )


# ==================================================
# MANAGE CUSTOMER
# ==================================================

def manage_customer():

    st.subheader(
        "✏️ Manage Customer"
    )

    customers = get_all_customers()

    if not customers:

        st.info(
            "No customers are available."
        )

        return

    customer_options = {
        (
            f"{customer.name} "
            f"| {customer.phone or 'No phone'}"
        ): customer.id
        for customer in customers
    }

    selected_customer = st.selectbox(
        "Select Customer",
        list(customer_options.keys()),
    )

    customer_id = customer_options[
        selected_customer
    ]

    customer = next(
        (
            item
            for item in customers
            if item.id == customer_id
        ),
        None,
    )

    if not customer:
        st.error(
            "Customer could not be found."
        )
        return

    st.divider()

    active = getattr(
        customer,
        "active",
        True,
    )

    st.write(
        f"**Current Status:** "
        f"{'Active' if active else 'Inactive'}"
    )

    edit_tab, status_tab, delete_tab = st.tabs(
        [
            "✏️ Edit",
            "🔄 Status",
            "🗑️ Delete",
        ]
    )


    # ==================================================
    # EDIT
    # ==================================================

    with edit_tab:

        with st.form(
            f"edit_customer_{customer.id}"
        ):

            col1, col2 = st.columns(2)

            with col1:

                name = st.text_input(
                    "Customer Name *",
                    value=customer.name or "",
                )

                contact_person = st.text_input(
                    "Contact Person",
                    value=getattr(
                        customer,
                        "contact_person",
                        "",
                    ) or "",
                )

                phone = st.text_input(
                    "Phone Number",
                    value=customer.phone or "",
                )

                email = st.text_input(
                    "Email",
                    value=customer.email or "",
                )

            with col2:

                customer_types = [
                    "Retail",
                    "Wholesale",
                    "Distributor",
                    "Corporate",
                    "Institution",
                    "Export",
                    "Other",
                ]

                current_type = getattr(
                    customer,
                    "customer_type",
                    "Retail",
                ) or "Retail"

                if current_type not in customer_types:
                    customer_types.append(
                        current_type
                    )

                customer_type = st.selectbox(
                    "Customer Type",
                    customer_types,
                    index=customer_types.index(
                        current_type
                    ),
                )

                location = st.text_input(
                    "Location",
                    value=getattr(
                        customer,
                        "location",
                        "",
                    ) or "",
                )

                country = st.text_input(
                    "Country",
                    value=getattr(
                        customer,
                        "country",
                        "",
                    ) or "",
                )

            address = st.text_area(
                "Address",
                value=customer.address or "",
            )

            update_button = st.form_submit_button(
                "💾 Update Customer",
                use_container_width=True,
            )

        if update_button:

            if not name.strip():

                st.error(
                    "Customer name is required."
                )

                return

            try:

                updated = update_customer(
                    customer_id=customer.id,
                    name=name,
                    phone=phone,
                    email=email,
                    address=address,
                    customer_type=customer_type,
                    location=location,
                    country=country,
                    contact_person=contact_person,
                )

                if updated:

                    st.success(
                        f"Customer '{updated.name}' "
                        "updated successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Customer not found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to update customer: {e}"
                )


    # ==================================================
    # STATUS
    # ==================================================

    with status_tab:

        if active:

            st.success(
                "This customer is currently active."
            )

            if st.button(
                "🔴 Deactivate Customer",
                use_container_width=True,
            ):

                try:

                    updated = set_customer_status(
                        customer.id,
                        False,
                    )

                    if updated:

                        st.success(
                            "Customer deactivated."
                        )

                        st.rerun()

                except Exception as e:

                    st.error(
                        f"Unable to change status: {e}"
                    )

        else:

            st.warning(
                "This customer is currently inactive."
            )

            if st.button(
                "🟢 Activate Customer",
                use_container_width=True,
            ):

                try:

                    updated = set_customer_status(
                        customer.id,
                        True,
                    )

                    if updated:

                        st.success(
                            "Customer activated."
                        )

                        st.rerun()

                except Exception as e:

                    st.error(
                        f"Unable to change status: {e}"
                    )


    # ==================================================
    # DELETE
    # ==================================================

    with delete_tab:

        st.warning(
            "Deleting a customer is permanent."
        )

        confirm_delete = st.checkbox(
            "I understand that this customer will be permanently deleted."
        )

        if st.button(
            "🗑️ Delete Customer",
            use_container_width=True,
            disabled=not confirm_delete,
        ):

            try:

                deleted = delete_customer(
                    customer.id
                )

                if deleted:

                    st.success(
                        "Customer deleted successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Customer could not be found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to delete customer: {e}"
                )


# ==================================================
# STANDALONE EXECUTION
# ==================================================

if __name__ == "__main__":
    customers_page()