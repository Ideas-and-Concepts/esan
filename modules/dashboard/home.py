"""
Esan ERP
Main Overview Dashboard

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

import streamlit as st

from services.dashboard_service import get_kpis

def dashboard_home():
"""
Render the main Esan ERP Overview dashboard.
"""

st.title("🏠 Overview")
st.caption(
    "Nile Harvest Foods Ltd. | "
    "Enterprise Milling & Packaging Management System"
)

# ==================================================
# LOAD KPIs
# ==================================================

try:
    kpis = get_kpis()
except Exception as e:
    st.error("Unable to load dashboard information.")
    st.exception(e)
    return

# ==================================================
# COMMERCIAL KPIs
# ==================================================

st.markdown("### 📊 Business Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Customers",
        f"{kpis.get('customers', 0):,}"
    )

with col2:
    st.metric(
        "Sales Orders",
        f"{kpis.get('orders', 0):,}"
    )

with col3:
    st.metric(
        "Invoiced",
        f"UGX {kpis.get('invoiced', 0):,.0f}"
    )

with col4:
    st.metric(
        "Collected",
        f"UGX {kpis.get('collected', 0):,.0f}"
    )

# ==================================================
# OPERATIONS KPIs
# ==================================================

st.markdown("### 🏭 Operations")

col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric(
        "Products",
        f"{kpis.get('products', 0):,}"
    )

with col6:
    st.metric(
        "Stock",
        f"{kpis.get('stock_kg', 0):,.1f} Kg"
    )

with col7:
    st.metric(
        "Milling Batches",
        f"{kpis.get('milling_batches', 0):,}"
    )

with col8:
    st.metric(
        "Packaging Batches",
        f"{kpis.get('packaging_batches', 0):,}"
    )

# ==================================================
# FACTORY STATUS
# ==================================================

st.markdown("### 🏭 Factory Status")

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    st.success("🟢 Milling Line 1")
    st.caption("Running")

with status_col2:
    st.success("🟢 Warehouse")
    st.caption("Operational")

with status_col3:
    st.warning("🟡 Packaging Line")
    st.caption("Maintenance Scheduled")

# ==================================================
# SYSTEM STATUS
# ==================================================

st.markdown("### ⚙️ System Status")

system_col1, system_col2 = st.columns(2)

with system_col1:
    st.success("🟢 Database Connected")

with system_col2:
    st.success("🟢 ERP System Online")