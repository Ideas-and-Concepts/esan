"""
Packaging Dashboard – uses production_service
"""

import streamlit as st
import pandas as pd
from services.production_service import (
    create_packaging_batch, get_all_packaging_batches
)

def packaging_dashboard():
    st.title("📦 Packaging")
    tab1, tab2 = st.tabs(["Active Batches", "New Batch"])
    with tab1:
        batches = get_all_packaging_batches()
        if batches:
            data = [{
                "Batch #": b.batch_number,
                "Product": b.product_name,
                "Input Qty": b.input_quantity,
                "Packed Qty": b.packed_quantity,
                "Package Size": b.package_size,
                "Status": b.status
            } for b in batches]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No batches.")
    with tab2:
        with st.form("new_packaging"):
            product = st.text_input("Product Name")
            input_qty = st.number_input("Input Quantity", min_value=0.0)
            packed_qty = st.number_input("Packed Quantity", min_value=0.0)
            size = st.selectbox("Package Size", ["1kg", "2kg", "5kg", "10kg", "25kg"])
            if st.form_submit_button("Start Batch"):
                if product and input_qty > 0:
                    b = create_packaging_batch(product, input_qty, packed_qty, size)
                    st.success(f"Batch {b.batch_number} started!")
                    st.rerun()
