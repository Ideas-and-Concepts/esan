"""
Esan ERP - Purchases Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

This module manages completed/active purchases using the
existing PurchaseOrder database model.

Functions:
- View purchases
- Create purchase
- Edit purchase
- Delete purchase
- Update purchase status
"""

import streamlit as st
import pandas as pd

from services.procurement_service import (
    get_all_purchase_orders,
    create_purchase_order,
    update_purchase_order,
    delete_purchase_order,
    update_purchase_order_status,
    get_all_suppliers,
)


# ==================================================
# PURCHASE STATUS OPTIONS
# ==================================================

PURCHASE_STATUSES = [
    "Draft",
    "Pending Approval",
    "Approved",
    "Ordered",
    "Partially Received",
    "Received",
    "Cancelled",
]


# ==================================================
# MAIN PAGE
# ==================================================

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


# ==================================================
# CREATE PURCHASE
# ==================================================

def create_purchase_form():

    st.subheader("Create New Purchase")

    suppliers = get_all_suppliers()

    if not suppliers:
        st.warning(
            "No suppliers are registered yet. "
            "Please register a supplier first."
        )
        return

    supplier_options = {
        f"{supplier.name} | "
        f"{supplier.phone or 'No phone'}": supplier.id
        for supplier in suppliers
    }

    selected_supplier = st.selectbox(
        "Supplier",
        list(supplier_options.keys()),
        key="purchase_supplier",
    )

    supplier_id = supplier_options[selected_supplier]

    st.markdown("### Purchase Items")

    item_count = st.number_input(
        "Number of Items",
        min_value=1,
        max_value=20,
        value=1,
        step=1,
        key="purchase_item_count",
    )

    items_data = []
    total_amount = 0.0

    for i in range(int(item_count)):

        st.markdown(f"#### Item {i + 1}")

        col1, col2, col3 = st.columns([3, 1, 1])

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

        item_total = quantity * unit_price
        total_amount += item_total

        st.write(
            f"Item Total: **UGX {item_total:,.2f}**"
        )

        if product_name.strip():

            items_data.append(
                {
                    "product_name": product_name.strip(),
                    "quantity": quantity,
                    "unit_price": unit_price,
                }
            )

    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        status = st.selectbox(
            "Purchase Status",
            PURCHASE_STATUSES,
            index=0,
            key="purchase_status",
        )

    with col2:
        st.metric(
            "Total Purchase",
            f"UGX {total_amount:,.2f}",
        )

    if st.button(
        "💾 Save Purchase",
        type="primary",
        use_container_width=True,
    ):

        if not items_data:
            st.error(
                "Please enter at least one product or raw material."
            )
            return

        for item in items_data:

            if item["quantity"] <= 0:
                st.error(
                    f"Quantity for "
                    f"{item['product_name']} "
                    "must be greater than zero."
                )
                return

            if item["unit_price"] < 0:
                st.error(
                    f"Unit price for "
                    f"{item['product_name']} "
                    "cannot be negative."
                )
                return

        try:

            purchase = create_purchase_order(
                supplier_id=supplier_id,
                items_data=items_data,
                status=status,
            )

            st.success(
                f"Purchase {purchase.po_number} "
                "created successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to create purchase: {e}"
            )


# ==================================================
# VIEW PURCHASES
# ==================================================

