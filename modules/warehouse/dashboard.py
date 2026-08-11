"""
Warehouse Dashboard
"""

import streamlit as st
import pandas as pd
from services.warehouse_service import get_all_warehouses, create_warehouse, get_all_products, get_low_stock_products, record_stock_movement, update_product_quantity

def warehouse_dashboard():
    st.title("📦 Warehouse")
    tab1, tab2, tab3 = st.tabs(["Inventory", "Movements", "Warehouses"])
    with tab1:
        inventory_view()
    with tab2:
        movement_view()
    with tab3:
        warehouses_view()

def inventory_view():
    products = get_all_products()
    if products:
        data = [{
            'Product': p.name,
            'Category': p.category,
            'Quantity': p.quantity,
            'Unit': p.unit
        } for p in products]
        st.dataframe(pd.DataFrame(data), use_container_width=True)

        low = get_low_stock_products(100)
        if low:
            st.warning(f"{len(low)} products below threshold.")
    else:
        st.info("No products.")

def movement_view():
    st.subheader("Record Stock Movement")
    products = get_all_products()
    prod_options = {p.name: p.id for p in products}
    with st.form("stock_movement_form"):
        product = st.selectbox("Product", list(prod_options.keys()))
        movement_type = st.selectbox("Type", ["Addition", "Deduction", "Transfer"])
        quantity = st.number_input("Quantity", min_value=0.0)
        reference = st.text_input("Reference")
        if st.form_submit_button("Record"):
            change = quantity if movement_type == "Addition" else -quantity
            update_product_quantity(prod_options[product], change)
            record_stock_movement(prod_options[product], movement_type, quantity, reference)
            st.success("Movement recorded")
            st.rerun()

def warehouses_view():
    warehouses = get_all_warehouses()
    if warehouses:
        for wh in warehouses:
            with st.expander(wh.name):
                st.write(f"Location: {wh.location}, Capacity: {wh.capacity}")
    else:
        st.info("No warehouses.")
        with st.form("add_warehouse"):
            name = st.text_input("Name")
            location = st.text_input("Location")
            capacity = st.number_input("Capacity", min_value=0.0)
            if st.form_submit_button("Add"):
                if name:
                    create_warehouse(name, location, capacity)
                    st.success("Added")
                    st.rerun()