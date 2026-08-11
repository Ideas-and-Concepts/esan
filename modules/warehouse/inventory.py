"""
Esan ERP Warehouse Inventory Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

import streamlit as st
import pandas as pd

from services.warehouse_service import (
get_all_products,
create_product,
update_product,
delete_product,
add_stock,
remove_stock,
get_stock_movements,
)

def inventory_page():

st.title("📦 Warehouse Inventory")

products = get_all_products()

# ==================================================
# INVENTORY SUMMARY
# ==================================================

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

col1, col2, col3 = st.columns(3)

col1.metric(
    "Products",
    total_products,
)

col2.metric(
    "Total Stock",
    f"{total_stock:,.1f} Kg",
)

col3.metric(
    "Stock Value",
    f"UGX {total_value:,.2f}",
)

st.divider()

# ==================================================
# TABS
# ==================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📋 Inventory",
        "➕ Add Product",
        "✏️ Edit Product",
        "🔄 Stock Adjustment",
    ]
)

# ==================================================
# INVENTORY LIST
# ==================================================

with tab1:

    if not products:

        st.info(
            "No products have been registered yet."
        )

    else:

        data = []

        for product in products:

            data.append(
                {
                    "ID": product.id,
                    "Product": product.name,
                    "Category": product.category or "",
                    "Unit": product.unit or "Kg",
                    "Quantity": float(
                        product.quantity or 0
                    ),
                    "Cost Price": float(
                        product.cost_price or 0
                    ),
                    "Selling Price": float(
                        product.selling_price or 0
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

        st.subheader("🗑️ Delete Product")

        product_options = {
            f"{product.name} | ID {product.id}":
                product.id
            for product in products
        }

        selected_product = st.selectbox(
            "Product",
            list(product_options.keys()),
            key="delete_product_select",
        )

        if st.button(
            "🗑️ Delete Product",
            type="secondary",
            use_container_width=True,
        ):

            product_id = product_options[
                selected_product
            ]

            try:

                deleted = delete_product(
                    product_id
                )

                if deleted:

                    st.success(
                        "Product deleted successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Product was not found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to delete product: {e}"
                )

# ==================================================
# ADD PRODUCT
# ==================================================

with tab2:

    st.subheader("➕ Add New Product")

    with st.form("add_product_form"):

        name = st.text_input(
            "Product Name"
        )

        category = st.text_input(
            "Category"
        )

        unit = st.selectbox(
            "Unit",
            [
                "Kg",
                "Tonnes",
                "Bags",
                "Pieces",
            ],
        )

        quantity = st.number_input(
            "Opening Stock",
            min_value=0.0,
            step=1.0,
        )

        cost_price = st.number_input(
            "Cost Price",
            min_value=0.0,
            step=100.0,
        )

        selling_price = st.number_input(
            "Selling Price",
            min_value=0.0,
            step=100.0,
        )

        submitted = st.form_submit_button(
            "💾 Save Product",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            if not name.strip():

                st.error(
                    "Product name is required."
                )

            else:

                try:

                    create_product(
                        name=name,
                        category=category,
                        unit=unit,
                        quantity=quantity,
                        cost_price=cost_price,
                        selling_price=selling_price,
                    )

                    st.success(
                        "Product added successfully."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Unable to create product: {e}"
                    )

# ==================================================
# EDIT PRODUCT
# ==================================================

with tab3:

    st.subheader("✏️ Edit Product")

    if not products:

        st.info(
            "No products available for editing."
        )

    else:

        product_options = {
            f"{product.name} | ID {product.id}":
                product.id
            for product in products
        }

        selected_product = st.selectbox(
            "Select Product",
            list(product_options.keys()),
            key="edit_product_select",
        )

        product_id = product_options[
            selected_product
        ]

        product = next(
            (
                p for p in products
                if p.id == product_id
            ),
            None,
        )

        if product:

            with st.form("edit_product_form"):

                name = st.text_input(
                    "Product Name",
                    value=product.name or "",
                )

                category = st.text_input(
                    "Category",
                    value=product.category or "",
                )

                unit = st.selectbox(
                    "Unit",
                    [
                        "Kg",
                        "Tonnes",
                        "Bags",
                        "Pieces",
                    ],
                    index=(
                        [
                            "Kg",
                            "Tonnes",
                            "Bags",
                            "Pieces",
                        ].index(product.unit)
                        if product.unit
                        in [
                            "Kg",
                            "Tonnes",
                            "Bags",
                            "Pieces",
                        ]
                        else 0
                    ),
                )

                quantity = st.number_input(
                    "Quantity",
                    min_value=0.0,
                    value=float(
                        product.quantity or 0
                    ),
                    step=1.0,
                )

                cost_price = st.number_input(
                    "Cost Price",
                    min_value=0.0,
                    value=float(
                        product.cost_price or 0
                    ),
                    step=100.0,
                )

                selling_price = st.number_input(
                    "Selling Price",
                    min_value=0.0,
                    value=float(
                        product.selling_price or 0
                    ),
                    step=100.0,
                )

                submitted = st.form_submit_button(
                    "💾 Update Product",
                    type="primary",
                    use_container_width=True,
                )

                if submitted:

                    try:

                        update_product(
                            product_id=product.id,
                            name=name,
                            category=category,
                            unit=unit,
                            quantity=quantity,
                            cost_price=cost_price,
                            selling_price=selling_price,
                        )

                        st.success(
                            "Product updated successfully."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Unable to update product: {e}"
                        )

# ==================================================
# STOCK ADJUSTMENT
# ==================================================

with tab4:

    st.subheader("🔄 Stock Adjustment")

    if not products:

        st.info(
            "No products available."
        )

    else:

        product_options = {
            f"{product.name} | "
            f"Current: {product.quantity or 0} "
            f"{product.unit or 'Kg'}":
                product.id
            for product in products
        }

        selected_product = st.selectbox(
            "Product",
            list(product_options.keys()),
            key="stock_product_select",
        )

        product_id = product_options[
            selected_product
        ]

        movement_type = st.radio(
            "Stock Movement",
            [
                "Stock In",
                "Stock Out",
            ],
            horizontal=True,
        )

        quantity = st.number_input(
            "Quantity",
            min_value=0.1,
            step=0.1,
        )

        reference = st.text_input(
            "Reference",
            placeholder="e.g. GRN-0001 / SALE-0001",
        )

        if st.button(
            "💾 Apply Stock Adjustment",
            type="primary",
            use_container_width=True,
        ):

            try:

                if movement_type == "Stock In":

                    add_stock(
                        product_id,
                        quantity,
                        reference,
                    )

                else:

                    remove_stock(
                        product_id,
                        quantity,
                        reference,
                    )

                st.success(
                    "Stock adjustment completed."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Unable to adjust stock: {e}"
                )

    st.divider()

    st.subheader("📜 Recent Stock Movements")

    movements = get_stock_movements()

    if movements:

        movement_data = []

        for movement in movements:

            movement_data.append(
                {
                    "Product ID":
                        movement.product_id,
                    "Type":
                        movement.movement_type,
                    "Quantity":
                        movement.quantity,
                    "Reference":
                        movement.reference or "",
                    "Date":
                        (
                            movement.created_at.strftime(
                                "%Y-%m-%d %H:%M"
                            )
                            if movement.created_at
                            else ""
                        ),
                }
            )

        st.dataframe(
            pd.DataFrame(movement_data),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No stock movements recorded yet."
        )

if name == "main":
inventory_page()