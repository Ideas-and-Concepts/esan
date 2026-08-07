"""
Esan ERP Packaging Dashboard
Nile Harvest Foods Ltd.
"""

import streamlit as st

from modules.packaging.batches import packaging_batches_page
from modules.packaging.production import packaging_production_page


def packaging_dashboard():

    st.title("📦 Packaging Management")


    tab1, tab2 = st.tabs(
        [
            "📦 Packaging Batches",
            "⚙️ Production"
        ]
    )


    with tab1:
        packaging_batches_page()


    with tab2:
        packaging_production_page()