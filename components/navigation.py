"""
Esan ERP Navigation
Nile Harvest Foods Ltd.
"""
import streamlit as st


def esan_navigation():

    menu = st.sidebar.radio(

        "Navigation",

        [

            "Overview",

            "🌾 Procurement",

            "📦 Warehouse",

            "🏭 Milling",

            "📦 Packaging",

            "🚚 Sales & Distribution",

            "💰 Finance",

            "📊 Reports"

        ]

    )

    return menu