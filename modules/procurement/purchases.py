"""
Esan ERP - Purchases & Receiving Module

Nile Harvest Foods Ltd.

Functions:
- Record purchases
- Receive goods
- Link purchases to Purchase Orders
- Add multiple purchase items
- Edit purchases
- Delete purchases
- Change purchase status
- View purchase history
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from services.procurement_service import (
    get_all_suppliers,
    get_all_purchase_orders,
    get_all_purchases,
    create_purchase,
    update_purchase,
    delete_purchase,
    update_purchase_status,
)


# ==================================================
# MAIN PAGE
# ==================================================

def purchases_page():

    st.title("📥 Purchase & Receiving Management")

    tab1, tab2, tab3 = st.tabs(
        [
            "➕ Record Purchase",
            "📋 Purchases",
            "⚙️ Manage",
        ]
    )

    with tab1:
        create_purchase_form()

    with tab2:
        view_purchases()

    with tab3:
        manage_purchases()


# ==================================================
# CREATE PURCHASE
# ==================================================

def create_purchase_form():

    st.subheader("Record New Purchase / Goods Received")

    suppliers = get_all_suppliers()
    purchase_orders = get_all_purchase_orders()

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
        key="purchase_supplier",
    )

    supplier_id = supplier_options[
        selected_supplier
    ]

    # --------------------------------------------------
    # PURCHASE ORDER
    # --------------------------------------------------

    matching_pos = [
        po
        for po in purchase_orders
        if po.supplier_id == supplier_id
    ]

    po_options = {
        "No Purchase Order":
            None
    }

    for po in matching_pos:

        po_options[
            f"{po.po_number} | "
            f"{po.status} | "
            f"UGX {po.total_amount:,.2f}"
        ] = po.id

    selected_po = st.selectbox(
        "Purchase Order",
        list(po_options.keys()),
        key="purchase_po",
    )

    purchase_order_id = po_options[
        selected_po
    ]

    st.markdown("### Purchase Details")

    col1, col2 = st.columns(2)

    with col1:

        received_date = st.date_input(
            "Received Date",
            value=datetime.today().date(),
        )

    with col2:

        warehouse = st.text_input(
            "Receiving Warehouse",
            placeholder="e.g. Main Warehouse",
        )

    # --------------------------------------------------
    # ITEMS
    # --------------------------------------------------

    st.markdown("### 📦 Purchased Items")

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

        total_amount += item_total

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        status = st.selectbox(
            "Purchase Status",
            [
                "Received",
                "Partially Received",
                "Pending Inspection",
                "Accepted",
                "Rejected",
                "Cancelled",
            ],
            key="purchase_status",
        )

    with col2:

        st.metric(
            "Total Purchase",
            f"UGX {total_amount:,.2f}",
        )

    notes = st.text_area(
        "Notes",
        placeholder=(
            "Additional receiving or purchase notes..."
        ),
    )

    submitted = st.button(
        "💾 Record Purchase",
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

            purchase = create_purchase(
                supplier_id=supplier_id,
                items_data=items_data,
                purchase_order_id=purchase_order_id,
                status=status,
                received_date=datetime.combine(
                    received_date,
                    datetime.min.time(),
                ),
                warehouse=warehouse,
                notes=notes,
            )

            st.success(
                f"Purchase "
                f"{purchase.purchase_number} "
                "recorded successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to record purchase: {e}"
            )


# ==================================================
# VIEW PURCHASES
# ==================================================

def view_purchases():

    st.subheader("📋 Purchase History")

    purchases = get_all_purchases()

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

        po_number = (
            purchase.purchase_order.po_number
            if purchase.purchase_order
            else "Direct Purchase"
        )

        data.append(
            {
                "ID":
                    purchase.id,

                "Purchase Number":
                    purchase.purchase_number,

                "Supplier":
                    supplier_name,

                "Purchase Order":
                    po_number,

                "Status":
                    purchase.status,

                "Warehouse":
                    purchase.warehouse or "",

                "Total":
                    f"UGX "
                    f"{purchase.total_amount:,.2f}",

                "Received":
                    (
                        purchase.received_date.strftime(
                            "%Y-%m-%d"
                        )
                        if purchase.received_date
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

    st.metric(
        "Total Purchase Value",
        f"UGX "
        f"{sum(p.total_amount or 0 for p in purchases):,.2f}",
    )


# ==================================================
# MANAGE PURCHASES
# ==================================================

def manage_purchases():

    st.subheader("⚙️ Manage Purchases")

    purchases = get_all_purchases()

    if not purchases:

        st.info(
            "There are no purchases to manage."
        )

        return

    purchase_options = {}

    for purchase in purchases:

        supplier_name = (
            purchase.supplier.name
            if purchase.supplier
            else "Unknown Supplier"
        )

        purchase_options[
            f"{purchase.purchase_number} | "
            f"{supplier_name} | "
            f"UGX {purchase.total_amount:,.2f}"
        ] = purchase.id

    selected_purchase = st.selectbox(
        "Select Purchase",
        list(purchase_options.keys()),
    )

    purchase_id = purchase_options[
        selected_purchase
    ]

    purchase = next(
        (
            p for p in purchases
            if p.id == purchase_id
        ),
        None,
    )

    if not purchase:
        st.error("Purchase not found.")
        return

    # ==================================================
    # PURCHASE INFORMATION
    # ==================================================

    st.markdown("### Purchase Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Purchase Number",
            purchase.purchase_number,
        )

    with col2:
        st.metric(
            "Total",
            f"UGX "
            f"{purchase.total_amount:,.2f}",
        )

    with col3:
        st.metric(
            "Status",
            purchase.status,
        )

    # ==================================================
    # ITEMS
    # ==================================================

    st.markdown("### Purchased Items")

    items_data = []

    for item in purchase.items:

        items_data.append(
            {
                "Product":
                    item.product_name,
                "Quantity":
                    item.quantity,
                "Unit Price":
                    f"UGX "
                    f"{item.unit_price:,.2f}",
                "Total":
                    f"UGX "
                    f"{item.total:,.2f}",
            }
        )

    if items_data:

        st.dataframe(
            pd.DataFrame(items_data),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # ==================================================
    # STATUS
    # ==================================================

    st.markdown("### 🔄 Change Status")

    new_status = st.selectbox(
        "New Status",
        [
            "Received",
            "Partially Received",
            "Pending Inspection",
            "Accepted",
            "Rejected",
            "Cancelled",
        ],
        index=(
            [
                "Received",
                "Partially Received",
                "Pending Inspection",
                "Accepted",
                "Rejected",
                "Cancelled",
            ].index(purchase.status)
            if purchase.status in [
                "Received",
                "Partially Received",
                "Pending Inspection",
                "Accepted",
                "Rejected",
                "Cancelled",
            ]
            else 0
        ),
    )

    if st.button(
        "🔄 Update Status",
        use_container_width=True,
    ):

        try:

            updated = update_purchase_status(
                purchase.id,
                new_status,
            )

            if updated:

                st.success(
                    f"{updated.purchase_number} "
                    f"updated to {updated.status}."
                )

                st.rerun()

        except Exception as e:

            st.error(
                f"Unable to update status: {e}"
            )

    st.divider()

    # ==================================================
    # DELETE
    # ==================================================

    st.markdown("### 🗑️ Delete Purchase")

    confirm_delete = st.checkbox(
        "I understand that deleting this purchase cannot be undone.",
        key=f"confirm_delete_purchase_{purchase.id}",
    )

    if st.button(
        "🗑️ Delete Purchase",
        type="secondary",
        disabled=not confirm_delete,
        use_container_width=True,
    ):

        try:

            deleted = delete_purchase(
                purchase.id
            )

            if deleted:

                st.success(
                    f"{purchase.purchase_number} "
                    "deleted successfully."
                )

                st.rerun()

            else:

                st.error(
                    "Purchase could not be found."
                )

        except Exception as e:

            st.error(
                f"Unable to delete purchase: {e}"
            )


# ==================================================
# STANDALONE EXECUTION
# ==================================================

if __name__ == "__main__":
    purchases_page()