"""
Esan ERP - Streamlit Application
Nile Harvest Foods Ltd.
Version 1.0.0 Alpha
"""

import os
from datetime import datetime

import streamlit as st

from config import (
    APP_NAME,
    COMPANY_NAME,
    VERSION
)

from database import (
    Base,
    engine,
    SessionLocal
)

from services.user_service import create_admin


# =====================================
# DATABASE INITIALIZATION
# =====================================

try:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    create_admin(db)
    db.close()

except Exception as e:
    st.error("Database initialization failed")
    st.exception(e)


# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================
# HEADER
# =====================================

st.title("🌾 Esan ERP")

st.subheader(
    COMPANY_NAME
)

st.caption(
    f"Enterprise Milling & Packaging Management System | {VERSION}"
)


# =====================================
# SIDEBAR
# =====================================

logo_path = "assets/logo.png"

if os.path.exists(logo_path):
    st.sidebar.image(
        logo_path,
        width=150
    )
else:
    st.sidebar.markdown(
        "🌾 **ESAN ERP**"
    )


st.sidebar.divider()

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


# =====================================
# DASHBOARD
# =====================================

if menu == "Dashboard":

    st.header(
        "📊 Executive Dashboard"
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:
        st.metric(
            "Production Today",
            "0 Tonnes"
        )


    with col2:
        st.metric(
            "Raw Material Stock",
            "0 Tonnes"
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
        "🏭 Plant Operations"
    )


    operations = {
        "Department": [
            "Procurement",
            "Warehouse",
            "Milling",
            "Packaging",
            "Distribution"
        ],

        "Status": [
            "Ready",
            "Ready",
            "Ready",
            "Ready",
            "Ready"
        ]
    }


    st.table(
        operations
    )


# =====================================
# OTHER MODULES
# =====================================

else:

    st.header(
        f"📁 {menu}"
    )

    st.info(
        f"{menu} module will be activated in the next Esan development sprint."
    )


# =====================================
# FOOTER
# =====================================

st.divider()

st.caption(
    f"© {datetime.now().year} Nile Harvest Foods Ltd. | Powered by Esan ERP"
)