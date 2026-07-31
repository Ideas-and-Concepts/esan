"""
Milling Dashboard – uses production_service
"""

import streamlit as st
import pandas as pd
from services.production_service import (
    create_milling_batch, complete_milling_batch, get_all_milling_batches
)

def milling_dashboard():
    st.title("🏭 Milling")
    tab1, tab2 = st.tabs(["Active Batches", "New Batch"])
    with tab1:
        batches = get_all_milling_batches()
        if batches:
            data = [{
                "Batch #": b.batch_number,
                "Raw Material": b.raw_material,
                "Input Qty": b.input_quantity,
                "Output Qty": b.output_quantity,
                "Wastage": b.wastage,
                "Status": b.status
            } for b in batches]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No batches.")
    with tab2:
        with st.form("new_milling"):
            raw = st.text_input("Raw Material")
            input_qty = st.number_input("Input Quantity (Kg)", min_value=0.0)
            if st.form_submit_button("Start Batch"):
                if raw and input_qty > 0:
                    b = create_milling_batch(raw, input_qty)
                    st.success(f"Batch {b.batch_number} started!")
                    st.rerun()
                else:
                    st.error("Fill all fields.")
