"""
Costing Module
Esan ERP - Cost of Goods Sold Estimation
"""

import streamlit as st
import pandas as pd
from database import SessionLocal
from models import MillingBatch, PackagingBatch, Product
from sqlalchemy import func

def get_db():
    return SessionLocal()

def costing_page():
    st.title("🧮 Costing & COGS")
    db = get_db()
    try:
        # Total raw material cost from milling
        milling_cost = db.query(func.sum(MillingBatch.wastage * 0 + MillingBatch.input_quantity * 2.5)).scalar() or 0  # simplified
        # Packaging cost
        packaging_cost = db.query(func.sum(PackagingBatch.packed_quantity * 0.5)).scalar() or 0

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Est. Milling Cost", f"${milling_cost:,.2f}")
        with col2:
            st.metric("Est. Packaging Cost", f"${packaging_cost:,.2f}")

        st.markdown("---")
        st.subheader("Product Cost Breakdown")
        products = db.query(Product).all()
        if products:
            data = []
            for p in products:
                # Simplified: assume cost_price is raw material cost
                data.append({
                    'Product': p.name,
                    'Cost Price': f"${p.cost_price:,.2f}",
                    'Selling Price': f"${p.selling_price:,.2f}",
                    'Margin': f"${(p.selling_price or 0) - (p.cost_price or 0):,.2f}"
                })
            st.dataframe(pd.DataFrame(data), use_container_width=True)
    finally:
        db.close()