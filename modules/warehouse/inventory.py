"""
Esan ERP Warehouse Inventory

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:
- View inventory
- Add products
- Update products
- Delete products
- Adjust stock
"""

import streamlit as st
import pandas as pd

from services.warehouse_service import (
    get_all_products,
    create_product,
    update_product,
    delete_product,
    adjust_stock,
)


def inventory_page():

    st.title("📦 Inventory Management")

    tab1, tab2, tab3 = st.tabs(
        [
            "📋 Inventory",
            "➕ Add Product",
            "🔄 Stock Adjustment",
        ]
    )

    with tab1:
        view_inventory()

    with tab2:
        add_product()

    with tab3:
        stock_adjustment()


# ==================================================
# VIEW INVENTORY
# ==================================================

def view_inventory():

    st.subheader("Current Inventory")

    products = get_all_products()

    if not products:

        st.info(
            "No products have been registered yet."
        )
        return

    data = []

    for product in products:

        data.append(
            {
                "ID":
                    product.id,

                "Product":
                    product.name,

                "Category":
                    product.category or "",

                "Unit":
                    product.unit,

                "Quantity":
                    product.quantity or 0,

                "Cost Price":
                    f"UGX "
                    f"{product.cost_price or 0:,.2f}",

                "Selling Price":
                    f"UGX "
                    f"{product.selling_price or 0:,.2f}",
            }
        )

    df = pd.DataFrame(data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("✏️ Product Management")

    product_options = {
        f"{product.name} | "
        f"{product.quantity or 0:,.1f} {product.unit}":
        product.id
        for product in products
    }

    selected_product = st.selectbox(
        "Select Product",
        list(product_options.keys()),
    )

    selected_id = product_options[
        selected_product
    ]

    selected = next(
        (
            product
            for product in products
            if product.id == selected_id
        ),
        None,
    )

    if not selected:
        return

    with st.form("edit_product_form"):

        st.markdown("### Edit Product")

        name = st.text_input(
            "Product Name",
            value=selected.name or "",
        )

        category = st.text_input(
            "Category",
            value=selected.category or "",
        )

        unit = st.text_input(
            "Unit",
            value=selected.unit or "Kg",
        )

        cost_price = st.number_input(
            "Cost Price",
            min_value=0.0,
            value=float(
                selected.cost_price or 0
            ),
            step=100.0,
        )

        selling_price = st.number_input(
            "Selling Price",
            min_value=0.0,
            value=float(
                selected.selling_price or 0
            ),
            step=100.0,
        )

        submitted = st.form_submit_button(
            "💾 Save Changes",
            use_container_width=True,
        )

        if submitted:

            if not name.strip():

                st.error(
                    "Product name is required."
                )
                return

            try:

                update_product(
                    product_id=selected.id,
                    name=name.strip(),
                    category=category.strip(),
                    unit=unit.strip(),
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

    st.divider()

    st.subheader("🗑️ Delete Product")

    st.warning(
        "Deleting a product cannot be undone."
    )

    if st.button(
        "Delete Selected Product",
        use_container_width=True,
    ):

        try:

            deleted = delete_product(
                selected.id
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

def add_product():

    st.subheader("Add New Product")

    with st.form("add_product_form"):

        name = st.text_input(
            "Product Name",
            placeholder="e.g. Maize Flour",
        )

        category = st.text_input(
            "Category",
            placeholder="e.g. Finished Product",
        )

        unit = st.selectbox(
            "Unit",
            [
                "Kg",
                "Tonnes",
                "Bags",
                "Units",
            ],
        )

        quantity = st.number_input(
            "Opening Quantity",
            min_value=0.0,
            step=0.1,
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
            "➕ Add Product",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            if not name.strip():

                st.error(
                    "Product name is required."
                )
                return

            try:

                create_product(
                    name=name.strip(),
                    category=category.strip(),
                    unit=unit,
                    quantity=quantity,
                    cost_price=cost_price,
                    selling_price=selling_price,
                )

                st.success(
                    f"{name} added successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Unable to add product: {e}"
                )


# ==================================================
# STOCK ADJUSTMENT
# ==================================================

def stock_adjustment():

    st.subheader("🔄 Stock Adjustment")

    products = get_all_products()

    if not products:

        st.info(
            "No products are available."
        )
        return

    product_options = {
        f"{product.name} | "
        f"{product.quantity or 0:,.1f} {product.unit}":
        product.id
        for product in products
    }

    selected = st.selectbox(
        "Product",
        list(product_options.keys()),
    )

    product_id = product_options[
        selected
    ]

    adjustment_type = st.selectbox(
        "Adjustment Type",
        [
            "Stock In",
            "Stock Out",
        ],
    )

    quantity = st.number_input(
        "Quantity",
        min_value=0.1,
        step=0.1,
    )

    reference = st.text_input(
        "Reference",
        placeholder="e.g. GRN-0001",
    )

    if st.button(
        "Apply Stock Adjustment",
        type="primary",
        use_container_width=True,
    ):

        if quantity <= 0:

            st.error(
                "Quantity must be greater than zero."
            )
            return

        try:

            movement_type = (
                "IN"
                if adjustment_type == "Stock In"
                else "OUT"
            )

            adjust_stock(
                product_id=product_id,
                quantity=quantity,
                movement_type=movement_type,
                reference=reference,
            )

            st.success(
                "Stock adjusted successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to adjust stock: {e}"
            )


if __name__ == "__main__":
    inventory_page()