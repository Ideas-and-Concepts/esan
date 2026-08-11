"""
Esan ERP
Main Dashboard / Overview

Nile Harvest Foods Ltd.
"""

import streamlit as st

from services.dashboard_service import get_kpis


def dashboard_home():
    """
    Render the main Esan ERP Overview dashboard.
    """

    st.title("🏠 Overview")
    st.caption(
        "Nile Harvest Foods Ltd. | Enterprise Milling & Packaging Management System"
    )

    try:
        kpis = get_kpis()

    except Exception as e:
        st.error("Unable to load dashboard information.")
        st.exception(e)
        return

    # ==================================================
    # SALES & CUSTOMER KPIs
    # ==================================================

    st.subheader("📊 Business Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Customers",
            f"{kpis['customers']:,}",
        )

    with col2:
        st.metric(
            "Sales Orders",
            f"{kpis['orders']:,}",
        )

    with col3:
        st.metric(
            "Invoiced",
            f"UGX {kpis['invoiced']:,.0f}",
        )

    with col4:
        st.metric(
            "Collected",
            f"UGX {kpis['collected']:,.0f}",
        )

    st.divider()

    # ==================================================
    # OPERATIONS KPIs
    # ==================================================

    st.subheader("🏭 Operations")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Products",
            f"{kpis['products']:,}",
        )

    with col2:
        st.metric(
            "Stock",
            f"{kpis['stock_kg']:,.1f} Kg",
        )

    with col3:
        st.metric(
            "Milling Batches",
            f"{kpis['milling_batches']:,}",
        )

    with col4:
        st.metric(
            "Packaging Batches",
            f"{kpis['packaging_batches']:,}",
        )

    st.divider()

    # ==================================================
    # FACTORY STATUS
    # ==================================================

    st.subheader("🏭 Factory Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.success("🟢 Milling Line 1\n\nRunning")

    with col2:
        st.success("🟢 Warehouse\n\nOperational")

    with col3:
        st.info("🔵 Packaging Line\n\nScheduled Maintenance")

    st.divider()

    st.caption(
        "Esan ERP | Nile Harvest Foods Ltd."
    )