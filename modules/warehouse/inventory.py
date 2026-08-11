"""
Esan ERP - Warehouse Inventory Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:
- Add products
- Edit products
- Delete products
- View inventory
- Stock In
- Stock Out
- Stock Adjustment
- Low-stock monitoring
- Stock movement history
"""

import streamlit as st
import pandas as pd

from services.warehouse_service import (
    get_all_products,
    create_product,
    update_product,
    delete_product,
    stock_in,
    stock_out,
    adjust_stock,
    get_stock_movements,
    get_low_stock_products,
)


# ============================================================
# MAIN INVENTORY PAGE
# ============================================================

def inventory_page():

    st.title("📦 Warehouse Inventory")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📋 Inventory",
            "➕ Add Product",
            "📥 Stock In",
            "📤 Stock Out",
            "📜 Stock Movements",
        ]
    )

    with tab1:
        inventory_list()

    with tab2:
        add_product_form()

    with tab3:
        stock_in_form()

    with tab4:
        stock_out_form()

    with tab5:
        stock_movement_history()


# ============================================================
# INVENTORY LIST
# ============================================================

def inventory_list():

    st.subheader("📋 Current Inventory")

    products = get_all_products()

    if not products:
        st.info(
            "No products have been registered yet. "
            "Use 'Add Product' to create your first inventory item."
        )
        return

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search = st.text_input(
        "🔎 Search Product",
        placeholder="Search by product name or category...",
        key="inventory_search",
    )

    if search:
        search_lower = search.lower()

        products = [
            product
            for product in products
            if search_lower in (product.name or "").lower()
            or search_lower in (product.category or "").lower()
        ]

    if not products:
        st.warning("No matching products found.")
        return

    # --------------------------------------------------------
    # INVENTORY TABLE
    # --------------------------------------------------------

    data = []

    for product in products:

        quantity = float(product.quantity or 0)
        cost_price = float(product.cost_price or 0)
        selling_price = float(product.selling_price or 0)

        inventory_value = quantity * cost_price

        data.append(
            {
                "ID": product.id,
                "Product": product.name,
                "Category": product.category or "",
                "Unit": product.unit or "Kg",
                "Stock": f"{quantity:,.2f}",
                "Cost Price": f"UGX {cost_price:,.2f}",
                "Selling Price": f"UGX {selling_price:,.2f}",
                "Stock Value": f"UGX {inventory_value:,.2f}",
            }
        )

    df = pd.DataFrame(data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # INVENTORY KPIs
    # --------------------------------------------------------

    total_products = len(products)

    total_stock = sum(
        float(product.quantity or 0)
        for product in products
    )

    total_value = sum(
        float(product.quantity or 0)
        * float(product.cost_price or 0)
        for product in products
    )

    low_stock_count = sum(
        1
        for product in products
        if float(product.quantity or 0) <= 10
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Products",
        total_products,
    )

    col2.metric(
        "Total Stock",
        f"{total_stock:,.2f}",
    )

    col3.metric(
        "Inventory Value",
        f"UGX {total_value:,.2f}",
    )

    col4.metric(
        "Low Stock",
        low_stock_count,
    )

    # --------------------------------------------------------
    # LOW STOCK
    # --------------------------------------------------------

    st.divider()

    st.subheader("⚠️ Low Stock Items")

    low_stock = [
        product
        for product in products
        if float(product.quantity or 0) <= 10
    ]

    if not low_stock:

        st.success(
            "All products are currently above the low-stock threshold."
        )

    else:

        low_stock_data = []

        for product in low_stock:

            low_stock_data.append(
                {
                    "Product": product.name,
                    "Category": product.category or "",
                    "Stock": float(product.quantity or 0),
                    "Unit": product.unit or "Kg",
                }
            )

        st.dataframe(
            pd.DataFrame(low_stock_data),
            use_container_width=True,
            hide_index=True,
        )

    # --------------------------------------------------------
    # PRODUCT MANAGEMENT
    # --------------------------------------------------------

    st.divider()

    st.subheader("⚙️ Product Management")

    product_options = {
        f"{product.name} | ID {product.id}": product.id
        for product in products
    }

    if not product_options:
        return

    selected_product_label = st.selectbox(
        "Select Product",
        list(product_options.keys()),
        key="inventory_management_product",
    )

    selected_product_id = product_options[
        selected_product_label
    ]

    selected_product = next(
        (
            product
            for product in products
            if product.id == selected_product_id
        ),
        None,
    )

    if not selected_product:
        return

    edit_col, delete_col = st.columns(2)

    with edit_col:

        with st.expander("✏️ Edit Product"):

            edit_product_form(selected_product)

    with delete_col:

        with st.expander("🗑️ Delete Product"):

            st.warning(
                "Deleting a product is permanent. "
                "Products with stock movement history cannot be deleted."
            )

            confirm_delete = st.checkbox(
                "I understand that this action cannot be undone.",
                key=f"confirm_delete_{selected_product.id}",
            )

            if st.button(
                "🗑️ Delete Product",
                type="secondary",
                use_container_width=True,
                key=f"delete_product_{selected_product.id}",
            ):

                if not confirm_delete:

                    st.error(
                        "Please confirm deletion first."
                    )
                    return

                try:

                    deleted = delete_product(
                        selected_product.id
                    )

                    if deleted:

                        st.success(
                            f"Product '{selected_product.name}' "
                            "deleted successfully."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Product could not be found."
                        )

                except Exception as e:

                    st.error(
                        f"Unable to delete product: {e}"
                    )


# ============================================================
# ADD PRODUCT
# ============================================================

def add_product_form():

    st.subheader("➕ Register New Product")

    with st.form("add_product_form"):

        name = st.text_input(
            "Product Name",
            placeholder="e.g. Maize Grain",
        )

        col1, col2 = st.columns(2)

        with col1:

            category = st.text_input(
                "Category",
                placeholder="e.g. Raw Material",
            )

            unit = st.selectbox(
                "Unit",
                [
                    "Kg",
                    "Tonnes",
                    "Bags",
                    "Pieces",
                    "Litres",
                ],
            )

        with col2:

            opening_quantity = st.number_input(
                "Opening Stock",
                min_value=0.0,
                step=0.1,
                value=0.0,
            )

            cost_price = st.number_input(
                "Cost Price",
                min_value=0.0,
                step=100.0,
                value=0.0,
            )

            selling_price = st.number_input(
                "Selling Price",
                min_value=0.0,
                step=100.0,
                value=0.0,
            )

        submitted = st.form_submit_button(
            "💾 Save Product",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if not name.strip():

        st.error(
            "Product name is required."
        )
        return

    try:

        product = create_product(
            name=name,
            category=category,
            unit=unit,
            quantity=opening_quantity,
            cost_price=cost_price,
            selling_price=selling_price,
        )

        st.success(
            f"Product '{product.name}' "
            "created successfully."
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"Unable to create product: {e}"
        )


# ============================================================
# EDIT PRODUCT
# ============================================================

def edit_product_form(product):

    with st.form(
        f"edit_product_form_{product.id}"
    ):

        name = st.text_input(
            "Product Name",
            value=product.name or "",
        )

        category = st.text_input(
            "Category",
            value=product.category or "",
        )

        unit_options = [
            "Kg",
            "Tonnes",
            "Bags",
            "Pieces",
            "Litres",
        ]

        current_unit = product.unit or "Kg"

        if current_unit not in unit_options:
            unit_options.append(current_unit)

        unit = st.selectbox(
            "Unit",
            unit_options,
            index=unit_options.index(current_unit),
        )

        cost_price = st.number_input(
            "Cost Price",
            min_value=0.0,
            value=float(product.cost_price or 0),
            step=100.0,
        )

        selling_price = st.number_input(
            "Selling Price",
            min_value=0.0,
            value=float(product.selling_price or 0),
            step=100.0,
        )

        st.caption(
            f"Current stock: "
            f"{float(product.quantity or 0):,.2f} "
            f"{product.unit or 'Kg'}"
        )

        submitted = st.form_submit_button(
            "💾 Update Product",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    try:

        updated = update_product(
            product_id=product.id,
            name=name,
            category=category,
            unit=unit,
            cost_price=cost_price,
            selling_price=selling_price,
        )

        if updated:

            st.success(
                f"Product '{updated.name}' "
                "updated successfully."
            )

            st.rerun()

        else:

            st.error(
                "Product not found."
            )

    except Exception as e:

        st.error(
            f"Unable to update product: {e}"
        )


# ============================================================
# STOCK IN
# ============================================================

def stock_in_form():

    st.subheader("📥 Stock In")

    products = get_all_products()

    if not products:

        st.info(
            "No products are available. "
            "Create a product first."
        )
        return

    product_options = {
        f"{product.name} | "
        f"Current Stock: "
        f"{float(product.quantity or 0):,.2f} "
        f"{product.unit or 'Kg'}": product.id
        for product in products
    }

    selected = st.selectbox(
        "Product",
        list(product_options.keys()),
        key="stock_in_product",
    )

    product_id = product_options[selected]

    product = next(
        (
            p
            for p in products
            if p.id == product_id
        ),
        None,
    )

    if not product:
        return

    quantity = st.number_input(
        f"Quantity ({product.unit or 'Kg'})",
        min_value=0.01,
        step=0.1,
        value=1.0,
        key="stock_in_quantity",
    )

    reference = st.text_input(
        "Reference",
        placeholder="e.g. GRN-0001 / Purchase Order PO-2026-0001",
        key="stock_in_reference",
    )

    if st.button(
        "📥 Receive Stock",
        type="primary",
        use_container_width=True,
        key="stock_in_button",
    ):

        try:

            updated_product = stock_in(
                product_id=product_id,
                quantity=quantity,
                reference=reference,
            )

            st.success(
                f"{quantity:,.2f} {updated_product.unit or 'units'} "
                f"added to {updated_product.name}."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to receive stock: {e}"
            )


# ============================================================
# STOCK OUT
# ============================================================

def stock_out_form():

    st.subheader("📤 Stock Out")

    products = get_all_products()

    if not products:

        st.info(
            "No products are available."
        )
        return

    product_options = {
        f"{product.name} | "
        f"Available: "
        f"{float(product.quantity or 0):,.2f} "
        f"{product.unit or 'Kg'}": product.id
        for product in products
    }

    selected = st.selectbox(
        "Product",
        list(product_options.keys()),
        key="stock_out_product",
    )

    product_id = product_options[selected]

    product = next(
        (
            p
            for p in products
            if p.id == product_id
        ),
        None,
    )

    if not product:
        return

    available_stock = float(
        product.quantity or 0
    )

    quantity = st.number_input(
        f"Quantity ({product.unit or 'Kg'})",
        min_value=0.01,
        max_value=max(available_stock, 0.01),
        step=0.1,
        value=min(1.0, max(available_stock, 0.01)),
        key="stock_out_quantity",
    )

    reference = st.text_input(
        "Reference",
        placeholder="e.g. Sales Order SO-0001 / Issue Note",
        key="stock_out_reference",
    )

    if available_stock <= 0:

        st.warning(
            "This product currently has no available stock."
        )

    if st.button(
        "📤 Issue Stock",
        type="primary",
        use_container_width=True,
        key="stock_out_button",
    ):

        try:

            updated_product = stock_out(
                product_id=product_id,
                quantity=quantity,
                reference=reference,
            )

            st.success(
                f"{quantity:,.2f} {updated_product.unit or 'units'} "
                f"issued from {updated_product.name}."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to issue stock: {e}"
            )


# ============================================================
# STOCK MOVEMENT HISTORY
# ============================================================

def stock_movement_history():

    st.subheader("📜 Stock Movement History")

    products = get_all_products()

    if not products:

        st.info(
            "No products are available."
        )
        return

    filter_options = {
        "All Products": None
    }

    for product in products:

        filter_options[
            f"{product.name} | ID {product.id}"
        ] = product.id

    selected_product = st.selectbox(
        "Filter by Product",
        list(filter_options.keys()),
        key="movement_product_filter",
    )

    product_id = filter_options[
        selected_product
    ]

    movement_type = st.selectbox(
        "Movement Type",
        [
            "All",
            "Stock In",
            "Stock Out",
            "Adjustment",
        ],
        key="movement_type_filter",
    )

    selected_movement_type = (
        None
        if movement_type == "All"
        else movement_type
    )

    movements = get_stock_movements(
        product_id=product_id,
        movement_type=selected_movement_type,
    )

    if not movements:

        st.info(
            "No stock movements found."
        )
        return

    product_lookup = {
        product.id: product
        for product in products
    }

    data = []

    for movement in movements:

        product = product_lookup.get(
            movement.product_id
        )

        quantity = float(
            movement.quantity or 0
        )

        data.append(
            {
                "Date": (
                    movement.created_at.strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    if movement.created_at
                    else ""
                ),
                "Product": (
                    product.name
                    if product
                    else f"Product #{movement.product_id}"
                ),
                "Movement": movement.movement_type,
                "Quantity": f"{quantity:,.2f}",
                "Reference": movement.reference or "",
            }
        )

    st.dataframe(
        pd.DataFrame(data),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# STANDALONE EXECUTION
# ============================================================

if __name__ == "__main__":
    inventory_page()