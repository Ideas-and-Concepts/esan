"""
Esan ERP Dashboard Home
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

import streamlit as st

from services.dashboard_service import get_kpis

def dashboard_home():
"""Render the main Esan ERP overview dashboard."""

st.title("🌾 Overview")

try:
    kpis = get_kpis()
except Exception as e:
    st.error("Unable to load dashboard data.")
    st.caption(f"Dashboard error: {e}")
    return

# ==================================================
# KPI CARDS
# ==================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Customers",
        kpis.get("customers", 0),
    )

with col2:
    st.metric(
        "Sales Orders",
        kpis.get("orders", 0),
    )

with col3:
    st.metric(
        "Invoiced",
        f"UGX {kpis.get('invoiced', 0):,.2f}",
    )

with col4:
    st.metric(
        "Collected",
        f"UGX {kpis.get('collected', 0):,.2f}",
    )

st.divider()

# ==================================================
# OPERATIONS KPIs
# ==================================================

col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric(
        "Products",
        kpis.get("products", 0),
    )

with col6:
    st.metric(
        "Stock",
        f"{kpis.get('stock_kg', 0):,.1f} Kg",
    )

with col7:
    st.metric(
        "Milling Batches",
        kpis.get("milling_batches", 0),
    )

with col8:
    st.metric(
        "Packaging Batches",
        kpis.get("packaging_batches", 0),
    )

st.divider()

# ==================================================
# ERP STATUS
# ==================================================

st.subheader("🏭 Factory Status")

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    st.success("🟢 Milling Operations")

with status_col2:
    st.success("🟢 Warehouse Operations")

with status_col3:
    st.info("🔵 Packaging Operations")