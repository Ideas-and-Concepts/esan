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
- Update purchase order status
"""

import streamlit as st
import pandas as pd

from services.procurement_service import (
    get_all_suppliers,
    get_all_purchase_orders,
    create_purchase_order,
    update_purchase_order_status,
)


# ==================================================
# MAIN PURCHASE ORDERS PAGE
# ==================================================

def purchase_orders_page():

    st.title("📄 Purchase Order Management")

    tab1, tab2 = st.tabs(
        [
            "➕ Create Purchase Order",
            "📋 Purchase Orders",
        ]
    )

    with tab1:
        create_po_form()

    with tab2:
        view_purchase_orders()


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
    )

    supplier_id = supplier_options[selected_supplier]

    st.markdown("### Purchase Order Items")

    # Number of items
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

        try:

            purchase_order = create_purchase_order(
                supplier_id=supplier_id,
                items_data=items_data,
                status=status,
            )

            st.success(
                f"Purchase Order "
                f"{purchase_order.po_number} created successfully."
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

    st.subheader("Purchase Orders")

    purchase_orders = get_all_purchase_orders()

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
                "ID": po.id,
                "PO Number": po.po_number,
                "Supplier": supplier_name,
                "Status": po.status,
                "Total": f"UGX {po.total_amount:,.2f}",
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
    # PURCHASE ORDER STATUS MANAGEMENT
    # ==================================================

    st.subheader("🔄 Update Purchase Order Status")

    po_options = {
        f"{po.po_number} | "
        f"{po.supplier.name if po.supplier else 'Unknown Supplier'}":
            po.id
        for po in purchase_orders
    }

    selected_po = st.selectbox(
        "Purchase Order",
        options=list(po_options.keys()),
    )

    selected_po_id = po_options[selected_po]

    new_status = st.selectbox(
        "New Status",
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

            updated_po = update_purchase_order_status(
                selected_po_id,
                new_status,
            )

            if updated_po:

                st.success(
                    f"{updated_po.po_number} status updated to "
                    f"{updated_po.status}."
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
# OPTIONAL STANDALONE EXECUTION
# ==================================================

if __name__ == "__main__":
    purchase_orders_page()
