"""
Esan ERP - Procurement Purchase Orders Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:
- Create Purchase Orders
- Edit Purchase Orders
- Delete Purchase Orders
- Select suppliers
- Add multiple items
- Calculate totals
- View purchase orders
- Update status
"""

import streamlit as st
import pandas as pd

from services.procurement_service import (
    get_all_suppliers,
    get_all_purchase_orders,
    create_purchase_order,
    update_purchase_order,
    update_purchase_order_status,
    delete_purchase_order,
)


# ==================================================
# MAIN PAGE
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
            "Please register a supplier first."
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

        st.markdown(
            f"#### Item {i + 1}"
        )

        col1, col2, col3 = st.columns(
            [3, 1, 1]
        )

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

        item_total = (
            quantity * unit_price
        )

        st.write(
            f"Item Total: "
            f"**UGX {item_total:,.2f}**"
        )

        total_amount += item_total

        if product_name.strip():

            items_data.append(
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

    col1, col2 = st.columns([2, 1])

    with col1:

        status = st.selectbox(
            "Purchase Order Status",
            [
                "Draft",
                "Pending Approval",
                "Approved",
                "Ordered",
            ],
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
                "Please enter at least one product."
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

            purchase_order = (
                create_purchase_order(
                    supplier_id=supplier_id,
                    items_data=items_data,
                    status=status,
                )
            )

            st.success(
                f"Purchase Order "
                f"{purchase_order.po_number} "
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

    purchase_orders = (
        get_all_purchase_orders()
    )

    if not purchase_orders:

        st.info(
            "No purchase orders have been created yet."
        )

        return

    data = []

    for po in purchase_orders:

        supplier_name = (
            po.supplier.name
            if po.supplier
            else "Unknown Supplier"
        )

        data.append(
            {
                "ID":
                    po.id,
                "PO Number":
                    po.po_number,
                "Supplier":
                    supplier_name,
                "Status":
                    po.status,
                "Total":
                    f"UGX {po.total_amount:,.2f}",
                "Created":
                    (
                        po.created_at.strftime(
                            "%Y-%m-%d"
                        )
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


# ==================================================
# MANAGE PURCHASE ORDERS
# ==================================================

def manage_purchase_orders():

    st.subheader(
        "⚙️ Manage Purchase Orders"
    )

    purchase_orders = (
        get_all_purchase_orders()
    )

    if not purchase_orders:

        st.info(
            "No purchase orders available."
        )

        return

    po_options = {
        f"{po.po_number} | "
        f"{po.supplier.name if po.supplier else 'Unknown Supplier'}":
            po.id
        for po in purchase_orders
    }

    selected_po = st.selectbox(
        "Select Purchase Order",
        list(po_options.keys()),
    )

    po_id = po_options[selected_po]

    current_po = next(
        (
            po
            for po in purchase_orders
            if po.id == po_id
        ),
        None,
    )

    if not current_po:

        st.error(
            "Purchase Order could not be found."
        )

        return

    action = st.radio(
        "Action",
        [
            "Edit Purchase Order",
            "Change Status",
            "Delete Purchase Order",
        ],
        horizontal=True,
    )

    # ==================================================
    # EDIT
    # ==================================================

    if action == "Edit Purchase Order":

        suppliers = get_all_suppliers()

        supplier_options = {
            f"{supplier.name} | "
            f"{supplier.phone or 'No phone'}":
                supplier.id
            for supplier in suppliers
        }

        current_supplier_label = next(
            (
                label
                for label, sid
                in supplier_options.items()
                if sid == current_po.supplier_id
            ),
            list(supplier_options.keys())[0],
        )

        selected_supplier = st.selectbox(
            "Supplier",
            list(supplier_options.keys()),
            index=list(
                supplier_options.keys()
            ).index(
                current_supplier_label
            ),
        )

        supplier_id = supplier_options[
            selected_supplier
        ]

        st.markdown(
            "### Purchase Order Items"
        )

        existing_items = list(
            current_po.items
        )

        item_count = st.number_input(
            "Number of Items",
            min_value=1,
            max_value=20,
            value=max(
                1,
                len(existing_items)
            ),
            step=1,
            key="edit_po_item_count",
        )

        items_data = []
        total_amount = 0.0

        for i in range(
            int(item_count)
        ):

            existing_item = (
                existing_items[i]
                if i < len(existing_items)
                else None
            )

            col1, col2, col3 = (
                st.columns([3, 1, 1])
            )

            with col1:

                product_name = st.text_input(
                    "Product / Raw Material",
                    value=(
                        existing_item.product_name
                        if existing_item
                        else ""
                    ),
                    key=f"edit_po_product_{i}",
                )

            with col2:

                quantity = st.number_input(
                    "Quantity",
                    min_value=0.0,
                    value=float(
                        existing_item.quantity
                        if existing_item
                        else 0
                    ),
                    step=0.1,
                    key=f"edit_po_quantity_{i}",
                )

            with col3:

                unit_price = st.number_input(
                    "Unit Price",
                    min_value=0.0,
                    value=float(
                        existing_item.unit_price
                        if existing_item
                        else 0
                    ),
                    step=100.0,
                    key=f"edit_po_price_{i}",
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

                items_data.append(
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
            f"UGX {total_amount:,.2f}",
        )

        status_options = [
            "Draft",
            "Pending Approval",
            "Approved",
            "Ordered",
            "Partially Received",
            "Received",
            "Cancelled",
        ]

        current_status = (
            current_po.status
            if current_po.status
            in status_options
            else "Draft"
        )

        status = st.selectbox(
            "Status",
            status_options,
            index=status_options.index(
                current_status
            ),
            key="edit_po_status",
        )

        if st.button(
            "💾 Save Purchase Order",
            type="primary",
            use_container_width=True,
        ):

            if not items_data:

                st.error(
                    "At least one item is required."
                )

                return

            try:

                updated = (
                    update_purchase_order(
                        po_id=po_id,
                        supplier_id=supplier_id,
                        items_data=items_data,
                        status=status,
                    )
                )

                if updated:

                    st.success(
                        f"{updated.po_number} "
                        "updated successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Purchase Order not found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to update Purchase Order: {e}"
                )

    # ==================================================
    # CHANGE STATUS
    # ==================================================

    elif action == "Change Status":

        status_options = [
            "Draft",
            "Pending Approval",
            "Approved",
            "Ordered",
            "Partially Received",
            "Received",
            "Cancelled",
        ]

        current_status = (
            current_po.status
            if current_po.status
            in status_options
            else "Draft"
        )

        new_status = st.selectbox(
            "New Status",
            status_options,
            index=status_options.index(
                current_status
            ),
        )

        if st.button(
            "🔄 Update Status",
            type="primary",
            use_container_width=True,
        ):

            try:

                updated = (
                    update_purchase_order_status(
                        po_id,
                        new_status,
                    )
                )

                if updated:

                    st.success(
                        f"{updated.po_number} "
                        f"status changed to "
                        f"{updated.status}."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Purchase Order not found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to change status: {e}"
                )

    # ==================================================
    # DELETE
    # ==================================================

    else:

        st.warning(
            "⚠️ Deleting a Purchase Order is permanent."
        )

        st.write(
            f"Selected PO: **{current_po.po_number}**"
        )

        st.write(
            f"Supplier: **"
            f"{current_po.supplier.name if current_po.supplier else 'Unknown'}"
            "**"
        )

        st.write(
            f"Total: **UGX "
            f"{current_po.total_amount:,.2f}**"
        )

        confirm = st.checkbox(
            "I understand that this action cannot be undone."
        )

        if st.button(
            "🗑️ Delete Purchase Order",
            type="primary",
            disabled=not confirm,
            use_container_width=True,
        ):

            try:

                success, message = (
                    delete_purchase_order(
                        po_id
                    )
                )

                if success:

                    st.success(message)
                    st.rerun()

                else:

                    st.error(message)

            except Exception as e:

                st.error(
                    f"Unable to delete Purchase Order: {e}"
                )


# ==================================================
# STANDALONE EXECUTION
# ==================================================

if __name__ == "__main__":
    purchase_orders_page()