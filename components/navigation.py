import streamlit as st


def floating_menu():

    menu = st.radio(

        "",

        [

        "🏠 Dashboard",
        "🌾 Procurement",
        "📦 Warehouse",
        "🏭 Milling",
        "📦 Packaging",
        "🚚 Sales & Distribution",
        "💰 Finance",
        "📊 Reports"

        ],

        horizontal=True

    )

    return menu