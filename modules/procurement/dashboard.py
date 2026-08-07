"""
Esan ERP Procurement Dashboard

Nile Harvest Foods Ltd.
"""

import streamlit as st

from modules.procurement.suppliers import suppliers_page
from modules.procurement.purchase_orders import purchase_orders_page


def procurement_dashboard():

    st.title("🌾 Procurement Management")


    tab1, tab2 = st.tabs(
        [
            "👨‍🌾 Suppliers",
            "📄 Purchase Orders"
        ]
    )


    with tab1:

        suppliers_page()



    with tab2:

        purchase_orders_page()