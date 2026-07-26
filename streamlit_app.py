"""
Esan ERP - Streamlit Application
Nile Harvest Foods Ltd.
Version 1.0.0 Alpha
"""

import streamlit as st
from datetime import datetime

from config import (
    APP_NAME,
    COMPANY_NAME,
    VERSION
)

from database import Base, engine


# -----------------------------
# Database Initialisation
# -----------------------------

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    st.error("Database initialization failed")
    st.exception(e)


# -----------------------------
# Page Configuration
# -----------------------------

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# -----------------------------
# Company Header
# -----------------------------

st.title("🌾 Esan ERP")

st.subheader(
    COMPANY_NAME
)

st.caption(
    f"Enterprise Milling & Packaging Management System | {VERSION}"
)


# -----------------------------
# Sidebar Navigation
# -----------------------------

st.sidebar.image(
    "assets/logo.png",
    width=150
)

st.sidebar.title(
    "Esan Control Centre"
)


menu = st.sidebar.selectbox(
    "Navigate",
    [
        "Dashboard",
        "Procurement",
        "Warehouse",
        "Milling",
        "Packaging",
        "Sales",
        "Finance",
        "Logistics",
        "HR",
        "Maintenance",
        "Reports",
        "AI Assistant",
        "Settings"
    ]
)


# -----------------------------
# Dashboard
# -----------------------------

if menu == "Dashboard":

    st.header(
        "📊 Executive Dashboard"
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:
        st.metric(
            "Production Today",
            "0 tonnes"
        )


    with col2:
        st.metric(
            "Raw Material Stock",
            "0 tonnes"
        )


    with col3:
        st.metric(
            "Sales Today",
            "UGX 0"
        )


    with col4:
        st.metric(
            "Machine Status",
            "Online"
        )


    st.divider()


    st.subheader(
        "Operational Summary"
    )


    data = {
        "Area": [
            "Milling",
            "Packaging",
            "Warehouse",
            "Distribution"
        ],
        "Status": [
            "Ready",
            "Ready",
            "Ready",
            "Ready"
        ]
    }


    st.table(data)


# -----------------------------
# Other Modules
# -----------------------------

else:

    st.header(
        f"📁 {menu}"
    )


    st.info(
        f"{menu} module is under development."
    )


# -----------------------------
# Footer
# -----------------------------

st.divider()

st.caption(
    f"© {datetime.now().year} Nile Harvest Foods Ltd. | Powered by Esan ERP"
)