def view_purchases():

    st.subheader("Purchase Records")

    purchases = get_all_purchase_orders()

    if not purchases:

        st.info(
            "No purchases have been recorded yet."
        )

        return

    data = []

    for purchase in purchases:

        supplier_name = (
            purchase.supplier.name
            if purchase.supplier
            else "Unknown Supplier"
        )

        data.append(
            {
                "ID": purchase.id,
                "Purchase No.": purchase.po_number,
                "Supplier": supplier_name,
                "Status": purchase.status,
                "Total": (
                    f"UGX "
                    f"{purchase.total_amount:,.2f}"
                ),
                "Date": (
                    purchase.created_at.strftime(
                        "%Y-%m-%d"
                    )
                    if purchase.created_at
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

    # ==================================================
    # MANAGEMENT
    # ==================================================

    st.subheader("⚙️ Purchase Management")

    purchase_options = {
        f"{purchase.po_number} | "
        f"{purchase.supplier.name if purchase.supplier else 'Unknown Supplier'}":
            purchase.id
        for purchase in purchases
    }

    selected_purchase = st.selectbox(
        "Select Purchase",
        list(purchase_options.keys()),
        key="selected_purchase",
    )

    purchase_id = purchase_options[selected_purchase]

    action = st.radio(
        "Action",
        [
            "Update Status",
            "Edit Purchase",
            "Delete Purchase",
        ],
        horizontal=True,
    )

    # ==================================================
    # UPDATE STATUS
    # ==================================================

    if action == "Update Status":

        new_status = st.selectbox(
            "New Status",
            PURCHASE_STATUSES,
            key="purchase_new_status",
        )

        if st.button(
            "🔄 Update Status",
            use_container_width=True,
        ):

            try:

                updated = update_purchase_order_status(
                    purchase_id,
                    new_status,
                )

                if updated:

                    st.success(
                        f"{updated.po_number} "
                        f"status updated to "
                        f"{updated.status}."
                    )

                    st.rerun()

                else:
                    st.error(
                        "Purchase not found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to update status: {e}"
                )

    # ==================================================
    # EDIT PURCHASE
    # ==================================================

    elif action == "Edit Purchase":

        selected = next(
            (
                purchase
                for purchase in purchases
                if purchase.id == purchase_id
            ),
            None,
        )

        if not selected:
            st.error("Purchase not found.")
            return

        st.markdown("### Edit Purchase")

        supplier_options_edit = {
            f"{supplier.name} | "
            f"{supplier.phone or 'No phone'}": supplier.id
            for supplier in suppliers
        }

        current_supplier_label = next(
            (
                label
                for label, sid
                in supplier_options_edit.items()
                if sid == selected.supplier_id
            ),
            list(supplier_options_edit.keys())[0],
        )

        edit_supplier = st.selectbox(
            "Supplier",
            list(supplier_options_edit.keys()),
            index=list(
                supplier_options_edit.keys()
            ).index(current_supplier_label),
            key="edit_purchase_supplier",
        )

        edit_supplier_id = supplier_options_edit[
            edit_supplier
        ]

        edit_status = st.selectbox(
            "Status",
            PURCHASE_STATUSES,
            index=(
                PURCHASE_STATUSES.index(selected.status)
                if selected.status in PURCHASE_STATUSES
                else 0
            ),
            key="edit_purchase_status",
        )

        if st.button(
            "💾 Save Changes",
            type="primary",
            use_container_width=True,
        ):

            try:

                updated = update_purchase_order(
                    po_id=purchase_id,
                    supplier_id=edit_supplier_id,
                    status=edit_status,
                )

                if updated:

                    st.success(
                        f"{updated.po_number} "
                        "updated successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Purchase not found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to update purchase: {e}"
                )

    # ==================================================
    # DELETE PURCHASE
    # ==================================================

    elif action == "Delete Purchase":

        st.warning(
            "⚠️ Deleting a purchase will also remove "
            "its purchase items."
        )

        confirm_delete = st.checkbox(
            "I understand that this action cannot be undone.",
            key="confirm_purchase_delete",
        )

        if st.button(
            "🗑️ Delete Purchase",
            type="secondary",
            use_container_width=True,
            disabled=not confirm_delete,
        ):

            try:

                deleted = delete_purchase_order(
                    purchase_id
                )

                if deleted:

                    st.success(
                        "Purchase deleted successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Purchase not found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to delete purchase: {e}"
                )


# ==================================================
# STANDALONE
# ==================================================

if __name__ == "__main__":
    purchases_page()