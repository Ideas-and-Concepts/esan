"""
Esan ERP
Dashboard Home / Overview

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

import logging
import streamlit as st


logger = logging.getLogger("esan_erp.dashboard")


# ============================================================
# SAFE KPI SERVICE IMPORT
# ============================================================

try:
    from services.dashboard_service import get_kpis

    KPI_SERVICE_AVAILABLE = True

except Exception as exc:

    KPI_SERVICE_AVAILABLE = False
    get_kpis = None

    logger.exception(
        "Dashboard KPI service failed to load: %s",
        exc,
    )


# ============================================================
# DEFAULT KPI STRUCTURE
# ============================================================

DEFAULT_KPIS = {
    "customers": 0,
    "orders": 0,
    "invoiced": 0.0,
    "collected": 0.0,
    "products": 0,
    "stock_kg": 0.0,
    "milling_batches": 0,
    "packaging_batches": 0,
}


# ============================================================
# LOAD KPIs
# ============================================================

def load_kpis():
    """
    Safely load dashboard KPIs.

    If the KPI service is unavailable, the dashboard remains
    operational and displays zero values instead of crashing.
    """

    if not KPI_SERVICE_AVAILABLE:

        logger.warning(
            "Dashboard KPI service is unavailable."
        )

        return DEFAULT_KPIS.copy()

    try:

        data = get_kpis()

        if not isinstance(data, dict):

            logger.warning(
                "get_kpis() did not return a dictionary."
            )

            return DEFAULT_KPIS.copy()

        kpis = DEFAULT_KPIS.copy()

        for key in kpis:

            if key in data and data[key] is not None:

                kpis[key] = data[key]

        return kpis

    except Exception as exc:

        logger.exception(
            "Unable to load dashboard KPIs: %s",
            exc,
        )

        return DEFAULT_KPIS.copy()


# ============================================================
# FORMAT CURRENCY
# ============================================================

def format_currency(value):
    """
    Format ERP currency values.

    Current default display is USD.
    This can later be changed to UGX when the finance
    configuration is finalized.
    """

    try:

        return f"${float(value):,.2f}"

    except (TypeError, ValueError):

        return "$0.00"


# ============================================================
# FORMAT NUMBER
# ============================================================

def format_number(value, decimals=1):

    try:

        return f"{float(value):,.{decimals}f}"

    except (TypeError, ValueError):

        return f"{0:,.{decimals}f}"


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_home():

    # --------------------------------------------------------
    # PAGE HEADER
    # --------------------------------------------------------

    st.title("🌾 Esan ERP")

    st.caption(
        "Enterprise Milling & Packaging Management System"
    )

    st.markdown(
        "### 🏠 Overview"
    )

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    kpis = load_kpis()

    # --------------------------------------------------------
    # COMMERCIAL KPIs
    # --------------------------------------------------------

    st.markdown("#### 📊 Commercial Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Customers",
            f"{int(kpis['customers']):,}",
        )

    with col2:

        st.metric(
            "Sales Orders",
            f"{int(kpis['orders']):,}",
        )

    with col3:

        st.metric(
            "Invoiced",
            format_currency(kpis["invoiced"]),
        )

    with col4:

        st.metric(
            "Collected",
            format_currency(kpis["collected"]),
        )

    # --------------------------------------------------------
    # OPERATIONS KPIs
    # --------------------------------------------------------

    st.markdown("#### 🏭 Operations Overview")

    col5, col6, col7, col8 = st.columns(4)

    with col5:

        st.metric(
            "Products",
            f"{int(kpis['products']):,}",
        )

    with col6:

        st.metric(
            "Stock",
            f"{format_number(kpis['stock_kg'])} Kg",
        )

    with col7:

        st.metric(
            "Milling Batches",
            f"{int(kpis['milling_batches']):,}",
        )

    with col8:

        st.metric(
            "Packaging Batches",
            f"{int(kpis['packaging_batches']):,}",
        )

    # --------------------------------------------------------
    # FACTORY STATUS
    # --------------------------------------------------------

    st.markdown("---")

    st.markdown("#### 🏭 Factory Status")

    status_col1, status_col2, status_col3 = st.columns(3)

    with status_col1:

        st.success(
            "🟢 Milling Line 1\n\n"
            "Running"
        )

    with status_col2:

        st.success(
            "🟢 Warehouse\n\n"
            "Operational"
        )

    with status_col3:

        st.warning(
            "🟡 Packaging Line\n\n"
            "Maintenance Scheduled"
        )

    # --------------------------------------------------------
    # SYSTEM STATUS
    # --------------------------------------------------------

    if not KPI_SERVICE_AVAILABLE:

        st.info(
            "ℹ️ Dashboard is running, but the KPI service "
            "is currently unavailable. KPI values will remain "
            "at zero until the dashboard service is restored."
        )