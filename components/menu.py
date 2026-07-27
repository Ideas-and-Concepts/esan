import streamlit as st

def main_menu():

    return st.segmented_control(
        "Navigation",
        [
            "🏠 Home",
            "🌾 Procurement",
            "📦 Warehouse",
            "🏭 Milling",
            "📦 Packaging",
            "🚚 Sales",
            "💰 Finance",
            "📊 Reports",
            "⚙ Admin"
        ],
        default="🏠 Home"
    )