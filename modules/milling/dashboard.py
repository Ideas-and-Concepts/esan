"""
Esan ERP Milling Dashboard
Nile Harvest Foods Ltd.
"""

import streamlit as st

from modules.milling.batches import milling_batches_page
from modules.milling.production import production_page


def milling_dashboard():

    st.title("🏭 Milling Management")


    tab1, tab2 = st.tabs(
        [
            "🌽 Milling Batches",
            "⚙️ Production"
        ]
    )


    with tab1:
        milling_batches_page()


    with tab2:
        production_page()