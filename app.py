"""
Esan ERP Main Application
"""

import streamlit as st

from config import (
    APP_NAME,
    COMPANY_NAME,
    VERSION
)


st.set_page_config(
    page_title=APP_NAME,
    layout="wide"
)


st.title(APP_NAME)

st.subheader(
    COMPANY_NAME
)

st.caption(
    f"Version {VERSION}"
)


st.sidebar.title(
    "Esan Modules"
)


modules = [
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


for module in modules:

    st.sidebar.button(
        module
    )


st.header(
    "Executive Overview"
)


col1, col2, col3 = st.columns(3)


with col1:
    st.metric(
        "Production Today",
        "0 tonnes"
    )


with col2:
    st.metric(
        "Inventory",
        "0 tonnes"
    )


with col3:
    st.metric(
        "Revenue",
        "UGX 0"
    )


st.info(
    "Esan ERP foundation is running successfully."
)