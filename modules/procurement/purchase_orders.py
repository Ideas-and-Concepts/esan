"""
Esan ERP - Procurement Purchase Orders Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:
- Create Purchase Orders
- View Purchase Orders
- Edit Purchase Orders
- Delete Purchase Orders
- Update Purchase Order Status
- Select suppliers
- Add multiple purchase order items
- Calculate purchase order totals
"""

import streamlit as st
import pandas as pd

from services.procurement_service import (
    get_all_suppliers,
    get_all_purchase_orders,
    create_purchase_order,
    update_purchase_order,
    delete_purchase_order,
    update_purchase_order_status,
)


# ==================================================
# CONSTANTS
# ==================================================

PO_STATUSES = [
    "Draft",
    "Pending Approval",
    "Approved",
    "Ordered",
    "Partially Received",
    "Received",
    "Cancelled",
]


# ==================================================
# MAIN PURCHASE ORDERS PAGE
# ==================================================

def purchase_orders_page():

    st.title("📄 Purchase Order Management")

    tab1, tab2, tab3 = st.tabs(
        [
            "➕ Create Purchase Order",
            "📋 Purchase Orders",
            "⚙️ Manage Purchase Orders",
        ]
    )

    with tab1:
        create_po_form()

    with tab2:
        view_purchase_orders()

    with tab3:
        manage_purchase_orders()


# ==================================================
# CREATE PURCHASE ORDER
# ==================================================

def create_po_form():

    st.subheader("Create New Purchase Order")

    suppliers = get_all_suppliers()

    if not suppliers:
        st.warning(
            "No suppliers are registered yet. "
            "Please register a supplier before creating a purchase order."
        )
        return

    supplier_options = {
        f"{supplier.name} | {supplier.phone or 'No phone'}":
        supplier.id
        for supplier in suppliers
    }

    selected_supplier = st.selectbox(
        "Supplier",
        options=list(supplier_options.keys()),
    )

    supplier_id = supplier_options[selected_supplier]

    st.markdown("### Purchase Order Items")

    item_count = st.number_input(
        "Number of Items",
        min_value=1,
        max_value=20,
        value=1,
        step=1,
    )

    items_data = []

    total_amount = 0.0

    for i in range(int(item_count)):

        st.markdown(f"#### Item {i + 1}")

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:

            product_name = st.text_input(
                "Product / Raw Material",
                key=f"po_product_{i}",
                placeholder="e.g. Maize Grain",
            )

        with col2:

            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                step=0.1,
                key=f"po_quantity_{i}",
            )

        with col3:

            unit_price = st.number_input(
                "Unit Price",
                min_value=0.0,
                step=100.0,
                key=f"po_price_{i}",
            )

        item_total = quantity * unit_price

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

        total_amount += item_total

    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:

        status = st.selectbox(
            "Purchase Order Status",
            PO_STATUSES,
        )

    with col2:

        st.metric(
            "Total Purchase Order",
            f"UGX {total_amount:,.2f}",
        )

    submitted = st.button(
        "💾 Create Purchase Order",
        type="primary",
        use_container_width=True,
    )

    if submitted:

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

            purchase_order = create_purchase_order(
                supplier_id=supplier_id,
                items_data=items_data,
                status=status,
            )

            st.success(
                f"Purchase Order "
                f"{purchase_order['po_number']} "
                "created successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to create Purchase Order: {e}"
            )


# ==================================================
# VIEW PURCHASE ORDERS
# ==================================================

