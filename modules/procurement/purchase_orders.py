"""
Esan ERP - Procurement Purchase Orders Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:
- Create Purchase Orders
- Select suppliers
- Add multiple purchase order items
- Calculate purchase order totals
- View purchase orders
- Edit purchase orders
- Delete purchase orders
- Update purchase order status
- View purchase order details
- Safe SQLAlchemy session handling
"""

import streamlit as st
import pandas as pd

from services.procurement_service import (
    get_all_suppliers,
    get_all_purchase_orders,
    create_purchase_order,
    update_purchase_order_status,
    update_purchase_order,
    delete_purchase_order,
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
        f"{supplier.name} | {supplier.phone or 'No phone'}": supplier.id
        for supplier in suppliers
    }

    selected_supplier = st.selectbox(
        "Supplier",
        options=list(supplier_options.keys()),
        key="create_po_supplier",
    )

    supplier_id = supplier_options[selected_supplier]

    st.markdown("### Purchase Order Items")

    item_count = st.number_input(
        "Number of Items",
        min_value=1,
        max_value=20,
        value=1,
        step=1,
        key="create_po_item_count",
    )

    items_data = []
    total_amount = 0.0

    for i in range(int(item_count)):

        st.markdown(f"#### Item {i + 1}")

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            product_name = st.text_input(
                "Product / Raw Material",
                key=f"create_po_product_{i}",
                placeholder="e.g. Maize Grain",
            )

        with col2:
            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                step=0.1,
                key=f"create_po_quantity_{i}",
            )

        with col3:
            unit_price = st.number_input(
                "Unit Price",
                min_value=0.0,
                step=100.0,
                key=f"create_po_price_{i}",
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
            PO_STATUSES[:4],
            key="create_po_status",
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
        key="create_purchase_order_button",
    )

    if not submitted:
        return

    # ----------------------------------------------
    # VALIDATION
    # ----------------------------------------------

    if not items_data:

        st.error(
            "Please enter at least one product or raw material."
        )

        return

    for item in items_data:

        if item["quantity"] <= 0:

            st.error(
                f"Quantity for {item['product_name']} "
                "must be greater than zero."
            )

            return

        if item["unit_price"] < 0:

            st.error(
                f"Unit price for {item['product_name']} "
                "cannot be negative."
            )

            return

    # ----------------------------------------------
    # CREATE
    # ----------------------------------------------

    try:

        purchase_order = create_purchase_order(
            supplier_id=supplier_id,
            items_data=items_data,
            status=status,
        )

        po_number = getattr(
            purchase_order,
            "po_number",
            "Purchase Order",
        )

        st.success(
            f"Purchase Order {po_number} "
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

        # IMPORTANT:
        # Do NOT access po.supplier here.
        #
        # The service layer should provide supplier_name
        # while the SQLAlchemy session is active.

        supplier_name = getattr(
            po,
            "supplier_name",
            None,
        )

        if not supplier_name:

            supplier_name = "Unknown Supplier"

        data.append(
            {
                "ID": po.id,
                "PO Number": po.po_number,
                "Supplier": supplier_name,
                "Status": po.status,
                "Total": f"UGX {po.total_amount or 0:,.2f}",
                "Created": (
                    po.created_at.strftime("%Y-%m-%d")
                    if po.created_at
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
    # VIEW DETAILS
    # ==================================================

    st.subheader("👁️ Purchase Order Details")

    po_options = {
        f"{po.po_number} | "
        f"{getattr(po, 'supplier_name', 'Unknown Supplier')}":
            po.id
        for po in purchase_orders
    }

    selected_po_label = st.selectbox(
        "Select Purchase Order",
        options=list(po_options.keys()),
        key="view_po_selection",
    )

    selected_po_id = po_options[selected_po_label]

    selected_po = next(
        (
            po
            for po in purchase_orders
            if po.id == selected_po_id
        ),
        None,
    )

    if selected_po:

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "PO Number",
                selected_po.po_number,
            )

        with col2:
            st.metric(
                "Status",
                selected_po.status,
            )

        with col3:
            st.metric(
                "Total",
                f"UGX {selected_po.total_amount or 0:,.2f}",
            )

        st.write(
            f"**Supplier:** "
            f"{getattr(selected_po, 'supplier_name', 'Unknown Supplier')}"
        )

        st.write(
            f"**Created:** "
            f"{selected_po.created_at.strftime('%Y-%m-%d %H:%M') "
            if selected_po.created_at
            else 'N/A'}"
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

    po_options = {
        f"{po.po_number} | "
        f"{getattr(po, 'supplier_name', 'Unknown Supplier')}":
            po.id
        for po in purchase_orders
    }

    selected_label = st.selectbox(
        "Purchase Order",
        list(po_options.keys()),
        key="manage_po_selection",
    )

    selected_id = po_options[selected_label]

    selected_po = next(
        (
            po
            for po in purchase_orders
            if po.id == selected_id
        ),
        None,
    )

    if not selected_po:
        st.error("Purchase Order could not be found.")
        return

    st.divider()

    edit_tab, status_tab, delete_tab = st.tabs(
        [
            "✏️ Edit",
            "🔄 Status",
            "🗑️ Delete",
        ]
    )

    # ==================================================
    # EDIT PURCHASE ORDER
    # ==================================================

    with edit_tab:

        st.markdown("### ✏️ Edit Purchase Order")

        suppliers = get_all_suppliers()

        if not suppliers:

            st.warning(
                "No suppliers are available."
            )

        else:

            supplier_options = {
                f"{supplier.name} | "
                f"{supplier.phone or 'No phone'}":
                    supplier.id
                for supplier in suppliers
            }

            current_supplier_id = getattr(
                selected_po,
                "supplier_id",
                None,
            )

            supplier_labels = list(
                supplier_options.keys()
            )

            current_supplier_index = 0

            for index, supplier_label in enumerate(
                supplier_labels
            ):

                if supplier_options[supplier_label] == current_supplier_id:
                    current_supplier_index = index
                    break

            selected_supplier = st.selectbox(
                "Supplier",
                supplier_labels,
                index=current_supplier_index,
                key="edit_po_supplier",
            )

            new_supplier_id = supplier_options[
                selected_supplier
            ]

            new_status = st.selectbox(
                "Status",
                PO_STATUSES,
                index=(
                    PO_STATUSES.index(selected_po.status)
                    if selected_po.status in PO_STATUSES
                    else 0
                ),
                key="edit_po_status",
            )

            new_total = st.number_input(
                "Purchase Order Total",
                min_value=0.0,
                value=float(
                    selected_po.total_amount or 0
                ),
                step=100.0,
                key="edit_po_total",
            )

            save_edit = st.button(
                "💾 Save Changes",
                type="primary",
                use_container_width=True,
                key="save_po_changes",
            )

            if save_edit:

                try:

                    updated = update_purchase_order(
                        purchase_order_id=selected_po.id,
                        supplier_id=new_supplier_id,
                        total_amount=new_total,
                        status=new_status,
                    )

                    if updated:

                        st.success(
                            f"{selected_po.po_number} "
                            "updated successfully."
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

    # ==================================================
    # STATUS
    # ==================================================

    with status_tab:

        st.markdown(
            "### 🔄 Change Purchase Order Status"
        )

        new_status = st.selectbox(
            "New Status",
            PO_STATUSES,
            index=(
                PO_STATUSES.index(selected_po.status)
                if selected_po.status in PO_STATUSES
                else 0
            ),
            key="manage_po_new_status",
        )

        if st.button(
            "🔄 Update Status",
            type="primary",
            use_container_width=True,
            key="manage_po_status_button",
        ):

            try:

                updated_po = update_purchase_order_status(
                    selected_po.id,
                    new_status,
                )

                if updated_po:

                    st.success(
                        f"{selected_po.po_number} "
                        f"status changed to {new_status}."
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

    # ==================================================
    # DELETE
    # ==================================================

    with delete_tab:

        st.markdown(
            "### 🗑️ Delete Purchase Order"
        )

        st.warning(
            "Deleting a Purchase Order is permanent. "
            "Its purchase order items will also be removed."
        )

        confirm_delete = st.checkbox(
            "I understand that this action cannot be undone.",
            key="confirm_delete_po",
        )

        if st.button(
            "🗑️ Delete Purchase Order",
            type="secondary",
            use_container_width=True,
            disabled=not confirm_delete,
            key="delete_po_button",
        ):

            try:

                deleted = delete_purchase_order(
                    selected_po.id
                )

                if deleted:

                    st.success(
                        f"{selected_po.po_number} "
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