"""
Esan ERP Procurement Dashboard
Nile Harvest Foods Ltd.
"""

import streamlit as st

from modules.procurement.suppliers import suppliers_page

# Purchase Orders is loaded safely so that a problem there
# does not prevent the Procurement Dashboard from opening.
try:
    from modules.procurement.purchase_orders import purchase_orders_page
except Exception as e:
    purchase_orders_page = None
    st.session_state.setdefault("procurement_purchase_order_error", str(e))


def procurement_dashboard():
    """
    Main Procurement Dashboard.

    Contains:
    - Suppliers
    - Purchase Orders
    """

    st.title("🌾 Procurement Management")
    st.caption("Manage agricultural suppliers and purchase orders.")

    tab1, tab2 = st.tabs(
        [
            "👨‍🌾 Suppliers",
            "📄 Purchase Orders",
        ]
    )

    # ==================================================
    # SUPPLIERS
    # ==================================================

    with tab1:
        try:
            suppliers_page()
        except Exception as e:
            st.error("Unable to load Supplier Management.")
            st.exception(e)

    # ==================================================
    # PURCHASE ORDERS
    # ==================================================

    with tab2:
        if purchase_orders_page:
            try:
                purchase_orders_page()
            except Exception as e:
                st.error("Unable to load Purchase Orders.")
                st.exception(e)
        else:
            st.warning(
                "Purchase Orders module is not available yet."
            )

            error = st.session_state.get(
                "procurement_purchase_order_error"
            )

            if error:
                with st.expander("Technical information"):
                    st.code(error)