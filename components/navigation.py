"""
Navigation Component
Esan ERP - Sidebar Menu
"""

import streamlit as st

def esan_navigation():
    """Render sidebar navigation and return selected menu item."""

    menu_options = {
        "🏠 Overview": "Overview",
        "🌾 Procurement": "🌾 Procurement",
        "📦 Warehouse": "📦 Warehouse",
        "🏭 Milling": "🏭 Milling",
        "📦 Packaging": "📦 Packaging",
        "🚚 Sales": "🚚 Sales",
        "💰 Finance": "💰 Finance",
        "🚚 Logistics": "🚚 Logistics",
        "👥 HR & Employees": "👥 HR & Employees",
        "🔧 Maintenance": "🔧 Maintenance",
        "📊 Reports": "📊 Reports",
        "🤖 AI Assistant": "🤖 AI Assistant",
    }

    # Admin‑only items
    if st.session_state.get("role", "user") == "Administrator":
        menu_options["🔐 Administration"] = "🔐 Administration"

    # Use a selectbox for the sidebar
    choice = st.sidebar.selectbox(
        "Navigation",
        list(menu_options.keys()),
        format_func=lambda x: x  # show icon + label
    )
    return menu_options[choice]