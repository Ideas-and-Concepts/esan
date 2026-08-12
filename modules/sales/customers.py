"""
Esan ERP
Sales & Distribution - Customers

Customer management interface.
"""

import streamlit as st

from database import SessionLocal

from services.customer_service import (
    get_all_customers,
    get_customer,
    create_customer,
    update_customer,
    delete_customer,
)


def customers_page():

    st.subheader("👥 Customers")
    st.caption(
        "Manage customers for Sales & Distribution."
    )

    db = SessionLocal()

    try:

        # ==================================================
        # TABS
        # ==================================================

        tab_create, tab_view, tab_edit, tab_delete = st.tabs(
            [
                "➕ Create",
                "📋 View",
                "✏️ Edit",
                "🗑️ Delete",
            ]
        )

        # ==================================================
        # CREATE
        # ==================================================

        with tab_create:

            st.markdown("### Create Customer")

            with st.form("create_customer_form"):

                name = st.text_input(
                    "Customer Name *"
                )

                customer_type = st.selectbox(
                    "Customer Type",
                    [
                        "Retail",
                        "Wholesale",
                        "Distributor",
                        "Corporate",
                        "Other",
                    ],
                )

                phone = st.text_input(
                    "Phone"
                )

                email = st.text_input(
                    "Email"
                )

                address = st.text_area(
                    "Address"
                )

                submitted = st.form_submit_button(
                    "Create Customer",
                    use_container_width=True,
                    type="primary",
                )

                if submitted:

                    if not name.strip():

                        st.error(
                            "Customer name is required."
                        )

                    else:

                        try:

                            customer = create_customer(
                                db=db,
                                name=name,
                                phone=phone,
                                email=email,
                                address=address,
                                customer_type=customer_type,
                            )

                            st.success(
                                f"Customer '{customer.name}' created successfully."
                            )

                            st.rerun()

                        except Exception as e:

                            db.rollback()

                            st.error(
                                f"Unable to create customer: {e}"
                            )

        # ==================================================
        # VIEW
        # ==================================================

        with tab_view:

            st.markdown("### Customer Directory")

            customers = get_all_customers(db)

            if not customers:

                st.info(
                    "No customers have been registered yet."
                )

            else:

                rows = []

                for customer in customers:

                    rows.append(
                        {
                            "ID": customer.id,
                            "Name": customer.name,
                            "Type": customer.customer_type,
                            "Phone": customer.phone or "",
                            "Email": customer.email or "",
                            "Address": customer.address or "",
                        }
                    )

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

        # ==================================================
        # EDIT
        # ==================================================

        with tab_edit:

            st.markdown("### Edit Customer")

            customers = get_all_customers(db)

            if not customers:

                st.info(
                    "There are no customers to edit."
                )

            else:

                customer_options = {
                    f"{customer.id} - {customer.name}":
                    customer.id
                    for customer in customers
                }

                selected_label = st.selectbox(
                    "Select Customer",
                    list(customer_options.keys()),
                )

                selected_id = customer_options[
                    selected_label
                ]

                customer = get_customer(
                    db,
                    selected_id,
                )

                if customer:

                    with st.form(
                        "edit_customer_form"
                    ):

                        name = st.text_input(
                            "Customer Name *",
                            value=customer.name or "",
                        )

                        customer_types = [
                            "Retail",
                            "Wholesale",
                            "Distributor",
                            "Corporate",
                            "Other",
                        ]

                        current_type = (
                            customer.customer_type
                            if customer.customer_type
                            in customer_types
                            else "Retail"
                        )

                        customer_type = st.selectbox(
                            "Customer Type",
                            customer_types,
                            index=customer_types.index(
                                current_type
                            ),
                        )

                        phone = st.text_input(
                            "Phone",
                            value=customer.phone or "",
                        )

                        email = st.text_input(
                            "Email",
                            value=customer.email or "",
                        )

                        address = st.text_area(
                            "Address",
                            value=customer.address or "",
                        )

                        submitted = st.form_submit_button(
                            "Save Changes",
                            use_container_width=True,
                            type="primary",
                        )

                        if submitted:

                            if not name.strip():

                                st.error(
                                    "Customer name is required."
                                )

                            else:

                                try:

                                    update_customer(
                                        db=db,
                                        customer_id=selected_id,
                                        name=name,
                                        phone=phone,
                                        email=email,
                                        address=address,
                                        customer_type=customer_type,
                                    )

                                    st.success(
                                        "Customer updated successfully."
                                    )

                                    st.rerun()

                                except Exception as e:

                                    db.rollback()

                                    st.error(
                                        f"Unable to update customer: {e}"
                                    )

        # ==================================================
        # DELETE
        # ==================================================

        with tab_delete:

            st.markdown("### Delete Customer")

            customers = get_all_customers(db)

            if not customers:

                st.info(
                    "There are no customers to delete."
                )

            else:

                customer_options = {
                    f"{customer.id} - {customer.name}":
                    customer.id
                    for customer in customers
                }

                selected_label = st.selectbox(
                    "Select Customer",
                    list(customer_options.keys()),
                    key="delete_customer_select",
                )

                selected_id = customer_options[
                    selected_label
                ]

                customer = get_customer(
                    db,
                    selected_id,
                )

                if customer:

                    st.warning(
                        f"You are about to delete "
                        f"**{customer.name}**."
                    )

                    st.caption(
                        "Only delete customers that have no "
                        "dependent sales transactions."
                    )

                    confirm = st.checkbox(
                        "I understand that this action cannot be undone.",
                        key="confirm_customer_delete",
                    )

                    if st.button(
                        "🗑️ Delete Customer",
                        disabled=not confirm,
                        use_container_width=True,
                        type="secondary",
                    ):

                        try:

                            deleted = delete_customer(
                                db,
                                selected_id,
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

                            db.rollback()

                            st.error(
                                "Customer cannot be deleted "
                                "because it may have related "
                                f"transactions.\n\n{e}"
                            )

    finally:

        db.close()