def view_purchase_orders():

    st.subheader("📋 Purchase Orders")

    purchase_orders = get_all_purchase_orders()

    if not purchase_orders:

        st.info(
            "No purchase orders have been created yet."
        )

        return

    data = []

    for po in purchase_orders:

        data.append(
            {
                "ID": po["id"],
                "PO Number": po["po_number"],
                "Supplier": po.get(
                    "supplier_name",
                    "Unknown Supplier"
                ),
                "Status": po["status"],
                "Total": (
                    f"UGX "
                    f"{po['total_amount']:,.2f}"
                ),
                "Created": po.get(
                    "created_date",
                    ""
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
# MANAGE PURCHASE ORDERS
# ==================================================

def manage_purchase_orders():

    st.subheader("⚙️ Manage Purchase Orders")

    purchase_orders = get_all_purchase_orders()

    if not purchase_orders:

        st.info(
            "There are no purchase orders to manage."
        )

        return

    po_options = {}

    for po in purchase_orders:

        supplier_name = po.get(
            "supplier_name",
            "Unknown Supplier"
        )

        label = (
            f"{po['po_number']} | "
            f"{supplier_name} | "
            f"UGX {po['total_amount']:,.2f}"
        )

        po_options[label] = po

    selected_label = st.selectbox(
        "Select Purchase Order",
        list(po_options.keys()),
    )

    selected_po = po_options[selected_label]

    po_id = selected_po["id"]

    st.divider()

    # ==================================================
    # CURRENT DETAILS
    # ==================================================

    st.markdown("### 📄 Purchase Order Details")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "PO Number",
            selected_po["po_number"],
        )

    with col2:

        st.metric(
            "Supplier",
            selected_po.get(
                "supplier_name",
                "Unknown"
            ),
        )

    with col3:

        st.metric(
            "Current Status",
            selected_po["status"],
        )

    st.metric(
        "Current Total",
        f"UGX {selected_po['total_amount']:,.2f}",
    )

    st.divider()

    # ==================================================
    # EDIT PURCHASE ORDER
    # ==================================================

    st.markdown("### ✏️ Edit Purchase Order")

    suppliers = get_all_suppliers()

    if not suppliers:

        st.warning(
            "No suppliers available."
        )

        return

    supplier_options = {
        f"{supplier.name} | "
        f"{supplier.phone or 'No phone'}":
        supplier.id
        for supplier in suppliers
    }

    current_supplier_id = selected_po.get(
        "supplier_id"
    )

    supplier_labels = list(
        supplier_options.keys()
    )

    current_supplier_label = supplier_labels[0]

    for label, supplier_id in supplier_options.items():

        if supplier_id == current_supplier_id:

            current_supplier_label = label

            break

    edit_supplier_label = st.selectbox(
        "Supplier",
        supplier_labels,
        index=supplier_labels.index(
            current_supplier_label
        ),
        key=f"edit_supplier_{po_id}",
    )

    edit_supplier_id = supplier_options[
        edit_supplier_label
    ]

    st.markdown("#### Purchase Order Items")

    existing_items = selected_po.get(
        "items",
        []
    )

    if not existing_items:

        st.info(
            "This purchase order has no item details."
        )

        existing_items = [
            {
                "product_name": "",
                "quantity": 0.0,
                "unit_price": 0.0,
            }
        ]

    edited_items = []

    edit_total = 0.0

    for index, item in enumerate(existing_items):

        col1, col2, col3 = st.columns(
            [3, 1, 1]
        )

        with col1:

            product_name = st.text_input(
                "Product / Raw Material",
                value=item.get(
                    "product_name",
                    ""
                ),
                key=f"edit_product_{po_id}_{index}",
            )

        with col2:

            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                value=float(
                    item.get(
                        "quantity",
                        0
                    )
                ),
                step=0.1,
                key=f"edit_quantity_{po_id}_{index}",
            )

        with col3:

            unit_price = st.number_input(
                "Unit Price",
                min_value=0.0,
                value=float(
                    item.get(
                        "unit_price",
                        0
                    )
                ),
                step=100.0,
                key=f"edit_price_{po_id}_{index}",
            )

        item_total = quantity * unit_price

        edit_total += item_total

        if product_name.strip():

            edited_items.append(
                {
                    "product_name":
                        product_name.strip(),

                    "quantity":
                        quantity,

                    "unit_price":
                        unit_price,
                }
            )

    st.metric(
        "Updated Total",
        f"UGX {edit_total:,.2f}",
    )

    edit_status = st.selectbox(
        "Status",
        PO_STATUSES,
        index=(
            PO_STATUSES.index(
                selected_po["status"]
            )
            if selected_po["status"]
            in PO_STATUSES
            else 0
        ),
        key=f"edit_status_{po_id}",
    )

    if st.button(
        "💾 Save Changes",
        type="primary",
        use_container_width=True,
        key=f"save_po_{po_id}",
    ):

        if not edited_items:

            st.error(
                "At least one purchase order item is required."
            )

            return

        for item in edited_items:

            if item["quantity"] <= 0:

                st.error(
                    f"Quantity for "
                    f"{item['product_name']} "
                    "must be greater than zero."
                )

                return

        try:

            updated_po = update_purchase_order(
                po_id=po_id,
                supplier_id=edit_supplier_id,
                items_data=edited_items,
                status=edit_status,
            )

            if updated_po:

                st.success(
                    "Purchase Order updated successfully."
                )

                st.rerun()

            else:

                st.error(
                    "Purchase Order could not be found."
                )

        except Exception as e:

            st.error(
                f"Unable to update Purchase Order: {e}"
            )

    st.divider()

    # ==================================================
    # STATUS MANAGEMENT
    # ==================================================

    st.markdown(
        "### 🔄 Change Purchase Order Status"
    )

    status_col1, status_col2 = st.columns(
        [2, 1]
    )

    with status_col1:

        new_status = st.selectbox(
            "New Status",
            PO_STATUSES,
            index=(
                PO_STATUSES.index(
                    selected_po["status"]
                )
                if selected_po["status"]
                in PO_STATUSES
                else 0
            ),
            key=f"status_change_{po_id}",
        )

    with status_col2:

        st.write("")
        st.write("")

        if st.button(
            "🔄 Update Status",
            use_container_width=True,
            key=f"update_status_{po_id}",
        ):

            try:

                updated_po = update_purchase_order_status(
                    po_id,
                    new_status,
                )

                if updated_po:

                    st.success(
                        f"Purchase Order "
                        f"{selected_po['po_number']} "
                        f"changed to "
                        f"{new_status}."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Purchase Order not found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to update status: {e}"
                )

    st.divider()

    # ==================================================
    # DELETE PURCHASE ORDER
    # ==================================================

    st.markdown(
        "### 🗑️ Delete Purchase Order"
    )

    st.warning(
        "Deleting a purchase order is permanent. "
        "The purchase order and its items will be removed."
    )

    confirm_delete = st.checkbox(
        "I understand that this action cannot be undone.",
        key=f"confirm_delete_{po_id}",
    )

    if confirm_delete:

        if st.button(
            "🗑️ Delete Purchase Order",
            type="secondary",
            use_container_width=True,
            key=f"delete_po_{po_id}",
        ):

            try:

                deleted = delete_purchase_order(
                    po_id
                )

                if deleted:

                    st.success(
                        f"Purchase Order "
                        f"{selected_po['po_number']} "
                        "deleted successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Purchase Order not found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to delete Purchase Order: {e}"
                )


# ==================================================
# STANDALONE EXECUTION
# ==================================================

if __name__ == "__main__":

    purchase_orders_page()