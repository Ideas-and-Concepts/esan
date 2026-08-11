"""
Esan ERP Procurement Dashboard

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

import logging
import streamlit as st

logger = logging.getLogger(name)

==================================================

SAFE MODULE IMPORT

==================================================

def _safe_import(module_path, function_name):
"""
Safely import a procurement submodule.

Returns:
    callable | None
"""
try:
    module = __import__(
        module_path,
        fromlist=[function_name]
    )

    function = getattr(module, function_name, None)

    if function is None:
        logger.warning(
            "%s does not contain %s",
            module_path,
            function_name
        )

    return function

except Exception as e:
    logger.exception(
        "Failed to load %s.%s: %s",
        module_path,
        function_name,
        e
    )
    return None

==================================================

LOAD PROCUREMENT SUBMODULES

==================================================

suppliers_page = _safe_import(
"modules.procurement.suppliers",
"suppliers_page"
)

purchase_orders_page = _safe_import(
"modules.procurement.purchase_orders",
"purchase_orders_page"
)

==================================================

FALLBACK PAGE

==================================================

def _module_unavailable(module_name):
"""
Display a controlled message when a procurement
submodule cannot be loaded.
"""

st.warning(
    f"⚠️ {module_name} is currently unavailable."
)

st.caption(
    "The Procurement module is loaded, but this "
    "submodule needs to be fixed before it can be used."
)

==================================================

PROCUREMENT DASHBOARD

==================================================

def procurement_dashboard():

st.title("🌾 Procurement Management")

st.caption(
    "Manage suppliers, agricultural procurement, "
    "purchase orders and incoming materials."
)

st.divider()

# ==================================================
# PROCUREMENT SUMMARY
# ==================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Suppliers",
        "0"
    )

with col2:
    st.metric(
        "Purchase Orders",
        "0"
    )

with col3:
    st.metric(
        "Pending Orders",
        "0"
    )

with col4:
    st.metric(
        "Procurement Value",
        "UGX 0"
    )

st.divider()

# ==================================================
# PROCUREMENT TABS
# ==================================================

tab1, tab2 = st.tabs(
    [
        "👨‍🌾 Suppliers",
        "📄 Purchase Orders"
    ]
)

# ==================================================
# SUPPLIERS
# ==================================================

with tab1:

    if suppliers_page:

        try:
            suppliers_page()

        except Exception as e:

            logger.exception(
                "Suppliers module failed: %s",
                e
            )

            st.error(
                "The Suppliers module encountered an error."
            )

    else:

        _module_unavailable(
            "Suppliers"
        )

# ==================================================
# PURCHASE ORDERS
# ==================================================

with tab2:

    if purchase_orders_page:

        try:
            purchase_orders_page()

        except Exception as e:

            logger.exception(
                "Purchase Orders module failed: %s",
                e
            )

            st.error(
                "The Purchase Orders module encountered an error."
            )

    else:

        _module_unavailable(
            "Purchase Orders"
        )