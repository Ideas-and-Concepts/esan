"""
Esan ERP Purchases Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:
- View purchases
- Create purchases
- Update purchase status
- Delete purchases
"""

import streamlit as st
import pandas as pd

from services.procurement_service import (
    get_all_suppliers,
    get_all_purchases,
    create_purchase,
    update_purchase_status,
    delete_purchase,
)


def purchases_page():

    st.title("🛒 Purchase Management")

    tab1, tab2 = st.tabs(
        [
            "➕ New Purchase",
            "📋 Purchases",
        ]
    )

    with tab1:
        create_purchase_form()

    with tab2:
        view_purchases()


def create_purchase_form():

    st.subheader("Create New Purchase")

    suppliers = get_all_suppliers()

    if not suppliers:
        st.warning(
            "No suppliers are registered. "
            "Please add a supplier first."
        )
        return

    supplier_options = {
        f"{supplier.name} | "
        f"{supplier.phone or 'No phone'}":
        supplier.id
        for supplier in suppliers
    }

    selected_supplier = st.selectbox(
        "Supplier",
        list(supplier_options.keys()),
    )

    supplier_id = supplier_options[
        selected_supplier
    ]

    st.markdown("### Purchase Items")

    item_count = st.number_input(
        "Number of Items",
        min_value=1,
        max_value=20,
        value=1,
        step=1,
    )

    items = []
    total_amount = 0.0

    for i in range(int(item_count)):

        st.markdown(
            f"#### Item {i + 1}"
        )

        col1, col2, col3 = st.columns(
            [3, 1, 1]
        )

        with col1:
            product_name = st.text_input(
                "Product / Raw Material",
                key=f"purchase_product_{i}",
                placeholder="e.g. Maize Grain",
            )

        with col2:
            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                step=0.1,
                key=f"purchase_quantity_{i}",
            )

        with col3:
            unit_price = st.number_input(
                "Unit Price",
                min_value=0.0,
                step=100.0,
                key=f"purchase_price_{i}",
            )

        item_total = (
            quantity * unit_price
        )

        st.write(
            f"Item Total: "
            f"**UGX {item_total:,.2f}**"
        )

        total_amount += item_total

        if product_name.strip():

            items.append(
                {
                    "product_name":
                        product_name.strip(),
                    "quantity":
                        quantity,
                    "unit_price":
                        unit_price,
                }
            )

    st.divider()

    status = st.selectbox(
        "Purchase Status",
        [
            "Draft",
            "Pending Approval",
            "Approved",
            "Ordered",
            "Received",
        ],
    )

    st.metric(
        "Total Purchase",
        f"UGX {total_amount:,.2f}",
    )

    if st.button(
        "💾 Save Purchase",
        type="primary",
        use_container_width=True,
    ):

        if not items:
            st.error(
                "Please enter at least one product."
            )
            return

        for item in items:

            if item["quantity"] <= 0:
                st.error(
                    f"Quantity for "
                    f"{item['product_name']} "
                    f"must be greater than zero."
                )
                return

        try:

            purchase = create_purchase(
                supplier_id=supplier_id,
                items_data=items,
                status=status,
            )

            st.success(
                f"Purchase "
                f"{purchase['po_number']} "
                f"created successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to create purchase: {e}"
            )


def view_purchases():

    st.subheader("Purchase Records")

    purchases = get_all_purchases()

    if not purchases:

        st.info(
            "No purchases have been recorded yet."
        )
        return

    data = []

    for purchase in purchases:

        data.append(
            {
                "ID":
                    purchase["id"],

                "Purchase No.":
                    purchase["po_number"],

                "Supplier":
                    purchase["supplier_name"],

                "Status":
                    purchase["status"],

                "Total":
                    f"UGX "
                    f"{purchase['total_amount']:,.2f}",

                "Created":
                    (
                        purchase["created_at"]
                        .strftime("%Y-%m-%d")
                        if purchase["created_at"]
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

    st.divider()

    st.subheader(
        "🔄 Purchase Management"
    )

    purchase_options = {
        f"{purchase['po_number']} | "
        f"{purchase['supplier_name']}":
        purchase["id"]
        for purchase in purchases
    }

    selected_purchase = st.selectbox(
        "Select Purchase",
        list(purchase_options.keys()),
    )

    selected_id = purchase_options[
        selected_purchase
    ]

    col1, col2 = st.columns(2)

    with col1:

        new_status = st.selectbox(
            "Status",
            [
                "Draft",
                "Pending Approval",
                "Approved",
                "Ordered",
                "Partially Received",
                "Received",
                "Cancelled",
            ],
        )

        if st.button(
            "🔄 Update Status",
            use_container_width=True,
        ):

            try:

                result = update_purchase_status(
                    selected_id,
                    new_status,
                )

                if result:

                    st.success(
                        f"{result['po_number']} "
                        f"updated to "
                        f"{result['status']}."
                    )

                    st.rerun()

            except Exception as e:

                st.error(
                    f"Unable to update purchase: {e}"
                )

    with col2:

        st.warning(
            "Deleting a purchase cannot be undone."
        )

        if st.button(
            "🗑️ Delete Purchase",
            use_container_width=True,
        ):

            try:

                deleted = delete_purchase(
                    selected_id
                )

                if deleted:

                    st.success(
                        "Purchase deleted successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Purchase was not found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to delete purchase: {e}"
                )


if __name__ == "__main__":
    purchases_page()