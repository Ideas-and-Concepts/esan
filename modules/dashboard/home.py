"""
Dashboard Home
Esan ERP - Main Overview
"""

import streamlit as st
from services.dashboard_service import get_kpis

def dashboard_home():
    st.title("🏠 Dashboard")
    kpis = get_kpis()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Customers", kpis['customers'])
    col2.metric("Sales Orders", kpis['orders'])
    col3.metric("Invoiced", f"${kpis['invoiced']:,.2f}")
    col4.metric("Collected", f"${kpis['collected']:,.2f}")

    st.markdown("---")
    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Products", kpis['products'])
    col6.metric("Stock (Kg)", f"{kpis['stock_kg']:,.1f}")
    col7.metric("Milling Batches", kpis['milling_batches'])
    col8.metric("Packaging Batches", kpis['packaging_batches'])
