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

from database import Base, engine, SessionLocal


try:

    Base.metadata.create_all(
        bind=engine
    )

except Exception as e:

    st.error(
        "Database startup error"
    )

    st.exception(e)

from models import User

from auth import verify_password

from services.user_service import create_admin

from pathlib import Path

css_file = Path("assets/style.css")

if css_file.exists():
    with open(css_file) as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

from components.dashboard_cards import (
    kpi_card,
    factory_status,
    notification
)

st.subheader(
    "🏭 Factory Control Centre"
)


status1, status2 = st.columns(2)


with status1:

    factory_status(
        "Milling Line 1",
        "Running"
    )

    factory_status(
        "Milling Line 2",
        "Running"
    )

    factory_status(
        "Packaging Line",
        "Warning"
    )


with status2:

    factory_status(
        "Raw Material Warehouse",
        "Running"
    )

    factory_status(
        "Dispatch Yard",
        "Running"
    )

    factory_status(
        "Maintenance",
        "Warning"
    )

st.subheader(
    "🔔 Notifications"
)


alerts = [
    "New maize delivery expected today",
    "Packaging material below reorder level",
    "Production batch MB-001 completed",
    "Truck scheduled for Juba dispatch"
]


for alert in alerts:

    notification(alert)

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

st.subheader(
    "📊 Business Overview"
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    kpi_card(
        "Production",
        "128 Tonnes",
        "+12%",
        "🌾"
    )


with col2:

    kpi_card(
        "Sales Today",
        "UGX 45.2M",
        "+8%",
        "💰"
    )


with col3:

    kpi_card(
        "Inventory",
        "685 Tonnes",
        "+5%",
        "📦"
    )


with col4:

    kpi_card(
        "Orders",
        "24",
        "+3",
        "🚚"
    )

# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌾",
    layout="wide"
)


# =====================================
# SESSION STATE
# =====================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None


# =====================================
# LOGIN FUNCTION
# =====================================

def login(username, password):

    db = SessionLocal()

    user = (
        db.query(User)
        .filter(
            User.username == username
        )
        .first()
    )

    db.close()


    if user:

        if verify_password(
            password,
            user.password_hash
        ):

            st.session_state.logged_in = True
            st.session_state.username = user.username
            st.session_state.role = user.role

            return True

    return False



# =====================================
# LOGIN PAGE
# =====================================

if not st.session_state.logged_in:

    st.title("🌾 Esan ERP")

    st.subheader(
        COMPANY_NAME
    )

    st.write(
        "Please login to access the management system."
    )


    username = st.text_input(
        "Username"
    )


    password = st.text_input(
        "Password",
        type="password"
    )


    if st.button("Login"):

        if login(
            username,
            password
        ):

            st.success(
                "Login successful"
            )

            st.rerun()

        else:

            st.error(
                "Invalid username or password"
            )


    st.info(
        "Default administrator: admin / admin123"
    )


    st.stop()



# =====================================
# MAIN APPLICATION
# =====================================

st.title("🌾 Esan ERP")

st.subheader(
    COMPANY_NAME
)


st.sidebar.success(
    f"User: {st.session_state.username}"
)

st.sidebar.info(
    f"Role: {st.session_state.role}"
)


if st.sidebar.button("Logout"):

    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

    st.rerun()



# =====================================
# NAVIGATION
# =====================================

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
        "Reports",
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


    c1, c2, c3, c4 = st.columns(4)


    c1.metric(
        "Production Today",
        "0 Tonnes"
    )

    c2.metric(
        "Raw Materials",
        "0 Tonnes"
    )

    c3.metric(
        "Sales",
        "UGX 0"
    )

    c4.metric(
        "Machine Status",
        "Online"
    )


else:

    st.header(
        f"📁 {menu}"
    )

    st.info(
        f"{menu} module will be developed in the next phase."
    )



st.divider()

st.caption(
    f"© {datetime.now().year} Nile Harvest Foods Ltd. | Esan ERP"
)