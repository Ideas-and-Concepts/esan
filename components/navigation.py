"""
Esan ERP Navigation
Nile Harvest Foods Ltd.
"""

import streamlit as st


def esan_navigation():

    # Logo area
    st.sidebar.markdown(
        """
        <div style="text-align:center;">
            <h1>🌾</h1>
            <h2>ESAN ERP</h2>
            <p>Nile Harvest Foods Ltd.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


    st.sidebar.divider()


    menu = st.sidebar.selectbox(

        "Navigation",

        [

            "🏠 Dashboard",

            "🌾 Procurement",

            "📦 Warehouse",

            "🏭 Milling",

            "📦 Packaging",

            "🚚 Sales & Distribution",

            "💰 Finance",

            "📊 Reports",

            "⚙ Settings"

        ]

    )


    st.sidebar.divider()


    st.sidebar.caption(
        "Enterprise Milling & Packaging Management System"
    )


    return menu